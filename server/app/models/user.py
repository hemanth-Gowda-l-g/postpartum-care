from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask import current_app
from ..utils.database import mongo

class User:
    @staticmethod
    def create_user(email, password, role='mother', name=None, delivery_type=None, due_date=None, conditions=None):
        """Create a new user in the database"""
        if User.find_by_email(email):
            return None  # User already exists
        
        hashed_password = generate_password_hash(password)
        
        user_data = {
            'email': email,
            'password': hashed_password,
            'role': role,
            'name': name,
            'delivery_type': delivery_type,
            'due_date': due_date,
            'conditions': conditions or [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        
        result = mongo.db.users.insert_one(user_data)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        """Find a user by email"""
        return mongo.db.users.find_one({'email': email})

    @staticmethod
    def find_by_id(user_id):
        """Find a user by ID"""
        return mongo.db.users.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def verify_password(user, password):
        """Verify the user's password"""
        if not user or not user.get('password'):
            return False
        return check_password_hash(user['password'], password)

    @staticmethod
    def update_user(user_id, update_data):
        """Update user information"""
        if 'password' in update_data:
            update_data['password'] = generate_password_hash(update_data['password'])
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0

    @staticmethod
    def get_all_patients():
        """Get all users with role 'mother'"""
        return list(mongo.db.users.find({'role': 'mother'}))

    @staticmethod
    def get_all_doctors():
        """Get all users with role 'doctor'"""
        return list(mongo.db.users.find({'role': 'doctor'}))

    @staticmethod
    def get_users_by_role(role):
        """Get all users with a specific role"""
        return list(mongo.db.users.find({'role': role, 'is_active': True}))

    @staticmethod
    def get_healthcare_providers():
        """Get all healthcare providers"""
        provider_roles = ['healthcare_provider', 'mental_health_specialist', 'nutritionist']
        return list(mongo.db.users.find({
            'role': {'$in': provider_roles},
            'is_active': True
        }))

    @staticmethod
    def update_user_role(user_id, new_role):
        """Update user role (admin only)"""
        try:
            result = mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'role': new_role,
                    'updated_at': datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False

    @staticmethod
    def deactivate_user(user_id):
        """Deactivate a user account"""
        try:
            result = mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'is_active': False,
                    'deactivated_at': datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False

    @staticmethod
    def get_user_stats():
        """Get user statistics for admin dashboard"""
        try:
            pipeline = [
                {'$match': {'is_active': True}},
                {'$group': {
                    '_id': '$role',
                    'count': {'$sum': 1}
                }}
            ]

            stats = list(mongo.db.users.aggregate(pipeline))
            total_users = mongo.db.users.count_documents({'is_active': True})

            return {
                'total_users': total_users,
                'by_role': {stat['_id']: stat['count'] for stat in stats}
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}