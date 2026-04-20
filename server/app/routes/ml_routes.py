def contains_self_harm_language(text: str) -> bool:
    """Simple heuristic to detect self-harm/suicidal ideation cues."""
    if not isinstance(text, str):
        return False
    t = text.lower()
    patterns = [
        r"\bsuicid(e|al)\b",
        r"\bkill myself\b",
        r"\bend my life\b",
        r"\bharm myself\b",
        r"\bself[- ]?harm\b",
        r"\bhurt myself\b",
        r"\bno reason to live\b",
        r"\btake my life\b",
        r"\bi want to die\b",
        r"\bwish i were dead\b",
    ]
    return any(re.search(p, t) for p in patterns)
import os
import joblib
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from app.utils.database import mongo
from ..models.nutrition_model import NutritionModel
from typing import Dict, Any
from math import isnan
import re

# Optional: Hugging Face emotion analysis (lazy init) — mental-health relevant
emotion_analyzer = None
def get_emotion_analyzer():
    global emotion_analyzer
    if emotion_analyzer is None:
        try:
            from transformers import pipeline
            # Emotion model with labels: anger, disgust, fear, joy, neutral, sadness, surprise
            # Ref: https://huggingface.co/j-hartmann/emotion-english-distilroberta-base
            emotion_analyzer = pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base', return_all_scores=True)
        except Exception as e:
            print(f"⚠️ Failed to initialize Hugging Face emotion analyzer: {e}")
            emotion_analyzer = None
    return emotion_analyzer

# Import utility functions

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# --- PPD Risk Analysis Components ---
# Load PPD Risk Analysis ML components
# Corrected path to point to the ml/models directory at the workspace root
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) , 'ml', 'models')

model = None
calibrated_model = None
label_encoders = None
imputer = None
features = None

try:
    # Load model bundle
    model_bundle_path = os.path.join(MODEL_DIR, 'ppd_model_bundle.pkl')
    if os.path.exists(model_bundle_path):
        model_bundle = joblib.load(model_bundle_path)
        model = model_bundle['model']
        label_encoders = model_bundle['label_encoders']
        imputer = model_bundle['imputer']
        features = model_bundle['features']
        # Optional calibrated model (e.g., CalibratedClassifierCV)
        calibrated_model = model_bundle.get('calibrated_model')
        print("✅ PPD Risk Analysis ML components loaded successfully")
    else:
        print(f"❌ PPD model bundle not found at {model_bundle_path}")

except Exception as e:
    print(f"❌ Error loading PPD Risk Analysis ML components: {e}")

# Helper function for age conversion (retained from previous logic for PPD analysis)
def age_to_numeric(age_str):
    if pd.isna(age_str):
        return np.nan
    if isinstance(age_str, (int, float)):
        return float(age_str)
    if '-' in str(age_str):
        low, high = map(int, str(age_str).split('-'))
        return (low + high) / 2
    return float(age_str)

# Define the mapping for categorical features based on the questions provided (retained for PPD analysis)
CATEGORICAL_QUESTIONS_MAP = {
    'Feeling sad or Tearful': ['No', 'Sometimes', 'Yes'],
    'Irritable towards baby & partner': ['No', 'Sometimes', 'Yes'],
    'Trouble sleeping at night': ['No', 'Yes', 'Two or more days a week'],
    'Problems concentrating or making decision': ['No', 'Yes', 'Often'],
    'Overeating or loss of appetite': ['No', 'Yes', 'Not at all'],
    'Feeling anxious': ['No', 'Yes'],
    'Feeling of guilt': ['No', 'Maybe', 'Yes'],
    'Problems of bonding with baby': ['No', 'Sometimes', 'Yes']
}

# Initialize nutrition model
nutrition_model = NutritionModel()

