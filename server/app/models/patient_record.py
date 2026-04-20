from datetime import datetime
from bson import ObjectId
from flask_pymongo import PyMongo

mongo = PyMongo()

class PatientRecord:
    @staticmethod
    def create_record(user_id, data):
        return mongo.db.patient_records.insert_one({
            'user_id': ObjectId(user_id),
            'blood_pressure': data.get('blood_pressure'),
            'mood': data.get('mood'),
            'notes': data.get('notes'),
            'created_at': datetime.utcnow()
        })
    
    @staticmethod
    def get_records(user_id):
        return list(mongo.db.patient_records.find({'user_id': ObjectId(user_id)}))