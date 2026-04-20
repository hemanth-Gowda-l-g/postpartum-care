import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

def save_model_bundle(data_path, output_dir='models'):
    """
    Train and save a PPD risk prediction model bundle.
    
    Args:
        data_path (str): Path to the CSV file containing the PPD dataset
        output_dir (str): Directory to save the trained model bundle
    """
    # Load the data
    data = pd.read_csv(data_path)
    
    # Data Cleaning
    data.replace(['', 'Not interested to say', 'Maybe'], np.nan, inplace=True)
    
    # Convert 'Age' to numerical
    def age_to_numeric(age_str):
        if pd.isna(age_str):
            return np.nan
        if '-' in age_str:
            low, high = map(int, age_str.split('-'))
            return (low + high) / 2
        return float(age_str)
    
    data['Age'] = data['Age'].apply(age_to_numeric)
    
    # Create target variable
    data['PPD_Risk'] = data['Suicide attempt'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # Select features
    features = [
        'Age', 'Feeling sad or Tearful', 'Irritable towards baby & partner', 
        'Trouble sleeping at night', 'Problems concentrating or making decision',
        'Overeating or loss of appetite', 'Feeling anxious', 'Feeling of guilt',
        'Problems of bonding with baby'
    ]
    
    # Preprocess features
    label_encoders = {}
    for feature in features[1:]:
        le = LabelEncoder()
        unique_values = data[feature].dropna().unique()
        le.fit(unique_values)
        data[feature] = data[feature].map(lambda x: le.transform([x])[0] if pd.notna(x) else np.nan)
        label_encoders[feature] = le
    
    # Handle missing values
    imputer = SimpleImputer(strategy='most_frequent')
    X = imputer.fit_transform(data[features])
    y = data['PPD_Risk'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Create model bundle
    model_bundle = {
        'model': model,
        'label_encoders': label_encoders,
        'imputer': imputer,
        'features': features,
        'questions': [
            ("Age (years)", "numerical"),
            ("Have you felt sad or tearful?", ["No", "Yes", "Sometimes"]),
            ("Have you felt irritable towards baby & partner?", ["No", "Yes", "Sometimes"]),
            ("Trouble sleeping at night?", ["No", "Yes", "Two or more days a week"]),
            ("Problems concentrating?", ["No", "Yes", "Often"]),
            ("Appetite changes?", ["No", "Yes", "Not at all"]),
            ("Feeling anxious?", ["No", "Yes"]),
            ("Excessive guilt?", ["No", "Yes", "Maybe"]),
            ("Difficulty bonding with baby?", ["No", "Yes", "Sometimes"])
        ]
    }
    
    # Save model bundle
    os.makedirs(output_dir, exist_ok=True)
    bundle_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir, 'ppd_model_bundle.pkl')
    joblib.dump(model_bundle, bundle_path)
    print(f"✅ Model bundle saved to {bundle_path}")
    
    # Print model accuracy
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy:.2f}")

if __name__ == "__main__":
    data_path = r'D:\postpartum-care-platform - Copy\ml\datasets\ppd\post natal data.csv'
    save_model_bundle(data_path) 