@ml_bp.route('/analyze-ppd', methods=['POST'])
@jwt_required()
def analyze_ppd():
    if model is None or label_encoders is None or imputer is None or features is None:
        return jsonify({"msg": "ML components not loaded on the server."}), 500

    current_user = get_jwt_identity()
    user_id = current_user # This is now the user ID string

    data = request.get_json()

    if not data:
        return jsonify({"msg": "No input data provided"}), 400

    # Age validation: PPD assessment applicable for age >= 15
    try:
        raw_age = data.get('Age')
        if raw_age is not None and str(raw_age).strip() != '':
            age_val = age_to_numeric(raw_age)
            if pd.notna(age_val) and float(age_val) < 15:
                return jsonify({
                    "msg": "Age must be 15 years or older for PPD assessment.",
                    "field": "Age"
                }), 400
    except Exception:
        # If age parsing fails, continue to imputer which will handle NaN, but do not block request
        pass

    # Prepare data for prediction
    input_data = {}
    # Use the feature names loaded from the model bundle to ensure correct order
    for feature in features:
        if feature == 'Age':
            input_data[feature] = [data.get(feature, np.nan)]
        elif feature in CATEGORICAL_QUESTIONS_MAP:
            answer = data.get(feature)
            if answer is None or answer not in CATEGORICAL_QUESTIONS_MAP[feature]:
                input_data[feature] = [np.nan]
            else:
                input_data[feature] = [answer]
        else:
            # Handle any other features if necessary, default to NaN
            input_data[feature] = [data.get(feature, np.nan)]
            # print(f"Warning: Unexpected feature '{feature}' in features list. Handled with NaN.")
            
    input_df = pd.DataFrame(input_data)

    # Preprocess the new data (same as training script)
    try:
        # Convert age to numeric
        if 'Age' in input_df.columns:
             input_df['Age'] = input_df['Age'].apply(age_to_numeric)

        # Label encode categorical features using the loaded encoders
        for feature in features:
             if feature != 'Age' and feature in label_encoders:
                 input_df.loc[:, feature] = input_df[feature].map(lambda x: label_encoders[feature].transform([x])[0] if pd.notna(x) and x in label_encoders[feature].classes_ else np.nan)

        # Impute missing values using the loaded imputer
        # Ensure the DataFrame has the same columns as the features used during imputer training and in the correct order.
        # Excluding 'risk_level' here as it's not part of the input features for the PPD risk model itself.
        X_new = imputer.transform(input_df[[f for f in features if f != 'risk_level']])

        # Make predictions
        prediction_numeric = model.predict(X_new)[0]
        # Prefer calibrated model probabilities if available
        if calibrated_model is not None and hasattr(calibrated_model, 'predict_proba'):
            probabilities = calibrated_model.predict_proba(X_new)[0]
        else:
            probabilities = model.predict_proba(X_new)[0] if hasattr(model, 'predict_proba') else None

        # Use probability-based thresholding for risk classification (binary)
        # Low: < 50% (no probability displayed)
        # High: >= 50% (display probability)
        prob_high = None
        urgent_flag = False
        if probabilities is not None:
            prob_high = float(probabilities[1])

            # --- Optional free-text emotion adjustment ---
            # Allow client to pass 'free_text' describing feelings in their own words.
            free_text = data.get('free_text') or data.get('notes') or data.get('journal')
            if isinstance(free_text, str) and free_text.strip():
                analyzer = get_emotion_analyzer()
                if analyzer is not None:
                    try:
                        res = analyzer(free_text[:1000], truncation=True)
                        # res is a list with one element (per input), which is a list of {label, score}
                        scores = {item['label'].lower(): float(item['score']) for item in res[0]}
                        # Define negative and positive emotion groups
                        neg_emotions = ['sadness', 'fear', 'anger', 'disgust']
                        pos_emotions = ['joy']
                        # neutral and surprise treated as near-neutral
                        neg_sum = sum(scores.get(e, 0.0) for e in neg_emotions)
                        pos_sum = sum(scores.get(e, 0.0) for e in pos_emotions)
                        # Risk signal in [-1, 1]
                        signal = max(-1.0, min(1.0, neg_sum - pos_sum))
                        # Blend: up to ±0.20 adjustment based on emotion signal
                        # Negative emotions increase risk; joy decreases
                        adjustment = max(-0.20, min(0.20, signal * 0.20))
                        prob_high = max(0.0, min(1.0, prob_high + adjustment))
                    except Exception as e:
                        print(f"⚠️ Emotion analysis failed: {e}")

                # Safety override: detect self-harm/suicidal ideation
                try:
                    if contains_self_harm_language(free_text):
                        urgent_flag = True
                except Exception:
                    pass

            prediction_result = "High Risk" if prob_high >= 0.50 else "Low Risk"
        else:
            # Fallback to model class prediction if probabilities are unavailable
            prediction_result = "High Risk" if prediction_numeric == 1 else "Low Risk"

        # --- Generate Assistance based on Risk Level ---
        assistance = {
            'recommendations': [],
            'resources': []
        }

        if prediction_result == "High Risk" or urgent_flag:
            assistance['recommendations'] = [
                "Seek immediate professional help from a healthcare provider or mental health specialist.",
                "Talk to your partner, family, or friends about how you're feeling.",
                "Prioritize self-care, even in small ways (rest, nutrition, gentle activity)."
            ]
            assistance['resources'] = [
                {'name': 'Postpartum Support International (PSI)', 'contact': '1-800-944-4773', 'website': 'https://www.postpartum.net/'},
                {'name': 'National Crisis and Suicide Lifeline', 'contact': '988'},
                {'name': 'Find a Perinatal Mental Health Specialist', 'website': 'https://psidirectory.com/'},
            ]
        else: # Low Risk
            assistance['recommendations'] = [
                "Continue to monitor your emotional well-being.",
                "Prioritize self-care, including adequate rest and nutrition.",
                "Maintain open communication with your support network.",
                "If symptoms change or worsen, consider retaking the assessment and consulting a healthcare provider."
            ]
            # Optionally add general wellness resources here

    except Exception as e:
        print(f"Error during data preprocessing or model prediction: {e}")
        # Return a more informative error if possible, but avoid exposing internal details
        return jsonify({"msg": "Error processing data or predicting PPD risk."}), 500

    # Store results in MongoDB
    try:
        ppd_result = {
            'user_id': ObjectId(user_id),
            'raw_answers': data, # Store raw answers from client
            'prediction': prediction_result,
            'probability': probabilities[1] if probabilities is not None else None, # Store probability of high risk
            'timestamp': datetime.utcnow(),
            'assistance': assistance # Store assistance provided
        }
        mongo.db.ppd_test_results.insert_one(ppd_result)
        print(f"PPD test results saved for user {user_id}")
    except Exception as e:
        print(f"Error saving PPD test results: {e}")
        # Log the error but don't necessarily return a 500 to the user if prediction was successful

    # Return prediction and probability to client, including assistance
    response_data = {
        "prediction": "High Risk" if urgent_flag else prediction_result,
        "assistance": assistance
    }
    # Include probability if >= 50% OR if urgent flag (to provide more context to clinicians)
    if probabilities is not None and prob_high is not None and (prob_high >= 0.50 or urgent_flag):
        response_data["probability"] = round(prob_high * 100, 2)
    if urgent_flag:
        response_data["urgent"] = True

    # Structured log for monitoring (non-PII)
    try:
        print({
            'ppd_inference': True,
            'risk': "High Risk" if urgent_flag else prediction_result,
            'prob_percent': round(prob_high * 100, 2) if prob_high is not None else None,
            'has_calibrated_model': calibrated_model is not None
        })
    except Exception:
        pass

    return jsonify(response_data), 200

