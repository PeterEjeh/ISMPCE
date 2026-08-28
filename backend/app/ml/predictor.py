"""Prediction logic with confidence intervals and scenario simulation (National & State-Level)."""

import os
import json
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import joblib
import torch

from ..config import DATA_DIR, MODELS_DIR
from .loader import get_best_model_name, get_models

STATE_MODELS_DIR = os.path.join(MODELS_DIR, "state_models")
STATE_DATA_PATH = os.path.join(DATA_DIR, "processed", "state_emissions_features.csv")


def _load_state_metadata():
    """Load state evaluation metrics, baseline levels, and sector profiles."""
    metrics_path = os.path.join(STATE_MODELS_DIR, "state_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {}


def _load_state_data():
    """Load state features master dataset."""
    if os.path.exists(STATE_DATA_PATH):
        return pd.read_csv(STATE_DATA_PATH)
    return None


def _load_state_model(state_name: str, model_type: str = "xgboost"):
    """Load trained state-specific model artifact."""
    slug = state_name.lower().replace(" ", "_")
    model_file = f"{slug}_{model_type}.joblib"
    path = os.path.join(STATE_MODELS_DIR, model_file)
    if os.path.exists(path):
        return joblib.load(path)
    fallback_path = os.path.join(STATE_MODELS_DIR, f"rivers_{model_type}.joblib")
    if os.path.exists(fallback_path):
        return joblib.load(fallback_path)
    return None


def _load_feature_data():
    """Load raw national feature data."""
    raw_path = os.path.join(DATA_DIR, "features_raw.csv")
    if os.path.exists(raw_path):
        return pd.read_csv(raw_path)
    return None


def _load_scaler_params():
    """Load scaler parameters for inverse transform."""
    path = os.path.join(DATA_DIR, "scaler_params.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None


def _get_feature_columns():
    """Get the national feature columns used during training."""
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        return metrics.get("feature_columns", [])
    return []


def _apply_scenario_to_features(
    features: np.ndarray,
    feature_cols: list,
    year_index: int,
    fossil_fuel_share_change: Optional[float],
    gdp_growth_rate: Optional[float],
    population_growth_rate: Optional[float],
    prev_co2_pred: Optional[float] = None,
) -> np.ndarray:
    """Apply scenario overrides across national feature vector."""
    scenario = features.copy()
    col_map = {name: idx for idx, name in enumerate(feature_cols)}

    if prev_co2_pred is not None and "co2_lag1" in col_map:
        scenario[col_map["co2_lag1"]] = prev_co2_pred

    if fossil_fuel_share_change is not None:
        annual_delta = (fossil_fuel_share_change / 10.0) * year_index
        for col in ("fossil_fuel_share", "fossil_fuel_share_in_electricity", "energy_share"):
            if col in col_map:
                scenario[col_map[col]] = max(5.0, min(100.0, scenario[col_map[col]] + annual_delta))

        if "renewable_energy_pct" in col_map:
            scenario[col_map["renewable_energy_pct"]] = max(0.0, min(95.0, scenario[col_map["renewable_energy_pct"]] - annual_delta))

        fossil_mult = max(0.2, 1.0 + (fossil_fuel_share_change / 100.0)) ** (year_index / 5.0)
        for col in ("oil_co2", "gas_co2", "coal_co2", "flaring_co2", "energy_co2"):
            if col in col_map:
                scenario[col_map[col]] *= fossil_mult

    if gdp_growth_rate is not None:
        growth_factor = (1.0 + gdp_growth_rate / 100.0) ** year_index
        for col in ("gdp", "gdp_constant_usd", "gdp_current_usd", "gdp_per_capita", "energy_per_gdp"):
            if col in col_map:
                scenario[col_map[col]] *= growth_factor
        if "gdp_yoy_growth" in col_map:
            scenario[col_map["gdp_yoy_growth"]] = gdp_growth_rate

    if population_growth_rate is not None:
        pop_factor = (1.0 + population_growth_rate / 100.0) ** year_index
        for col in ("population", "population_total"):
            if col in col_map:
                scenario[col_map[col]] *= pop_factor
        if "pop_yoy_growth" in col_map:
            scenario[col_map["pop_yoy_growth"]] = population_growth_rate
        if "population_growth_pct" in col_map:
            scenario[col_map["population_growth_pct"]] = population_growth_rate

    if "gdp_pop_interaction" in col_map and "gdp" in col_map and "population" in col_map:
        scenario[col_map["gdp_pop_interaction"]] = (scenario[col_map["gdp"]] * scenario[col_map["population"]]) / 1e18

    return scenario


def _predict_state_level(
    state_name: str,
    forecast_horizon: int,
    model_name: str,
    fossil_fuel_share_change: Optional[float],
    gdp_growth_rate: Optional[float],
    population_growth_rate: Optional[float],
) -> Tuple[str, List[Dict[str, Any]], bool]:
    """Execute prediction using dedicated State-Level Model."""
    state_meta = _load_state_metadata()
    df_state = _load_state_data()
    
    clean_name = state_name.replace(" (National)", "").replace(" (Case Study)", "").strip()
    if clean_name not in state_meta:
        for s in state_meta:
            if s.lower() == clean_name.lower() or clean_name.lower() in s.lower():
                clean_name = s
                break
                
    m_type = "xgboost" if (model_name and "xgb" in model_name.lower()) else ("random_forest" if (model_name and "random" in model_name.lower()) else "xgboost")
    model = _load_state_model(clean_name, m_type)
    
    state_rows = df_state[df_state["state"] == clean_name].sort_values("year") if df_state is not None else None
    if state_rows is None or len(state_rows) == 0:
        base_co2 = state_meta.get(clean_name, {}).get("latest_2022_co2", 4.5)
        last_year = 2024
    else:
        base_co2 = float(state_rows["co2"].iloc[-1])
        last_year = int(state_rows["year"].max())
        
    feat_cols = state_meta.get(clean_name, {}).get("feature_columns", [
        'co2_lag1', 'co2_lag2', 'co2_roll3', 'gdp', 'population', 'fossil_fuel_share',
        'oil_gas_co2', 'transport_co2', 'industry_co2', 'agriculture_co2'
    ])
    col_map = {c: i for i, c in enumerate(feat_cols)}
    
    last_row = state_rows.iloc[-1] if (state_rows is not None and len(state_rows) > 0) else None
    
    if last_row is not None:
        last_features = last_row[feat_cols].values.copy().astype(float)
    else:
        last_features = np.array([base_co2, base_co2*0.98, base_co2, 1e10, 5e6, 75.0, base_co2*0.4, base_co2*0.3, base_co2*0.2, base_co2*0.1])
        
    has_scenario = any(v is not None for v in (fossil_fuel_share_change, gdp_growth_rate, population_growth_rate))
    
    forecasts = []
    prev_baseline_co2 = base_co2
    prev_scenario_co2 = base_co2
    curr_base_feat = last_features.copy()
    
    prof = state_meta.get(clean_name, {}).get("profiles", {})
    oil_gas_share = prof.get("oil_gas_share", 0.25)
    transport_share = prof.get("transport_share", 0.35)
    industry_share = prof.get("industry_share", 0.20)
    
    for i in range(1, forecast_horizon + 1):
        year = last_year + i
        
        if "co2_lag1" in col_map and i > 1:
            curr_base_feat[col_map["co2_lag1"]] = prev_baseline_co2
        if "co2_roll3" in col_map and i > 1:
            curr_base_feat[col_map["co2_roll3"]] = (curr_base_feat[col_map["co2_roll3"]] * 2 + prev_baseline_co2) / 3.0
            
        if model is not None:
            delta_pred = float(model.predict(curr_base_feat.reshape(1, -1))[0])
            pred = round(prev_baseline_co2 + delta_pred, 2)
        else:
            pred = round(prev_baseline_co2 * (1.022), 2)
            
        prev_baseline_co2 = pred
        uncertainty = round(pred * 0.04 * np.sqrt(i), 2)
        
        point = {
            "year": year,
            "predicted_co2": pred,
            "confidence_lower": round(max(0, pred - uncertainty), 2),
            "confidence_upper": round(pred + uncertainty, 2),
            "scenario_co2": None,
            "scenario_lower": None,
            "scenario_upper": None,
        }
        
        if has_scenario:
            scen_feat = last_features.copy()
            if "co2_lag1" in col_map and i > 1:
                scen_feat[col_map["co2_lag1"]] = prev_scenario_co2
                
            if fossil_fuel_share_change is not None:
                state_fossil_weight = oil_gas_share * 1.2 + transport_share * 0.8 + industry_share * 0.6
                fossil_impact = (fossil_fuel_share_change / 100.0) * state_fossil_weight * (i / 5.0)
                if "fossil_fuel_share" in col_map:
                    scen_feat[col_map["fossil_fuel_share"]] += (fossil_fuel_share_change / 10.0) * i
            else:
                fossil_impact = 0.0
                
            if gdp_growth_rate is not None:
                gdp_impact = (gdp_growth_rate / 100.0) * (industry_share * 1.1 + transport_share * 0.7) * (i / 5.0)
                if "gdp" in col_map:
                    scen_feat[col_map["gdp"]] *= (1.0 + gdp_growth_rate / 100.0) ** i
            else:
                gdp_impact = 0.0
                
            if population_growth_rate is not None:
                pop_impact = (population_growth_rate / 100.0) * 0.35 * (i / 5.0)
                if "population" in col_map:
                    scen_feat[col_map["population"]] *= (1.0 + population_growth_rate / 100.0) ** i
            else:
                pop_impact = 0.0
                
            total_multiplier = max(0.2, 1.0 + fossil_impact + gdp_impact + pop_impact)
            
            if model is not None:
                scen_delta = float(model.predict(scen_feat.reshape(1, -1))[0])
                scen_pred = round((prev_scenario_co2 + scen_delta) * total_multiplier, 2)
            else:
                scen_pred = round(pred * total_multiplier, 2)
                
            prev_scenario_co2 = scen_pred
            scen_unc = round(scen_pred * 0.04 * np.sqrt(i), 2)
            point["scenario_co2"] = scen_pred
            point["scenario_lower"] = round(max(0, scen_pred - scen_unc), 2)
            point["scenario_upper"] = round(scen_pred + scen_unc, 2)
            
        forecasts.append(point)
        
    model_label = f"State-{m_type.upper()} ({clean_name} Model)"
    return model_label, forecasts, has_scenario


def predict_emissions(
    region: str,
    forecast_horizon: int,
    model_name: str = None,
    fossil_fuel_share_change: Optional[float] = None,
    gdp_growth_rate: Optional[float] = None,
    population_growth_rate: Optional[float] = None,
):
    """
    Generate CO2 emission forecasts for National or State-level targets.
    Routes to dedicated State-Level Models when a specific state is requested.
    """
    if region and region not in ("Nigeria", "Nigeria (National)", "National", "NGA"):
        return _predict_state_level(
            state_name=region,
            forecast_horizon=forecast_horizon,
            model_name=model_name,
            fossil_fuel_share_change=fossil_fuel_share_change,
            gdp_growth_rate=gdp_growth_rate,
            population_growth_rate=population_growth_rate,
        )

    models = get_models()
    if not models:
        raise ValueError("No models loaded")

    if model_name is None or model_name not in models:
        model_name = get_best_model_name()

    df = _load_feature_data()
    if df is None:
        raise ValueError("Feature data not found")

    feature_cols = _get_feature_columns()
    if not feature_cols:
        raise ValueError("Feature columns not found in metrics")

    col_map = {name: idx for idx, name in enumerate(feature_cols)}
    has_scenario = any(v is not None for v in (fossil_fuel_share_change, gdp_growth_rate, population_growth_rate))

    last_year = int(df["year"].max())
    co2_values = df["co2"].values
    co2_std = float(np.std(co2_values))

    last_features = df[feature_cols].iloc[-1].values.copy().astype(float)
    last_co2 = float(df["co2"].iloc[-1])

    forecasts = []

    if model_name in ("random_forest", "xgboost"):
        model = models[model_name]
        prev_baseline_co2 = last_co2
        prev_scenario_co2 = last_co2
        curr_baseline_features = last_features.copy()

        for i in range(1, forecast_horizon + 1):
            year = last_year + i

            if "co2_lag1" in col_map and i > 1:
                curr_baseline_features[col_map["co2_lag1"]] = prev_baseline_co2

            pred = float(model.predict(curr_baseline_features.reshape(1, -1))[0])
            prev_baseline_co2 = pred

            uncertainty = co2_std * 0.3 * np.sqrt(i)
            lower = pred - uncertainty
            upper = pred + uncertainty

            point = {
                "year": year,
                "predicted_co2": round(pred, 2),
                "confidence_lower": round(max(0, lower), 2),
                "confidence_upper": round(upper, 2),
                "scenario_co2": None,
                "scenario_lower": None,
                "scenario_upper": None,
            }

            if has_scenario:
                scen_features = _apply_scenario_to_features(
                    last_features, feature_cols, i,
                    fossil_fuel_share_change, gdp_growth_rate, population_growth_rate,
                    prev_co2_pred=prev_scenario_co2 if i > 1 else None,
                )
                scen_pred = float(model.predict(scen_features.reshape(1, -1))[0])
                prev_scenario_co2 = scen_pred
                scen_uncertainty = co2_std * 0.3 * np.sqrt(i)
                point["scenario_co2"] = round(scen_pred, 2)
                point["scenario_lower"] = round(max(0, scen_pred - scen_uncertainty), 2)
                point["scenario_upper"] = round(scen_pred + scen_uncertainty, 2)

            forecasts.append(point)

    elif model_name == "lstm":
        lstm_data = models["lstm"]
        model = lstm_data["model"]
        lookback = lstm_data["lookback"]

        norm_path = os.path.join(DATA_DIR, "features.csv")
        df_norm = pd.read_csv(norm_path)
        scaler_params = _load_scaler_params()

        recent_data = df_norm[feature_cols].iloc[-lookback:].values.copy()

        co2_params = scaler_params[scaler_params["feature"] == "co2"].iloc[0]
        co2_min, co2_max = co2_params["min"], co2_params["max"]

        for i in range(1, forecast_horizon + 1):
            year = last_year + i

            input_tensor = torch.FloatTensor(recent_data).unsqueeze(0)
            with torch.no_grad():
                pred_norm = model(input_tensor).item()

            pred = pred_norm * (co2_max - co2_min) + co2_min
            uncertainty = co2_std * 0.3 * np.sqrt(i)
            lower = pred - uncertainty
            upper = pred + uncertainty

            point = {
                "year": year,
                "predicted_co2": round(pred, 2),
                "confidence_lower": round(max(0, lower), 2),
                "confidence_upper": round(upper, 2),
                "scenario_co2": None,
                "scenario_lower": None,
                "scenario_upper": None,
            }

            if has_scenario:
                scale = 1.0
                if fossil_fuel_share_change is not None:
                    scale += (fossil_fuel_share_change / 100.0) * 0.4 * (i / 5.0)
                if gdp_growth_rate is not None:
                    scale += (gdp_growth_rate / 100.0) * 0.35 * (i / 5.0)
                if population_growth_rate is not None:
                    scale += (population_growth_rate / 100.0) * 0.3 * (i / 5.0)
                scen_pred = pred * max(0.4, scale)
                scen_uncertainty = co2_std * 0.3 * np.sqrt(i)
                point["scenario_co2"] = round(scen_pred, 2)
                point["scenario_lower"] = round(max(0, scen_pred - scen_uncertainty), 2)
                point["scenario_upper"] = round(scen_pred + scen_uncertainty, 2)

            forecasts.append(point)

    return model_name, forecasts, has_scenario
