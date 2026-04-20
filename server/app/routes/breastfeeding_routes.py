from flask import Blueprint
from ..controllers.breastfeeding_controller import BreastfeedingController

breastfeeding_bp = Blueprint('breastfeeding', __name__)

# Feeding sessions
@breastfeeding_bp.route('/feed/start', methods=['POST'])
def start_feed():
    return BreastfeedingController.start_feed()

@breastfeeding_bp.route('/feed/stop', methods=['POST'])
def stop_feed():
    return BreastfeedingController.stop_feed()

@breastfeeding_bp.route('/feed/history', methods=['GET'])
def feed_history():
    return BreastfeedingController.feed_history()

@breastfeeding_bp.route('/feed/summary', methods=['GET'])
def feed_summary():
    return BreastfeedingController.feed_summary()

# Pumping
@breastfeeding_bp.route('/pump', methods=['POST'])
def log_pump():
    return BreastfeedingController.log_pump()

@breastfeeding_bp.route('/pump/summary', methods=['GET'])
def pump_summary():
    return BreastfeedingController.pump_summary()

# Diapers
@breastfeeding_bp.route('/diaper', methods=['POST'])
def log_diaper():
    return BreastfeedingController.log_diaper()

@breastfeeding_bp.route('/diaper/summary', methods=['GET'])
def diaper_summary():
    return BreastfeedingController.diaper_summary()

# Weight
@breastfeeding_bp.route('/weight', methods=['POST'])
def log_weight():
    return BreastfeedingController.log_weight()

@breastfeeding_bp.route('/weight/history', methods=['GET'])
def weight_history():
    return BreastfeedingController.weight_history()

# Insights & Reminders
@breastfeeding_bp.route('/insights', methods=['GET'])
def insights():
    return BreastfeedingController.insights()

@breastfeeding_bp.route('/reminders', methods=['GET'])
def reminders():
    return BreastfeedingController.reminders()
