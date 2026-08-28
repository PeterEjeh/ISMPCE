"""
Train all three ML models for CO2 emissions prediction.

Models:
1. Random Forest (scikit-learn) — baseline
2. XGBoost with Optuna hyperparameter optimization
3. LSTM (PyTorch) — 2-layer stacked with dropout

Temporal split (no shuffle):
- Train: 1990-2015
- Validation: 2016-2019
- Test: 2020-2022

Serialization:
- Random Forest: joblib
- XGBoost: JSON
- LSTM: PyTorch state_dict
"""

import json
import os
import warnings

import joblib
import numpy as np
import optuna
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")


# ──────────────────────────────────────────────────────────────
# Data loading and splitting
# ──────────────────────────────────────────────────────────────

def load_data():
    """Load features and split temporally."""
    # Use raw features (not normalized) for tree models
    raw_path = os.path.join(PROCESSED_DIR, "features_raw.csv")
    norm_path = os.path.join(PROCESSED_DIR, "features.csv")

    df_raw = pd.read_csv(raw_path)
    df_norm = pd.read_csv(norm_path)

    target_col = "co2"
    exclude_cols = ["country", "iso_code", "year", target_col]
    feature_cols = [
        c for c in df_raw.columns
        if c not in exclude_cols and df_raw[c].dtype in [np.float64, np.int64, float, int]
    ]

    # Remove columns that are direct derivatives of target to prevent leakage
    leakage_cols = [
        "co2_per_capita", "co2_per_gdp", "co2_growth_abs", "co2_growth_prct",
        "cumulative_co2", "share_global_co2", "total_co2_owid", "total_sector_co2",
        "co2_yoy_growth", "co2_per_energy",
    ]
    feature_cols = [c for c in feature_cols if c not in leakage_cols]

    print(f"Using {len(feature_cols)} features for modeling")

    # Temporal split
    train_mask = df_raw["year"] <= 2015
    val_mask = (df_raw["year"] >= 2016) & (df_raw["year"] <= 2019)
    test_mask = (df_raw["year"] >= 2020) & (df_raw["year"] <= 2022)

    # For tree models (use raw data)
    X_train = df_raw.loc[train_mask, feature_cols].values
    y_train = df_raw.loc[train_mask, target_col].values
    X_val = df_raw.loc[val_mask, feature_cols].values
    y_val = df_raw.loc[val_mask, target_col].values
    X_test = df_raw.loc[test_mask, feature_cols].values
    y_test = df_raw.loc[test_mask, target_col].values

    # For LSTM (use normalized data)
    X_train_norm = df_norm.loc[train_mask, feature_cols].values
    y_train_norm = df_norm.loc[train_mask, target_col].values
    X_val_norm = df_norm.loc[val_mask, feature_cols].values
    y_val_norm = df_norm.loc[val_mask, target_col].values
    X_test_norm = df_norm.loc[test_mask, feature_cols].values
    y_test_norm = df_norm.loc[test_mask, target_col].values

    years_train = df_raw.loc[train_mask, "year"].values
    years_val = df_raw.loc[val_mask, "year"].values
    years_test = df_raw.loc[test_mask, "year"].values

    print(f"  Train: {len(X_train)} samples ({years_train.min()}-{years_train.max()})")
    print(f"  Val:   {len(X_val)} samples ({years_val.min()}-{years_val.max()})")
    print(f"  Test:  {len(X_test)} samples ({years_test.min()}-{years_test.max()})")

    return {
        "feature_cols": feature_cols,
        "target_col": target_col,
        "raw": {
            "X_train": X_train, "y_train": y_train,
            "X_val": X_val, "y_val": y_val,
            "X_test": X_test, "y_test": y_test,
        },
        "norm": {
            "X_train": X_train_norm, "y_train": y_train_norm,
            "X_val": X_val_norm, "y_val": y_val_norm,
            "X_test": X_test_norm, "y_test": y_test_norm,
        },
        "years": {
            "train": years_train, "val": years_val, "test": years_test,
        },
        "df_raw": df_raw,
        "df_norm": df_norm,
    }


