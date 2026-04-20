from flask import Blueprint, request, jsonify
from typing import Dict, List
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.nutrition_profile import NutritionProfile
from app.ml_services.nutrition_model import NutritionModel
from app.ml_services.xgb_recommender import XGBNutritionRecommender
from app.ml_services.dnn_recommender import DNNNutritionRecommender
from app.utils.permissions import require_permission, patient_data_access_required
from app.utils.database import mongo
from datetime import datetime, timedelta
import sys

nutrition_bp = Blueprint('nutrition', __name__)
nutrition_model = NutritionModel()
xgb_recommender = XGBNutritionRecommender()
dnn_recommender = DNNNutritionRecommender()

def generate_meal_plan(user_data: Dict) -> List[Dict]:
    """Generate a meal plan based on user preferences."""
    # This would typically come from a more comprehensive meal planning service or database
    # For now, using a simple rule-based approach with filtering

    all_meal_suggestions = [
        {
            'meal_type': 'Breakfast',
            'suggestions': [
                'Oats with nuts and fruits',
                'Poha with vegetables',
                'Idli with sambar',
                'Scrambled eggs with spinach',
                'Greek yogurt with berries',
                'Smoothie with protein powder'
            ]
        },
        {
            'meal_type': 'Lunch',
            'suggestions': [
                'Brown rice with dal and vegetables',
                'Roti with sabzi and curd',
                'Quinoa pulao with raita',
                'Grilled chicken salad',
                'Lentil soup with whole grain bread',
                'Fish curry with rice'
            ]
        },
        {
            'meal_type': 'Dinner',
            'suggestions': [
                'Khichdi with vegetables',
                'Chapati with dal and sabzi',
                'Vegetable soup with whole grain bread',
                'Baked salmon with roasted vegetables',
                'Paneer bhurji with roti'
            ]
        }
    ]

    filtered_meal_plan = []

    user_diet_type = user_data.get('dietType', '').lower()
    user_allergies = [a.strip().lower() for a in user_data.get('allergies', '').split(',') if a.strip()]

    # Define filtering keywords based on diet and allergies
    exclude_keywords = set()
    if user_diet_type == 'vegetarian':
        exclude_keywords.update(['chicken', 'mutton', 'fish', 'beef', 'egg'])
    elif user_diet_type == 'vegan':
        exclude_keywords.update(['chicken', 'mutton', 'fish', 'beef', 'egg', 'milk', 'curd', 'paneer', 'cheese', 'butter', 'ghee'])

    for allergy in user_allergies:
         if allergy == 'milk': exclude_keywords.update(['milk', 'curd', 'paneer', 'cheese', 'butter', 'ghee'])
         elif allergy == 'nuts': exclude_keywords.update(['nuts', 'almond', 'walnut', 'peanut', 'cashew'])
         elif allergy == 'gluten': exclude_keywords.update(['roti', 'chapati', 'paratha', 'bread'])
         # Add more allergy keywords as needed

    for meal_type_suggestions in all_meal_suggestions:
        filtered_suggestions = []
        for suggestion in meal_type_suggestions['suggestions']:
            # Check if any exclude keyword is present in the suggestion (case-insensitive)
            if not any(keyword in suggestion.lower() for keyword in exclude_keywords):
                filtered_suggestions.append(suggestion)

        if filtered_suggestions:
             filtered_meal_plan.append({
                 'meal_type': meal_type_suggestions['meal_type'],
                 'suggestions': filtered_suggestions
             })

    # If after filtering, a meal type has no suggestions, you might want to add a placeholder or message
    if not any(meal['meal_type'] == 'Breakfast' for meal in filtered_meal_plan):
        filtered_meal_plan.insert(0, {'meal_type': 'Breakfast', 'suggestions': ['No suitable breakfast suggestions based on your preferences.']})
    if not any(meal['meal_type'] == 'Lunch' for meal in filtered_meal_plan):
         # Find the correct position to insert Lunch if Breakfast exists
         insert_idx = 1 if any(meal['meal_type'] == 'Breakfast' for meal in filtered_meal_plan) else 0
         filtered_meal_plan.insert(insert_idx, {'meal_type': 'Lunch', 'suggestions': ['No suitable lunch suggestions based on your preferences.']})
    if not any(meal['meal_type'] == 'Dinner' for meal in filtered_meal_plan):
         # Find the correct position to insert Dinner
         insert_idx = 2 if any(meal['meal_type'] == 'Breakfast' for meal in filtered_meal_plan) + any(meal['meal_type'] == 'Lunch' for meal in filtered_meal_plan) == 2 else len(filtered_meal_plan)
         filtered_meal_plan.insert(insert_idx, {'meal_type': 'Dinner', 'suggestions': ['No suitable dinner suggestions based on your preferences.']})

    # Sort to ensure consistent order (Breakfast, Lunch, Dinner)
    order = {'Breakfast': 0, 'Lunch': 1, 'Dinner': 2}
    filtered_meal_plan.sort(key=lambda x: order.get(x['meal_type'], 99))

    return filtered_meal_plan

