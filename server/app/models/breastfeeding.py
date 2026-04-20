from datetime import datetime, timedelta
from bson import ObjectId
from ..utils.database import mongo


class BreastfeedingModel:
    """Data access and business logic for breastfeeding tracking."""

    # ---------------------- Feeding Sessions ----------------------
    @staticmethod
    def start_feed(user_id: str) -> str:
        doc = {
            'user_id': ObjectId(user_id),
            'started_at': datetime.utcnow(),
            'status': 'ongoing',
            'sides': [],  # list of {side: 'left'|'right', duration_sec: int}
            'type': 'breast',
            'notes': '',
        }
        res = mongo.db.feeding_sessions.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def stop_feed(user_id: str, session_id: str, payload: dict) -> dict:
        session = mongo.db.feeding_sessions.find_one({'_id': ObjectId(session_id), 'user_id': ObjectId(user_id)})
        if not session:
            raise ValueError('Session not found')

        ended_at = datetime.utcnow()
        started_at = session.get('started_at', ended_at)
        duration = int((ended_at - started_at).total_seconds())

        update = {
            'ended_at': ended_at,
            'duration_sec': duration,
            'status': 'completed',
            'sides': payload.get('sides', session.get('sides', [])),
            'type': payload.get('type', 'breast'),
            'bottle_amount_ml': payload.get('bottle_amount_ml'),
            'mood': payload.get('mood'),
            'pain_level': payload.get('pain_level'),
            'baby_behavior': payload.get('baby_behavior'),
            'sleep_after_min': payload.get('sleep_after_min'),
            'notes': payload.get('notes', ''),
        }

        mongo.db.feeding_sessions.update_one({'_id': session['_id']}, {'$set': update})
        update['session_id'] = session_id
        return update

    @staticmethod
    def get_feed_history(user_id: str, start: datetime, end: datetime) -> list:
        cur = mongo.db.feeding_sessions.find({
            'user_id': ObjectId(user_id),
            'started_at': {'$gte': start, '$lte': end}
        }).sort('started_at', 1)
        return [BreastfeedingModel._serialize(doc) for doc in cur]

    @staticmethod
    def get_feed_summary(user_id: str, start: datetime, end: datetime) -> dict:
        pipeline = [
            {'$match': {
                'user_id': ObjectId(user_id),
                'started_at': {'$gte': start, '$lte': end},
                'status': 'completed'
            }},
            {'$group': {
                '_id': None,
                'count': {'$sum': 1},
                'total_duration': {'$sum': {'$ifNull': ['$duration_sec', 0]}},
                'avg_mood': {'$avg': {'$ifNull': ['$mood', None]}},
                'avg_pain': {'$avg': {'$ifNull': ['$pain_level', None]}},
                'avg_sleep_after_min': {'$avg': {'$ifNull': ['$sleep_after_min', None]}}
            }}
        ]
        agg = list(mongo.db.feeding_sessions.aggregate(pipeline))
        summary = agg[0] if agg else {'count': 0, 'total_duration': 0}
        # avg gap between feeds
        history = BreastfeedingModel.get_feed_history(user_id, start, end)
        gaps = []
        for i in range(1, len(history)):
            prev_end = history[i-1].get('ended_at') or history[i-1]['started_at']
            cur_start = history[i]['started_at']
            gaps.append((cur_start - prev_end).total_seconds())
        avg_gap = sum(gaps)/len(gaps) if gaps else None
        # simple cluster-feed window detection (18-21 local fallback using UTC)
        hours = {}
        for h in history:
            hr = h['started_at'].hour
            hours[hr] = hours.get(hr, 0) + 1
        cluster_window = max(hours, key=hours.get) if hours else None
        return {
            'count': summary.get('count', 0),
            'total_duration_sec': summary.get('total_duration', 0),
            'avg_gap_sec': avg_gap,
            'cluster_hour': cluster_window,
            'avg_mood': summary.get('avg_mood'),
            'avg_pain': summary.get('avg_pain'),
            'avg_sleep_after_min': summary.get('avg_sleep_after_min'),
        }

    # ---------------------- Pumping ----------------------
    @staticmethod
    def log_pump(user_id: str, payload: dict) -> str:
        started_at = payload.get('started_at') or datetime.utcnow()
        ended_at = payload.get('ended_at') or started_at
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        if isinstance(ended_at, str):
            ended_at = datetime.fromisoformat(ended_at)
        duration = int((ended_at - started_at).total_seconds())
        outputs = payload.get('outputs', [])  # [{side, amount_ml}]
        total_ml = sum([o.get('amount_ml', 0) for o in outputs])
        doc = {
            'user_id': ObjectId(user_id),
            'started_at': started_at,
            'ended_at': ended_at,
            'duration_sec': duration,
            'outputs': outputs,
            'total_amount_ml': total_ml,
            'notes': payload.get('notes', '')
        }
        res = mongo.db.pumping_sessions.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def get_pump_summary(user_id: str, start: datetime, end: datetime) -> dict:
        pipeline = [
            {'$match': {
                'user_id': ObjectId(user_id),
                'started_at': {'$gte': start, '$lte': end}
            }},
            {'$group': {
                '_id': None,
                'count': {'$sum': 1},
                'total_ml': {'$sum': {'$ifNull': ['$total_amount_ml', 0]}},
                'total_duration': {'$sum': {'$ifNull': ['$duration_sec', 0]}}
            }}
        ]
        agg = list(mongo.db.pumping_sessions.aggregate(pipeline))
        return agg[0] if agg else {'count': 0, 'total_ml': 0, 'total_duration': 0}

    # ---------------------- Diapers ----------------------
    @staticmethod
    def log_diaper(user_id: str, payload: dict) -> str:
        doc = {
            'user_id': ObjectId(user_id),
            'timestamp': datetime.utcnow(),
            'wet_count': int(payload.get('wet_count', 0)),
            'dirty_count': int(payload.get('dirty_count', 0)),
            'notes': payload.get('notes', '')
        }
        res = mongo.db.diaper_logs.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def get_diaper_summary(user_id: str, start: datetime, end: datetime) -> dict:
        pipeline = [
            {'$match': {
                'user_id': ObjectId(user_id),
                'timestamp': {'$gte': start, '$lte': end}
            }},
            {'$group': {
                '_id': None,
                'wet_total': {'$sum': {'$ifNull': ['$wet_count', 0]}},
                'dirty_total': {'$sum': {'$ifNull': ['$dirty_count', 0]}}
            }}
        ]
        agg = list(mongo.db.diaper_logs.aggregate(pipeline))
        return agg[0] if agg else {'wet_total': 0, 'dirty_total': 0}

    # ---------------------- Weight ----------------------
    @staticmethod
    def log_weight(user_id: str, payload: dict) -> str:
        doc = {
            'user_id': ObjectId(user_id),
            'recorded_at': datetime.fromisoformat(payload['recorded_at']) if isinstance(payload.get('recorded_at'), str) else (payload.get('recorded_at') or datetime.utcnow()),
            'weight_kg': float(payload['weight_kg']),
            'notes': payload.get('notes', '')
        }
        res = mongo.db.baby_weights.insert_one(doc)
        return str(res.inserted_id)

    @staticmethod
    def get_weight_history(user_id: str, start: datetime, end: datetime) -> list:
        cur = mongo.db.baby_weights.find({
            'user_id': ObjectId(user_id),
            'recorded_at': {'$gte': start, '$lte': end}
        }).sort('recorded_at', 1)
        return [BreastfeedingModel._serialize(doc) for doc in cur]

    # ---------------------- Insights & Reminders ----------------------
    @staticmethod
    def get_insights(user_id: str, start: datetime, end: datetime) -> dict:
        feed_sum = BreastfeedingModel.get_feed_summary(user_id, start, end)
        diaper_sum = BreastfeedingModel.get_diaper_summary(user_id, start, end)
        insights = []
        if feed_sum['count'] < 8 and (end - start) <= timedelta(days=1):
            insights.append('Feeding frequency is below 8 today. Consider offering feeds more frequently.')
        if diaper_sum.get('wet_total', 0) >= 6:
            insights.append('Great job! 6+ wet diapers indicates good hydration.')
        if feed_sum.get('cluster_hour') is not None and 18 <= feed_sum['cluster_hour'] <= 21:
            insights.append('Pattern: cluster feeding typically occurs between 6–9 PM.')
        return {
            'insights': insights,
            'feed_summary': feed_sum,
            'diaper_summary': diaper_sum,
        }

    @staticmethod
    def get_reminders(user_id: str) -> dict:
        last = mongo.db.feeding_sessions.find({'user_id': ObjectId(user_id)}).sort('started_at', -1).limit(1)
        last_start = None
        for d in last:
            last_start = d.get('started_at')
        if not last_start:
            return {'since_last_feed_min': None, 'needs_reminder': False}
        delta_min = int((datetime.utcnow() - last_start).total_seconds() / 60)
        return {'since_last_feed_min': delta_min, 'needs_reminder': delta_min >= 180}

    # ---------------------- Utils ----------------------
    @staticmethod
    def _serialize(doc: dict) -> dict:
        if not doc:
            return {}
        d = dict(doc)
        d['id'] = str(d.pop('_id'))
        return d
