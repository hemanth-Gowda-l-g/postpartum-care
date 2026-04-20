from flask import Blueprint, request, jsonify
from ..controllers.care_plan_controller import CarePlanController

care_plan_bp = Blueprint('care_plan', __name__)

@care_plan_bp.route('/generate', methods=['POST'])
def generate_care_plan():
    """Generate ML-powered care plan"""
    return CarePlanController.generate_care_plan()

@care_plan_bp.route('/user/<user_id>', methods=['GET'])
def get_care_plan(user_id):
    """Get current care plan for user"""
    return CarePlanController.get_care_plan(user_id)

@care_plan_bp.route('/task/complete', methods=['PUT'])
def update_task_completion():
    """Update task completion status"""
    return CarePlanController.update_task_completion()

@care_plan_bp.route('/regenerate', methods=['POST'])
def regenerate_weekly_plan():
    """Regenerate weekly care plan"""
    return CarePlanController.regenerate_weekly_plan()

@care_plan_bp.route('/cluster/insights', methods=['GET'])
def get_cluster_insights():
    """Get ML clustering insights"""
    return CarePlanController.get_cluster_insights()

@care_plan_bp.route('/predict-cluster', methods=['POST'])
def predict_user_cluster():
    """Predict user cluster based on profile"""
    return CarePlanController.predict_user_cluster()
