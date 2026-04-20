from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from ..utils.database import mongo
from datetime import datetime, timedelta

sentiment_bp = Blueprint('sentiment', __name__, url_prefix='/api/sentiment')

@sentiment_bp.route('/timeseries', methods=['GET', 'OPTIONS'])
@cross_origin()
@jwt_required()
def sentiment_timeseries():
    if request.method == 'OPTIONS':
        return '', 200

    user_id = get_jwt_identity()
    try:
        days = max(1, min(int(request.args.get('days', 30)), 180))
    except Exception:
        days = 30

    start_dt = datetime.utcnow() - timedelta(days=days)

    try:
        pipeline = [
            { '$match': { 'user_id': user_id } },
            { '$unwind': '$messages' },
            { '$match': {
                'messages.sender': 'user',
                'messages.timestamp': { '$gte': start_dt }
            }},
            { '$project': {
                '_id': 0,
                'timestamp': '$messages.timestamp',
                'score': { '$ifNull': [ '$messages.sentiment.score', None ] },
                'label': { '$ifNull': [ '$messages.sentiment.label', None ] }
            }},
            { '$match': { 'score': { '$ne': None } }},
            { '$sort': { 'timestamp': 1 } }
        ]

        points = list(mongo.db.chats.aggregate(pipeline))

        # Aggregate by day (UTC) average
        daily = {}
        for p in points:
            day = p['timestamp'].date().isoformat()
            d = daily.setdefault(day, { 'sum': 0.0, 'n': 0 })
            d['sum'] += float(p.get('score', 0.0))
            d['n'] += 1
        daily_series = [
            { 'date': day, 'avg': (v['sum'] / v['n']) if v['n'] else 0.0, 'count': v['n'] }
            for day, v in sorted(daily.items())
        ]

        return jsonify({
            'points': points,          # raw chronological points
            'daily': daily_series,     # per-day averages
            'window_days': days
        }), 200
    except Exception as e:
        print(f"❌ Error building sentiment timeseries: {str(e)}")
        return jsonify({ 'error': 'Failed to build sentiment series' }), 500
