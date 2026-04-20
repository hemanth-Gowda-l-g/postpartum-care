import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os

def train_ppd_model(data_path, output_dir='models'):
    """
    Train a PPD risk prediction model using Random Forest.
    
    Args:
        data_path (str): Path to the CSV file containing the PPD dataset
        output_dir (str): Directory to save the trained model and preprocessors
    
    Returns:
        tuple: (model, imputer, label_encoders) - The trained model and preprocessors
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
        'Problems of bonding with baby', 'Feeling of worthlessness',
        'Thoughts of harming self', 'Feeling overwhelmed'
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
    
    # Cross-validation
    cv_scores = cross_val_score(RandomForestClassifier(random_state=42), X_train, y_train, cv=5)
    print("Cross-validation scores:", cv_scores)
    print("Average CV score:", cv_scores.mean())
    
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
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("\nModel Evaluation:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save model and preprocessors
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(model, os.path.join(output_dir, 'ppd_model.pkl'))
    joblib.dump(imputer, os.path.join(output_dir, 'imputer.pkl'))
    joblib.dump(label_encoders, os.path.join(output_dir, 'label_encoders.pkl'))
    
    # Plot confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Low Risk', 'High Risk'],
                yticklabels=['Low Risk', 'High Risk'])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.savefig(os.path.join(output_dir, 'confusion_matrix.png'))
    plt.close()
    
    # Plot feature importance
    feature_importance = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=feature_importance)
    plt.title('Feature Importance')
    plt.savefig(os.path.join(output_dir, 'feature_importance.png'))
    plt.close()
    
    return model, imputer, label_encoders

if __name__ == "__main__":
    # Train the model
    data_path = r'D:\postpartum-care-platform - Copy\ml\datasets\ppd\post natal data.csv'
    model, imputer, label_encoders = train_ppd_model(data_path)
