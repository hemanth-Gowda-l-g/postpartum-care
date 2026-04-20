from datetime import datetime
from app.utils.database import mongo
from bson import ObjectId

class SymptomTracking:
    @staticmethod
    def save_symptom_entry(user_id, symptom_name, value):
        """Saves a symptom tracking entry for a user."""
        return mongo.db.symptom_tracking.insert_one({
            'user_id': ObjectId(user_id),
            'symptom_name': symptom_name,
            'value': value, # Value could be numeric (e.g., 1-5 scale) or categorical
            'timestamp': datetime.utcnow()
        })

    @staticmethod
    def get_symptom_history(user_id, symptom_name, limit=None):
        """Retrieves historical symptom entries for a user and symptom."""
        query = {
            'user_id': ObjectId(user_id),
            'symptom_name': symptom_name
        }
        # Sort by timestamp descending (most recent first)
        cursor = mongo.db.symptom_tracking.find(query).sort('timestamp', -1)
        
        if limit is not None:
            cursor = cursor.limit(limit)
            
        # Return list of entries, converting ObjectId to string
        return [{
            'symptom_name': entry['symptom_name'],
            'value': entry['value'],
            'timestamp': entry['timestamp'].isoformat() # Convert datetime to string
        } for entry in cursor]

    @staticmethod
    def get_all_symptom_names_for_user(user_id):
        """Retrieves all unique symptom names tracked by a user."""
        query = {'user_id': ObjectId(user_id)}
        # Use distinct to get unique symptom names
        distinct_symptoms = mongo.db.symptom_tracking.distinct('symptom_name', query)
        return distinct_symptoms 