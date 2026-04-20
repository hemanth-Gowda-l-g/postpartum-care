from flask import request, jsonify
from datetime import datetime, timedelta
from ..models.breastfeeding import BreastfeedingModel
from flask_jwt_extended import jwt_required, get_jwt_identity


def _parse_range():
    # default: today (UTC) range
    now = datetime.utcnow()
    start_param = request.args.get('from')
    end_param = request.args.get('to')
    if start_param:
        start = datetime.fromisoformat(start_param)
    else:
        start = datetime(now.year, now.month, now.day)
    if end_param:
        end = datetime.fromisoformat(end_param)
    else:
        end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end


class BreastfeedingController:
    @staticmethod
    @jwt_required(optional=True)
    def start_feed():
        user_id = request.json.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        session_id = BreastfeedingModel.start_feed(user_id)
        return jsonify({'session_id': session_id}), 200

    @staticmethod
    @jwt_required(optional=True)
    def stop_feed():
        data = request.json or {}
        user_id = data.get('user_id') or get_jwt_identity()
        session_id = data.get('session_id')
        if not user_id or not session_id:
            return jsonify({'error': 'user_id and session_id are required'}), 400
        try:
            result = BreastfeedingModel.stop_feed(user_id, session_id, data)
            return jsonify(result), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 404

    @staticmethod
    @jwt_required(optional=True)
    def feed_history():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        items = BreastfeedingModel.get_feed_history(user_id, start, end)
        return jsonify({'items': items}), 200

    @staticmethod
    @jwt_required(optional=True)
    def feed_summary():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        summary = BreastfeedingModel.get_feed_summary(user_id, start, end)
        return jsonify(summary), 200

    @staticmethod
    @jwt_required(optional=True)
    def log_pump():
        data = request.json or {}
        user_id = data.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        _id = BreastfeedingModel.log_pump(user_id, data)
        return jsonify({'id': _id}), 200

    @staticmethod
    @jwt_required(optional=True)
    def pump_summary():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        summary = BreastfeedingModel.get_pump_summary(user_id, start, end)
        return jsonify(summary), 200

    @staticmethod
    @jwt_required(optional=True)
    def log_diaper():
        data = request.json or {}
        user_id = data.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        _id = BreastfeedingModel.log_diaper(user_id, data)
        return jsonify({'id': _id}), 200

    @staticmethod
    @jwt_required(optional=True)
    def diaper_summary():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        summary = BreastfeedingModel.get_diaper_summary(user_id, start, end)
        return jsonify(summary), 200

    @staticmethod
    @jwt_required(optional=True)
    def log_weight():
        data = request.json or {}
        user_id = data.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        try:
            _id = BreastfeedingModel.log_weight(user_id, data)
            return jsonify({'id': _id}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @staticmethod
    @jwt_required(optional=True)
    def weight_history():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        items = BreastfeedingModel.get_weight_history(user_id, start, end)
        return jsonify({'items': items}), 200

    @staticmethod
    @jwt_required(optional=True)
    def insights():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        start, end = _parse_range()
        data = BreastfeedingModel.get_insights(user_id, start, end)
        return jsonify(data), 200

    @staticmethod
    @jwt_required(optional=True)
    def reminders():
        user_id = request.args.get('user_id') or get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        data = BreastfeedingModel.get_reminders(user_id)
        return jsonify(data), 200
