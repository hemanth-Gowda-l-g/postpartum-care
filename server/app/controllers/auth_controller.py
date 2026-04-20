from flask import request, jsonify
from app.models.user import User
from app.utils.auth import (
    hash_password,
    verify_password,
    create_jwt_token
)

def register():
    """Handle user registration"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
            
        # Check for existing user
        if User.find_by_email(data['email']):
            return jsonify({'error': 'Email already exists'}), 409
            
        # Create new user
        hashed_pw = hash_password(data['password'])
        user_id = User.create_user(data['email'], hashed_pw)
        
        return jsonify({
            'message': 'User created successfully',
            'token': create_jwt_token(str(user_id.inserted_id))
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def login():
    """Handle user login"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
            
        # Verify credentials
        user = User.find_by_email(data['email'])
        if not user or not verify_password(user['password'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        return jsonify({
            'token': create_jwt_token(str(user['_id']))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500