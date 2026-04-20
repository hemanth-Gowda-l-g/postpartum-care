import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

"""
Train a nutrition model by merging USDA-style CSVs located in ml/datasets/nutrition/:
- food.csv (food metadata, includes food_id, description, food_category_id)
- food_category.csv (category_id -> category name)
- food_nutrient.csv (food_id, nutrient_id, amount)
- nutrient.csv (nutrient_id -> nutrient name, unit)
- measure_unit.csv (not strictly required; we aggregate per food as-is)

Default task: classify food_category from nutrient composition.
Output: A bundle joblib containing {'model','scaler','features','label_encoder','target'}
Saved by default to ml/models/nutrition_model.joblib
"""

def load_usda_frames(base_dir: Path):
    food = pd.read_csv(base_dir / 'food.csv')
    food_category = pd.read_csv(base_dir / 'food_category.csv')
    food_nutrient = pd.read_csv(base_dir / 'food_nutrient.csv')
    nutrient = pd.read_csv(base_dir / 'nutrient.csv')
    return food, food_category, food_nutrient, nutrient


def build_feature_matrix(food: pd.DataFrame,
                         food_nutrient: pd.DataFrame,
                         nutrient: pd.DataFrame,
                         nutrient_name_limit: int = 200) -> pd.DataFrame:
    # Join nutrient names
    fn = food_nutrient.merge(nutrient[['id', 'name']], left_on='nutrient_id', right_on='id', how='left')
    fn = fn.rename(columns={'name': 'nutrient_name'})

    # Some datasets have different id column names; normalize
    food_id_col = 'food_id' if 'food_id' in fn.columns else 'fdc_id' if 'fdc_id' in fn.columns else None
    if food_id_col is None:
        raise ValueError('Could not find food id column in food_nutrient.csv')

    # Aggregate total amount per food x nutrient
    agg = fn.groupby([food_id_col, 'nutrient_name'])['amount'].sum().reset_index()

    # Optionally reduce dimensionality by selecting top nutrients by coverage
    coverage = agg.groupby('nutrient_name')[food_id_col].nunique().sort_values(ascending=False)
    top_nutrients = coverage.head(nutrient_name_limit).index.tolist()
    agg = agg[agg['nutrient_name'].isin(top_nutrients)]

    # Pivot to wide matrix
    features = agg.pivot(index=food_id_col, columns='nutrient_name', values='amount').fillna(0.0)
    features.columns = [str(c) for c in features.columns]

    # Keep only foods that appear in food.csv
    food_id_col_food = 'id' if 'id' in food.columns else food_id_col
    common_ids = set(food[food_id_col_food].astype(features.index.dtype)).intersection(set(features.index))
    features = features.loc[sorted(common_ids)]

    return features


def attach_labels(features: pd.DataFrame, food: pd.DataFrame, food_category: pd.DataFrame) -> pd.DataFrame:
    # Standardize id columns
    food_id_col_food = 'id' if 'id' in food.columns else ('fdc_id' if 'fdc_id' in food.columns else None)
    if food_id_col_food is None:
        raise ValueError('Could not find food id column in food.csv')
    cat_id_col = 'food_category_id' if 'food_category_id' in food.columns else 'wweia_category_id' if 'wweia_category_id' in food.columns else None
    if cat_id_col is None:
        raise ValueError('Could not find category id column in food.csv')

    food_small = food[[food_id_col_food, cat_id_col]].dropna()

    # Join category name if available
    cat_name_col = 'description' if 'description' in food_category.columns else 'name' if 'name' in food_category.columns else None
    food_cat = food_small.merge(food_category, left_on=cat_id_col, right_on='id', how='left')
    if cat_name_col is None:
        # fallback to id as label
        food_cat['category_label'] = food_cat[cat_id_col].astype(str)
    else:
        food_cat['category_label'] = food_cat[cat_name_col].astype(str)

    # Align with features index
    food_cat = food_cat.set_index(food_id_col_food).loc[features.index]

    df = features.copy()
    df['__label__'] = food_cat['category_label']
    df = df.dropna(subset=['__label__'])
    return df


def train_category_classifier(df: pd.DataFrame, model_type: str = 'rf', random_state: int = 42):
    X = df.drop(columns=['__label__']).values
    feature_names = df.drop(columns=['__label__']).columns.tolist()

    le = LabelEncoder()
    y = le.fit_transform(df['__label__'].values)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=random_state, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    if model_type.lower() in ['xgb', 'xgboost']:
        try:
            from xgboost import XGBClassifier
        except ImportError as e:
            raise ImportError("xgboost is not installed. Please install it with 'pip install xgboost'.")
        clf = XGBClassifier(
            n_estimators=600,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            objective='multi:softprob',
            tree_method='hist',
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        clf = RandomForestClassifier(n_estimators=400, max_depth=None, n_jobs=-1, random_state=random_state)

    clf.fit(X_train_s, y_train)

    y_pred = clf.predict(X_test_s)
    report = classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0)
    acc = accuracy_score(y_test, y_pred)
    return clf, scaler, feature_names, le, report, acc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=str(Path(__file__).resolve().parents[1] / 'datasets' / 'nutrition'))
    parser.add_argument('--output', type=str, default=str(Path(__file__).resolve().parents[1] / 'models' / 'nutrition_model.joblib'))
    parser.add_argument('--nutrient_top_k', type=int, default=200)
    parser.add_argument('--model', type=str, default='rf', choices=['rf', 'xgb'], help='Choose model: rf (RandomForest) or xgb (XGBoost)')
    args = parser.parse_args()

    base_dir = Path(args.data_dir)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f'Loading datasets from: {base_dir}')
    food, food_category, food_nutrient, nutrient = load_usda_frames(base_dir)

    print('Building feature matrix...')
    features = build_feature_matrix(food, food_nutrient, nutrient, nutrient_name_limit=args.nutrient_top_k)

    print('Attaching labels...')
    df = attach_labels(features, food, food_category)

    print(f'Feature matrix shape: {df.shape[0]} rows, {df.shape[1]-1} features, {df["__label__"].nunique()} classes')

    print('Training classifier...')
    model, scaler, feature_names, le, report, acc = train_category_classifier(df, model_type=args.model)
    print('\nEvaluation (holdout):')
    print(report)
    print(f"Accuracy: {acc:.4f}")

    bundle = {
        'model': model,
        'scaler': scaler,
        'features': feature_names,
        'label_encoder': le,
        'target': 'food_category'
    }

    joblib.dump(bundle, out_path)
    print(f'\n✅ Saved model bundle to: {out_path}')


if __name__ == '__main__':
    main()