@ml_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_ml_stats():
    # Example: Load dataset stats (assuming this is still needed for the dashboard stats section)
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml', 'datasets', 'post_natal_data.csv')
    
    if not os.path.exists(data_path):
         # If the dataset isn't crucial for dashboard stats, you might return partial stats or a different message
         # For now, returning an error if the file is not found.
         # return jsonify({"msg": f"Dataset file not found at {data_path}"}), 500 # Or handle gracefully
         total_records = 0
         ppd_positive_percentage = 0
         print(f"⚠️ Dataset file not found at {data_path}. Cannot provide full dataset stats.")
    else:
         try:
            df = pd.read_csv(data_path)
            total_records = len(df)
            # Assuming 'PPD_Risk' column exists after training the main PPD model
            # You might need to load the trained data or aggregate results from MongoDB instead
            if 'PPD_Risk' in df.columns:
                 ppd_positive_count = df['PPD_Risk'].sum() # Assuming 1 for positive
                 ppd_positive_percentage = (ppd_positive_count / total_records) * 100 if total_records > 0 else 0
            else:
                 ppd_positive_percentage = 0
                 print("⚠️ 'PPD_Risk' column not found in dataset. Cannot calculate positive percentage.")

         except Exception as e:
            print(f"Error loading or processing dataset stats: {e}")
            # return jsonify({"msg": "Error loading ML dashboard stats."}) # Or handle gracefully
            total_records = 0
            ppd_positive_percentage = 0

    # You can add more ML-related stats here, e.g., count of PPD tests taken, distribution of risk levels from MongoDB
    try:
        total_ppd_tests = mongo.db.ppd_test_results.count_documents({})
        high_risk_tests = mongo.db.ppd_test_results.count_documents({'prediction': 'High Risk'})
        low_risk_tests = mongo.db.ppd_test_results.count_documents({'prediction': 'Low Risk'})

        return jsonify({
            'dataset_stats': {
                'size': total_records,
                # 'features': list(df.columns), # Uncomment if df is loaded and you want to show features
                'ppd_positive_percentage_in_dataset': round(ppd_positive_percentage, 1) # Renamed for clarity
            },
            'ppd_test_stats': {
                'total_tests': total_ppd_tests,
                'high_risk_tests': high_risk_tests,
                'low_risk_tests': low_risk_tests,
                'high_risk_percentage': round((high_risk_tests / total_ppd_tests) * 100, 1) if total_ppd_tests > 0 else 0
            }
        }), 200

    except Exception as e:
        print(f"❌ Error fetching PPD test stats from MongoDB: {e}")
        return jsonify({"msg": "Error loading ML dashboard stats."}), 500

@ml_bp.route('/predict-nutrition', methods=['POST'])
@jwt_required()
def predict_nutrition():
    if nutrition_model.model is None:
        return jsonify({"msg": "Nutrition model not loaded on the server."}), 500

    current_user = get_jwt_identity()
    user_id = current_user

    try:
        # Get prediction
        prediction_result = nutrition_model.predict(request.get_json())

        # Store results in MongoDB
        nutrition_result = {
            'user_id': ObjectId(user_id),
            'prediction': prediction_result['prediction'],
            'confidence': prediction_result['confidence'],
            'timestamp': datetime.utcnow()
        }
        mongo.db.nutrition_predictions.insert_one(nutrition_result)
        print(f"Nutrition prediction saved for user {user_id}")

        return jsonify(prediction_result), 200

    except Exception as e:
        print(f"Error during nutrition prediction: {e}")
        return jsonify({"msg": "Error processing nutrition prediction."}), 500