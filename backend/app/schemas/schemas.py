"""Pydantic schemas for API request/response validation."""

from typing import Optional

from pydantic import BaseModel, Field


# ── Emission schemas ──────────────────────────────────────────

class EmissionBase(BaseModel):
    year: int
    country: str = "Nigeria"
    state: Optional[str] = None
    sector: Optional[str] = None
    co2_value: float
    co2_per_capita: Optional[float] = None
    gdp: Optional[float] = None
    population: Optional[float] = None
    primary_energy_consumption: Optional[float] = None
    coal_co2: Optional[float] = None
    oil_co2: Optional[float] = None
    gas_co2: Optional[float] = None
    flaring_co2: Optional[float] = None
    cement_co2: Optional[float] = None
    energy_co2: Optional[float] = None
    oil_transport_co2: Optional[float] = None
    industrial_co2: Optional[float] = None


class EmissionResponse(EmissionBase):
    id: int

    model_config = {"from_attributes": True}


class EmissionListResponse(BaseModel):
    total: int
    data: list[EmissionResponse]


# ── Prediction schemas ────────────────────────────────────────

class PredictRequest(BaseModel):
    region: str = Field(default="Nigeria", description="Region label for display only; model always runs nationally")
    forecast_horizon: int = Field(
        default=5, ge=1, le=10, description="Number of years to forecast"
    )
    model_name: Optional[str] = Field(
        default=None, description="Model to use: random_forest, xgboost, or lstm. Defaults to best."
    )
    # Scenario override parameters (optional – defaults to no change)
    fossil_fuel_share_change: Optional[float] = Field(
        default=None, description="Percentage point change in fossil fuel share (e.g. -10 for 10% reduction)"
    )
    gdp_growth_rate: Optional[float] = Field(
        default=None, description="Annual GDP growth rate override in percent (e.g. 5.0)"
    )
    population_growth_rate: Optional[float] = Field(
        default=None, description="Annual population growth rate override in percent (e.g. 2.0)"
    )


class PredictionPoint(BaseModel):
    year: int
    predicted_co2: float
    confidence_lower: float
    confidence_upper: float
    scenario_co2: Optional[float] = None
    scenario_lower: Optional[float] = None
    scenario_upper: Optional[float] = None


class PredictResponse(BaseModel):
    region: str
    model_used: str
    forecast: list[PredictionPoint]
    has_scenario: bool = False


# ── State contribution schemas ───────────────────────────────

class StateContribution(BaseModel):
    name: str
    zone: str
    pop_share: float
    industrial_multiplier: float
    estimated_share: float   # % of national emissions
    estimated_co2: Optional[float] = None  # Mt, filled by API if latest known


class StatesContributionResponse(BaseModel):
    total_states: int
    note: str
    states: list[StateContribution]


# ── Model metrics schemas ────────────────────────────────────

class ModelMetrics(BaseModel):
    r2: float
    mae: float
    rmse: float


class ModelMetricsResponse(BaseModel):
    model_name: str
    test: ModelMetrics
    validation: ModelMetrics
    is_best: bool = False


class AllMetricsResponse(BaseModel):
    models: list[ModelMetricsResponse]
    best_model: str
