from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

class DailyCheckin:
    def __init__(self, user_id, mood, journal_entry, timestamp=None):
        if isinstance(user_id, str):
            self.user_id = user_id
        else:
             # Assuming user_id comes as ObjectId from JWT payload for consistency
            self.user_id = str(user_id)

        self.mood = mood
        self.journal_entry = journal_entry
        self.timestamp = timestamp if timestamp is not None else datetime.utcnow()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "mood": self.mood,
            "journal_entry": self.journal_entry,
            "timestamp": self.timestamp.isoformat()
        }

    @staticmethod
    def get_collection():
        client = MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'))
        db = client.get_database(os.environ.get('MONGODB_DB_NAME', 'postpartum_care'))
        return db.daily_checkins

    @staticmethod
    def save_checkin(user_id, mood, journal_entry):
        checkin_data = DailyCheckin(user_id, mood, journal_entry).to_dict()
        # Ensure uniqueness per day per user if needed, or allow multiple entries
        # For simplicity, allowing multiple entries per day for now.
        collection = DailyCheckin.get_collection()
        result = collection.insert_one(checkin_data)
        return result

    @staticmethod
    def get_checkins_for_user(user_id, limit=None):
        collection = DailyCheckin.get_collection()
        # Ensure user_id is correctly handled (string vs ObjectId)
        # Assuming user_id is stored as a string
        query = {"user_id": str(user_id)}
        
        cursor = collection.find(query).sort("timestamp", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        checkins = []
        for doc in cursor:
            # Convert ObjectId to string and datetime to ISO format if not already
            doc['_id'] = str(doc['_id'])
            if isinstance(doc.get('timestamp'), datetime):
                 doc['timestamp'] = doc['timestamp'].isoformat()
            checkins.append(doc)
            
        return checkins

    # You could add more methods here, e.g., to get checkins for a specific date range 