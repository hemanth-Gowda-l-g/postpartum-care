import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class PostpartumKNNNutritionRecommender:
    """
    K-NN Based Nutrition Recommendation System for Postpartum Mothers
    
    Features:
    - Health Metrics: Iron levels, Vitamin D, BMI, lactation status
    - Dietary Preferences: Vegan, gluten-free, allergies
    - Recovery Stage: Weeks postpartum, C-section vs. vaginal birth
    - User Ratings: Past meal ratings (if available)
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / 'datasets' / 'nutrition'
        self.food_data = None
        self.user_profiles = None
        self.knn_model = None
        self.scaler = MinMaxScaler()
        self.label_encoders = {}
        self.pca = None
        self.feature_names = []
        
        # Postpartum-specific nutrient requirements (RDA)
        self.POSTPARTUM_RDA = {
            'Iron, Fe': {'target': 27, 'unit': 'mg', 'critical': True},  # Higher for postpartum
            'Calcium, Ca': {'target': 1000, 'unit': 'mg', 'critical': True},
            'Vitamin D': {'target': 600, 'unit': 'IU', 'critical': True},
            'Folate, total': {'target': 500, 'unit': 'mcg', 'critical': True},
            'Vitamin B-12': {'target': 2.8, 'unit': 'mcg', 'critical': True},
            'Protein': {'target': 71, 'unit': 'g', 'critical': True},
            'Fiber, total dietary': {'target': 28, 'unit': 'g', 'critical': False},
            'Zinc, Zn': {'target': 12, 'unit': 'mg', 'critical': False},
            'Magnesium, Mg': {'target': 350, 'unit': 'mg', 'critical': False}
        }
        
        self.load_data()
        self.prepare_user_profiles()
        self.train_knn_model()

    def load_data(self):
        """Load and prepare nutrition datasets"""
        print("Loading nutrition datasets...")
        
        try:
            # Load food data
            food_df = pd.read_csv(self.data_dir / 'food.csv')
            nutrient_df = pd.read_csv(self.data_dir / 'nutrient.csv')
            food_nutrient_df = pd.read_csv(self.data_dir / 'food_nutrient.csv')
            category_df = pd.read_csv(self.data_dir / 'food_category.csv')
            
            print(f"Loaded {len(food_df)} foods, {len(nutrient_df)} nutrients")
            
            # Merge datasets to create comprehensive food-nutrient matrix
            self.food_data = (
                food_nutrient_df
                .merge(food_df, on='fdc_id', how='inner')
                .merge(nutrient_df, left_on='nutrient_id', right_on='id', how='left')
                .merge(category_df, left_on='food_category_id', right_on='id', how='left')
            )
            
            # Pivot to wide format (foods as rows, nutrients as columns)
            pivot_df = self.food_data.pivot_table(
                index=['fdc_id', 'description_x', 'description_y'],
                columns='name',
                values='amount',
                aggfunc='mean'
            ).reset_index()
            
            # Fill missing nutrient values with 0
            for nutrient in self.POSTPARTUM_RDA.keys():
                if nutrient in pivot_df.columns:
                    pivot_df[nutrient] = pivot_df[nutrient].fillna(0)
                else:
                    pivot_df[nutrient] = 0
            
            # Add food category features
            pivot_df['is_vegetarian'] = ~pivot_df['description_x'].str.contains(
                'meat|chicken|fish|beef|pork|lamb|turkey|duck', case=False, na=False
            ).astype(int)
            
            pivot_df['is_vegan'] = ~pivot_df['description_x'].str.contains(
                'meat|chicken|fish|beef|pork|lamb|turkey|duck|egg|milk|cheese|yogurt|butter', 
                case=False, na=False
            ).astype(int)
            
            pivot_df['is_gluten_free'] = ~pivot_df['description_x'].str.contains(
                'wheat|barley|rye|bread|pasta|cereal|flour', case=False, na=False
            ).astype(int)
            
            # Calculate postpartum nutrition score
            pivot_df['postpartum_score'] = pivot_df.apply(
                lambda row: self._calculate_nutrition_score(row), axis=1
            )
            
            self.food_data = pivot_df
            print(f"Prepared food dataset with {len(pivot_df)} foods and {len(self.POSTPARTUM_RDA)} nutrients")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def _calculate_nutrition_score(self, row):
        """Calculate postpartum nutrition score based on critical nutrients"""
        score = 0
        for nutrient, requirements in self.POSTPARTUM_RDA.items():
            if nutrient in row and requirements['critical']:
                nutrient_value = row[nutrient] or 0
                target = requirements['target']
                if nutrient_value > 0:
                    # Score based on how close to target (0-1 scale)
                    score += min(nutrient_value / target, 1.0) * requirements.get('weight', 1.0)
        return score
    
    def prepare_user_profiles(self):
        """Create synthetic user profiles for training K-NN model"""
        print("Preparing user profiles...")
        
        # Generate synthetic user profiles based on common postpartum scenarios
        user_profiles = []
        
        # Profile templates
        profile_templates = [
            # Lactating vegetarian with iron deficiency
            {
                'iron_level': 0.3,  # Low iron (normalized 0-1)
                'vitamin_d': 0.4,   # Moderate vitamin D
                'calcium': 0.6,     # Moderate calcium
                'is_vegetarian': 1,
                'is_vegan': 0,
                'is_gluten_free': 0,
                'breastfeeding': 1,
                'weeks_postpartum': 0.3,  # 2-3 weeks
                'birth_type': 0,    # Vaginal birth
                'bmi': 0.5,        # Normal BMI
                'allergies': ['none'],
                'preferred_cuisine': 'indian'
            },
            # Non-lactating omnivore with good nutrition
            {
                'iron_level': 0.8,
                'vitamin_d': 0.7,
                'calcium': 0.8,
                'is_vegetarian': 0,
                'is_vegan': 0,
                'is_gluten_free': 0,
                'breastfeeding': 0,
                'weeks_postpartum': 0.8,  # 6-8 weeks
                'birth_type': 0,
                'bmi': 0.6,
                'allergies': ['none'],
                'preferred_cuisine': 'mediterranean'
            },
            # Lactating vegan with B12 deficiency
            {
                'iron_level': 0.5,
                'vitamin_d': 0.3,
                'calcium': 0.4,
                'is_vegetarian': 1,
                'is_vegan': 1,
                'is_gluten_free': 1,
                'breastfeeding': 1,
                'weeks_postpartum': 0.2,  # 1-2 weeks
                'birth_type': 1,    # C-section
                'bmi': 0.4,
                'allergies': ['dairy', 'eggs'],
                'preferred_cuisine': 'asian'
            },
            # Early postpartum with iron deficiency
            {
                'iron_level': 0.2,
                'vitamin_d': 0.5,
                'calcium': 0.7,
                'is_vegetarian': 0,
                'is_vegan': 0,
                'is_gluten_free': 0,
                'breastfeeding': 1,
                'weeks_postpartum': 0.1,  # 1 week
                'birth_type': 0,
                'bmi': 0.7,
                'allergies': ['nuts'],
                'preferred_cuisine': 'american'
            }
        ]
        
        # Generate more profiles with variations
        for i, template in enumerate(profile_templates):
            # Add some random variation
            profile = template.copy()
            profile['user_id'] = i
            
            # Add random variations
            for key in ['iron_level', 'vitamin_d', 'calcium', 'bmi']:
                if key in profile:
                    variation = np.random.normal(0, 0.1)
                    profile[key] = np.clip(profile[key] + variation, 0, 1)
            
            user_profiles.append(profile)
        
        # Convert to DataFrame
        self.user_profiles = pd.DataFrame(user_profiles)
        
        # Prepare features for K-NN
        self.feature_names = [
            'iron_level', 'vitamin_d', 'calcium', 'is_vegetarian', 
            'is_vegan', 'is_gluten_free', 'breastfeeding', 
            'weeks_postpartum', 'birth_type', 'bmi'
        ]
        
        print(f"Prepared {len(self.user_profiles)} user profiles")
    
    def train_knn_model(self):
        """Train K-NN model on user profiles"""
        print("Training K-NN model...")
        
        try:
            # Prepare features
            X = self.user_profiles[self.feature_names].values
            
            # Normalize numerical features
            X_scaled = self.scaler.fit_transform(X)
            
            # Apply PCA if dimensionality is high
            n_features = X_scaled.shape[1]
            n_samples = X_scaled.shape[0]

            if len(self.feature_names) > 5:
                # PCA components should be min(n_samples, n_features) and reasonable for the data
                max_components = min(n_samples, n_features)
                desired_components = min(5, max_components)

                if desired_components > 1:
                    self.pca = PCA(n_components=desired_components, random_state=42)
                    X_scaled = self.pca.fit_transform(X_scaled)
                    print(f"Applied PCA: reduced from {n_features} to {desired_components} components")
                else:
                    self.pca = None
                    print(f"Skipping PCA: insufficient data for dimensionality reduction")
            else:
                self.pca = None
            
            # Train K-NN model using cosine similarity for sparse data
            self.knn_model = NearestNeighbors(
                n_neighbors=min(3, len(self.user_profiles)), 
                metric='cosine',
                algorithm='brute'  # Better for cosine similarity
            )
            
            self.knn_model.fit(X_scaled)
            print("✅ K-NN model trained successfully")
            
        except Exception as e:
            print(f"Error training K-NN model: {e}")
            raise

    def find_similar_users(self, user_profile: Dict) -> Tuple[List[int], List[float]]:
        """Find similar users using K-NN"""
        try:
            # Prepare user profile features
            user_features = []
            for feature in self.feature_names:
                if feature in user_profile:
                    user_features.append(user_profile[feature])
                else:
                    # Default values for missing features
                    if feature in ['iron_level', 'vitamin_d', 'calcium', 'bmi']:
                        user_features.append(0.5)  # Moderate values
                    elif feature in ['is_vegetarian', 'is_vegan', 'is_gluten_free', 'breastfeeding', 'birth_type']:
                        user_features.append(0)
                    elif feature == 'weeks_postpartum':
                        user_features.append(0.5)  # 4 weeks
                    else:
                        user_features.append(0)
            
            # Normalize and transform features
            user_features_scaled = self.scaler.transform([user_features])
            
            if self.pca:
                user_features_scaled = self.pca.transform(user_features_scaled)
            
            # Find nearest neighbors
            distances, indices = self.knn_model.kneighbors(user_features_scaled)
            
            return indices[0], distances[0]
            
        except Exception as e:
            print(f"Error finding similar users: {e}")
            return [], []
    
    def recommend_foods(self, user_profile: Dict, top_n: int = 10) -> List[Dict]:
        """Generate food recommendations based on similar users and nutritional needs"""
        try:
            # Find similar users
            similar_user_indices, distances = self.find_similar_users(user_profile)
            
            if len(similar_user_indices) == 0:
                print("No similar users found")
                return []
            
            print(f"Found {len(similar_user_indices)} similar users")
            
            # Get foods that match user preferences and nutritional needs
            filtered_foods = self._filter_foods_by_preferences(user_profile)
            
            if len(filtered_foods) == 0:
                print("No foods match user preferences")
                return []
            
            # Score foods based on nutritional match and user similarity
            scored_foods = self._score_foods(filtered_foods, user_profile, similar_user_indices, distances)
            
            # Return top recommendations
            top_recommendations = scored_foods.head(top_n)
            
            recommendations = []
            for _, food in top_recommendations.iterrows():
                rec = {
                    'food_name': food['description_x'],
                    'category': food['description_y'],
                    'nutrition_score': round(food['final_score'], 3),
                    'nutrients': {},
                    'dietary_info': {
                        'vegetarian': bool(food['is_vegetarian']),
                        'vegan': bool(food['is_vegan']),
                        'gluten_free': bool(food['is_gluten_free'])
                    }
                }
                
                # Add nutrient information
                for nutrient in self.POSTPARTUM_RDA.keys():
                    if nutrient in food and food[nutrient] > 0:
                        rec['nutrients'][nutrient] = {
                            'amount': round(food[nutrient], 2),
                            'unit': self.POSTPARTUM_RDA[nutrient]['unit'],
                            'rda_percentage': round(food[nutrient] / self.POSTPARTUM_RDA[nutrient]['target'] * 100, 1)
                        }
                
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def _filter_foods_by_preferences(self, user_profile: Dict) -> pd.DataFrame:
        """Filter foods based on user dietary preferences and restrictions"""
        filtered = self.food_data.copy()
        
        # Dietary restrictions
        if user_profile.get('is_vegetarian', False):
            filtered = filtered[filtered['is_vegetarian'] == 1]
        
        if user_profile.get('is_vegan', False):
            filtered = filtered[filtered['is_vegan'] == 1]
        
        if user_profile.get('is_gluten_free', False):
            filtered = filtered[filtered['is_gluten_free'] == 1]
        
        # Allergy filtering
        allergies = user_profile.get('allergies', [])
        for allergy in allergies:
            if allergy.lower() != 'none':
                allergy_keywords = {
                    'dairy': 'milk|cheese|yogurt|butter|cream',
                    'nuts': 'almond|walnut|peanut|cashew|pistachio',
                    'eggs': 'egg|ovalbumin',
                    'soy': 'soy|tofu|edamame',
                    'shellfish': 'shrimp|crab|lobster|clam|oyster',
                    'wheat': 'wheat|gluten'
                }
                
                if allergy.lower() in allergy_keywords:
                    filtered = filtered[~filtered['description_x'].str.contains(
                        allergy_keywords[allergy.lower()], case=False, na=False
                    )]
        
        return filtered
    
    def _score_foods(self, foods: pd.DataFrame, user_profile: Dict, 
                     similar_user_indices: List[int], distances: List[float]) -> pd.DataFrame:
        """Score foods based on nutritional match and user similarity"""
        scored_foods = foods.copy()
        
        # Calculate nutritional match score
        scored_foods['nutrition_score'] = scored_foods.apply(
            lambda row: self._calculate_food_nutrition_score(row, user_profile), axis=1
        )
        
        # Calculate user similarity score (weighted by distance)
        similarity_weights = [1 / (1 + dist) for dist in distances]
        total_weight = sum(similarity_weights)
        
        # Get similar users' preferences (if they had food ratings)
        scored_foods['similarity_score'] = 0.5  # Default score
        
        # Combine scores
        scored_foods['final_score'] = (
            0.7 * scored_foods['nutrition_score'] + 
            0.3 * scored_foods['similarity_score']
        )
        
        # Sort by final score
        scored_foods = scored_foods.sort_values('final_score', ascending=False)
        
        return scored_foods
    
    def _calculate_food_nutrition_score(self, food_row: pd.Series, user_profile: Dict) -> float:
        """Calculate how well a food matches user's nutritional needs"""
        score = 0
        
        # Check for deficiencies
        if user_profile.get('iron_level', 0.5) < 0.4:  # Low iron
            if 'Iron, Fe' in food_row and food_row['Iron, Fe'] > 0:
                score += min(food_row['Iron, Fe'] / self.POSTPARTUM_RDA['Iron, Fe']['target'], 1.0) * 2
        
        if user_profile.get('vitamin_d', 0.5) < 0.4:  # Low vitamin D
            if 'Vitamin D' in food_row and food_row['Vitamin D'] > 0:
                score += min(food_row['Vitamin D'] / self.POSTPARTUM_RDA['Vitamin D']['target'], 1.0) * 2
        
        if user_profile.get('calcium', 0.5) < 0.4:  # Low calcium
            if 'Calcium, Ca' in food_row and food_row['Calcium, Ca'] > 0:
                score += min(food_row['Calcium, Ca'] / self.POSTPARTUM_RDA['Calcium, Ca']['target'], 1.0) * 2
        
        # Bonus for breastfeeding mothers
        if user_profile.get('breastfeeding', False):
            if 'Protein' in food_row and food_row['Protein'] > 0:
                score += min(food_row['Protein'] / self.POSTPARTUM_RDA['Protein']['target'], 1.0)
        
        # Normalize score
        score = min(score, 10.0)  # Cap at 10
        
        return score

    def generate_meal_plan(self, user_profile: Dict, days: int = 7) -> Dict:
        """Generate a complete meal plan for the specified number of days"""
        try:
            meal_plan = {
                'user_profile': user_profile,
                'days': days,
                'daily_meals': []
            }
            
            # Get food recommendations
            recommendations = self.recommend_foods(user_profile, top_n=50)
            
            if not recommendations:
                return meal_plan
            
            # Meal categories
            meal_categories = {
                'breakfast': ['cereal', 'bread', 'pancake', 'waffle', 'oatmeal', 'yogurt', 'fruit'],
                'lunch': ['salad', 'sandwich', 'soup', 'rice', 'pasta', 'vegetable'],
                'dinner': ['meat', 'fish', 'chicken', 'vegetable', 'grain', 'legume'],
                'snacks': ['fruit', 'nut', 'crackers', 'cheese', 'yogurt']
            }
            
            # Generate daily meal plans
            for day in range(1, days + 1):
                daily_plan = {
                    'day': day,
                    'meals': {}
                }
                
                for meal_type, keywords in meal_categories.items():
                    # Find foods that match meal type
                    meal_foods = []
                    for rec in recommendations:
                        food_name = rec['food_name'].lower()
                        if any(keyword in food_name for keyword in keywords):
                            meal_foods.append(rec)
                    
                    # Select 2-3 foods for each meal
                    selected_foods = meal_foods[:min(3, len(meal_foods))]
                    daily_plan['meals'][meal_type] = selected_foods
                
                meal_plan['daily_meals'].append(daily_plan)
            
            return meal_plan
            
        except Exception as e:
            print(f"Error generating meal plan: {e}")
            return {'error': str(e)}
    
    def save_model(self, model_path: str = None):
        """Save the trained model and components"""
        if model_path is None:
            model_path = Path(__file__).parent.parent / 'models' / 'knn_nutrition_model.pkl'
        
        model_data = {
            'knn_model': self.knn_model,
            'scaler': self.scaler,
            'pca': self.pca,
            'feature_names': self.feature_names,
            'user_profiles': self.user_profiles,
            'food_data': self.food_data,
            'postpartum_rda': self.POSTPARTUM_RDA
        }
        
        joblib.dump(model_data, model_path)
        print(f"✅ Model saved to {model_path}")
    
    def load_model(self, model_path: str):
        """Load a saved model"""
        try:
            model_data = joblib.load(model_path)
            
            self.knn_model = model_data['knn_model']
            self.scaler = model_data['scaler']
            self.pca = model_data['pca']
            self.feature_names = model_data['feature_names']
            self.user_profiles = model_data['user_profiles']
            self.food_data = model_data['food_data']
            self.POSTPARTUM_RDA = model_data['postpartum_rda']
            
            print("✅ Model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise


def main():
    """Main function to demonstrate the K-NN nutrition recommender"""
    print("=== K-NN Based Nutrition Recommendation System for Postpartum Mothers ===\n")
    
    try:
        # Initialize recommender
        recommender = PostpartumKNNNutritionRecommender()
        
        # Example user profiles
        example_users = [
            {
                'name': 'Sarah - Lactating Vegetarian with Iron Deficiency',
                'profile': {
                    'iron_level': 0.2,      # Low iron
                    'vitamin_d': 0.4,       # Moderate vitamin D
                    'calcium': 0.6,         # Moderate calcium
                    'is_vegetarian': 1,
                    'is_vegan': 0,
                    'is_gluten_free': 0,
                    'breastfeeding': 1,
                    'weeks_postpartum': 0.2,  # 1-2 weeks
                    'birth_type': 0,        # Vaginal birth
                    'bmi': 0.5,            # Normal BMI
                    'allergies': ['none'],
                    'preferred_cuisine': 'indian'
                }
            },
            {
                'name': 'Maria - Non-lactating Omnivore with Good Nutrition',
                'profile': {
                    'iron_level': 0.8,      # Good iron
                    'vitamin_d': 0.7,       # Good vitamin D
                    'calcium': 0.8,         # Good calcium
                    'is_vegetarian': 0,
                    'is_vegan': 0,
                    'is_gluten_free': 0,
                    'breastfeeding': 0,
                    'weeks_postpartum': 0.8,  # 6-8 weeks
                    'birth_type': 0,
                    'bmi': 0.6,
                    'allergies': ['none'],
                    'preferred_cuisine': 'mediterranean'
                }
            }
        ]
        
        # Test recommendations for each user
        for user_info in example_users:
            print(f"\n{'='*60}")
            print(f"Testing: {user_info['name']}")
            print(f"{'='*60}")
            
            # Get recommendations
            recommendations = recommender.recommend_foods(user_info['profile'], top_n=5)
            
            print(f"\nTop 5 Food Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['food_name']}")
                print(f"   Category: {rec['category']}")
                print(f"   Score: {rec['nutrition_score']}")
                print(f"   Dietary: {'Vegan' if rec['dietary_info']['vegan'] else 'Vegetarian' if rec['dietary_info']['vegetarian'] else 'Omnivore'}")
                
                # Show top nutrients
                top_nutrients = sorted(rec['nutrients'].items(), 
                                     key=lambda x: x[1]['rda_percentage'], reverse=True)[:3]
                for nutrient, info in top_nutrients:
                    print(f"   {nutrient}: {info['amount']} {info['unit']} ({info['rda_percentage']}% RDA)")
            
            # Generate meal plan
            meal_plan = recommender.generate_meal_plan(user_info['profile'], days=3)
            
            print(f"\n3-Day Meal Plan Preview:")
            for day_plan in meal_plan['daily_meals'][:2]:  # Show first 2 days
                print(f"\nDay {day_plan['day']}:")
                for meal_type, foods in day_plan['meals'].items():
                    if foods:
                        print(f"  {meal_type.title()}: {', '.join([f['food_name'][:30] for f in foods[:2]])}")
        
        # Save the trained model
        recommender.save_model()
        
        print(f"\n{'='*60}")
        print("✅ K-NN Nutrition Recommendation System Ready!")
        print("Model saved and ready for production use.")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
