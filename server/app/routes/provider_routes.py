from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from ..models.user import User
from ..models.user_assignment import UserAssignment
from ..models.nutrition_profile import NutritionProfile
from ..utils.permissions import require_healthcare_provider, require_clinical_access, patient_data_access_required
from ..utils.database import mongo
from bson import ObjectId
from flask_cors import CORS

provider_bp = Blueprint('provider', __name__)
CORS(provider_bp)

@provider_bp.route('/patients', methods=['GET'])
@require_healthcare_provider()
def get_assigned_patients():
    """Get patients assigned to the current provider"""
    try:
        provider_id = get_jwt_identity()
        patients = UserAssignment.get_provider_patients(provider_id)
        
        return jsonify({
            'patients': patients,
            'total': len(patients)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/profile', methods=['GET'])
@require_healthcare_provider()
@patient_data_access_required()
def get_patient_profile(patient_id):
    """Get detailed patient profile"""
    try:
        # Get basic user info
        patient = User.find_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Remove sensitive data
        patient['_id'] = str(patient['_id'])
        patient.pop('password', None)
        
        # Get nutrition profile
        nutrition_profile = NutritionProfile(patient_id).get_profile()
        if nutrition_profile:
            nutrition_profile['_id'] = str(nutrition_profile['_id'])
            nutrition_profile['user_id'] = str(nutrition_profile['user_id'])
        
        # Get recent check-ins
        recent_checkins = list(mongo.db.daily_checkins.find(
            {'user_id': patient_id}
        ).sort('timestamp', -1).limit(10))
        
        for checkin in recent_checkins:
            checkin['_id'] = str(checkin['_id'])
        
        return jsonify({
            'patient': patient,
            'nutrition_profile': nutrition_profile,
            'recent_checkins': recent_checkins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/progress', methods=['GET'])
@require_healthcare_provider()
@patient_data_access_required()
def get_patient_progress(patient_id):
    """Get patient progress data"""
    try:
        # Get nutrition progress
        nutrition_profile = NutritionProfile(patient_id).get_profile()
        progress_data = {}
        
        if nutrition_profile:
            progress_data = nutrition_profile.get('progress_tracking', {})
        
        # Get mood trends from check-ins
        mood_pipeline = [
            {'$match': {'user_id': patient_id}},
            {'$sort': {'timestamp': -1}},
            {'$limit': 30},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                'avg_mood': {'$avg': '$mood'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        mood_trends = list(mongo.db.daily_checkins.aggregate(mood_pipeline))
        
        return jsonify({
            'nutrition_progress': progress_data,
            'mood_trends': mood_trends
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/notes', methods=['GET'])
@require_healthcare_provider()
@patient_data_access_required()
def get_patient_notes(patient_id):
    """Get provider notes for a patient"""
    try:
        provider_id = get_jwt_identity()
        
        notes = list(mongo.db.provider_notes.find({
            'patient_id': ObjectId(patient_id),
            'provider_id': ObjectId(provider_id)
        }).sort('created_at', -1))
        
        for note in notes:
            note['_id'] = str(note['_id'])
            note['patient_id'] = str(note['patient_id'])
            note['provider_id'] = str(note['provider_id'])
        
        return jsonify({'notes': notes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/notes', methods=['POST'])
@require_healthcare_provider()
@patient_data_access_required()
def add_patient_note(patient_id):
    """Add a note for a patient"""
    try:
        provider_id = get_jwt_identity()
        data = request.get_json()
        
        note_text = data.get('note')
        note_type = data.get('type', 'general')  # general, assessment, treatment, follow_up
        
        if not note_text:
            return jsonify({'error': 'Note text is required'}), 400
        
        note = {
            'patient_id': ObjectId(patient_id),
            'provider_id': ObjectId(provider_id),
            'note': note_text,
            'type': note_type,
            'created_at': datetime.utcnow(),
            'is_private': data.get('is_private', False)
        }
        
        result = mongo.db.provider_notes.insert_one(note)
        
        return jsonify({
            'message': 'Note added successfully',
            'note_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/dashboard-stats', methods=['GET'])
@require_healthcare_provider()
def get_provider_dashboard_stats():
    """Get statistics for provider dashboard"""
    try:
        provider_id = get_jwt_identity()
        
        # Get assigned patients count
        patients = UserAssignment.get_provider_patients(provider_id)
        total_patients = len(patients)
        
        # Get recent activity
        recent_checkins = mongo.db.daily_checkins.count_documents({
            'user_id': {'$in': [p['patient_id'] for p in patients]},
            'timestamp': {'$gte': datetime.utcnow() - timedelta(days=7)}
        })
        
        # Get high-risk patients (example: low mood scores)
        high_risk_patients = []
        for patient in patients:
            recent_mood = list(mongo.db.daily_checkins.find({
                'user_id': patient['patient_id']
            }).sort('timestamp', -1).limit(5))
            
            if recent_mood:
                avg_mood = sum(checkin.get('mood', 5) for checkin in recent_mood) / len(recent_mood)
                if avg_mood < 3:  # Low mood threshold
                    high_risk_patients.append({
                        'patient_id': patient['patient_id'],
                        'patient_name': patient['patient_name'],
                        'avg_mood': round(avg_mood, 1)
                    })
        
        return jsonify({
            'total_patients': total_patients,
            'recent_checkins': recent_checkins,
            'high_risk_patients': high_risk_patients,
            'alerts_count': len(high_risk_patients)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/care-plan', methods=['GET'])
@require_healthcare_provider()
@patient_data_access_required()
def get_patient_care_plan(patient_id):
    """Get care plan for a patient"""
    try:
        care_plan = mongo.db.care_plans.find_one({
            'patient_id': ObjectId(patient_id),
            'is_active': True
        })
        
        if care_plan:
            care_plan['_id'] = str(care_plan['_id'])
            care_plan['patient_id'] = str(care_plan['patient_id'])
            care_plan['created_by'] = str(care_plan['created_by'])
        
        return jsonify({'care_plan': care_plan})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provider_bp.route('/patients/<patient_id>/care-plan', methods=['POST'])
@require_healthcare_provider()
@patient_data_access_required()
def create_patient_care_plan(patient_id):
    """Create or update care plan for a patient"""
    try:
        provider_id = get_jwt_identity()
        data = request.get_json()
        
        # Deactivate existing care plan
        mongo.db.care_plans.update_many(
            {'patient_id': ObjectId(patient_id)},
            {'$set': {'is_active': False}}
        )
        
        # Create new care plan
        care_plan = {
            'patient_id': ObjectId(patient_id),
            'created_by': ObjectId(provider_id),
            'title': data.get('title', 'Care Plan'),
            'goals': data.get('goals', []),
            'interventions': data.get('interventions', []),
            'timeline': data.get('timeline', {}),
            'notes': data.get('notes', ''),
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.care_plans.insert_one(care_plan)
        
        return jsonify({
            'message': 'Care plan created successfully',
            'care_plan_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
