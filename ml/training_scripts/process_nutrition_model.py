import os
import joblib
import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import MinMaxScaler

def process_nutrition_model():
    # Define paths
    base_dir = Path(__file__).parent.parent
    dataset_dir = base_dir / 'datasets' / 'nutrition'
    model_dir = base_dir / 'models'
    
    # Create models directory if it doesn't exist
    model_dir.mkdir(exist_ok=True)
    
    try:
        # Load datasets
        food = pd.read_csv(dataset_dir / 'food.csv', usecols=['fdc_id', 'description', 'food_category_id'])
        nutrient = pd.read_csv(dataset_dir / 'nutrient.csv', usecols=['id', 'name', 'unit_name'])
        food_nutrient = pd.read_csv(dataset_dir / 'food_nutrient.csv', usecols=['fdc_id', 'nutrient_id', 'amount'])
        category = pd.read_csv(dataset_dir / 'food_category.csv', usecols=['id', 'description'])
        
        # Define postpartum requirements
        POSTPARTUM_RDA = {
            'Protein': {'target': 71, 'unit': 'g', 'critical': True},
            'Total lipid (fat)': {'target': 70, 'unit': 'g', 'critical': False},
            'Iron, Fe': {'target': 9, 'unit': 'mg', 'critical': True},
            'Calcium, Ca': {'target': 1000, 'unit': 'mg', 'critical': True},
            'Vitamin B-12': {'target': 2.8, 'unit': 'µg', 'critical': True},
            'Folate, total': {'target': 600, 'unit': 'µg', 'critical': True},
            'Vitamin D (D2 + D3)': {'target': 15, 'unit': 'µg', 'critical': True},
            'Choline, total': {'target': 550, 'unit': 'mg', 'critical': False},
            'Energy': {'target': 2640, 'unit': 'kcal', 'critical': True}
        }
        
        # Prepare dataset
        df = (
            food_nutrient.merge(food, on='fdc_id', how='inner', validate='many_to_one')
                        .merge(nutrient, left_on='nutrient_id', right_on='id', how='left', validate='many_to_one')
                        .merge(category, left_on='food_category_id', right_on='id', how='left', validate='many_to_one')
        )
        
        # Pivot to wide format
        pivot_df = df.pivot_table(
            index=['fdc_id', 'description_x', 'description_y'],
            columns='name',
            values='amount',
            aggfunc='mean'
        ).reset_index()
        
        # Fill NA and create labels
        critical_nutrients = [k for k,v in POSTPARTUM_RDA.items() if v['critical']]
        for nut in POSTPARTUM_RDA:
            if nut in pivot_df.columns:
                pivot_df[nut] = pivot_df[nut].fillna(0)
                if nut in critical_nutrients:
                    pivot_df[f'{nut}_label'] = (
                        pivot_df[nut] >= 0.15 * POSTPARTUM_RDA[nut]['target']
                    ).astype(int)
        
        pivot_df['postpartum_supportive'] = pivot_df[[f'{n}_label' for n in critical_nutrients]].max(axis=1)
        
        # Train model
        features = [k for k in POSTPARTUM_RDA.keys() if k in pivot_df.columns]
        X = pivot_df[features]
        y = pivot_df['postpartum_supportive']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y)
        
        scaler = MinMaxScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Save model and scaler
        model_bundle = {
            'model': model,
            'scaler': scaler,
            'features': features
        }
        model_path = model_dir / 'nutrition_model.joblib'
        joblib.dump(model_bundle, model_path)
        print(f"✅ Nutrition model saved to {model_path}")
        
    except Exception as e:
        print(f"❌ Error processing nutrition model: {e}")

if __name__ == '__main__':
    process_nutrition_model() 