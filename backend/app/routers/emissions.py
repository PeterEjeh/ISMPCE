"""Emissions data endpoint."""

import os
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..config import DATA_DIR
from ..database import get_db
from ..models.emission import Emission
from ..schemas import EmissionListResponse, EmissionResponse

router = APIRouter(prefix="/emissions", tags=["Emissions"])

_state_df_cache = None


def _get_state_dataframe():
    global _state_df_cache
    if _state_df_cache is not None:
        return _state_df_cache

    candidates = [
        os.path.join(DATA_DIR, "state_emissions_features.csv"),
        os.path.join(DATA_DIR, "processed", "state_emissions_features.csv"),
    ]
    for p in candidates:
        if os.path.exists(p):
            _state_df_cache = pd.read_csv(p)
            return _state_df_cache
    return None


@router.get("", response_model=EmissionListResponse)
def get_emissions(
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    year_start: Optional[int] = Query(None, description="Start year (inclusive)"),
    year_end: Optional[int] = Query(None, description="End year (inclusive)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve emission records with optional filters.

    Filterable by country, state, sector, and year range.
    Supports state-level historical emissions (1990-2024) across Nigeria's 36 states and FCT.
    """
    # Check if a specific state is requested (e.g., 'Lagos', 'Rivers')
    if isinstance(state, str) and state.strip():
        clean_state = state.replace(" (National)", "").replace(" (Case Study)", "").strip()
        if clean_state.lower() not in ("nigeria", "national", "all", ""):
            df_state = _get_state_dataframe()
            if df_state is not None:
                matches = df_state[df_state["state"].str.lower() == clean_state.lower()]
                if not matches.empty:
                    matches = matches.sort_values("year")
                    if year_start is not None:
                        matches = matches[matches["year"] >= year_start]
                    if year_end is not None:
                        matches = matches[matches["year"] <= year_end]

                    results = []
                    for idx, row in matches.iterrows():
                        results.append(
                            EmissionResponse(
                                id=int(idx) + 10000,
                                year=int(row["year"]),
                                country="Nigeria",
                                state=str(row["state"]),
                                sector=None,
                                co2_value=round(float(row["co2"]), 3),
                                oil_co2=round(float(row["oil_gas_co2"]), 3) if pd.notna(row.get("oil_gas_co2")) else None,
                                oil_transport_co2=round(float(row["transport_co2"]), 3) if pd.notna(row.get("transport_co2")) else None,
                                industrial_co2=round(float(row["industry_co2"]), 3) if pd.notna(row.get("industry_co2")) else None,
                            )
                        )
                    return EmissionListResponse(total=len(results), data=results)

    # National database query
    query = db.query(Emission)
    filters = []

    if isinstance(country, str) and country.strip():
        filters.append(Emission.country == country.strip())
    if isinstance(state, str) and state.strip():
        clean_state = state.replace(" (National)", "").replace(" (Case Study)", "").strip()
        if clean_state.lower() not in ("nigeria", "national", "all", ""):
            filters.append(Emission.state == clean_state)
    if isinstance(sector, str) and sector.strip():
        filters.append(Emission.sector == sector.strip())
    if isinstance(year_start, int):
        filters.append(Emission.year >= year_start)
    if isinstance(year_end, int):
        filters.append(Emission.year <= year_end)

    if filters:
        query = query.filter(and_(*filters))

    query = query.order_by(Emission.year)
    results = query.all()

    return EmissionListResponse(
        total=len(results),
        data=[EmissionResponse.model_validate(r) for r in results],
    )

