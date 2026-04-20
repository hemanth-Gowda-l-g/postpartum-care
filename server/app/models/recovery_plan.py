from datetime import datetime
from app.utils.database import mongo

class RecoveryPlan:
    @staticmethod
    def create_plan(user_id, delivery_type):
        base_plan = {
            'vaginal': [...],  # tasks for vaginal birth
            'c-section': [...]  # tasks for c-section
        }
        return mongo.db.recovery_plans.insert_one({
            'user_id': user_id,
            'delivery_type': delivery_type,
            'tasks': base_plan[delivery_type],
            'created_at': datetime.utcnow()
        })
