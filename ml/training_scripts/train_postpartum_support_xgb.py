import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

# POSTPARTUM RDA mirrors the notebook's approach
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


def load_usda(base_dir: Path):
    food = pd.read_csv(base_dir / 'food.csv', usecols=['fdc_id', 'description', 'food_category_id'])
    nutrient = pd.read_csv(base_dir / 'nutrient.csv', usecols=['id', 'name', 'unit_name'])
    food_nutrient = pd.read_csv(base_dir / 'food_nutrient.csv', usecols=['fdc_id', 'nutrient_id', 'amount'])
    category = pd.read_csv(base_dir / 'food_category.csv', usecols=['id', 'description'])
    return food, nutrient, food_nutrient, category


def prepare_dataset(food, nutrient, food_nutrient, category):
    df = (
        food_nutrient.merge(food, on='fdc_id', how='inner')
                     .merge(nutrient, left_on='nutrient_id', right_on='id', how='left')
                     .merge(category, left_on='food_category_id', right_on='id', how='left')
    )

    # Pivot to wide by food (use fdc_id + description)
    # After merges, there may be duplicate 'description' columns -> pandas adds _x/_y
    desc_col = 'description_x' if 'description_x' in df.columns else ('description' if 'description' in df.columns else None)
    if desc_col is None:
        desc_col = 'description_y' if 'description_y' in df.columns else None
    if desc_col is None:
        # Fallback if no description columns remain
        df['food_desc'] = df['fdc_id'].astype(str)
        desc_col = 'food_desc'

    pivot_df = df.pivot_table(
        index=['fdc_id', desc_col],
        columns='name',
        values='amount',
        aggfunc='mean'
    ).reset_index()

    # Ensure POSTPARTUM_RDA nutrients exist
    for nut in POSTPARTUM_RDA:
        if nut not in pivot_df.columns:
            pivot_df[nut] = 0.0
        else:
            pivot_df[nut] = pivot_df[nut].fillna(0.0)

    # Build target: postpartum_supportive if any critical nutrient >= 15% of target
    critical = [k for k, v in POSTPARTUM_RDA.items() if v['critical']]
    for nut in critical:
        pivot_df[f'{nut}_label'] = (pivot_df[nut] >= 0.15 * POSTPARTUM_RDA[nut]['target']).astype(int)
    pivot_df['postpartum_supportive'] = pivot_df[[f'{n}_label' for n in critical]].max(axis=1)

    features = list(POSTPARTUM_RDA.keys())
    return pivot_df, features


def train_xgb(df: pd.DataFrame, features):
    from xgboost import XGBClassifier

    X = df[features]
    y = df['postpartum_supportive']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = XGBClassifier(
        n_estimators=600,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        objective='binary:logistic',
        tree_method='hist',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_s, y_train)

    y_pred = (model.predict_proba(X_test_s)[:, 1] >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=4)
    cm = confusion_matrix(y_test, y_pred)

    return model, scaler, features, acc, report, cm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=str(Path(__file__).resolve().parents[1] / 'datasets' / 'nutrition'))
    parser.add_argument('--output', type=str, default=str(Path(__file__).resolve().parents[1] / 'models' / 'nutrition_postpartum_xgb.joblib'))
    args = parser.parse_args()

    base_dir = Path(args.data_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f'Loading USDA data from: {base_dir}')
    food, nutrient, food_nutrient, category = load_usda(base_dir)

    print('Preparing dataset (postpartum_supportive target)...')
    df, features = prepare_dataset(food, nutrient, food_nutrient, category)
    print(f'Dataset rows: {len(df)}, features: {len(features)}')

    print('Training XGBoost...')
    model, scaler, features, acc, report, cm = train_xgb(df, features)

    print('\nEvaluation:')
    print(f'Accuracy: {acc:.4f}')
    print('\nClassification report:')
    print(report)
    print('\nConfusion matrix:')
    print(cm)

    bundle = {
        'model': model,
        'scaler': scaler,
        'features': features,
        'target': 'postpartum_supportive'
    }
    joblib.dump(bundle, out_path)
    print(f'\n✅ Saved XGBoost bundle to: {out_path}')


if __name__ == '__main__':
    main()
