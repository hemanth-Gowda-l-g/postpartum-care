from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
from .utils.database import mongo
from flask import request, jsonify
from datetime import timedelta

jwt = JWTManager()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    # Configuration
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}})
    mongo.init_app(app)
    jwt.init_app(app)
    
    # Handle CORS preflight requests globally
    @app.route('/<path:dummy>', methods=['OPTIONS'])
    def _cors_preflight(dummy):
        response = app.make_default_options_response()
        return response

    @app.route('/', methods=['OPTIONS'])
    def _cors_preflight_root():
        response = app.make_default_options_response()
        return response

    
    # Initialize roles
    from .models.role import Role
    Role.initialize_default_roles()

    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.dashboard_routes import dashboard_bp
    from .routes.ml_routes import ml_bp
    from .routes.chatbot_routes import chatbot_bp
    from .routes.nutrition import nutrition_bp
    from .routes.symptom_tracking_routes import symptom_tracking_bp
    from .routes.daily_checkin_routes import daily_checkin_bp
    from .routes.admin_routes import admin_bp
    from .routes.provider_routes import provider_bp
    from .routes.task_routes import task_bp
    from .routes.care_plan import care_plan_bp
    from .routes.ppd_routes import ppd_bp
    from .routes.breastfeeding_routes import breastfeeding_bp
    from .routes.sentiment_routes import sentiment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(sentiment_bp, url_prefix='/api/sentiment')
    app.register_blueprint(nutrition_bp, url_prefix='/api/nutrition')
    app.register_blueprint(symptom_tracking_bp, url_prefix='/api/symptom-tracking')
    app.register_blueprint(daily_checkin_bp, url_prefix='/api/daily-checkin')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(provider_bp, url_prefix='/api/provider')
    app.register_blueprint(task_bp, url_prefix='/api/tasks') # Register the new task blueprint
    app.register_blueprint(care_plan_bp, url_prefix='/api/care-plan')
    app.register_blueprint(ppd_bp, url_prefix='/api/ppd')
    app.register_blueprint(breastfeeding_bp, url_prefix='/api/breastfeeding')

    # Initialize chatbot on startup
    try:
        from .ml_services.chatbot.rag_service import rag_service
        print("🤖 Initializing chatbot...")
        if rag_service.initialize():
            print("✅ Chatbot initialized successfully")
        else:
            print("❌ Failed to initialize chatbot")
    except Exception as e:
        print(f"❌ Error initializing chatbot: {str(e)}")

    return app
