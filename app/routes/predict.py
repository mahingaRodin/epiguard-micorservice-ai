import time

from fastapi import APIRouter, HTTPException
from app.schemas.predict import PredictRequest, PredictResponse
from app.model.inference import predict
from app.routes.metrics import PREDICTION_COUNT, PREDICTION_LATENCY

router = APIRouter(tags=["Prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Run ML triage prediction",
    description=(
        "Accepts patient demographics and symptom severities (1–5), "
        "returns risk score, priority level, and predicted disease cluster."
    ),
)
def predict_endpoint(request: PredictRequest):
    start = time.perf_counter()
    try:
        symptoms = [
            {"symptom_type": s.symptom_type, "severity": s.severity}
            for s in request.symptoms
        ]
        result = predict(
            patient_id=request.patient_id,
            age=request.age,
            gender=request.gender,
            district=request.district,
            symptoms=symptoms,
        )
        PREDICTION_COUNT.labels(priority_level=result["priority_level"]).inc()
        return PredictResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        PREDICTION_LATENCY.observe(time.perf_counter() - start)
