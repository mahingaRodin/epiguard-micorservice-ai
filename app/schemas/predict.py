from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class PriorityLevel(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


class SymptomInput(BaseModel):
    symptom_type: str
    severity: int = Field(ge=1, le=5)


class PredictRequest(BaseModel):
    patient_id: str
    age: int = Field(ge=1, le=150)
    gender: str
    district: str
    symptoms: List[SymptomInput]


class PredictResponse(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    priority_level: PriorityLevel
    predicted_disease: str
    model_version: str
