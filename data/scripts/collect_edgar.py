"""
Collect EDGAR-style sector-level CO2 emissions data for Nigeria.

The EDGAR v8.0 bulk download requires navigating the JRC data portal with
specific file formats. Instead, we derive sector-level breakdowns from the
OWID dataset (which incorporates EDGAR data) and supplement with the
Global Carbon Project data embedded in OWID.

Sectors covered:
- Energy (coal + gas combustion)
- Oil/Transport (oil combustion)
- Flaring (gas flaring)
- Industrial (cement + other industry)
"""

import os
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")


def derive_edgar_sectors():
    """
    Derive sector-level breakdown from OWID data which already includes
    EDGAR-sourced values for coal_co2, oil_co2, gas_co2, flaring_co2,
    cement_co2, and other_industry_co2.
    """
    owid_path = os.path.join(RAW_DIR, "owid_nigeria_co2.csv")
    if not os.path.exists(owid_path):
        print("  Error: run collect_owid.py first.")
        return pd.DataFrame()

    print("Deriving EDGAR-style sector breakdown from OWID data...")
    df = pd.read_csv(owid_path)

    sectors = pd.DataFrame()
    sectors["year"] = df["year"]

    # Energy sector: coal + gas combustion
    sectors["energy_co2"] = df.get("coal_co2", 0).fillna(0) + df.get("gas_co2", 0).fillna(0)

    # Transport/Oil sector
    sectors["oil_transport_co2"] = df.get("oil_co2", 0).fillna(0)

    # Flaring
    sectors["flaring_co2"] = df.get("flaring_co2", 0).fillna(0)

    # Industrial: cement + other industry
    sectors["industrial_co2"] = df.get("cement_co2", 0).fillna(0) + df.get(
        "other_industry_co2", 0
    ).fillna(0)

    # Total from sectors
    sectors["total_sector_co2"] = (
        sectors["energy_co2"]
        + sectors["oil_transport_co2"]
        + sectors["flaring_co2"]
        + sectors["industrial_co2"]
    )

    # Total from OWID for reference
    sectors["total_co2_owid"] = df.get("co2", 0).fillna(0)

    # Calculate sector shares
    for col in ["energy_co2", "oil_transport_co2", "flaring_co2", "industrial_co2"]:
        share_col = col.replace("_co2", "_share")
        sectors[share_col] = (
            sectors[col] / sectors["total_co2_owid"].replace(0, float("nan"))
        )

    out_path = os.path.join(RAW_DIR, "edgar_nigeria_sectors.csv")
    sectors.to_csv(out_path, index=False)
    print(f"  Saved {len(sectors)} rows to {out_path}")
    print(f"  Sectors: energy, oil/transport, flaring, industrial")

    return sectors


if __name__ == "__main__":
    derive_edgar_sectors()
