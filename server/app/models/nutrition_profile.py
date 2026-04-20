from datetime import datetime, timedelta
from bson import ObjectId
from app import mongo

class NutritionProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.collection = mongo.db.nutrition_profiles

    def create_profile(self, profile_data):
        profile = {
            'user_id': ObjectId(self.user_id),
            'breastfeeding': profile_data.get('breastfeeding'),
            'diet_type': profile_data.get('dietType'),
            'allergies': profile_data.get('allergies', '').split(','),
            'deficiency': profile_data.get('deficiency'),
            'preferred_cuisine': profile_data.get('preferredCuisine'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'nutrition_goals': [],
            'meal_plans': [],
            'progress_tracking': {
                'daily_calories': [],
                'protein_intake': [],
                'hydration': [],
                'supplements': []
            }
        }
        return self.collection.insert_one(profile)

    def get_profile(self):
        return self.collection.find_one({'user_id': ObjectId(self.user_id)})

    def update_profile(self, profile_data):
        update_data = {
            'breastfeeding': profile_data.get('breastfeeding'),
            'diet_type': profile_data.get('dietType'),
            'allergies': profile_data.get('allergies', '').split(','),
            'deficiency': profile_data.get('deficiency'),
            'preferred_cuisine': profile_data.get('preferredCuisine'),
            'updated_at': datetime.utcnow()
        }
        return self.collection.update_one(
            {'user_id': ObjectId(self.user_id)},
            {'$set': update_data}
        )

    def add_nutrition_goal(self, goal):
        goal['created_at'] = datetime.utcnow()
        goal['completed'] = False
        return self.collection.update_one(
            {'user_id': ObjectId(self.user_id)},
            {'$push': {'nutrition_goals': goal}}
        )

    def add_meal_plan(self, meal_plan):
        meal_plan['created_at'] = datetime.utcnow()
        return self.collection.update_one(
            {'user_id': ObjectId(self.user_id)},
            {'$push': {'meal_plans': meal_plan}}
        )

    def track_progress(self, category, value):
        tracking_entry = {
            'date': datetime.utcnow(),
            'value': value
        }
        return self.collection.update_one(
            {'user_id': ObjectId(self.user_id)},
            {'$push': {f'progress_tracking.{category}': tracking_entry}}
        )

    def get_progress_history(self, category, days=30):
        profile = self.get_profile()
        if not profile or 'progress_tracking' not in profile:
            return []
        
        tracking_data = profile['progress_tracking'].get(category, [])
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return [entry for entry in tracking_data if entry['date'] >= cutoff_date] 