@nutrition_bp.route('/predict', methods=['POST'])
@jwt_required()
@require_permission('access_nutrition_tools')
def predict_nutrition():
    try:
        print("Received nutrition prediction request.", file=sys.stderr)
        data = request.get_json()
        print(f"Request data: {data}", file=sys.stderr)
        user_id = get_jwt_identity()
        print(f"User ID from JWT: {user_id}", file=sys.stderr)
        
        # Validate required fields
        required_fields = ['breastfeeding', 'dietType', 'allergies', 'deficiency', 'preferredCuisine']
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}", file=sys.stderr)
                return jsonify({'error': f'Missing required field: {field}'}), 400
        # Compute sentiment from daily check-ins so each entry impacts scoring.
        # We use a recency-weighted average over 7 days and also capture the latest mood.
        sent_last7_avg = None
        sent_current = None
        latest_mood = None
        latest_mood_ts = None
        sentiment_source = None
        try:
            start_dt = datetime.utcnow() - timedelta(days=7)
            now_dt = datetime.utcnow()
            mood_to_sent = {1: -0.8, 2: -0.4, 3: 0.0, 4: 0.3, 5: 0.6}
            # Pull recent check-ins with valid mood only
            mood_docs = list(mongo.db.daily_checkins.aggregate([
                { '$match': { 'user_id': str(user_id) } },
                { '$addFields': { 'ts': { '$toDate': '$timestamp' } } },
                { '$match': { 'ts': { '$gte': start_dt }, 'mood': { '$in': [1,2,3,4,5] } } },
                { '$project': { '_id': 0, 'mood': 1, 'ts': 1 } },
                { '$sort': { 'ts': 1 } }
            ]))
            if mood_docs:
                import math
                # Exponential recency weighting with 3-day half-life
                half_life_days = 3.0
                lam = math.log(2) / half_life_days
                weights = []
                sents = []
                for d in mood_docs:
                    ts = d.get('ts')
                    mood = int(d.get('mood', 0))
                    if ts is None or mood not in mood_to_sent:
                        continue
                    days_ago = max(0.0, (now_dt - ts).total_seconds() / 86400.0)
                    w = math.exp(-lam * days_ago)
                    weights.append(w)
                    sents.append(mood_to_sent[mood])
                if weights:
                    num = sum(w * s for w, s in zip(weights, sents))
                    den = sum(weights)
                    sent_last7_avg = float(num / den) if den > 0 else None
                    sentiment_source = 'daily_checkins_weighted'
                # latest mood (most recent document)
                last_doc = mood_docs[-1]
                latest_mood = int(last_doc.get('mood')) if last_doc.get('mood') is not None else None
                latest_mood_ts = last_doc.get('ts')
                if latest_mood in mood_to_sent:
                    sent_current = float(mood_to_sent[latest_mood])
            if sent_last7_avg is None:
                # Fallback: chats sentiments (simple mean)
                chat_pipeline = [
                    { '$match': { 'user_id': user_id } },
                    { '$unwind': '$messages' },
                    { '$match': {
                        'messages.sender': 'user',
                        'messages.timestamp': { '$gte': start_dt },
                        'messages.sentiment.score': { '$exists': True }
                    }},
                    { '$group': {
                        '_id': None,
                        'avg': { '$avg': '$messages.sentiment.score' },
                        'n': { '$sum': 1 }
                    }}
                ]
                agg = list(mongo.db.chats.aggregate(chat_pipeline))
                if agg and agg[0].get('n', 0) > 0:
                    sent_last7_avg = float(agg[0]['avg'])
                    sentiment_source = 'chats'
        except Exception as e:
            print(f"[Nutrition] Sentiment aggregation failed: {e}", file=sys.stderr)
            sent_last7_avg = None
            sent_current = None
            latest_mood = None
            latest_mood_ts = None
            sentiment_source = None

        # Inject sentiment feature into user dict for recommender
        user_with_sent = dict(data)
        if sent_last7_avg is not None:
            user_with_sent['sent_last7_avg'] = sent_last7_avg
        if sent_current is not None:
            user_with_sent['sent_current'] = sent_current

        # Force DNN-only engine; do not fallback to XGB
        model_pref = str(data.get('model', 'dnn')).lower()
        if model_pref != 'dnn':
            model_pref = 'dnn'
        if not getattr(dnn_recommender, 'available', False):
            return jsonify({'error': 'DNN model not available. Train the model first (ml/training_scripts/train_dnn_ranker.py).'}), 503
        engine_label = 'dnn'
        engine = dnn_recommender

        print(f"Generating {engine_label.upper()}-based food recommendations...", file=sys.stderr)
        recs = engine.recommend(user_with_sent, top_k=20)
        print(f"Top {len(recs)} recommendations generated.", file=sys.stderr)

        # Build AI insights (non-KNN) from recommendations
        def_nutrient_map = {
            'iron': 'Iron, Fe',
            'b12': 'Vitamin B-12',
            'calcium': 'Calcium, Ca',
            'vitamin_d': 'Vitamin D (D2 + D3)',
            'folate': 'Folate, total',
            'zinc': 'Zinc, Zn',
        }
        top_for_stats = recs[:10] if len(recs) > 10 else recs
        # rda coverage
        rda_cov = []
        if top_for_stats:
            # collect per nutrient rda_pct
            by_nutr = {}
            for r in top_for_stats:
                for n in r.get('nutrients', []):
                    by_nutr.setdefault(n['name'], []).append(float(n.get('rda_pct', 0)))
            for name, vals in by_nutr.items():
                try:
                    avg_pct = sum(vals)/len(vals)
                except ZeroDivisionError:
                    avg_pct = 0.0
                rda_cov.append({'nutrient': name, 'avg_pct': round(avg_pct, 1)})

        # deficiency focus (support list or single string) with alias mapping
        def_raw = data.get('deficiency', [])
        if isinstance(def_raw, str):
            # allow comma-separated values
            parts = [p.strip() for p in def_raw.split(',')] if def_raw else []
            def_list = [p for p in parts if p] if parts else ([] if def_raw.lower() in ('', 'none') else [def_raw])
        else:
            def_list = list(def_raw)

        # map common aliases used by the UI
        alias_to_key = {
            'iron': 'iron', 'fe': 'iron',
            'b12': 'b12', 'vitamin b12': 'b12', 'cobalamin': 'b12',
            'calcium': 'calcium', 'ca': 'calcium',
            'vitamin d': 'vitamin_d', 'vit d': 'vitamin_d', 'vitamin_d': 'vitamin_d', 'd3': 'vitamin_d',
            'folate': 'folate', 'b9': 'folate',
            'zinc': 'zinc', 'zn': 'zinc',
        }

        def_focus_list = []
        seen_targets = set()
        for d in def_list:
            d_norm = str(d).strip().lower()
            canonical = alias_to_key.get(d_norm, d_norm)
            key = def_nutrient_map.get(canonical)
            if not key or canonical in seen_targets:
                continue
            ranked = []
            for r in recs:
                match = next((n for n in r.get('nutrients', []) if n.get('name') == key), None)
                if match:
                    ranked.append({
                        'description': r.get('description',''),
                        'amount': match.get('amount', 0),
                        'unit': match.get('unit',''),
                        'rda_pct': match.get('rda_pct', 0)
                    })
            ranked.sort(key=lambda x: float(x.get('rda_pct', 0)), reverse=True)
            def_focus_list.append({
                'target': canonical,
                'nutrient_key': key,
                'top_foods': ranked[:3]
            })
            seen_targets.add(canonical)

        # model confidence stats
        scores = [float(r.get('score', 0)) for r in recs]
        if scores:
            scores_sorted = sorted(scores)
            mid = len(scores)//2
            median = (scores_sorted[mid] if len(scores)%2==1 else (scores_sorted[mid-1]+scores_sorted[mid])/2)
            model_conf = {
                'mean': round(sum(scores)/len(scores), 3),
                'median': round(median, 3),
                'high_conf_count': sum(1 for s in scores if s >= 0.9)
            }
        else:
            model_conf = {'mean': 0, 'median': 0, 'high_conf_count': 0}

        # filter impact and diversity
        meta = (engine.last_meta or {})
        diversity = {
            'unique_categories': len({r.get('category','') for r in recs if r.get('category')})
        }

        ai_insights = {
            'rda_coverage': rda_cov,
            'deficiency_focus': (def_focus_list[0] if len(def_focus_list) == 1 else def_focus_list),
            'model_confidence': model_conf,
            'filter_impact': {
                'candidates_after_filters': meta.get('candidates_after_filters'),
                'cuisine_matches': meta.get('cuisine_matches'),
                'seafood_matches': meta.get('seafood_matches')
            },
            'diversity': diversity,
            'sentiment': {
                'last7_avg': sent_last7_avg,
                'current': sent_current,
                'latest_mood': latest_mood,
                'latest_mood_time': latest_mood_ts.isoformat() if latest_mood_ts else None,
                'source': sentiment_source,
                'adjustment': (engine.last_meta or {}).get('sentiment_adjustment') if hasattr(engine, 'last_meta') else None
            }
        }
        
        print("Generating rule-based recommendations...", file=sys.stderr)
        # Generate recommendations based on user input (existing logic)
        recommendations = generate_recommendations(data)
        print("Rule-based recommendations generated.", file=sys.stderr)
        
        print("Generating meal plan...", file=sys.stderr)
        # Generate meal plan based on user input (updated logic)
        meal_plan = generate_meal_plan(data)
        print("Meal plan generated.", file=sys.stderr)
        
        print(f"Attempting to save/update profile for user ID: {user_id}", file=sys.stderr)
        # Save or update user profile
        profile = NutritionProfile(user_id)
        existing_profile = profile.get_profile()
        if existing_profile:
            print("Existing profile found, updating...", file=sys.stderr)
            profile.update_profile(data)
            print("Profile updated.", file=sys.stderr)
        else:
            print("No existing profile found, creating...", file=sys.stderr)
            profile.create_profile(data)
            print("Profile created.", file=sys.stderr)
        
        print("Returning success response.", file=sys.stderr)
        # You might want to structure the response to clearly separate ML predictions
        # from the generated recommendations and meal plan if they serve different purposes
        return jsonify({
            'recommendations': recommendations,
            'meal_plan': meal_plan,
            'model_used': engine_label,
            'xgb_recommendations': recs,
            'ai_insights': ai_insights
        })

    except Exception as e:
        print(f"An error occurred during nutrition prediction: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': 'Failed to generate nutrition recommendations'}), 500

@nutrition_bp.route('/track', methods=['POST'])
@jwt_required()
def track_progress():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        required_fields = ['category', 'value']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        profile = NutritionProfile(user_id)
        profile.track_progress(data['category'], data['value'])
        
        return jsonify({'message': 'Progress tracked successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@nutrition_bp.route('/progress/<category>', methods=['GET'])
@jwt_required()
def get_progress(category):
    try:
        user_id = get_jwt_identity()
        profile = NutritionProfile(user_id)
        progress_data = profile.get_progress_history(category)
        
        return jsonify({'progress': progress_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@nutrition_bp.route('/meal-plan', methods=['GET'])
@jwt_required()
@require_permission('view_own_meal_plans')
def get_meal_plan():
    # This route is separate from the predict route, and would typically fetch
    # a pre-generated or saved meal plan. If we want it to be dynamic based on current
    # preferences, it might need to accept preferences or fetch the user's saved profile.
    try:
        user_id = get_jwt_identity()
        profile = NutritionProfile(user_id)
        user_profile_data = profile.get_profile()

        if not user_profile_data:
            return jsonify({'error': 'Profile not found'}), 404

        # Build meal plan from XGB model recommendations when available,
        # otherwise fall back to the rule-based planner used by predict().
        recs = xgb_recommender.recommend(user_profile_data, top_k=15) if getattr(xgb_recommender, 'available', False) else []
        if not recs:
            meal_plan = generate_meal_plan(user_profile_data)
            return jsonify({'meal_plan': meal_plan, 'source': 'rule-based'})

        # Map top foods into Breakfast/Lunch/Dinner buckets (simple round-robin)
        buckets = {'Breakfast': [], 'Lunch': [], 'Dinner': []}
        order = ['Breakfast', 'Lunch', 'Dinner']
        for i, r in enumerate(recs):
            buckets[order[i % 3]].append(r.get('description', f"Food #{i+1}"))

        meal_plan = [
            {'meal_type': k, 'suggestions': v} for k, v in buckets.items()
        ]

        return jsonify({'meal_plan': meal_plan, 'source': 'xgb'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_recommendations(user_data: Dict) -> List[Dict]:
    recommendations = []

    # Breastfeeding recommendations
    if user_data.get('breastfeeding') == 'yes':
        recommendations.append({
            'title': 'Breastfeeding Nutrition',
            'description': 'Increase your daily caloric intake by ~500 kcal and ensure ample fluids. Emphasize omega-3 sources (flaxseed, walnuts, fatty fish if non-veg) and calcium-rich foods (dairy, ragi, sesame).'
        })
    elif user_data.get('breastfeeding') == 'no':
        # Provide a completely different focus than the breastfeeding path
        recommendations.append({
            'title': 'Postpartum Recovery (Not Breastfeeding)',
            'description': 'Aim for a steady, nutrient-dense pattern without extra calories. Build plates around whole grains (millets, brown rice), legumes (moong, chickpea, rajma), and colorful vegetables.'
        })
        recommendations.append({
            'title': 'Lean Protein & Fiber Focus',
            'description': 'Prioritize lean proteins (eggs, fish/chicken if non-veg; tofu/paneer/daal if veg) and high-fiber options (oats, whole wheat, fruits with peels) to support recovery and satiety.'
        })
        recommendations.append({
            'title': 'Micronutrient Repletion',
            'description': 'Support iron and folate repletion post-delivery with rajma, beetroot, spinach, citrus, and sprouts. Space tea/coffee away from iron-rich meals to aid absorption.'
        })

    # Diet type specific recommendations
    if user_data.get('dietType') == 'vegan':
        recommendations.append({
            'title': 'Vegan Diet Support',
            'description': 'Focus on plant-based protein sources like legumes, tofu, and quinoa. Consider supplementing with B12 and iron if needed.'
        })
    elif user_data.get('dietType') == 'vegetarian':
         recommendations.append({
            'title': 'Vegetarian Diet Support',
            'description': 'Ensure adequate intake of iron, B12, and calcium through plant-based sources or supplements.'
        })

    # Deficiency specific recommendations (support list or comma-separated string)
    def_raw = user_data.get('deficiency', [])
    if isinstance(def_raw, str):
        parts = [p.strip().lower() for p in def_raw.split(',') if p.strip()]
        def_list = parts if parts else ([def_raw.lower()] if def_raw else [])
    else:
        def_list = [str(d).strip().lower() for d in def_raw if str(d).strip()]

    # Map aliases to canonical keys
    alias_to_key = {
        'iron': 'iron',
        'fe': 'iron',
        'b12': 'b12',
        'vitamin b12': 'b12',
        'cobalamin': 'b12',
        'calcium': 'calcium',
        'ca': 'calcium',
        'vitamin d': 'vitamin_d',
        'vit d': 'vitamin_d',
        'vitamin_d': 'vitamin_d',
        'd3': 'vitamin_d',
        'folate': 'folate',
        'b9': 'folate',
        'zinc': 'zinc',
        'zn': 'zinc',
    }

    deficiency_recs = {
        'iron': {
            'title': 'Iron-Rich Foods',
            'description': 'Add iron-rich foods like spinach, lentils, kidney beans, chickpeas, tofu, pumpkin seeds, and fortified cereals. Combine with vitamin C sources (citrus, amla, bell pepper) to enhance absorption; avoid tea/coffee with iron-rich meals.'
        },
        'b12': {
            'title': 'Vitamin B12 Sources',
            'description': 'Include B12 from eggs, dairy (milk, curd, paneer), fish/lean meats, or fortified plant milks and cereals. Vegetarians/vegans may require a B12 supplement as advised by your provider.'
        },
        'calcium': {
            'title': 'Calcium Support',
            'description': 'Increase calcium with milk, curd, paneer, ragi (finger millet), sesame seeds, almonds, tofu, and leafy greens. Pair with vitamin D and space calcium and iron supplements for optimal absorption.'
        },
        'vitamin_d': {
            'title': 'Vitamin D Support',
            'description': 'Expose to safe morning sunlight 10–20 mins if possible. Add vitamin D sources like fortified milk, mushrooms (UV-exposed), egg yolk, and fatty fish (salmon, mackerel). Discuss supplementation if advised.'
        },
        'folate': {
            'title': 'Folate (B9) Support',
            'description': 'Include folate-rich foods such as lentils, chickpeas, rajma, spinach, methi, asparagus, citrus, avocado, and fortified grains. Cook lightly to preserve folate.'
        },
        'zinc': {
            'title': 'Zinc Support',
            'description': 'Add zinc sources like chickpeas, lentils, pumpkin seeds, cashews, whole grains, dairy, eggs, and seafood. Soak/sprout legumes to improve mineral bioavailability.'
        },
    }

    seen_titles = set()
    for d in def_list:
        key = alias_to_key.get(d, d)
        rec = deficiency_recs.get(key)
        if rec and rec['title'] not in seen_titles:
            recommendations.append(rec)
            seen_titles.add(rec['title'])

    # Cuisine specific recommendations (can be expanded)
    if user_data.get('preferredCuisine', '').lower() == 'indian':
        recommendations.append({
            'title': 'Indian Cuisine Recommendations',
            'description': 'Include traditional postpartum foods like ghee, moong dal, and methi. Opt for whole grain rotis and include plenty of vegetables.'
        })

    # General postpartum recommendations
    recommendations.append({
        'title': 'General Postpartum Nutrition',
        'description': 'Focus on whole foods, stay hydrated, and eat regular meals. Include a variety of fruits, vegetables, and protein sources.'
    })

    # Filter recommendations based on allergies - simple check
    user_allergies = [a.strip().lower() for a in user_data.get('allergies', '').split(',') if a.strip()]
    if user_allergies:
        filtered_recommendations = []
        for rec in recommendations:
            # Simple check: if allergy keyword is in description, exclude
            if not any(allergy in rec['description'].lower() for allergy in user_allergies):
                 filtered_recommendations.append(rec)
        recommendations = filtered_recommendations

    return recommendations