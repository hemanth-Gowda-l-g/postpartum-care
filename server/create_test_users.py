#!/usr/bin/env python3
"""
Script to create test users for different roles in the postpartum care platform
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.utils.database import mongo
from app import create_app

def create_test_users():
    """Create test users for each role"""
    
    # Initialize the app to set up database connection
    app = create_app()
    
    with app.app_context():
        test_users = [
            {
                'email': 'patient@test.com',
                'password': 'password123',
                'role': 'mother',
                'name': 'Sarah Johnson',
                'delivery_type': 'vaginal',
                'due_date': '2024-01-15',
                'conditions': ['gestational_diabetes']
            },
            {
                'email': 'careplan@test.com',
                'password': 'password123',
                'role': 'mother',
                'name': 'Maria Rodriguez',
                'delivery_type': 'c_section',
                'due_date': '2024-02-01',
                'conditions': ['postpartum_depression_risk']
            },
            {
                'email': 'provider@test.com',
                'password': 'password123',
                'role': 'healthcare_provider',
                'name': 'Dr. Emily Chen',
                'delivery_type': None,
                'due_date': None,
                'conditions': []
            },
            {
                'email': 'mental@test.com',
                'password': 'password123',
                'role': 'mental_health_specialist',
                'name': 'Dr. Michael Rodriguez',
                'delivery_type': None,
                'due_date': None,
                'conditions': []
            },
            {
                'email': 'admin@test.com',
                'password': 'password123',
                'role': 'admin',
                'name': 'Admin User',
                'delivery_type': None,
                'due_date': None,
                'conditions': []
            }
        ]
        
        print("Creating test users...")
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = User.find_by_email(user_data['email'])
            if existing_user:
                print(f"❌ User {user_data['email']} already exists")
                continue
            
            # Create user
            user_id = User.create_user(
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role'],
                name=user_data['name'],
                delivery_type=user_data['delivery_type'],
                due_date=user_data['due_date'],
                conditions=user_data['conditions']
            )
            
            if user_id:
                print(f"✅ Created {user_data['role']} user: {user_data['email']} (ID: {user_id})")
            else:
                print(f"❌ Failed to create user: {user_data['email']}")
        
        print("\n🎉 Test users created successfully!")
        print("\nLogin credentials:")
        print("==================")
        for user_data in test_users:
            print(f"Role: {user_data['role']}")
            print(f"Email: {user_data['email']}")
            print(f"Password: {user_data['password']}")
            print(f"Name: {user_data['name']}")
            print("-" * 30)

if __name__ == '__main__':
    create_test_users()
