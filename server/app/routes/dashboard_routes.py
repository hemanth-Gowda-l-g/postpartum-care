from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.patient_record import PatientRecord  # Updated import
from bson import ObjectId

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/records', methods=['GET'])
@jwt_required()
def get_records():
    current_user = get_jwt_identity()
    records = PatientRecord.get_records(current_user['id'])
    
    for record in records:
        record['_id'] = str(record['_id'])
        record['user_id'] = str(record['user_id'])
    
    return jsonify(records), 200

@dashboard_bp.route('/add-record', methods=['POST'])
@jwt_required()
def add_record():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"msg": "No data provided"}), 400
    
    record_id = PatientRecord.create_record(current_user['id'], data)
    return jsonify({
        "msg": "Record added successfully",
        "record_id": str(record_id.inserted_id)
    }), 201

@dashboard_bp.route('/user-info', methods=['GET'])
@jwt_required()
def user_info():
    current_user = get_jwt_identity()
    return jsonify(current_user), 200

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    current_user = get_jwt_identity()
    
    # Get basic stats for the dashboard
    try:
        # For now, return basic stats - you can expand this later
        stats = {
            'total_records': 0,
            'recent_assessments': 0,
            'nutrition_recommendations': 0,
            'mental_health_score': 'Not assessed',
            'last_check_in': None,
            'upcoming_appointments': 0,
            'recovery_progress': 0
        }
        
        # You can add more complex queries here to get actual data
        # For example:
        # records = PatientRecord.get_records(current_user['id'])
        # stats['total_records'] = len(records)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard stats'}), 500
