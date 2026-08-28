"""
ISMPCE FastAPI Application

An Intelligent System for Monitoring and Predicting Nigeria's CO2 Emissions
"""

import os

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import API_DESCRIPTION, API_TITLE, API_VERSION, DATA_DIR
from .database import SessionLocal, init_db
from .ml.loader import load_models
from .models.emission import Emission
from .routers import emissions, metrics, predict, states

app = FastAPI(title=API_TITLE, description=API_DESCRIPTION, version=API_VERSION)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(emissions.router)
app.include_router(predict.router)
app.include_router(metrics.router)
app.include_router(states.router)


def seed_database():
    """Load processed emission data into the database."""
    db = SessionLocal()
    try:
        existing = db.query(Emission).count()
        if existing > 0:
            print(f"  Database already has {existing} records, skipping seed")
            return

        csv_path = os.path.join(DATA_DIR, "merged_emissions.csv")
        if not os.path.exists(csv_path):
            print(f"  Warning: {csv_path} not found, skipping seed")
            return

        df = pd.read_csv(csv_path)
        records = []

        for _, row in df.iterrows():
            record = Emission(
                year=int(row["year"]),
                country=row.get("country", "Nigeria"),
                state=None,  # National-level record
                co2_value=float(row.get("co2", 0)),
                co2_per_capita=float(row.get("co2_per_capita", 0)) if pd.notna(row.get("co2_per_capita")) else None,
                gdp=float(row.get("gdp", 0)) if pd.notna(row.get("gdp")) else None,
                population=float(row.get("population", 0)) if pd.notna(row.get("population")) else None,
                primary_energy_consumption=float(row.get("primary_energy_consumption", 0)) if pd.notna(row.get("primary_energy_consumption")) else None,
                coal_co2=float(row.get("coal_co2", 0)) if pd.notna(row.get("coal_co2")) else None,
                oil_co2=float(row.get("oil_co2", 0)) if pd.notna(row.get("oil_co2")) else None,
                gas_co2=float(row.get("gas_co2", 0)) if pd.notna(row.get("gas_co2")) else None,
                flaring_co2=float(row.get("flaring_co2", 0)) if pd.notna(row.get("flaring_co2")) else None,
                cement_co2=float(row.get("cement_co2", 0)) if pd.notna(row.get("cement_co2")) else None,
                energy_co2=float(row.get("energy_co2", 0)) if pd.notna(row.get("energy_co2")) else None,
                oil_transport_co2=float(row.get("oil_transport_co2", 0)) if pd.notna(row.get("oil_transport_co2")) else None,
                industrial_co2=float(row.get("industrial_co2", 0)) if pd.notna(row.get("industrial_co2")) else None,
            )
            records.append(record)

        # Also add sector-level records
        sector_mapping = {
            "Energy": "energy_co2",
            "Oil & Transport": "oil_transport_co2",
            "Flaring": "flaring_co2",
            "Industrial": "industrial_co2",
        }

        for _, row in df.iterrows():
            for sector_name, col in sector_mapping.items():
                val = row.get(col, 0)
                if pd.notna(val) and val > 0:
                    records.append(
                        Emission(
                            year=int(row["year"]),
                            country=row.get("country", "Nigeria"),
                            state=None,
                            sector=sector_name,
                            co2_value=float(val),
                        )
                    )

        db.add_all(records)
        db.commit()
        print(f"  Seeded {len(records)} emission records")
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize database and load models at startup."""
    print("Starting ISMPCE API...")

    # Initialize database
    print("Initializing database...")
    init_db()
    seed_database()

    # Load ML models
    print("Loading ML models...")
    load_models()

    print("ISMPCE API ready.")


@app.get("/", tags=["Root"])
def root():
    """API health check and info."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "endpoints": {
            "emissions": "/emissions",
            "predict": "/predict",
            "model_metrics": "/models/metrics",
            "docs": "/docs",
        },
    }
