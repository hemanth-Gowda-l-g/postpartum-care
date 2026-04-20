from datetime import datetime
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

mongo = PyMongo()

class User:
    @staticmethod
    def create_user(email, password, role):
        hashed_password = generate_password_hash(password)
        return mongo.db.users.insert_one({
            'email': email,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.utcnow()
        })
    
    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({'email': email})
    
    @staticmethod
    def verify_password(user, password):
        return check_password_hash(user['password'], password)

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