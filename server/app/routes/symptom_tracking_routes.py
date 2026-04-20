from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.errors import InvalidId
from app.models.symptom_tracking import SymptomTracking
from app.models.ppd_assessment import PPDAssessment # Import to get symptom names from questions
from flask_cors import cross_origin # Import cross_origin

symptom_tracking_bp = Blueprint('symptom_tracking', __name__, url_prefix='/api/symptom-tracking')

@symptom_tracking_bp.route('/track', methods=['POST'])
@jwt_required()
@cross_origin()
def track_symptom():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'symptom_name' not in data or 'value' not in data:
        return jsonify({'msg': 'Missing symptom_name or value in request body'}), 400

    symptom_name = data['symptom_name']
    value = data['value']

    try:
        result = SymptomTracking.save_symptom_entry(user_id, symptom_name, value)
        return jsonify({'msg': 'Symptom entry saved successfully', 'entry_id': str(result.inserted_id)}), 201
    except InvalidId:
        return jsonify({'msg': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'msg': f'Error saving symptom entry: {str(e)}'}), 500

@symptom_tracking_bp.route('/history/<symptom_name>', methods=['GET'])
@jwt_required()
@cross_origin()
def get_history(symptom_name):
    user_id = get_jwt_identity()
    limit = request.args.get('limit', type=int)

    try:
        history = SymptomTracking.get_symptom_history(user_id, symptom_name, limit)
        return jsonify(history), 200
    except InvalidId:
        return jsonify({'msg': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'msg': f'Error retrieving symptom history: {str(e)}'}), 500

@symptom_tracking_bp.route('/symptoms', methods=['GET'])
@jwt_required()
def get_user_symptom_names():
    user_id = get_jwt_identity()
    try:
        symptom_names = SymptomTracking.get_all_symptom_names_for_user(user_id)
        return jsonify(symptom_names), 200
    except InvalidId:
        return jsonify({'msg': 'Invalid user ID'}), 400
    except Exception as e:
        return jsonify({'msg': f'Error retrieving symptom names: {str(e)}'}), 500

@symptom_tracking_bp.route('/all-possible-symptoms', methods=['GET'])
@jwt_required()
@cross_origin()
def get_all_possible_symptoms():
    # This route provides the list of symptoms from the PPD assessment
    # as potential symptoms the user might want to track.
    try:
        # Access the questions dictionary from the PPD assessment logic
        # This might require refactoring to make the questions accessible, 
        # or ideally, store these trackable symptoms in a separate config/database.
        # For now, we'll manually list the relevant ones from the PPD questions.
        # Ensure this list matches the keys used in the PPD assessment data.
        ppd_assessment_questions_keys = [
             'Feeling sad or Tearful',
             'Irritable towards baby & partner',
             'Trouble sleeping at night',
             'Problems concentrating or making decision',
             'Overeating or loss of appetite',
             'Feeling anxious',
             'Feeling of guilt',
             'Problems of bonding with baby'
        ]
        # We can also add other general symptoms not directly from the PPD test
        # For example: 'Energy Level', 'Motivation', 'Appetite', 'Sleep Quality'
        
        all_symptoms = ppd_assessment_questions_keys # Using PPD questions as initial list
        
        return jsonify(all_symptoms), 200
    except Exception as e:
        return jsonify({'msg': f'Error retrieving possible symptom list: {str(e)}'}), 500 