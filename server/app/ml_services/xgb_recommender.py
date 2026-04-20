import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import joblib

# Mirror RDA used in training
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

class XGBNutritionRecommender:
    def __init__(self) -> None:
        # Resolve project root and paths
        current_dir = Path(__file__).resolve().parents[3]
        self.data_dir = current_dir / 'ml' / 'datasets' / 'nutrition'
        self.model_path = current_dir / 'ml' / 'models' / 'nutrition_model.joblib'

        self.bundle = None
        self.food_df: pd.DataFrame | None = None
        self.features: List[str] = list(POSTPARTUM_RDA.keys())
        self.last_meta: Dict[str, Any] | None = None
        self.available = False

        try:
            self._load_bundle()
            self._load_food_features()
            self.available = True
            print(f"[XGB] Bundle loaded from {self.model_path}")
            if self.food_df is not None:
                print(f"[XGB] Food feature table ready: {len(self.food_df)} rows, {len(self.features)} features")
        except Exception as e:
            self.bundle = None
            self.food_df = None
            self.available = False
            print(f"[XGB] Initialization failed: {e}")

    def _load_bundle(self) -> None:
        if self.model_path.exists():
            self.bundle = joblib.load(self.model_path)
        else:
            self.bundle = None
            raise FileNotFoundError(f"XGB bundle not found at {self.model_path}")

    def _load_food_features(self) -> None:
        # Load USDA CSVs and pivot like the training script
        food = pd.read_csv(self.data_dir / 'food.csv', usecols=['fdc_id', 'description', 'food_category_id'])
        nutrient = pd.read_csv(self.data_dir / 'nutrient.csv', usecols=['id', 'name', 'unit_name'])
        food_nutrient = pd.read_csv(self.data_dir / 'food_nutrient.csv', usecols=['fdc_id', 'nutrient_id', 'amount'])
        category = pd.read_csv(self.data_dir / 'food_category.csv', usecols=['id', 'description']).rename(columns={'description': 'category'})

        df = (
            food_nutrient.merge(food, on='fdc_id', how='inner')
                         .merge(nutrient, left_on='nutrient_id', right_on='id', how='left')
        )
        pivot_df = df.pivot_table(
            index=['fdc_id'], columns='name', values='amount', aggfunc='mean'
        ).reset_index()

        # Ensure features exist
        for col in self.features:
            if col not in pivot_df.columns:
                pivot_df[col] = 0.0
            else:
                pivot_df[col] = pivot_df[col].fillna(0.0)

        # Attach description and category for display
        meta = food.merge(category, left_on='food_category_id', right_on='id', how='left')
        meta = meta[['fdc_id', 'description', 'category']]
        self.food_df = pivot_df.merge(meta, on='fdc_id', how='left')

    def _apply_filters(self, df: pd.DataFrame, user: Dict[str, Any]) -> pd.DataFrame:
        diet = str(user.get('dietType', '')).lower()
        allergies = [a.strip().lower() for a in str(user.get('allergies', '')).split(',') if a.strip()]

        # Basic text filters using description/category
        def ok_row(row: pd.Series) -> bool:
            text = f"{str(row.get('description','')).lower()} {str(row.get('category','')).lower()}"
            if diet == 'vegetarian':
                banned = [
                    # red meat
                    'beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat',
                    # poultry
                    'chicken','turkey','duck','quail',
                    # seafood and fish
                    'fish','seafood','prawn','shrimp','crab','lobster','oyster','mussel','clam','squid','octopus',
                    'anchovy','salmon','tuna','sardine','mackerel','cod','tilapia','trout','snapper','eel',
                    # eggs and animal derivatives (common vegetarian exclusion)
                    'egg','eggs','yolk','albumen','gelatin','gelatine','lard'
                ]
                if any(b in text for b in banned):
                    return False
            elif diet == 'pescatarian':
                # Exclude red meat and poultry; allow fish/seafood; eggs allowed
                banned = [
                    # red meat
                    'beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat',
                    'beef product','pork product','beef products','pork products','beef flavor','pork flavor','meat flavor',
                    # poultry
                    'chicken','turkey','duck','quail','chicken flavor','poultry'
                ]
                if any(b in text for b in banned):
                    return False
            elif diet == 'vegan':
                banned = [
                    # all meat/seafood
                    'beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat',
                    'chicken','turkey','duck','quail',
                    'fish','seafood','prawn','shrimp','crab','lobster','oyster','mussel','clam','squid','octopus',
                    'anchovy','salmon','tuna','sardine','mackerel','cod','tilapia','trout','snapper','eel',
                    # eggs and dairy
                    'egg','eggs','yolk','albumen',
                    'milk','curd','paneer','cheese','butter','ghee','yogurt','yoghurt','whey',
                    # other animal products
                    'gelatin','gelatine','honey','lard'
                ]
                if any(b in text for b in banned):
                    return False
            for allergy in allergies:
                if allergy == 'milk' and any(b in text for b in ['milk','curd','paneer','cheese','butter','ghee','yogurt']):
                    return False
                if allergy == 'nuts' and any(b in text for b in ['nut','almond','walnut','peanut','cashew']):
                    return False
                if allergy == 'gluten' and any(b in text for b in ['wheat','barley','rye','bread','roti','chapati','paratha']):
                    return False
            return True

        mask = df.apply(ok_row, axis=1)
        return df[mask].copy()

    def recommend(self, user: Dict[str, Any], top_k: int = 20) -> List[Dict[str, Any]]:
        if not self.available or self.bundle is None or self.food_df is None:
            self.last_meta = {'candidates_after_filters': 0}
            return []
        model = self.bundle['model']
        scaler = self.bundle['scaler']

        df = self.food_df.copy()
        df = self._apply_filters(df, user)
        print(f"[XGB] After filters, candidate foods: {len(df)}")
        # initialize meta
        meta: Dict[str, Any] = {
            'candidates_after_filters': int(len(df))
        }

        X = df[self.features].values
        Xs = scaler.transform(X)
        proba = model.predict_proba(Xs)[:, 1]  # probability of postpartum_supportive
        print(f"[XGB] Ran predict_proba on shape {Xs.shape}")
        df['score'] = proba

        # Cuisine-aware boosting
        cuisine = str(user.get('preferredCuisine', '')).lower()
        if cuisine == 'indian':
            indian_terms = [
                # staples and grains
                'basmati','rice','millet','ragi','jowar','bajra',
                # legumes/pulses
                'lentil','lentils','chickpea','chickpeas','garbanzo','rajma','kidney bean','moong','urad','masoor',
                # dishes and forms
                'dal','khichdi','poha','upma','idli','dosa','sambar','rasam','biryani','pulao','paratha','chapati','roti','sabzi','curry',
                # vegetables often in indian cooking
                'spinach','palak','saag','cauliflower','gobi','okra','bhindi','eggplant','brinjal','baingan','methi',
                # spices/herbs (as hints)
                'turmeric','curry powder','coriander','cumin','fenugreek','mustard seed','cardamom','clove','cinnamon',
            ]
            # mark matches
            def match_indian(text: str) -> bool:
                t = str(text).lower()
                return any(term in t for term in indian_terms)
            df['cuisine_match'] = df['description'].apply(match_indian) | df['category'].apply(match_indian)
            matched = int(df['cuisine_match'].sum())
            print(f"[XGB] Indian cuisine preference: matched {matched} candidates")
            meta['cuisine_matches'] = matched
            # apply multiplicative boost/penalty to re-rank
            df.loc[df['cuisine_match'], 'score'] *= 1.25
            df.loc[~df['cuisine_match'], 'score'] *= 0.90
        else:
            meta['cuisine_matches'] = None

        # Diet-aware gentle boosting
        diet = str(user.get('dietType', '')).lower()
        if diet == 'pescatarian':
            seafood_terms = [
                'fish','seafood','prawn','shrimp','crab','lobster','oyster','mussel','clam','squid','octopus',
                'anchovy','salmon','tuna','sardine','mackerel','cod','tilapia','trout','snapper','eel'
            ]
            def match_seafood(text: str) -> bool:
                t = str(text).lower()
                return any(term in t for term in seafood_terms)
            df['seafood_match'] = df['description'].apply(match_seafood) | df['category'].apply(match_seafood)
            matched_sf = int(df['seafood_match'].sum())
            print(f"[XGB] Pescatarian diet: boosting {matched_sf} seafood candidates")
            meta['seafood_matches'] = matched_sf
            df.loc[df['seafood_match'], 'score'] *= 1.15
        else:
            meta['seafood_matches'] = None

        # Sentiment-aware adjustments (post-hoc reranking):
        # Expect optional fields injected by caller: 'sent_last7_avg', 'sent_var_7d', 'pct_negative_7d'
        sent_avg = None
        try:
            sent_avg = float(user.get('sent_last7_avg')) if user.get('sent_last7_avg') is not None else None
        except Exception:
            sent_avg = None
        if sent_avg is not None:
            # Compute a nutrient support index per row using critical postpartum nutrients
            critical_feats = ['Energy','Protein','Iron, Fe','Vitamin B-12','Folate, total','Calcium, Ca']
            # Safe defaults for missing columns
            for cf in critical_feats:
                if cf not in df.columns:
                    df[cf] = 0.0
            def support_index(row):
                s = 0.0
                for cf in critical_feats:
                    target = POSTPARTUM_RDA[cf]['target'] if cf in POSTPARTUM_RDA else 0.0
                    val = float(row.get(cf, 0.0))
                    s += (val / target) if target else 0.0
                return s
            sup = df.apply(support_index, axis=1)
            # Normalize to mean ~0.3-0.6 typical; keep bounded
            sup = sup.clip(lower=0.0, upper=2.0)
            df['support_index'] = sup

            if sent_avg <= -0.05:
                # More negative mood → boost supportive, nutrient-dense items modestly
                neg_strength = min(1.0, max(0.0, (-sent_avg) / 1.0))  # 0..1
                beta = 0.35
                df['score'] = df['score'] * (1.0 + beta * neg_strength * df['support_index'])
                meta['sentiment_adjustment'] = {
                    'mode': 'negative_boost', 'sent_last7_avg': sent_avg, 'beta': beta
                }
            elif sent_avg >= 0.3:
                # Strong positive → gentle preference for lighter options
                pos_strength = min(1.0, max(0.0, (sent_avg) / 1.0))
                gamma = 0.15
                df['score'] = df['score'] * (1.0 - gamma * pos_strength * (df['support_index'] * 0.5))
                meta['sentiment_adjustment'] = {
                    'mode': 'positive_lighten', 'sent_last7_avg': sent_avg, 'gamma': gamma
                }
            else:
                meta['sentiment_adjustment'] = {'mode': 'neutral', 'sent_last7_avg': sent_avg}

        top = df.sort_values('score', ascending=False).head(top_k)
        if not top.empty:
            print(f"[XGB] Top item: {top.iloc[0].get('description','')} | score={float(top.iloc[0]['score']):.4f}")

        # Build detailed nutrient breakdown with %RDA like the notebook
        recs: List[Dict[str, Any]] = []
        for _, row in top.iterrows():
            nutrients = []
            for feat in self.features:
                val = float(row.get(feat, 0.0))
                target = POSTPARTUM_RDA[feat]['target']
                unit = POSTPARTUM_RDA[feat]['unit']
                pct = (val / target) * 100 if target else 0.0
                nutrients.append({
                    'name': feat,
                    'amount': round(val, 2),
                    'unit': unit,
                    'rda_pct': round(pct, 1)
                })
            recs.append({
                'fdc_id': int(row['fdc_id']),
                'description': row.get('description', ''),
                'category': row.get('category', ''),
                'score': round(float(row['score']), 4),
                'nutrients': nutrients
            })
        # store meta for caller
        self.last_meta = meta
        return recs
