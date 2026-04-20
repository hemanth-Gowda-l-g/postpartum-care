import joblib
import os
import numpy as np
import pandas as pd
from typing import Dict, Any
from pathlib import Path

class NutritionModel:
    def __init__(self):
        # Corrected paths relative to the model file
        # Construct the path relative to the current file (__file__)
        model_path = Path(__file__).parent.parent.parent.parent / 'ml' / 'models' / 'nutrition_model.joblib'
        
        try:
            bundle = joblib.load(model_path)
            # Support both bundle dicts and legacy direct estimators
            if isinstance(bundle, dict) and {'model', 'scaler', 'features'}.issubset(bundle.keys()):
                self.model = bundle  # store the entire bundle for downstream methods
            else:
                # Legacy: wrap into a minimal bundle
                self.model = {
                    'model': bundle,
                    'scaler': None,
                    'features': []
                }
            print("✅ Nutrition model loaded successfully")
        except FileNotFoundError as e:
            print(f"❌ Error loading nutrition model: {e}")
            self.model = None

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make nutrition prediction based on input data"""
        if self.model is None:
            raise ValueError("Model not loaded")
            
        try:
            # Convert input data to the format expected by the model
            # This will need to be adjusted based on your model's requirements
            features = self._prepare_features(input_data)
            
            # Make prediction
            estimator = self.model['model'] if isinstance(self.model, dict) and 'model' in self.model else self.model
            prediction_idx = estimator.predict(features)
            probabilities = estimator.predict_proba(features) if hasattr(estimator, 'predict_proba') else None

            # Decode label if we have a label encoder
            if isinstance(self.model, dict) and 'label_encoder' in self.model and self.model['label_encoder'] is not None:
                prediction_label = self.model['label_encoder'].inverse_transform(prediction_idx)[0]
            else:
                # Fall back to raw value
                prediction_label = prediction_idx[0] if hasattr(prediction_idx, '__iter__') else prediction_idx
            
            return {
                'prediction': prediction_label,
                'confidence': round(max(probabilities[0]) * 100, 2) if probabilities is not None else None
            }
            
        except Exception as e:
            print(f"Error during prediction: {e}")
            raise

    def _prepare_features(self, input_data: Dict[str, Any]) -> np.ndarray:
        """Convert input data to model features"""
        if self.model is None or not isinstance(self.model, dict) or 'features' not in self.model or 'scaler' not in self.model:
            raise ValueError("Model bundle not fully loaded.")

        expected_features = self.model['features']
        scaler = self.model['scaler']

        # Create a DataFrame from input data
        # Ensure columns match expected features and fill missing with 0
        input_df = pd.DataFrame([input_data]) # Convert dict to DataFrame row

        # Add any missing expected features with a default value (0)
        for feature in expected_features:
            if feature not in input_df.columns:
                input_df[feature] = 0

        # Ensure the order of columns matches the training features
        input_df = input_df[expected_features]

        # Scale the input features
        if scaler is not None:
            scaled_features = scaler.transform(input_df)
        else:
            scaled_features = input_df.values

        return scaled_features