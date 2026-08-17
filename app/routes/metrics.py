from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

router = APIRouter(tags=["Monitoring"])

PREDICTION_COUNT = Counter(
    "epiguard_predictions_total",
    "Total number of ML triage predictions",
    ["priority_level"],
)
PREDICTION_LATENCY = Histogram(
    "epiguard_prediction_latency_seconds",
    "Prediction request latency in seconds",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)


@router.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
