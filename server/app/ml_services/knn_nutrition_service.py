import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
import joblib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class KNNNutritionService:
    """
    K-NN Based Nutrition Recommendation Service for Postpartum Mothers
    
    This service integrates with the existing nutrition system to provide
    personalized food recommendations using k-Nearest Neighbors algorithm.
    """
    
    def __init__(self):
        self.knn_model = None
        self.scaler = MinMaxScaler()
        self.pca = None
        self.feature_names = [
            'iron_level', 'vitamin_d', 'calcium', 'is_vegetarian', 
            'is_vegan', 'is_gluten_free', 'breastfeeding', 
            'weeks_postpartum', 'birth_type', 'bmi'
        ]
        
        # Postpartum-specific nutrient requirements
        self.POSTPARTUM_RDA = {
            'Iron, Fe': {'target': 27, 'unit': 'mg', 'critical': True},
            'Calcium, Ca': {'target': 1000, 'unit': 'mg', 'critical': True},
            'Vitamin D': {'target': 600, 'unit': 'IU', 'critical': True},
            'Folate, total': {'target': 500, 'unit': 'mcg', 'critical': True},
            'Vitamin B-12': {'target': 2.8, 'unit': 'mcg', 'critical': True},
            'Protein': {'target': 71, 'unit': 'g', 'critical': True}
        }
        
        # Load or create synthetic user profiles for K-NN training
        try:
            self.user_profiles = self._create_synthetic_profiles()
            self._train_knn_model()
        except Exception as e:
            print(f"❌ Error during K-NN service initialization: {e}")
            self.knn_model = None
            self.user_profiles = pd.DataFrame()  # Empty dataframe as fallback
    
    def _create_synthetic_profiles(self) -> pd.DataFrame:
        """Create synthetic user profiles for K-NN training"""
        profiles = []
        
        # Profile templates based on common postpartum scenarios
        templates = [
            # Lactating vegetarian with iron deficiency
            {
                'iron_level': 0.3, 'vitamin_d': 0.4, 'calcium': 0.6,
                'is_vegetarian': 1, 'is_vegan': 0, 'is_gluten_free': 0,
                'breastfeeding': 1, 'weeks_postpartum': 0.3, 'birth_type': 0, 'bmi': 0.5
            },
            # Non-lactating omnivore with good nutrition
            {
                'iron_level': 0.8, 'vitamin_d': 0.7, 'calcium': 0.8,
                'is_vegetarian': 0, 'is_vegan': 0, 'is_gluten_free': 0,
                'breastfeeding': 0, 'weeks_postpartum': 0.8, 'birth_type': 0, 'bmi': 0.6
            },
            # Lactating vegan with B12 deficiency
            {
                'iron_level': 0.5, 'vitamin_d': 0.3, 'calcium': 0.4,
                'is_vegetarian': 1, 'is_vegan': 1, 'is_gluten_free': 1,
                'breastfeeding': 1, 'weeks_postpartum': 0.2, 'birth_type': 1, 'bmi': 0.4
            },
            # Early postpartum with iron deficiency
            {
                'iron_level': 0.2, 'vitamin_d': 0.5, 'calcium': 0.7,
                'is_vegetarian': 0, 'is_vegan': 0, 'is_gluten_free': 0,
                'breastfeeding': 1, 'weeks_postpartum': 0.1, 'birth_type': 0, 'bmi': 0.7
            }
        ]
        
        # Generate profiles with variations
        for i, template in enumerate(templates):
            profile = template.copy()
            profile['user_id'] = i
            
            # Add random variations
            for key in ['iron_level', 'vitamin_d', 'calcium', 'bmi']:
                variation = np.random.normal(0, 0.1)
                profile[key] = np.clip(profile[key] + variation, 0, 1)
            
            profiles.append(profile)
        
        return pd.DataFrame(profiles)
    
    def _train_knn_model(self):
        """Train K-NN model on synthetic user profiles"""
        try:
            # Prepare features
            X = self.user_profiles[self.feature_names].values

            # Normalize features
            X_scaled = self.scaler.fit_transform(X)

            # Apply PCA for dimensionality reduction only if we have enough features
            n_features = X_scaled.shape[1]
            n_samples = X_scaled.shape[0]

            # PCA components should be min(n_samples, n_features) and reasonable for the data
            max_components = min(n_samples, n_features)
            desired_components = min(5, max_components)

            if desired_components > 1 and n_features > 2:
                self.pca = PCA(n_components=desired_components, random_state=42)
                X_scaled = self.pca.fit_transform(X_scaled)
                print(f"Applied PCA: reduced from {n_features} to {desired_components} components")
            else:
                self.pca = None
                print(f"Skipping PCA: using all {n_features} features")

            # Train K-NN model using cosine similarity
            self.knn_model = NearestNeighbors(
                n_neighbors=min(3, len(self.user_profiles)),
                metric='cosine',
                algorithm='brute'
            )

            self.knn_model.fit(X_scaled)
            print("✅ K-NN nutrition model trained successfully")

        except Exception as e:
            print(f"Error training K-NN model: {e}")
            self.knn_model = None
    
    def find_similar_users(self, user_profile: Dict) -> Tuple[List[int], List[float]]:
        """Find similar users using K-NN"""
        if self.knn_model is None:
            return [], []
        
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
            if self.pca is not None:
                user_features_scaled = self.pca.transform(user_features_scaled)
            
            # Find nearest neighbors
            distances, indices = self.knn_model.kneighbors(user_features_scaled)
            
            return indices[0], distances[0]
            
        except Exception as e:
            print(f"Error finding similar users: {e}")
            return [], []
    
    def enhance_recommendations(self, base_recommendations: List[Dict], 
                               user_profile: Dict) -> List[Dict]:
        """Enhance existing recommendations using K-NN similarity"""
        try:
            # Find similar users
            similar_user_indices, distances = self.find_similar_users(user_profile)
            
            if len(similar_user_indices) == 0:
                return base_recommendations
            
            # Calculate similarity weights
            similarity_weights = [1 / (1 + dist) for dist in distances]
            total_weight = sum(similarity_weights)
            
            # Enhance recommendations with K-NN insights
            enhanced_recommendations = []
            
            for rec in base_recommendations:
                enhanced_rec = rec.copy()
                
                # Add K-NN similarity score
                enhanced_rec['knn_similarity_score'] = round(
                    sum(similarity_weights) / len(similarity_weights), 3
                )
                
                # Boost score for foods that match similar users' preferences
                enhanced_rec['enhanced_score'] = enhanced_rec.get('score', 0) * (
                    1 + enhanced_rec['knn_similarity_score'] * 0.3
                )
                
                enhanced_recommendations.append(enhanced_rec)
            
            # Sort by enhanced score
            enhanced_recommendations.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)
            
            return enhanced_recommendations
            
        except Exception as e:
            print(f"Error enhancing recommendations: {e}")
            return base_recommendations
    
    def get_personalized_insights(self, user_profile: Dict) -> Dict:
        """Get personalized insights based on K-NN analysis"""
        try:
            similar_user_indices, distances = self.find_similar_users(user_profile)
            
            if len(similar_user_indices) == 0:
                return {'message': 'Unable to find similar user profiles'}
            
            # Analyze similar users
            similar_profiles = self.user_profiles.iloc[similar_user_indices]
            
            insights = {
                'similar_users_found': len(similar_user_indices),
                'average_similarity': round(1 / (1 + np.mean(distances)), 3),
                'common_characteristics': {},
                'nutritional_patterns': {},
                'recommendations': []
            }
            
            # Analyze common characteristics
            for feature in ['is_vegetarian', 'is_vegan', 'is_gluten_free', 'breastfeeding']:
                if feature in similar_profiles.columns:
                    most_common = similar_profiles[feature].mode().iloc[0]
                    insights['common_characteristics'][feature] = bool(most_common)
            
            # Analyze nutritional patterns
            for nutrient in ['iron_level', 'vitamin_d', 'calcium']:
                if nutrient in similar_profiles.columns:
                    avg_level = similar_profiles[nutrient].mean()
                    insights['nutritional_patterns'][nutrient] = {
                        'average_level': round(avg_level, 3),
                        'status': 'low' if avg_level < 0.4 else 'moderate' if avg_level < 0.7 else 'good'
                    }
            
            # Generate personalized recommendations
            if user_profile.get('iron_level', 0.5) < 0.4:
                insights['recommendations'].append({
                    'type': 'iron_boost',
                    'message': 'Consider iron-rich foods like spinach, lentils, and fortified cereals',
                    'priority': 'high'
                })
            
            if user_profile.get('vitamin_d', 0.5) < 0.4:
                insights['recommendations'].append({
                    'type': 'vitamin_d_boost',
                    'message': 'Include vitamin D sources like fatty fish, egg yolks, and fortified foods',
                    'priority': 'medium'
                })
            
            if user_profile.get('breastfeeding', False):
                insights['recommendations'].append({
                    'type': 'breastfeeding_support',
                    'message': 'Increase protein intake and stay well-hydrated for optimal milk production',
                    'priority': 'high'
                })
            
            return insights
            
        except Exception as e:
            print(f"Error getting personalized insights: {e}")
            return {'error': str(e)}
    
    def save_model(self, model_path: str = None):
        """Save the trained K-NN model"""
        if model_path is None:
            model_path = Path(__file__).parent.parent.parent / 'ml' / 'models' / 'knn_nutrition_model.pkl'
        
        try:
            model_data = {
                'knn_model': self.knn_model,
                'scaler': self.scaler,
                'pca': self.pca,
                'feature_names': self.feature_names,
                'user_profiles': self.user_profiles,
                'postpartum_rda': self.POSTPARTUM_RDA
            }
            
            joblib.dump(model_data, model_path)
            print(f"✅ K-NN nutrition model saved to {model_path}")
            
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self, model_path: str):
        """Load a saved K-NN model"""
        try:
            model_data = joblib.load(model_path)
            
            self.knn_model = model_data['knn_model']
            self.scaler = model_data['scaler']
            self.pca = model_data['pca']
            self.feature_names = model_data['feature_names']
            self.user_profiles = model_data['user_profiles']
            self.POSTPARTUM_RDA = model_data['postpartum_rda']
            
            print("✅ K-NN nutrition model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise


# Example usage and testing
if __name__ == "__main__":
    print("=== Testing K-NN Nutrition Service ===\n")
    
    try:
        # Initialize service
        knn_service = KNNNutritionService()
        
        # Test with example user profile
        test_profile = {
            'iron_level': 0.2,      # Low iron
            'vitamin_d': 0.4,       # Moderate vitamin D
            'calcium': 0.6,         # Moderate calcium
            'is_vegetarian': 1,
            'is_vegan': 0,
            'is_gluten_free': 0,
            'breastfeeding': 1,
            'weeks_postpartum': 0.2,  # 1-2 weeks
            'birth_type': 0,        # Vaginal birth
            'bmi': 0.5
        }
        
        # Test similar user finding
        similar_indices, distances = knn_service.find_similar_users(test_profile)
        print(f"Found {len(similar_indices)} similar users")
        print(f"Similarity distances: {[round(d, 3) for d in distances]}")
        
        # Test personalized insights
        insights = knn_service.get_personalized_insights(test_profile)
        print(f"\nPersonalized Insights:")
        print(f"- Similar users found: {insights['similar_users_found']}")
        print(f"- Average similarity: {insights['average_similarity']}")
        print(f"- Recommendations: {len(insights['recommendations'])}")
        
        # Save model
        knn_service.save_model()
        
        print("\n✅ K-NN Nutrition Service test completed successfully!")
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
