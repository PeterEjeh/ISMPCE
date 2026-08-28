"""Load serialized ML models at application startup."""

import json
import os

import joblib
import numpy as np
import torch
import torch.nn as nn
from xgboost import XGBRegressor

from ..config import MODELS_DIR


# ── LSTM model class (must match training definition) ─────────

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
        out = self.fc(out[:, -1, :])
        return out


# ── Global model registry ────────────────────────────────────

_models = {}
_metrics = {}


def load_models():
    """Load all trained model artifacts. Called once at startup."""
    global _models, _metrics

    # Random Forest
    rf_path = os.path.join(MODELS_DIR, "random_forest.joblib")
    if os.path.exists(rf_path):
        _models["random_forest"] = joblib.load(rf_path)
        print(f"  Loaded Random Forest from {rf_path}")

    # XGBoost
    xgb_path = os.path.join(MODELS_DIR, "xgboost_model.json")
    if os.path.exists(xgb_path):
        xgb = XGBRegressor()
        xgb.load_model(xgb_path)
        _models["xgboost"] = xgb
        print(f"  Loaded XGBoost from {xgb_path}")

    # LSTM
    lstm_path = os.path.join(MODELS_DIR, "lstm_model", "model.pt")
    if os.path.exists(lstm_path):
        checkpoint = torch.load(lstm_path, map_location="cpu", weights_only=True)
        model = LSTMModel(
            input_size=checkpoint["input_size"],
            hidden_size_1=checkpoint["hidden_size_1"],
            hidden_size_2=checkpoint["hidden_size_2"],
            dropout=checkpoint["dropout"],
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        _models["lstm"] = {
            "model": model,
            "lookback": checkpoint["lookback"],
            "input_size": checkpoint["input_size"],
        }
        print(f"  Loaded LSTM from {lstm_path}")

    # Metrics
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            _metrics = json.load(f)
        print(f"  Loaded metrics from {metrics_path}")

    print(f"  Models loaded: {list(_models.keys())}")
    return _models


def get_models():
    """Return the model registry."""
    return _models


def get_metrics():
    """Return stored metrics."""
    return _metrics


def get_best_model_name():
    """Return the name of the best model."""
    return _metrics.get("best_model", "xgboost")
