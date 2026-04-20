from flask import request, jsonify
from ..models.care_plan import CarePlan
from ..models.user import User
from datetime import datetime, timedelta
from ..utils.database import mongo
import sys
import traceback

class CarePlanController:
    """Controller for Care Plan ML-powered recommendations"""
    
    @staticmethod
    def generate_care_plan():
        """Generate a new care plan for a user using ML clustering"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['user_id', 'epds_score', 'postpartum_week', 'delivery_type', 'feeding']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            # Get user information
            user = User.find_by_id(data['user_id'])
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
            
            # Prepare user profile for ML model
            user_profile = {
                'user_id': data['user_id'],
                'epds_score': data['epds_score'],
                'postpartum_week': data['postpartum_week'],
                'delivery_type': data['delivery_type'],
                'feeding': data['feeding'],
                'specific_concerns': data.get('specific_concerns', 'General recovery'),
                'delivery_date': data.get('delivery_date', datetime.now().isoformat()),
                # Add default values for enhanced ML features
                'pain_level': data.get('pain_level', 3),
                'mood_score': data.get('mood_score', 5),
                'energy_level': data.get('energy_level', 4),
                'sleep_hours': data.get('sleep_hours', 5),
                'support_level': data.get('support_level', 3),
                'age': data.get('age', 28),
                'previous_pregnancies': data.get('previous_pregnancies', 0),
                'has_complications': data.get('has_complications', False),
                'cultural_preferences': data.get('cultural_preferences', {})
            }

            # Sentiment aggregation (latest mood + 7-day recency-weighted average) with chat fallback
            sent_last7_avg = None
            sentiment_source = None
            latest_mood = None
            sent_current = None
            try:
                start_dt = datetime.utcnow() - timedelta(days=7)
                # Fetch last 7 days mood check-ins
                mood_docs = list(mongo.db.daily_checkins.find({
                    'user_id': str(data['user_id'])
                }))
                # Compute recency-weighted average in Python to mirror nutrition route behavior
                # Mapping chosen to emphasize low mood: 1:-0.8, 2:-0.4, 3:0.0, 4:0.3, 5:0.6
                mood_to_sent = {1: -0.8, 2: -0.4, 3: 0.0, 4: 0.3, 5: 0.6}
                weighted_sum = 0.0
                weight_total = 0.0
                half_life_days = 3.0
                decay_lambda = 0.6931471805599453 / half_life_days  # ln(2)/half_life
                now = datetime.utcnow()

                # Identify latest mood
                latest_ts = None
                for doc in mood_docs:
                    try:
                        ts = doc.get('timestamp')
                        # Convert to datetime if stored as string/number; attempt $toDate equivalent
                        if isinstance(ts, (int, float)):
                            ts_dt = datetime.utcfromtimestamp(ts / 1000.0 if ts > 1e12 else ts)
                        elif isinstance(ts, str):
                            ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                        else:
                            ts_dt = ts
                        if not ts_dt:
                            continue
                        if ts_dt >= start_dt:
                            mood = int(doc.get('mood', 3))
                            sent = mood_to_sent.get(mood, 0.0)
                            days_ago = (now - ts_dt).total_seconds() / 86400.0
                            w = pow(2.0, -days_ago / half_life_days)  # exponential decay
                            weighted_sum += sent * w
                            weight_total += w
                        # Track latest mood regardless (prefer the most recent)
                        if latest_ts is None or ts_dt > latest_ts:
                            latest_ts = ts_dt
                            latest_mood = int(doc.get('mood', 3))
                    except Exception:
                        continue

                if weight_total > 0:
                    sent_last7_avg = float(weighted_sum / weight_total)
                    sentiment_source = 'daily_checkins'

                if latest_mood is not None:
                    sent_current = float(mood_to_sent.get(latest_mood, 0.0))

                # Fallback to chats sentiments if no check-ins contributed
                if sent_last7_avg is None:
                    agg = list(mongo.db.chats.aggregate([
                        { '$match': { 'user_id': data['user_id'] } },
                        { '$unwind': '$messages' },
                        { '$match': {
                            'messages.sender': 'user',
                            'messages.timestamp': { '$gte': start_dt },
                            'messages.sentiment.score': { '$exists': True }
                        }},
                        { '$group': { '_id': None, 'avg': { '$avg': '$messages.sentiment.score' }, 'n': { '$sum': 1 } } }
                    ]))
                    if agg and agg[0].get('n', 0) > 0:
                        sent_last7_avg = float(agg[0]['avg'])
                        sentiment_source = 'chats'
            except Exception as e:
                print(f"[CarePlan] Sentiment aggregation failed: {e}", file=sys.stderr)

            # Blend latest and last7 to get a stable yet responsive sentiment signal
            if sent_last7_avg is not None or sent_current is not None:
                # Defaults if one is missing
                s7 = sent_last7_avg if sent_last7_avg is not None else 0.0
                sc = sent_current if sent_current is not None else s7
                sent_blended = 0.6 * s7 + 0.4 * sc
                user_profile.update({
                    'sentiment_context': {
                        'sent_last7_avg': s7,
                        'latest_mood': latest_mood,
                        'sent_current': sc,
                        'sent_blended': sent_blended,
                        'sentiment_source': sentiment_source
                    }
                })

            # Create care plan using ML model
            care_plan_id = CarePlan.create_care_plan(data['user_id'], user_profile)
            
            if care_plan_id:
                # Get the created care plan
                care_plan = CarePlan.get_care_plan_by_user_id(data['user_id'])
                
                return jsonify({
                    'success': True,
                    'message': 'Care plan generated successfully using ML clustering',
                    'care_plan_id': care_plan_id,
                    'care_plan': {
                        'cluster_id': care_plan.get('cluster_id', 0),
                        'postpartum_week': care_plan.get('postpartum_week', 4),
                        'cluster_info': care_plan.get('cluster_info', {}),
                        'weekly_priorities': care_plan.get('weekly_priorities', []),
                        'daily_tasks': care_plan.get('daily_tasks', []),
                        'resources': care_plan.get('resources', []),
                        'health_monitoring': care_plan.get('health_monitoring', {}),
                        'personalization_context': care_plan.get('personalization_context', {}),
                        'sentiment_context': care_plan.get('sentiment_context', user_profile.get('sentiment_context', {})),
                        'progress_tracking': care_plan.get('progress_tracking', {
                            'total_tasks': 0,
                            'completed_tasks': 0,
                            'completion_percentage': 0
                        })
                    }
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate care plan'
                }), 500
                
        except Exception as e:
            print(f"Error in generate_care_plan: {e}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @staticmethod
    def get_care_plan(user_id):
        """Get current care plan for a user"""
        try:
            care_plan = CarePlan.get_care_plan_by_user_id(user_id)
            
            if care_plan:
                return jsonify({
                    'success': True,
                    'care_plan': {
                        'id': str(care_plan['_id']),
                        'cluster_id': care_plan.get('cluster_id', 0),
                        'postpartum_week': care_plan.get('postpartum_week', 4),
                        'cluster_info': care_plan.get('cluster_info', {}),
                        'weekly_priorities': care_plan.get('weekly_priorities', []),
                        'daily_tasks': care_plan.get('daily_tasks', []),
                        'resources': care_plan.get('resources', []),
                        'completed_tasks': care_plan.get('completed_tasks', 0),
                        'completion_percentage': care_plan.get('completion_percentage', 0),
                        'created_at': care_plan['created_at'].isoformat(),
                        'updated_at': care_plan['updated_at'].isoformat()
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'No active care plan found for user'
                }), 404
                
        except Exception as e:
            print(f"Error in get_care_plan: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @staticmethod
    def update_task_completion():
        """Update task completion status"""
        try:
            data = request.get_json()
            print(f"Task completion request data: {data}")
            
            # Validate required fields
            required_fields = ['care_plan_id', 'task_id', 'completed']
            for field in required_fields:
                if field not in data:
                    print(f"Missing field: {field}")
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            success = CarePlan.update_task_completion(
                data['care_plan_id'],
                data['task_id'],
                data['completed']
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Task completion updated successfully'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update task completion'
                }), 400
                
        except Exception as e:
            print(f"Error in update_task_completion: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @staticmethod
    def regenerate_weekly_plan():
        """Regenerate care plan for a new week"""
        try:
            data = request.get_json()
            
            if 'user_id' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field: user_id'
                }), 400
            
            new_plan_id = CarePlan.regenerate_weekly_plan(data['user_id'])
            
            if new_plan_id:
                # Get the new care plan
                care_plan = CarePlan.get_care_plan_by_user_id(data['user_id'])
                
                return jsonify({
                    'success': True,
                    'message': 'Weekly care plan regenerated successfully',
                    'care_plan_id': new_plan_id,
                    'care_plan': {
                        'cluster_id': care_plan['cluster_id'],
                        'week_indicator': care_plan['week_indicator'],
                        'priorities': care_plan['priorities'],
                        'daily_tasks': care_plan['daily_tasks'],
                        'resources': care_plan['resources'],
                        'progress_tracking': care_plan['progress_tracking']
                    }
                }), 201
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to regenerate weekly plan'
                }), 500
                
        except Exception as e:
            print(f"Error in regenerate_weekly_plan: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @staticmethod
    def get_cluster_insights():
        """Get insights about ML clustering for admin/analytics"""
        try:
            care_plan_model = CarePlan()
            
            cluster_insights = {
                'total_clusters': len(care_plan_model.cluster_profiles),
                'cluster_profiles': {}
            }
            
            for cluster_id, profile in care_plan_model.cluster_profiles.items():
                cluster_insights['cluster_profiles'][cluster_id] = {
                    'avg_epds_score': profile.get('avg_epds_score', 0),
                    'avg_postpartum_week': profile.get('avg_postpartum_week', 0),
                    'most_common_delivery': profile.get('most_common_delivery', 'unknown'),
                    'most_common_feeding': profile.get('most_common_feeding', 'unknown'),
                    'most_common_concern': profile.get('most_common_concern', 'unknown'),
                    'high_risk_ppd_percentage': profile.get('high_risk_ppd_percentage', 0),
                    'care_focus': profile.get('care_focus', [])
                }
            
            return jsonify({
                'success': True,
                'cluster_insights': cluster_insights
            }), 200
            
        except Exception as e:
            print(f"Error in get_cluster_insights: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    @staticmethod
    def predict_user_cluster():
        """Predict which cluster a user profile belongs to"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['epds_score', 'postpartum_week', 'delivery_type', 'feeding']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400
            
            care_plan_model = CarePlan()
            cluster_id = care_plan_model.predict_cluster(data)
            cluster_profile = care_plan_model.cluster_profiles.get(cluster_id, {})
            
            return jsonify({
                'success': True,
                'predicted_cluster': cluster_id,
                'cluster_profile': {
                    'avg_epds_score': cluster_profile.get('avg_epds_score', 0),
                    'avg_postpartum_week': cluster_profile.get('avg_postpartum_week', 0),
                    'most_common_delivery': cluster_profile.get('most_common_delivery', 'unknown'),
                    'most_common_feeding': cluster_profile.get('most_common_feeding', 'unknown'),
                    'most_common_concern': cluster_profile.get('most_common_concern', 'unknown'),
                    'high_risk_ppd_percentage': cluster_profile.get('high_risk_ppd_percentage', 0),
                    'care_focus': cluster_profile.get('care_focus', [])
                }
            }), 200
            
        except Exception as e:
            print(f"Error in predict_user_cluster: {e}")
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
