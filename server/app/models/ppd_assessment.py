from datetime import datetime
from app.utils.database import mongo

class PPDAssessment:
    @staticmethod
    def save_assessment(user_id, responses, risk_score):
        return mongo.db.ppd_assessments.insert_one({
            'user_id': user_id,
            'responses': responses,
            'risk_score': risk_score,
            'date': datetime.utcnow()
        })
    
    @staticmethod
    def get_latest_assessment(user_id):
        """Get the most recent PPD assessment for a user"""
        return mongo.db.ppd_assessments.find_one(
            {'user_id': user_id},
            sort=[('date', -1)]
        )
    
    @staticmethod
    def convert_risk_to_epds_score(risk_percentage):
        """Convert PPD risk percentage (0-1) to approximate EPDS score (0-30)"""
        # Risk percentage is typically 0-1, convert to EPDS-like score
        # Higher risk = higher EPDS score
        if risk_percentage <= 0.3:  # Low risk
            return int(risk_percentage * 30)  # 0-9
        elif risk_percentage <= 0.6:  # Moderate risk  
            return int(9 + (risk_percentage - 0.3) * 40)  # 9-21
        else:  # High risk
            return int(21 + (risk_percentage - 0.6) * 22.5)  # 21-30