def evaluate_model(y_true, y_pred, model_name):
    """Calculate R2, MAE, RMSE."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"  {model_name} -> R2: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    return {"r2": round(r2, 4), "mae": round(mae, 4), "rmse": round(rmse, 4)}


# ──────────────────────────────────────────────────────────────
# Model 1: Random Forest
# ──────────────────────────────────────────────────────────────

def train_random_forest(data):
    """Train Random Forest regressor."""
    print("\n--- Training Random Forest ---")
    d = data["raw"]

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_split=3,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(d["X_train"], d["y_train"])

    # Evaluate
    pred_val = rf.predict(d["X_val"])
    pred_test = rf.predict(d["X_test"])

    print("  Validation:")
    val_metrics = evaluate_model(d["y_val"], pred_val, "RF")
    print("  Test:")
    test_metrics = evaluate_model(d["y_test"], pred_test, "RF")

    # Feature importance
    importances = pd.Series(
        rf.feature_importances_, index=data["feature_cols"]
    ).sort_values(ascending=False)
    print("  Top 10 features:")
    for feat, imp in importances.head(10).items():
        print(f"    {feat}: {imp:.4f}")

    # Save
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "random_forest.joblib")
    joblib.dump(rf, model_path)
    print(f"  Saved to {model_path}")

    return rf, {
        "validation": val_metrics,
        "test": test_metrics,
        "feature_importance": importances.head(10).to_dict(),
    }


# ──────────────────────────────────────────────────────────────
# Model 2: XGBoost with Optuna
# ──────────────────────────────────────────────────────────────

def train_xgboost(data):
    """Train XGBoost with Optuna-based Bayesian hyperparameter optimization."""
    print("\n--- Training XGBoost with Optuna ---")
    d = data["raw"]

    def objective(trial):
        params = {
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        }

        model = XGBRegressor(**params, random_state=42, verbosity=0)
        model.fit(d["X_train"], d["y_train"])
        pred_val = model.predict(d["X_val"])
        return mean_squared_error(d["y_val"], pred_val)

    print("  Running 50 Optuna trials...")
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=50, show_progress_bar=False)

    print(f"  Best trial MSE: {study.best_value:.4f}")
    print(f"  Best params: {study.best_params}")

    # Train final model with best params
    best_params = study.best_params
    xgb = XGBRegressor(**best_params, random_state=42, verbosity=0)
    xgb.fit(d["X_train"], d["y_train"])

    # Evaluate
    pred_val = xgb.predict(d["X_val"])
    pred_test = xgb.predict(d["X_test"])

    print("  Validation:")
    val_metrics = evaluate_model(d["y_val"], pred_val, "XGBoost")
    print("  Test:")
    test_metrics = evaluate_model(d["y_test"], pred_test, "XGBoost")

    # Save
    model_path = os.path.join(MODELS_DIR, "xgboost_model.json")
    xgb.save_model(model_path)
    print(f"  Saved to {model_path}")

    # Save best params
    params_path = os.path.join(MODELS_DIR, "xgboost_params.json")
    with open(params_path, "w") as f:
        json.dump(best_params, f, indent=2)

    return xgb, {
        "validation": val_metrics,
        "test": test_metrics,
        "best_params": best_params,
    }


# ──────────────────────────────────────────────────────────────
# Model 3: LSTM (PyTorch)
# ──────────────────────────────────────────────────────────────

class LSTMModel(nn.Module):
    """Stacked 2-layer LSTM for time-series regression."""

    def __init__(self, input_size, hidden_size_1=64, hidden_size_2=32, dropout=0.2):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden_size_1, batch_first=True)
        self.dropout1 = nn.Dropout(dropout)
        self.lstm2 = nn.LSTM(hidden_size_1, hidden_size_2, batch_first=True)
        self.dropout2 = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size_2, 1)

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out)
        out = self.fc(out[:, -1, :])  # Take last time step
        return out


def create_sequences(X, y, lookback=5):
    """Create sliding window sequences for LSTM."""
    Xs, ys = [], []
    for i in range(lookback, len(X)):
        Xs.append(X[i - lookback : i])
        ys.append(y[i])
    return np.array(Xs), np.array(ys)


def train_lstm(data):
    """Train LSTM model with early stopping and LR scheduling."""
    print("\n--- Training LSTM (PyTorch) ---")

    # Use normalized data for LSTM
    d = data["norm"]

    # Combine train + val for sequence creation, then re-split
    # This ensures we have enough data for lookback windows
    X_all = np.vstack([d["X_train"], d["X_val"], d["X_test"]])
    y_all = np.concatenate([d["y_train"], d["y_val"], d["y_test"]])

    lookback = 5
    X_seq, y_seq = create_sequences(X_all, y_all, lookback)

    # Re-split sequences based on original temporal boundaries
    n_train = len(d["X_train"]) - lookback
    n_val = len(d["X_val"])
    n_test = len(d["X_test"])

    # Adjust for sequence creation offset
    train_end = max(1, n_train)
    val_end = train_end + n_val

    X_train_seq = X_seq[:train_end]
    y_train_seq = y_seq[:train_end]
    X_val_seq = X_seq[train_end:val_end]
    y_val_seq = y_seq[train_end:val_end]
    X_test_seq = X_seq[val_end:]
    y_test_seq = y_seq[val_end:]

    print(f"  Sequences -> Train: {len(X_train_seq)}, Val: {len(X_val_seq)}, Test: {len(X_test_seq)}")

    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train_seq)
    y_train_t = torch.FloatTensor(y_train_seq).unsqueeze(1)
    X_val_t = torch.FloatTensor(X_val_seq)
    y_val_t = torch.FloatTensor(y_val_seq).unsqueeze(1)
    X_test_t = torch.FloatTensor(X_test_seq)
    y_test_t = torch.FloatTensor(y_test_seq).unsqueeze(1)

    # Model
    input_size = X_train_seq.shape[2]
    model = LSTMModel(input_size, hidden_size_1=64, hidden_size_2=32, dropout=0.2)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=10
    )

    # Training loop with early stopping
    best_val_loss = float("inf")
    patience = 15
    patience_counter = 0
    best_state = None

    print("  Training...")
    for epoch in range(500):
        model.train()
        optimizer.zero_grad()
        output = model(X_train_t)
        loss = criterion(output, y_train_t)
        loss.backward()
        optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_output = model(X_val_t)
            val_loss = criterion(val_output, y_val_t).item()

        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_state = model.state_dict().copy()
        else:
            patience_counter += 1

        if (epoch + 1) % 50 == 0:
            print(f"    Epoch {epoch+1}: train_loss={loss.item():.6f}, val_loss={val_loss:.6f}")

        if patience_counter >= patience:
            print(f"    Early stopping at epoch {epoch+1}")
            break

    # Load best model
    if best_state is not None:
        model.load_state_dict(best_state)

    # Evaluate on test set
    model.eval()
    with torch.no_grad():
        # Get predictions in normalized space
        pred_val_norm = model(X_val_t).numpy().flatten()
        pred_test_norm = model(X_test_t).numpy().flatten()

    # Inverse transform predictions back to original scale
    scaler_params = pd.read_csv(os.path.join(PROCESSED_DIR, "scaler_params.csv"))
    co2_params = scaler_params[scaler_params["feature"] == "co2"].iloc[0]
    co2_min, co2_max = co2_params["min"], co2_params["max"]

    def inverse_minmax(vals, vmin, vmax):
        return vals * (vmax - vmin) + vmin

    pred_val_orig = inverse_minmax(pred_val_norm, co2_min, co2_max)
    pred_test_orig = inverse_minmax(pred_test_norm, co2_min, co2_max)
    y_val_orig = inverse_minmax(y_val_seq, co2_min, co2_max)
    y_test_orig = inverse_minmax(y_test_seq, co2_min, co2_max)

    print("  Validation:")
    val_metrics = evaluate_model(y_val_orig, pred_val_orig, "LSTM")
    print("  Test:")
    test_metrics = evaluate_model(y_test_orig, pred_test_orig, "LSTM")

    # Save model
    os.makedirs(os.path.join(MODELS_DIR, "lstm_model"), exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "lstm_model", "model.pt")
    torch.save({
        "model_state_dict": model.state_dict(),
        "input_size": input_size,
        "hidden_size_1": 64,
        "hidden_size_2": 32,
        "dropout": 0.2,
        "lookback": lookback,
    }, model_path)
    print(f"  Saved to {model_path}")

    return model, {
        "validation": val_metrics,
        "test": test_metrics,
    }


# ──────────────────────────────────────────────────────────────
# Backtest sanity check
# ──────────────────────────────────────────────────────────────

def backtest(data):
    """Train only up to 2020, forecast 2021-2022, compare with actuals."""
    print("\n--- Backtest Sanity Check ---")
    print("  Training RF up to 2020, forecasting 2021-2022...")

    df = data["df_raw"]
    feature_cols = data["feature_cols"]
    target_col = data["target_col"]

    bt_train = df[df["year"] <= 2020]
    bt_test = df[(df["year"] >= 2021) & (df["year"] <= 2022)]

    X_bt_train = bt_train[feature_cols].values
    y_bt_train = bt_train[target_col].values
    X_bt_test = bt_test[feature_cols].values
    y_bt_test = bt_test[target_col].values

    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
    rf.fit(X_bt_train, y_bt_train)
    pred = rf.predict(X_bt_test)

    print("  Backtest results (2021-2022):")
    bt_metrics = evaluate_model(y_bt_test, pred, "RF-Backtest")

    print("  Year-by-year comparison:")
    for i, year in enumerate(bt_test["year"].values):
        print(f"    {year}: actual={y_bt_test[i]:.2f}, predicted={pred[i]:.2f}, "
              f"error={abs(y_bt_test[i] - pred[i]):.2f}")

    return bt_metrics


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────

def main():
    data = load_data()

    # Train all three models
    rf_model, rf_results = train_random_forest(data)
    xgb_model, xgb_results = train_xgboost(data)
    lstm_model, lstm_results = train_lstm(data)

    # Backtest
    bt_metrics = backtest(data)

    # Compile and save metrics
    metrics = {
        "random_forest": {
            "test": rf_results["test"],
            "validation": rf_results["validation"],
        },
        "xgboost": {
            "test": xgb_results["test"],
            "validation": xgb_results["validation"],
            "best_params": xgb_results.get("best_params", {}),
        },
        "lstm": {
            "test": lstm_results["test"],
            "validation": lstm_results["validation"],
        },
        "backtest": bt_metrics,
        "feature_columns": data["feature_cols"],
    }

    # Determine best model
    test_r2 = {
        "random_forest": rf_results["test"]["r2"],
        "xgboost": xgb_results["test"]["r2"],
        "lstm": lstm_results["test"]["r2"],
    }
    best_model = max(test_r2, key=test_r2.get)
    metrics["best_model"] = best_model

    print(f"\n{'='*50}")
    print("FINAL RESULTS (Test Set)")
    print(f"{'='*50}")
    for name, r2 in test_r2.items():
        marker = " <-- BEST" if name == best_model else ""
        print(f"  {name}: R2={r2}{marker}")
    print(f"\nBest model for production: {best_model}")

    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
