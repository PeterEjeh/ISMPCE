"""Application configuration."""

import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'emissions.db')}")

# API
API_TITLE = "ISMPCE API"
API_DESCRIPTION = (
    "An Intelligent System for Monitoring and Predicting Nigeria's CO2 Emissions"
)
API_VERSION = "1.0.0"
