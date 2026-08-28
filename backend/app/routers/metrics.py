"""Model metrics endpoint."""

from fastapi import APIRouter

from ..ml.loader import get_best_model_name, get_metrics
from ..schemas import AllMetricsResponse, ModelMetrics, ModelMetricsResponse

router = APIRouter(prefix="/models", tags=["Model Metrics"])


@router.get("/metrics", response_model=AllMetricsResponse)
def get_model_metrics():
    """
    Return R2, MAE, and RMSE for each trained model.

    Includes both validation and test set metrics,
    and indicates which model was selected as best.
    """
    metrics = get_metrics()
    best_model = get_best_model_name()

    model_names = ["random_forest", "xgboost", "lstm"]
    results = []

    for name in model_names:
        if name in metrics:
            m = metrics[name]
            results.append(
                ModelMetricsResponse(
                    model_name=name,
                    test=ModelMetrics(**m["test"]),
                    validation=ModelMetrics(**m["validation"]),
                    is_best=(name == best_model),
                )
            )

    return AllMetricsResponse(models=results, best_model=best_model)
