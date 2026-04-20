import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import joblib
import os
import sys
import pandas as pd

class NutritionModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoders = None # Will load from file
        self.feature_names = [
            'breastfeeding',
            'diet_type',
            'deficiency',
            'preferred_cuisine'
        ]
        self.load_model_components() # Load model, scaler, and encoders on initialization

    def preprocess_data(self, data):
        """Preprocess raw user data using loaded encoders and scaler"""
        if self.label_encoders is None or self.scaler is None:
            print("❌ Scaler or Label Encoders not loaded.", file=sys.stderr)
            # Depending on requirements, could raise an error or return a default
            # raise RuntimeError("Scaler or Label Encoders not loaded.")
            # For graceful failure, return None or an indicator that preprocessing failed
            return None
            
        processed_data = {}
        # Ensure all expected features are present in incoming data, provide default if not
        # Using get with a default value (e.g., '') for string fields
        processed_data['breastfeeding'] = data.get('breastfeeding', '') # Assuming boolean or string 'yes'/'no'
        processed_data['diet_type'] = data.get('dietType', '')
        processed_data['deficiency'] = data.get('deficiency', '')
        processed_data['preferred_cuisine'] = data.get('preferredCuisine', '')

        # Handle boolean 'breastfeeding' if it comes as boolean, convert to string for encoder
        if isinstance(processed_data['breastfeeding'], bool):
            processed_data['breastfeeding'] = 'yes' if processed_data['breastfeeding'] else 'no'

        # Convert categorical variables to numerical using loaded encoders
        X = pd.DataFrame([processed_data]) # Create a DataFrame for consistent processing

        for col in self.feature_names:
            if col in self.label_encoders:
                 try:
                     # Ensure the value is in the known classes of the encoder
                     if X[col].iloc[0] not in self.label_encoders[col].classes_:
                          # Handle unseen values - assign to a default or raise error
                          print(f"Warning: Unseen value '{X[col].iloc[0]}' for categorical feature {col}. Assigning to default.", file=sys.stderr)
                          # Find the index of 'unknown' or a common default class, or use 0
                          # Simple approach: if unseen, assign 0 (assuming 0 is a common/safe default or corresponds to 'no'/'none')
                          X[col] = 0 # Assign a default numerical value
                     else:
                         X[col] = self.label_encoders[col].transform(X[col])
                 except ValueError as e:
                     print(f"Error transforming categorical feature {col}: {e}", file=sys.stderr)
                     # Handle transformation errors, e.g., due to unexpected data types
                     X[col] = 0 # Assign a default value on error
            elif col in X.columns: # Handle numerical features if any (though none in current feature_names)
                 # Ensure numerical type, handle NaNs if necessary
                 X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

        # Ensure feature order matches training
        X = X[self.feature_names]
        
        # Scale the features using the loaded scaler
        X_scaled = self.scaler.transform(X[self.feature_names])
        
        return X_scaled

    def predict(self, data):
        """Make a prediction using the loaded model"""
        if self.model is None:
            print("❌ Nutrition model not loaded. Cannot predict.", file=sys.stderr)
            # Depending on requirements, could raise an error or return a default
            # raise RuntimeError("Nutrition model not loaded.")
            return None # Return None or a default prediction if model is missing

        # Preprocess the data before making prediction
        processed_data = self.preprocess_data(data)
        
        if processed_data is None:
            print("❌ Data preprocessing failed. Cannot predict.", file=sys.stderr)
            return None # Return None if preprocessing failed

        # Ensure the loaded model has predict_proba method before calling
        if not hasattr(self.model, 'predict_proba'):
             print("❌ Loaded model does not have predict_proba method.", file=sys.stderr)
             # raise AttributeError("Loaded model does not have predict_proba method.")
             # For graceful failure, perhaps return a default prediction or error indicator
             return None

        # Predict probabilities and return the probabilities for the first (and likely only) sample
        try:
            predictions = self.model.predict_proba(processed_data)[0]
            print(f"✅ Prediction successful. Probabilities: {predictions}", file=sys.stderr)
            return predictions
        except Exception as e:
             print(f"❌ Error during prediction: {e}", file=sys.stderr)
             # Handle prediction errors gracefully
             return None # Return None on prediction error


    def load_model_components(self):
        """Load the trained model, scaler, and label encoders"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..', '..') # Go up three directories to reach project root
        model_dir = os.path.join(project_root, 'ml', 'models')
        
        # File paths for the model trained on user features
        model_path = os.path.join(model_dir, 'nutrition_model.joblib') # Original model name
        scaler_path = os.path.join(model_dir, 'nutrition_scaler.joblib') # Original scaler name
        encoders_path = os.path.join(model_dir, 'nutrition_encoders.joblib') # Original encoders name

        print(f"Attempting to load model from: {model_path}", file=sys.stderr)
        print(f"Attempting to load scaler from: {scaler_path}", file=sys.stderr)
        print(f"Attempting to load encoders from: {encoders_path}", file=sys.stderr)

        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"✅ Nutrition model loaded successfully from {model_path}", file=sys.stderr)
            else:
                print(f"⚠️ Nutrition model file not found at {model_path}. Ensure train_and_save_nutrition_model.py has been run.", file=sys.stderr)
                self.model = None

            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print(f"✅ Nutrition scaler loaded successfully from {scaler_path}", file=sys.stderr)
            else:
                print(f"⚠️ Nutrition scaler file not found at {scaler_path}. Ensure train_and_save_nutrition_model.py has been run.", file=sys.stderr)
                self.scaler = None

            if os.path.exists(encoders_path):
                self.label_encoders = joblib.load(encoders_path)
                print(f"✅ Nutrition encoders loaded successfully from {encoders_path}", file=sys.stderr)
            else:
                print(f"⚠️ Nutrition encoders file not found at {encoders_path}. Ensure train_and_save_nutrition_model.py has been run.", file=sys.stderr)
                self.label_encoders = None

        except Exception as e:
            print(f"❌ Error loading nutrition model components: {e}", file=sys.stderr)
            self.model = None
            self.scaler = None
            self.label_encoders = None

