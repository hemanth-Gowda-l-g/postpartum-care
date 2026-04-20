from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.recovery_plan import RecoveryPlan

@jwt_required()
def create_recovery_plan():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    plan = RecoveryPlan.create_plan(user_id, data['delivery_type'])
    return jsonify({'plan_id': str(plan.inserted_id)}), 201
