import os
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / 'ml' / 'datasets' / 'nutrition'
MODELS_DIR = PROJECT_ROOT / 'ml' / 'models'
XGB_BUNDLE = MODELS_DIR / 'nutrition_model.joblib'
DNN_SCALER = MODELS_DIR / 'dnn_scaler.joblib'
DNN_WEIGHTS = MODELS_DIR / 'dnn_ranker.pt'

# Features aligned with existing pipeline
POSTPARTUM_RDA = [
    'Protein', 'Total lipid (fat)', 'Iron, Fe', 'Calcium, Ca',
    'Vitamin B-12', 'Folate, total', 'Vitamin D (D2 + D3)',
    'Choline, total', 'Energy'
]

class MLP(nn.Module):
    def __init__(self, in_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)


def load_food_feature_table() -> pd.DataFrame:
    food = pd.read_csv(DATA_DIR / 'food.csv', usecols=['fdc_id', 'description', 'food_category_id'])
    nutrient = pd.read_csv(DATA_DIR / 'nutrient.csv', usecols=['id', 'name'])
    food_nutrient = pd.read_csv(DATA_DIR / 'food_nutrient.csv', usecols=['fdc_id', 'nutrient_id', 'amount'])
    category = pd.read_csv(DATA_DIR / 'food_category.csv', usecols=['id', 'description']).rename(columns={'description': 'category'})

    df = food_nutrient.merge(food, on='fdc_id', how='inner').merge(nutrient, left_on='nutrient_id', right_on='id', how='left')
    pivot_df = df.pivot_table(index=['fdc_id'], columns='name', values='amount', aggfunc='mean').reset_index()
    # Ensure features present
    for col in POSTPARTUM_RDA:
        if col not in pivot_df.columns:
            pivot_df[col] = 0.0
        else:
            pivot_df[col] = pivot_df[col].fillna(0.0)
    meta = food.merge(category, left_on='food_category_id', right_on='id', how='left')
    meta = meta[['fdc_id', 'description', 'category']]
    pivot_df = pivot_df.merge(meta, on='fdc_id', how='left')
    return pivot_df


def soft_labels_from_xgb(pivot_df: pd.DataFrame) -> np.ndarray:
    if not XGB_BUNDLE.exists():
        raise FileNotFoundError(f"XGB bundle not found at {XGB_BUNDLE}")
    bundle = joblib.load(XGB_BUNDLE)
    model = bundle['model']
    scaler = bundle['scaler']
    X = pivot_df[POSTPARTUM_RDA].values
    Xs = scaler.transform(X)
    proba = model.predict_proba(Xs)[:, 1]
    return proba.astype(np.float32)


def train():
    print("[DNN Train] Loading data table...")
    pivot_df = load_food_feature_table()
    y = soft_labels_from_xgb(pivot_df)
    X = pivot_df[POSTPARTUM_RDA].values.astype(np.float32)

    print("[DNN Train] Splitting train/val...")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train).astype(np.float32)
    X_val_s = scaler.transform(X_val).astype(np.float32)

    joblib.dump(scaler, DNN_SCALER)
    print(f"[DNN Train] Saved scaler to {DNN_SCALER}")

    train_ds = TensorDataset(torch.from_numpy(X_train_s), torch.from_numpy(y_train.reshape(-1, 1)))
    val_ds = TensorDataset(torch.from_numpy(X_val_s), torch.from_numpy(y_val.reshape(-1, 1)))

    train_loader = DataLoader(train_ds, batch_size=512, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=1024)

    model = MLP(in_dim=X.shape[1])
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    best_val = float('inf')
    patience = 5
    bad_epochs = 0
    max_epochs = 40

    print("[DNN Train] Starting training...")
    for epoch in range(1, max_epochs + 1):
        model.train()
        tr_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            preds = model(xb)
            loss = criterion(preds, yb)
            loss.backward()
            optimizer.step()
            tr_loss += loss.item() * xb.size(0)
        tr_loss /= len(train_loader.dataset)

        # validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                preds = model(xb)
                loss = criterion(preds, yb)
                val_loss += loss.item() * xb.size(0)
        val_loss /= len(val_loader.dataset)
        scheduler.step(val_loss)

        print(f"Epoch {epoch:02d} | train_loss={tr_loss:.4f} | val_loss={val_loss:.4f}")

        if val_loss + 1e-5 < best_val:
            best_val = val_loss
            bad_epochs = 0
            torch.save(model.state_dict(), DNN_WEIGHTS)
            print(f"[DNN Train] Saved checkpoint to {DNN_WEIGHTS}")
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print("[DNN Train] Early stopping.")
                break

    print("[DNN Train] Training complete.")


if __name__ == '__main__':
    os.makedirs(MODELS_DIR, exist_ok=True)
    train()
