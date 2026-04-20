from flask import Blueprint
from app.controllers.ppd_controller import assess_ppd, get_latest_ppd_score

ppd_bp = Blueprint('ppd', __name__)

ppd_bp.route('/assess', methods=['POST'])(assess_ppd)
ppd_bp.route('/latest-score/<user_id>', methods=['GET'])(get_latest_ppd_score)
