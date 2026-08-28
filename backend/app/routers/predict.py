"""Prediction endpoint."""

from fastapi import APIRouter, HTTPException

from ..ml.predictor import predict_emissions
from ..schemas import PredictRequest, PredictResponse, PredictionPoint

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.post("", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Generate CO2 emission forecasts with widening confidence intervals.

    The region field is accepted for display purposes only. The underlying
    model always runs on the national (Nigeria) dataset since no state-level
    CO2 dataset exists for Nigeria.

    Optionally supply scenario override parameters to simulate policy changes:
    - fossil_fuel_share_change: percentage-point change in fossil fuel share
    - gdp_growth_rate: annual GDP growth rate override (%)
    - population_growth_rate: annual population growth rate override (%)
    When provided, the response includes both baseline and scenario forecasts.
    """
    try:
        model_used, forecasts, has_scenario = predict_emissions(
            region=request.region,
            forecast_horizon=request.forecast_horizon,
            model_name=request.model_name,
            fossil_fuel_share_change=request.fossil_fuel_share_change,
            gdp_growth_rate=request.gdp_growth_rate,
            population_growth_rate=request.population_growth_rate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    return PredictResponse(
        region=request.region,
        model_used=model_used,
        forecast=[PredictionPoint(**f) for f in forecasts],
        has_scenario=has_scenario,
    )
