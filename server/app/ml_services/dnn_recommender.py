import os
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib

# Reuse RDA feature names to align with existing pipeline
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


class _MLP(nn.Module):
    def __init__(self, in_dim: int):
        super().__init__()
        # IMPORTANT: name must be 'net' to match training script state_dict keys
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1), nn.Sigmoid()  # predict supportive probability
        )

    def forward(self, x):
        return self.net(x)


class DNNNutritionRecommender:
    def __init__(self) -> None:
        # Resolve project root and paths
        current_dir = Path(__file__).resolve().parents[3]
        self.data_dir = current_dir / 'ml' / 'datasets' / 'nutrition'
        self.model_dir = current_dir / 'ml' / 'models'
        self.model_path = self.model_dir / 'dnn_ranker.pt'
        self.scaler_path = self.model_dir / 'dnn_scaler.joblib'

        self.features: List[str] = list(POSTPARTUM_RDA.keys())
        self.food_df: pd.DataFrame | None = None
        self.model: _MLP | None = None
        self.scaler = None
        self.device = torch.device('cpu')
        self.available: bool = False
        self.last_meta: Dict[str, Any] | None = None

        try:
            self._load_food_features()
            if self.model_path.exists() and self.scaler_path.exists():
                self._load_model()
                self.available = True
                print(f"[DNN] Model loaded from {self.model_path}")
            else:
                print(f"[DNN] Model/scaler not found. Fallback will be used.")
        except Exception as e:
            print(f"[DNN] Initialization failed: {e}")
            self.available = False

    def _load_food_features(self) -> None:
        # Same pivoting as XGB recommender
        food = pd.read_csv(self.data_dir / 'food.csv', usecols=['fdc_id', 'description', 'food_category_id'])
        nutrient = pd.read_csv(self.data_dir / 'nutrient.csv', usecols=['id', 'name', 'unit_name'])
        food_nutrient = pd.read_csv(self.data_dir / 'food_nutrient.csv', usecols=['fdc_id', 'nutrient_id', 'amount'])
        category = pd.read_csv(self.data_dir / 'food_category.csv', usecols=['id', 'description']).rename(columns={'description': 'category'})

        df = (
            food_nutrient.merge(food, on='fdc_id', how='inner')
                        .merge(nutrient, left_on='nutrient_id', right_on='id', how='left')
        )
        pivot_df = df.pivot_table(index=['fdc_id'], columns='name', values='amount', aggfunc='mean').reset_index()
        for col in self.features:
            if col not in pivot_df.columns:
                pivot_df[col] = 0.0
            else:
                pivot_df[col] = pivot_df[col].fillna(0.0)
        meta = food.merge(category, left_on='food_category_id', right_on='id', how='left')
        meta = meta[['fdc_id', 'description', 'category']]
        self.food_df = pivot_df.merge(meta, on='fdc_id', how='left')

    def _load_model(self) -> None:
        self.model = _MLP(in_dim=len(self.features))
        self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        self.model.eval()
        self.scaler = joblib.load(self.scaler_path)

    def _apply_filters(self, df: pd.DataFrame, user: Dict[str, Any]) -> pd.DataFrame:
        # copy the basic filters from XGB recommender to maintain parity
        diet = str(user.get('dietType', '')).lower()
        allergies = [a.strip().lower() for a in str(user.get('allergies', '')).split(',') if a.strip()]

        def ok_row(row: pd.Series) -> bool:
            text = f"{str(row.get('description','')).lower()} {str(row.get('category','')).lower()}"
            if diet == 'vegetarian':
                banned = ['beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat','chicken','turkey','duck','quail','fish','seafood','prawn','shrimp','crab','lobster','oyster','mussel','clam','squid','octopus','anchovy','salmon','tuna','sardine','mackerel','cod','tilapia','trout','snapper','eel','egg','eggs','yolk','albumen','gelatin','gelatine','lard']
                if any(b in text for b in banned):
                    return False
            elif diet == 'pescatarian':
                banned = ['beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat','beef product','pork product','beef products','pork products','beef flavor','pork flavor','meat flavor','chicken','turkey','duck','quail','chicken flavor','poultry']
                if any(b in text for b in banned):
                    return False
            elif diet == 'vegan':
                banned = ['beef','pork','mutton','lamb','veal','bacon','ham','pepperoni','salami','sausage','meat','chicken','turkey','duck','quail','fish','seafood','prawn','shrimp','crab','lobster','oyster','mussel','clam','squid','octopus','anchovy','salmon','tuna','sardine','mackerel','cod','tilapia','trout','snapper','eel','egg','eggs','yolk','albumen','milk','curd','paneer','cheese','butter','ghee','yogurt','yoghurt','whey','gelatin','gelatine','honey','lard']
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
        if not self.available or self.food_df is None or self.model is None:
            raise RuntimeError("DNN recommender not available")

        df = self.food_df.copy()
        df = self._apply_filters(df, user)
        meta: Dict[str, Any] = {'candidates_after_filters': int(len(df))}

        X = df[self.features].values.astype(np.float32)
        Xs = self.scaler.transform(X).astype(np.float32)
        with torch.no_grad():
            scores = self.model(torch.from_numpy(Xs)).squeeze(1).numpy()
        df['score'] = scores

        # Optional cuisine boost to match XGB behavior
        cuisine = str(user.get('preferredCuisine', '')).lower()
        if cuisine == 'indian':
            indian_terms = ['basmati','rice','millet','ragi','jowar','bajra','lentil','lentils','chickpea','chickpeas','garbanzo','rajma','kidney bean','moong','urad','masoor','dal','khichdi','poha','upma','idli','dosa','sambar','rasam','biryani','pulao','paratha','chapati','roti','sabzi','curry','spinach','palak','saag','cauliflower','gobi','okra','bhindi','eggplant','brinjal','baingan','methi','turmeric','curry powder','coriander','cumin','fenugreek','mustard seed','cardamom','clove','cinnamon']
            def match_indian(text: str) -> bool:
                t = str(text).lower()
                return any(term in t for term in indian_terms)
            df['cuisine_match'] = df['description'].apply(match_indian) | df['category'].apply(match_indian)
            matched = int(df['cuisine_match'].sum())
            meta['cuisine_matches'] = matched
            df.loc[df['cuisine_match'], 'score'] *= 1.25
            df.loc[~df['cuisine_match'], 'score'] *= 0.90
        else:
            meta['cuisine_matches'] = None

        # Sentiment-aware reranking (continuous effect): blend 7-day avg with latest mood
        eff_sent = None
        try:
            sent_avg = float(user.get('sent_last7_avg')) if user.get('sent_last7_avg') is not None else None
        except Exception:
            sent_avg = None
        try:
            sent_cur = float(user.get('sent_current')) if user.get('sent_current') is not None else None
        except Exception:
            sent_cur = None
        # Blend: emphasize trend but react to latest
        if sent_avg is not None and sent_cur is not None:
            eff_sent = 0.6 * sent_avg + 0.4 * sent_cur
        elif sent_avg is not None:
            eff_sent = sent_avg
        elif sent_cur is not None:
            eff_sent = sent_cur
        if eff_sent is not None:
            critical_feats = ['Energy','Protein','Iron, Fe','Vitamin B-12','Folate, total','Calcium, Ca']
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
            sup = df.apply(support_index, axis=1).clip(lower=0.0, upper=2.0)
            df['support_index'] = sup
            # Normalize sentiment approximately to [-1, 1] based on mapping range and clamp
            norm = max(-1.0, min(1.0, eff_sent / 0.6))
            # Positive mood slightly deprioritizes heavy-support foods; negative mood boosts support foods
            alpha = 0.30  # global sensitivity
            support_weight = (df['support_index'] / 2.0)  # 0..1
            df['score'] = df['score'] * (1.0 + alpha * norm * (2.0 * support_weight - 0.5))
            meta['sentiment_adjustment'] = {
                'mode': 'continuous',
                'sent_last7_avg': sent_avg,
                'sent_current': sent_cur,
                'effective_sent': eff_sent,
                'norm': float(norm),
                'alpha': alpha,
                'support_index_mean': float(support_weight.mean()) if len(support_weight) else None
            }

        top = df.sort_values('score', ascending=False).head(top_k)
        recs: List[Dict[str, Any]] = []
        for _, row in top.iterrows():
            nutrients = []
            for feat in self.features:
                val = float(row.get(feat, 0.0))
                target = POSTPARTUM_RDA[feat]['target']
                unit = POSTPARTUM_RDA[feat]['unit']
                pct = (val / target) * 100 if target else 0.0
                nutrients.append({'name': feat, 'amount': round(val, 2), 'unit': unit, 'rda_pct': round(pct, 1)})
            recs.append({
                'fdc_id': int(row['fdc_id']),
                'description': row.get('description', ''),
                'category': row.get('category', ''),
                'score': round(float(row['score']), 4),
                'nutrients': nutrients
            })
        self.last_meta = meta
        return recs
