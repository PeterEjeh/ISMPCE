"""
Download OWID CO2 dataset and filter for Nigeria.
Source: https://github.com/owid/co2-data
"""

import os
import urllib.request
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
OWID_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"

COLUMNS_OF_INTEREST = [
    "country",
    "year",
    "iso_code",
    "co2",
    "co2_per_capita",
    "co2_per_gdp",
    "coal_co2",
    "oil_co2",
    "gas_co2",
    "flaring_co2",
    "cement_co2",
    "other_industry_co2",
    "co2_growth_abs",
    "co2_growth_prct",
    "cumulative_co2",
    "population",
    "gdp",
    "primary_energy_consumption",
    "energy_per_capita",
    "energy_per_gdp",
    "share_global_co2",
]


def download_owid():
    """Download the full OWID CO2 CSV and filter for Nigeria."""
    print("Downloading OWID CO2 dataset...")
    os.makedirs(RAW_DIR, exist_ok=True)
    temp_path = os.path.join(RAW_DIR, "owid_co2_full.csv")

    # Download with proper headers
    req = urllib.request.Request(OWID_URL, headers={"User-Agent": "ISMPCE/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        with open(temp_path, "wb") as f:
            f.write(response.read())

    df_full = pd.read_csv(temp_path)
    print(f"  Full dataset: {len(df_full):,} rows, {len(df_full.columns)} columns")
    print(f"  Latest year in dataset: {df_full['year'].max()}")

    # Filter for Nigeria from 1990 onward
    df_nigeria = df_full[
        (df_full["country"] == "Nigeria") & (df_full["year"] >= 1990)
    ].copy()

    # Keep only columns of interest (drop any that don't exist in this version)
    available_cols = [c for c in COLUMNS_OF_INTEREST if c in df_nigeria.columns]
    missing_cols = [c for c in COLUMNS_OF_INTEREST if c not in df_nigeria.columns]
    if missing_cols:
        print(f"  Note: columns not found in dataset: {missing_cols}")

    df_nigeria = df_nigeria[available_cols].reset_index(drop=True)

    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "owid_nigeria_co2.csv")
    df_nigeria.to_csv(out_path, index=False)
    print(f"  Saved {len(df_nigeria)} rows to {out_path}")
    print(f"  Year range: {df_nigeria['year'].min()} - {df_nigeria['year'].max()}")

    return df_nigeria


if __name__ == "__main__":
    download_owid()
