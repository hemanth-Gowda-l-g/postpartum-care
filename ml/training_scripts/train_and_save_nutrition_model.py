import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import joblib
import os
import sys

# ======================
# POSTPARTUM REQUIREMENTS (COMPREHENSIVE) - Copied from notebook
# ======================

POSTPARTUM_RDA = {
    # Macronutrients
    'Protein': {'target': 71, 'unit': 'g', 'critical': True},
    'Total lipid (fat)': {'target': 70, 'unit': 'g', 'critical': False},
    
    # Micronutrients
    'Iron, Fe': {'target': 9, 'unit': 'mg', 'critical': True},
    'Calcium, Ca': {'target': 1000, 'unit': 'mg', 'critical': True},
    'Vitamin B-12': {'target': 2.8, 'unit': 'µg', 'critical': True},
    'Folate, total': {'target': 600, 'unit': 'µg', 'critical': True},
    'Vitamin D (D2 + D3)': {'target': 15, 'unit': 'µg', 'critical': True},
    'Choline, total': {'target': 550, 'unit': 'mg', 'critical': False},
    
    # Breastfeeding adjustments
    'Energy': {'target': 2640, 'unit': 'kcal', 'critical': True}
}

# ======================
# DATA LOADING AND PROCESSING - Adapted from notebook
# ======================

def load_and_prepare_data():
    """Create a dummy dataset for training based on user profile features"""
    # Define possible values for the user profile features
    breastfeeding_vals = ['yes', 'no']
    diet_type_vals = ['vegetarian', 'vegan', 'omnivore']
    deficiency_vals = ['none', 'iron', 'b12']
    preferred_cuisine_vals = ['indian', 'mediterranean', 'asian', 'western']
    
    # Create all possible combinations of features
    from itertools import product
    data_list = []
    for bf, dt, dfcncy, cuisine in product(breastfeeding_vals, diet_type_vals, deficiency_vals, preferred_cuisine_vals):
        data_list.append({
            'breastfeeding': bf,
            'diet_type': dt,
            'deficiency': dfcncy,
            'preferred_cuisine': cuisine,
            # Dummy target variable: higher if breastfeeding, vegan, iron deficient, or indian cuisine
            'target': (1 if bf == 'yes' else 0) + \
                      (1 if dt == 'vegan' else 0) + \
                      (1 if dfcncy == 'iron' else 0) + \
                      (1 if cuisine == 'indian' else 0)
        })
    
    df = pd.DataFrame(data_list)
    
    # Create a binary target (e.g., recommend if target score is above a threshold)
    threshold = df['target'].mean()
    df['postpartum_supportive'] = (df['target'] > threshold).astype(int)
    
    return df

# ======================
# MODEL TRAINING AND SAVING
# ======================

def train_and_save_model(data):
    """Train and save the Random Forest classifier model, scaler, and encoders"""
    if data is None or data.empty:
        print("No data available for training.", file=sys.stderr)
        return

    try:
        # Define features (these should match the backend's expected features)
        features = ['breastfeeding', 'diet_type', 'deficiency', 'preferred_cuisine']
        X = data[features].copy() # Use .copy() to avoid SettingWithCopyWarning
        y = data['postpartum_supportive']

        if X.empty or y.empty:
            print("Features or target is empty after data preparation.", file=sys.stderr)
            return

        # Encode categorical features
        label_encoders = {}
        for col in features:
            if X[col].dtype == 'object':
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col])
                label_encoders[col] = le

        # Handle potential class imbalance if target distribution is skewed
        if y.nunique() > 1:
             X_train, X_test, y_train, y_test = train_test_split(
                 X, y, test_size=0.2, random_state=42, stratify=y)
        else:
             # Handle case where all samples belong to the same class
             X_train, X_test, y_train, y_test = train_test_split(
                 X, y, test_size=0.2, random_state=42)
             print("Warning: All samples in training data belong to the same class.", file=sys.stderr)

        # Scale features
        scaler = MinMaxScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        # Train Random Forest model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=5,
            class_weight='balanced',  # Handle class imbalance
            random_state=42
        )
        model.fit(X_train_scaled, y_train)

        # Define the path to save the model, scaler, and encoders
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, '..', 'models')
        model_path = os.path.join(model_dir, 'nutrition_model.joblib')
        scaler_path = os.path.join(model_dir, 'nutrition_scaler.joblib')
        encoders_path = os.path.join(model_dir, 'nutrition_encoders.joblib')

        # Create the models directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

        # Save the trained model, scaler, and encoders
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        joblib.dump(label_encoders, encoders_path)

        print(f"✅ Nutrition model saved to: {model_path}", file=sys.stderr)
        print(f"✅ Nutrition scaler saved to: {scaler_path}", file=sys.stderr)
        print(f"✅ Nutrition encoders saved to: {encoders_path}", file=sys.stderr)

    except Exception as e:
        print(f"❌ Error during model training or saving: {e}", file=sys.stderr)

# ======================
# MAIN EXECUTION
# ======================

if __name__ == "__main__":
    print("=== Training and Saving Nutrition Model ===", file=sys.stderr)
    
    nutrition_data = load_and_prepare_data()
    if nutrition_data is not None and not nutrition_data.empty:
        train_and_save_model(nutrition_data)
    else:
        print("Model training skipped due to data loading or preparation errors or empty data.", file=sys.stderr) 