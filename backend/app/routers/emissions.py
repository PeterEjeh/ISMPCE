"""Emissions data endpoint."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.emission import Emission
from ..schemas import EmissionListResponse, EmissionResponse

router = APIRouter(prefix="/emissions", tags=["Emissions"])


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
    """
    query = db.query(Emission)

    filters = []
    if country:
        filters.append(Emission.country == country)
    if state:
        filters.append(Emission.state == state)
    if sector:
        filters.append(Emission.sector == sector)
    if year_start is not None:
        filters.append(Emission.year >= year_start)
    if year_end is not None:
        filters.append(Emission.year <= year_end)

    if filters:
        query = query.filter(and_(*filters))

    query = query.order_by(Emission.year)
    results = query.all()

    return EmissionListResponse(
        total=len(results),
        data=[EmissionResponse.model_validate(r) for r in results],
    )
