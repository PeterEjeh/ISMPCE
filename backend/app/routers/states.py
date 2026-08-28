"""States contribution endpoint – estimated CO2 share per Nigeria state."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.emission import Emission
from ..schemas import StateContribution, StatesContributionResponse

router = APIRouter(prefix="/states", tags=["States"])

# ---------------------------------------------------------------------------
# State definitions with population share and industrial activity multiplier.
# The industrial multiplier is > 1 for major oil-producing and industrial states
# (e.g. Rivers, Delta, Lagos, Kano) and 1.0 for the rest.
#
# Estimated CO2 share = 0.60 × popShare + 0.40 × (popShare × industrialMultiplier)
# then normalised so all shares sum to 100%.
#
# Data sources for population shares: NBS 2022 projections.
# Industrial multipliers: expert estimation based on NNPC flaring data,
# industrial census, and World Bank Nigeria reports.
# ---------------------------------------------------------------------------

_STATES = [
    {"name": "Abia",         "zone": "South East",    "popShare": 0.019, "industrialMultiplier": 1.2},
    {"name": "Adamawa",      "zone": "North East",    "popShare": 0.018, "industrialMultiplier": 1.0},
    {"name": "Akwa Ibom",    "zone": "South South",   "popShare": 0.027, "industrialMultiplier": 2.8},
    {"name": "Anambra",      "zone": "South East",    "popShare": 0.025, "industrialMultiplier": 1.3},
    {"name": "Bauchi",       "zone": "North East",    "popShare": 0.030, "industrialMultiplier": 1.0},
    {"name": "Bayelsa",      "zone": "South South",   "popShare": 0.010, "industrialMultiplier": 3.0},
    {"name": "Benue",        "zone": "North Central", "popShare": 0.027, "industrialMultiplier": 1.0},
    {"name": "Borno",        "zone": "North East",    "popShare": 0.026, "industrialMultiplier": 1.0},
    {"name": "Cross River",  "zone": "South South",   "popShare": 0.018, "industrialMultiplier": 1.4},
    {"name": "Delta",        "zone": "South South",   "popShare": 0.027, "industrialMultiplier": 3.2},
    {"name": "Ebonyi",       "zone": "South East",    "popShare": 0.014, "industrialMultiplier": 1.0},
    {"name": "Edo",          "zone": "South South",   "popShare": 0.020, "industrialMultiplier": 1.6},
    {"name": "Ekiti",        "zone": "South West",    "popShare": 0.016, "industrialMultiplier": 1.0},
    {"name": "Enugu",        "zone": "South East",    "popShare": 0.020, "industrialMultiplier": 1.2},
    {"name": "FCT Abuja",    "zone": "North Central", "popShare": 0.019, "industrialMultiplier": 1.1},
    {"name": "Gombe",        "zone": "North East",    "popShare": 0.015, "industrialMultiplier": 1.0},
    {"name": "Imo",          "zone": "South East",    "popShare": 0.025, "industrialMultiplier": 1.5},
    {"name": "Jigawa",       "zone": "North West",    "popShare": 0.028, "industrialMultiplier": 1.0},
    {"name": "Kaduna",       "zone": "North West",    "popShare": 0.039, "industrialMultiplier": 1.4},
    {"name": "Kano",         "zone": "North West",    "popShare": 0.057, "industrialMultiplier": 1.8},
    {"name": "Katsina",      "zone": "North West",    "popShare": 0.035, "industrialMultiplier": 1.0},
    {"name": "Kebbi",        "zone": "North West",    "popShare": 0.020, "industrialMultiplier": 1.0},
    {"name": "Kogi",         "zone": "North Central", "popShare": 0.020, "industrialMultiplier": 1.3},
    {"name": "Kwara",        "zone": "North Central", "popShare": 0.015, "industrialMultiplier": 1.0},
    {"name": "Lagos",        "zone": "South West",    "popShare": 0.060, "industrialMultiplier": 2.5},
    {"name": "Nasarawa",     "zone": "North Central", "popShare": 0.012, "industrialMultiplier": 1.0},
    {"name": "Niger",        "zone": "North Central", "popShare": 0.026, "industrialMultiplier": 1.1},
    {"name": "Ogun",         "zone": "South West",    "popShare": 0.023, "industrialMultiplier": 1.5},
    {"name": "Ondo",         "zone": "South West",    "popShare": 0.022, "industrialMultiplier": 1.6},
    {"name": "Osun",         "zone": "South West",    "popShare": 0.022, "industrialMultiplier": 1.0},
    {"name": "Oyo",          "zone": "South West",    "popShare": 0.035, "industrialMultiplier": 1.4},
    {"name": "Plateau",      "zone": "North Central", "popShare": 0.019, "industrialMultiplier": 1.0},
    {"name": "Rivers",       "zone": "South South",   "popShare": 0.035, "industrialMultiplier": 3.5},
    {"name": "Sokoto",       "zone": "North West",    "popShare": 0.023, "industrialMultiplier": 1.0},
    {"name": "Taraba",       "zone": "North East",    "popShare": 0.015, "industrialMultiplier": 1.0},
    {"name": "Yobe",         "zone": "North East",    "popShare": 0.015, "industrialMultiplier": 1.0},
    {"name": "Zamfara",      "zone": "North West",    "popShare": 0.021, "industrialMultiplier": 1.0},
]


def _compute_contributions(latest_national_co2: float | None) -> list[dict]:
    """Compute each state's estimated share of national CO2 emissions."""
    # Raw weight = 60% population + 40% (population × industrial multiplier)
    raw = []
    for s in _STATES:
        w = 0.60 * s["popShare"] + 0.40 * (s["popShare"] * s["industrialMultiplier"])
        raw.append((s, w))

    total_weight = sum(w for _, w in raw)

    result = []
    for s, w in raw:
        share_pct = round((w / total_weight) * 100, 2)
        estimated_co2 = round(latest_national_co2 * w / total_weight, 2) if latest_national_co2 else None
        result.append({
            "name": s["name"],
            "zone": s["zone"],
            "pop_share": s["popShare"],
            "industrial_multiplier": s["industrialMultiplier"],
            "estimated_share": share_pct,
            "estimated_co2": estimated_co2,
        })

    # Sort by estimated share descending
    result.sort(key=lambda x: x["estimated_share"], reverse=True)
    return result


@router.get("/contribution", response_model=StatesContributionResponse)
def get_states_contribution(db: Session = Depends(get_db)):
    """
    Return each Nigerian state's estimated share of national CO2 emissions.

    Estimation method: weighted blend of 60% population share and
    40% population-weighted industrial activity multiplier, normalised
    to sum to 100%.

    NOTE: Sub-national CO2 measurement data does not exist publicly for
    Nigeria. These figures are statistical estimates, not measured values.
    """
    # Fetch the most recent national total from the database
    latest_co2 = (
        db.query(func.max(Emission.co2_value))
        .filter(Emission.sector.is_(None))
        .scalar()
    )

    contributions = _compute_contributions(latest_co2)

    return StatesContributionResponse(
        total_states=len(contributions),
        note=(
            "Estimated state-level contributions based on population share (60%) "
            "and industrial activity multipliers (40%). "
            "No measured sub-national CO2 dataset exists for Nigeria; "
            "these are statistical estimates only."
        ),
        states=[StateContribution(**c) for c in contributions],
    )
