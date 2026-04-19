from fastapi import APIRouter, HTTPException
from app.schemas.predict import PredictRequest, PredictResponse
from app.model.inference import predict

router = APIRouter(tags=["Prediction"])


@router.post("/predict", response_model=PredictResponse)
def predict_endpoint(request: PredictRequest):
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
        return PredictResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
