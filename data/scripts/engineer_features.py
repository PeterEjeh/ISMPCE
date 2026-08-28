"""
Feature engineering for CO2 emissions prediction.
Creates lag features, rolling averages, interaction terms,
and applies Min-Max normalization.
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "processed")


def engineer_features():
    """Load merged data and create ML-ready features."""
    input_path = os.path.join(PROCESSED_DIR, "merged_emissions.csv")
    df = pd.read_csv(input_path)
    print(f"Loaded merged dataset: {len(df)} rows x {len(df.columns)} columns")

    # Target variable
    target_col = "co2"

    # --- Lag features ---
    print("Engineering lag features...")
    for lag in [1, 2, 3]:
        df[f"co2_lag{lag}"] = df[target_col].shift(lag)

    # --- Rolling averages ---
    print("Engineering rolling averages...")
    df["co2_roll_3yr"] = df[target_col].rolling(window=3, min_periods=1).mean()
    df["co2_roll_5yr"] = df[target_col].rolling(window=5, min_periods=1).mean()

    # --- Fossil fuel share ---
    print("Engineering fossil fuel share...")
    fossil_sum = df["coal_co2"].fillna(0) + df["oil_co2"].fillna(0) + df["gas_co2"].fillna(0)
    df["fossil_fuel_share"] = fossil_sum / df[target_col].replace(0, np.nan)
    df["fossil_fuel_share"] = df["fossil_fuel_share"].fillna(0)

    # --- GDP x Population interaction ---
    print("Engineering interaction terms...")
    df["gdp_pop_interaction"] = df["gdp"] * df["population"]

    # --- Year-over-year growth rates ---
    df["co2_yoy_growth"] = df[target_col].pct_change()
    df["gdp_yoy_growth"] = df["gdp"].pct_change()
    df["pop_yoy_growth"] = df["population"].pct_change()

    # --- Energy intensity ---
    df["energy_intensity"] = df["primary_energy_consumption"] / df["gdp"].replace(0, np.nan)
    df["co2_per_energy"] = df[target_col] / df["primary_energy_consumption"].replace(0, np.nan)

    # --- Fill NaN from lag/shift operations ---
    df = df.bfill().ffill().fillna(0)

    # Save feature-engineered data (before normalization) for reference
    features_raw_path = os.path.join(PROCESSED_DIR, "features_raw.csv")
    df.to_csv(features_raw_path, index=False)
    print(f"Saved raw features: {len(df)} rows x {len(df.columns)} columns")

    # --- Define feature columns for modeling ---
    exclude_cols = ["country", "iso_code", "year", target_col]
    feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.float64, np.int64, float, int]]

    print(f"\nFeature columns ({len(feature_cols)}):")
    for col in feature_cols:
        print(f"  {col}")

    # --- Min-Max normalization ---
    print("\nApplying Min-Max normalization...")
    scaler = MinMaxScaler()
    df_normalized = df.copy()
    df_normalized[feature_cols] = scaler.fit_transform(df[feature_cols])

    # Also normalize the target
    target_scaler = MinMaxScaler()
    df_normalized[[target_col]] = target_scaler.fit_transform(df[[target_col]])

    # Save normalized features
    features_path = os.path.join(PROCESSED_DIR, "features.csv")
    df_normalized.to_csv(features_path, index=False)
    print(f"Saved normalized features: {len(df_normalized)} rows x {len(df_normalized.columns)} columns")
    print(f"  Path: {features_path}")

    # Save scaler parameters for inverse transform later
    scaler_params = pd.DataFrame({
        "feature": feature_cols + [target_col],
        "min": list(scaler.data_min_) + [target_scaler.data_min_[0]],
        "max": list(scaler.data_max_) + [target_scaler.data_max_[0]],
        "scale": list(scaler.scale_) + [target_scaler.scale_[0]],
    })
    scaler_path = os.path.join(PROCESSED_DIR, "scaler_params.csv")
    scaler_params.to_csv(scaler_path, index=False)
    print(f"Saved scaler parameters to {scaler_path}")

    return df_normalized, feature_cols, target_col


if __name__ == "__main__":
    engineer_features()
