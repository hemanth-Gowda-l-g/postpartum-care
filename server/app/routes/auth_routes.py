from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from ..utils.database import mongo
from flask_cors import CORS
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)

# Configure CORS for the blueprint
CORS(auth_bp)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing email or password"}), 400
    
    if User.find_by_email(data['email']):
        return jsonify({"msg": "User already exists"}), 400
    
    user_id = User.create_user(
        email=data['email'],
        password=data['password'],
        role=data.get('role', 'mother'),
        name=data.get('name'),
        delivery_type=data.get('deliveryType'),
        due_date=data.get('dueDate'),
        conditions=data.get('conditions', [])
    )
    
    if not user_id:
        return jsonify({"msg": "Failed to create user"}), 500
    
    # Create access token for immediate login
    user = User.find_by_id(user_id)
    access_token = create_access_token(identity=str(user['_id']),
                                       additional_claims={
                                           'email': user['email'],
                                           'role': user['role']
                                       })
    
    return jsonify({
        "msg": "User created successfully",
        "access_token": access_token,
        "user": {
            "email": user['email'],
            "role": user['role'],
            "id": str(user['_id']),
            "name": user.get('name')
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing email or password"}), 400
    
    user = User.find_by_email(data['email'])
    
    if not user or not User.verify_password(user, data['password']):
        return jsonify({"msg": "Bad credentials"}), 401
    
    access_token = create_access_token(identity=str(user['_id']),
                                       additional_claims={
                                           'email': user['email'],
                                           'role': user['role']
                                       })
    
    return jsonify({
        "access_token": access_token,
        "user": {
            "email": user['email'],
            "role": user['role'],
            "id": str(user['_id'])
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return jsonify(user)

@auth_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No data provided'}), 400

    # Prevent updating email, role, and _id for security reasons
    data.pop('email', None)
    data.pop('role', None)
    data.pop('_id', None)

    updated = User.update_user(user_id, data)
    if not updated:
        return jsonify({'msg': 'Failed to update profile or no changes made'}), 400

    user = User.find_by_id(user_id)
    if not user:
        return jsonify({'msg': 'User not found'}), 404
    user['_id'] = str(user['_id'])
    user.pop('password', None)
    return jsonify(user), 200