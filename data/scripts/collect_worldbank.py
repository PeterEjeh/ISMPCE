"""
Fetch World Bank WDI indicators for Nigeria via REST API.
No API key required.
"""

import json
import os
import urllib.request
import urllib.error

import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
BASE_URL = "https://api.worldbank.org/v2/country/NG/indicator"

# Indicators to fetch
INDICATORS = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD": "gdp_constant_usd",
    "NY.GDP.PCAP.CD": "gdp_per_capita",
    "SP.POP.TOTL": "population_total",
    "SP.POP.GROW": "population_growth_pct",
    "EG.USE.PCAP.KG.OE": "energy_use_per_capita",
    "EG.ELC.ACCS.ZS": "electricity_access_pct",
    "EN.ATM.CO2E.KT": "co2_emissions_kt",
    "EN.ATM.CO2E.PC": "co2_per_capita_wb",
    "EG.FEC.RNEW.ZS": "renewable_energy_pct",
    "NV.IND.TOTL.ZS": "industry_value_added_pct_gdp",
}


def fetch_indicator(indicator_code, indicator_name):
    """Fetch a single indicator from the World Bank API."""
    url = f"{BASE_URL}/{indicator_code}?format=json&date=1990:2024&per_page=100"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ISMPCE/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"  Warning: failed to fetch {indicator_name}: {e}")
        return pd.DataFrame()

    if not isinstance(data, list) or len(data) < 2:
        print(f"  Warning: no data returned for {indicator_name}")
        return pd.DataFrame()

    records = []
    for entry in data[1]:
        if entry["value"] is not None:
            records.append({"year": int(entry["date"]), indicator_name: entry["value"]})

    return pd.DataFrame(records)


def download_worldbank():
    """Download all WDI indicators and merge into a single DataFrame."""
    print("Fetching World Bank WDI indicators for Nigeria...")

    dfs = []
    for code, name in INDICATORS.items():
        print(f"  Fetching {name} ({code})...")
        df = fetch_indicator(code, name)
        if not df.empty:
            dfs.append(df)
            print(f"    Got {len(df)} data points")
        else:
            print(f"    No data available")

    if not dfs:
        print("  Error: no data fetched from World Bank.")
        return pd.DataFrame()

    # Merge all indicators on year
    merged = dfs[0]
    for df in dfs[1:]:
        merged = merged.merge(df, on="year", how="outer")

    merged = merged.sort_values("year").reset_index(drop=True)

    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, "worldbank_nigeria.csv")
    merged.to_csv(out_path, index=False)
    print(f"  Saved {len(merged)} rows to {out_path}")
    print(f"  Year range: {merged['year'].min()} - {merged['year'].max()}")

    return merged


if __name__ == "__main__":
    download_worldbank()
