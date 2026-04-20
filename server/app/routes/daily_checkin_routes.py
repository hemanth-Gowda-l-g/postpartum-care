from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.daily_checkin import DailyCheckin
from flask_cors import cross_origin

daily_checkin_bp = Blueprint('daily_checkin', __name__, url_prefix='/api/daily-checkin')

@daily_checkin_bp.route('/save', methods=['POST'])
@jwt_required()
@cross_origin()
def save_daily_checkin():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'mood' not in data or 'journal_entry' not in data:
        return jsonify({'msg': 'Missing mood or journal_entry in request body'}), 400

    mood = data['mood']
    journal_entry = data['journal_entry']

    try:
        DailyCheckin.save_checkin(user_id, mood, journal_entry)
        return jsonify({'msg': 'Daily check-in saved successfully'}), 201
    except Exception as e:
        return jsonify({'msg': f'Error saving daily check-in: {str(e)}'}), 500

@daily_checkin_bp.route('/history', methods=['GET'])
@jwt_required()
@cross_origin()
def get_daily_checkin_history():
    user_id = get_jwt_identity()
    limit = request.args.get('limit', default=10, type=int) # Default to 10 most recent

    try:
        history = DailyCheckin.get_checkins_for_user(user_id, limit)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({'msg': f'Error retrieving daily check-in history: {str(e)}'}), 500 