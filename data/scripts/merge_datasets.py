"""
Merge OWID, World Bank, and EDGAR sector data into one clean table.
Apply interpolation, outlier detection, and save processed output.
"""

import os
import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "processed")


def load_owid():
    path = os.path.join(RAW_DIR, "owid_nigeria_co2.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Drop columns that will come from other sources or cause duplication
    drop_cols = ["country", "iso_code"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    return df


def load_worldbank():
    path = os.path.join(RAW_DIR, "worldbank_nigeria.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Rename to avoid conflicts with OWID columns
    rename_map = {}
    if "co2_emissions_kt" in df.columns:
        rename_map["co2_emissions_kt"] = "co2_wb_kt"
    if "co2_per_capita_wb" in df.columns:
        rename_map["co2_per_capita_wb"] = "co2_per_capita_wb"
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def load_edgar():
    path = os.path.join(RAW_DIR, "edgar_nigeria_sectors.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def iqr_outlier_cap(series):
    """Cap outliers using the IQR method (1.5 * IQR)."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return series.clip(lower=lower, upper=upper)


def merge_datasets():
    """Merge all data sources, clean, and save."""
    print("Loading data sources...")

    df_owid = load_owid()
    df_wb = load_worldbank()
    df_edgar = load_edgar()

    if df_owid.empty:
        print("  Error: OWID data not found. Run collect_owid.py first.")
        return

    # Start with OWID as the base
    merged = df_owid.copy()
    print(f"  OWID: {len(merged)} rows, {len(merged.columns)} columns")

    # Merge World Bank data
    if not df_wb.empty:
        # Remove columns that duplicate OWID (prefer OWID values)
        wb_cols_to_keep = ["year"] + [
            c for c in df_wb.columns if c != "year" and c not in merged.columns
        ]
        df_wb_subset = df_wb[wb_cols_to_keep]
        merged = merged.merge(df_wb_subset, on="year", how="left")
        print(f"  + World Bank: now {len(merged.columns)} columns")

    # Merge EDGAR sector data
    if not df_edgar.empty:
        edgar_cols = ["year"] + [
            c for c in df_edgar.columns if c != "year" and c not in merged.columns
        ]
        df_edgar_subset = df_edgar[edgar_cols]
        merged = merged.merge(df_edgar_subset, on="year", how="left")
        print(f"  + EDGAR sectors: now {len(merged.columns)} columns")

    # Add metadata columns
    merged.insert(0, "country", "Nigeria")
    merged.insert(1, "iso_code", "NGA")

    # Sort by year
    merged = merged.sort_values("year").reset_index(drop=True)

    # --- Interpolation for missing values ---
    print("\nApplying linear interpolation for missing values...")
    numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "year"]

    missing_before = merged[numeric_cols].isna().sum()
    for col in numeric_cols:
        merged[col] = merged[col].interpolate(method="linear", limit_direction="both")
    missing_after = merged[numeric_cols].isna().sum()

    filled = missing_before.sum() - missing_after.sum()
    print(f"  Filled {filled} missing values via interpolation")

    # --- IQR-based outlier detection ---
    print("Applying IQR-based outlier capping...")
    outlier_count = 0
    for col in numeric_cols:
        if col == "year":
            continue
        original = merged[col].copy()
        merged[col] = iqr_outlier_cap(merged[col])
        capped = (original != merged[col]).sum()
        if capped > 0:
            outlier_count += capped
            print(f"  {col}: {capped} values capped")

    print(f"  Total outliers capped: {outlier_count}")

    # Save
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    out_path = os.path.join(PROCESSED_DIR, "merged_emissions.csv")
    merged.to_csv(out_path, index=False)
    print(f"\nSaved merged dataset: {len(merged)} rows x {len(merged.columns)} columns")
    print(f"  Path: {out_path}")
    print(f"  Year range: {merged['year'].min()} - {merged['year'].max()}")
    print(f"\nColumns:")
    for col in merged.columns:
        non_null = merged[col].notna().sum()
        print(f"  {col}: {non_null}/{len(merged)} non-null")

    return merged


if __name__ == "__main__":
    merge_datasets()
