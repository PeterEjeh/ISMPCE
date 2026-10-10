"""
Unit tests for FastAPI endpoints:
- GET /
- GET /emissions
- POST /predict
- GET /models/metrics
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app, seed_database, init_db
from app.ml.loader import load_models

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Ensure database and models are loaded for testing."""
    init_db()
    seed_database()
    load_models()


def test_root_endpoint():
    """Test health check / info root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "ISMPCE API" in data["name"]
    assert "endpoints" in data
    assert "/emissions" in data["endpoints"].values()


def test_get_emissions_all():
    """Test retrieving all emissions."""
    response = client.get("/emissions")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] > 0
    assert len(data["data"]) > 0
    assert "co2_value" in data["data"][0]


def test_get_emissions_with_filter():
    """Test filtering emissions by year range."""
    response = client.get("/emissions?year_start=2015&year_end=2020")
    assert response.status_code == 200
    data = response.json()
    for item in data["data"]:
        assert 2015 <= item["year"] <= 2020


def test_predict_endpoint_default():
    """Test default prediction (best model)."""
    payload = {
        "region": "Nigeria",
        "forecast_horizon": 5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["region"] == "Nigeria"
    assert "model_used" in data
    assert len(data["forecast"]) == 5
    # Verify widening confidence interval
    intervals = [
        f["confidence_upper"] - f["confidence_lower"]
        for f in data["forecast"]
    ]
    # Check that confidence interval grows wider over time
    for i in range(1, len(intervals)):
        assert intervals[i] >= intervals[i - 1]


def test_predict_endpoint_specific_models():
    """Test predictions using specific national models: random_forest, xgboost, lstm."""
    for model_name in ["random_forest", "xgboost", "lstm"]:
        payload = {
            "region": "Nigeria",
            "forecast_horizon": 3,
            "model_name": model_name
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["model_used"] == model_name
        assert len(data["forecast"]) == 3


def test_predict_endpoint_state_level():
    """Test state-level prediction (e.g. Bauchi)."""
    payload = {
        "region": "Bauchi",
        "forecast_horizon": 3,
        "model_name": "xgboost"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Bauchi" in data["model_used"]
    assert len(data["forecast"]) == 3


def test_models_metrics():
    """Test model metrics endpoint."""
    response = client.get("/models/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 3
    model_names = [m["model_name"] for m in data["models"]]
    assert "random_forest" in model_names
    assert "xgboost" in model_names
    assert "lstm" in model_names
    assert "best_model" in data
