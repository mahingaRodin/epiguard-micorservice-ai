"""
epiguard-ai — Folder Structure Initializer
Run this once from the epiguard-ai/ root:
    python init_folder_structure.py
"""

import os
import sys
from pathlib import Path

# ── ANSI colors for terminal output ──────────────────────────────────────────
GREEN  = "\033[92m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def log_create(path: str, kind: str = "dir"):
    icon = "📁" if kind == "dir" else "📄"
    print(f"  {GREEN}✓{RESET} {icon}  {path}")

def log_skip(path: str):
    print(f"  {YELLOW}~{RESET} ⏭   {path} (already exists)")

def log_section(name: str):
    print(f"\n{BOLD}{BLUE}── {name}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# Directory + file definitions
# ═══════════════════════════════════════════════════════════════════════════════

DIRECTORIES = [
    # ── Core application ──────────────────────────────────────────────────────
    "app",
    "app/routes",
    "app/model",
    "app/schemas",
    "app/utils",
    "app/config",

    # ── gRPC (proto-generated files land here) ────────────────────────────────
    "proto",

    # ── Model training ────────────────────────────────────────────────────────
    "training",
    "training/scripts",
    "training/evaluation",

    # ── Data (gitignored — never committed) ───────────────────────────────────
    "data",
    "data/raw",
    "data/processed",
    "data/synthetic",

    # ── Saved models + artefacts ──────────────────────────────────────────────
    "app/model/artefacts",

    # ── EDA + experiment notebooks ────────────────────────────────────────────
    "notebooks",
    "notebooks/eda",
    "notebooks/experiments",
    "notebooks/evaluation",

    # ── Training run reports ──────────────────────────────────────────────────
    "training_reports",

    # ── Tests ─────────────────────────────────────────────────────────────────
    "tests",
    "tests/unit",
    "tests/integration",

    # ── Monitoring config ─────────────────────────────────────────────────────
    "monitoring",
    "monitoring/grafana",
    "monitoring/grafana/dashboards",
    "monitoring/grafana/datasources",

    # ── Scripts ───────────────────────────────────────────────────────────────
    "scripts",
]


# FILES: (relative_path, content)
FILES = [

    # ── app/__init__.py ───────────────────────────────────────────────────────
    ("app/__init__.py", ""),
    ("app/routes/__init__.py", ""),
    ("app/model/__init__.py", ""),
    ("app/schemas/__init__.py", ""),
    ("app/utils/__init__.py", ""),
    ("app/config/__init__.py", ""),

    # ── app/config/settings.py ────────────────────────────────────────────────
    ("app/config/settings.py", """\
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Server
    http_port: int = 8000
    grpc_port: int = 50051
    log_level: str = "INFO"

    # Model
    model_path: Path = Path("app/model/epiguard-ai.pkl")
    model_type: str = "logistic_regression"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "epiguard"
    postgres_user: str = "epiguard"
    postgres_password: str = "epiguard_dev"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_dev"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
"""),

    # ── app/main.py ───────────────────────────────────────────────────────────
    ("app/main.py", """\
import logging
import threading
from concurrent import futures

import grpc
import uvicorn
from fastapi import FastAPI

from app.config.settings import settings
from app.model.inference import load_model
from app.routes.predict import router as predict_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="epiguard-ai",
    description="EpiGuard ML triage and outbreak intelligence engine",
    version="1.0.0",
)

app.include_router(predict_router, prefix="/ml")


@app.on_event("startup")
async def startup():
    load_model()
    logger.info("epiguard-ai model loaded")
    thread = threading.Thread(target=_start_grpc_server, daemon=True)
    thread.start()
    logger.info("gRPC server thread started on port %d", settings.grpc_port)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "up", "service": "epiguard-ai", "version": "1.0.0"}


def _start_grpc_server():
    # Import here — proto files generated at Docker build time
    try:
        from app.grpc_server import MLTriageServicer, add_MLTriageServiceServicer_to_server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_MLTriageServiceServicer_to_server(MLTriageServicer(), server)
        server.add_insecure_port(f"[::]:{settings.grpc_port}")
        server.start()
        logger.info("gRPC server listening on port %d", settings.grpc_port)
        server.wait_for_termination()
    except ImportError as e:
        logger.warning("gRPC server not started — proto files missing: %s", e)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.http_port, reload=False)
"""),

    # ── app/grpc_server.py ────────────────────────────────────────────────────
    ("app/grpc_server.py", """\
\"\"\"
gRPC servicer — implements MLTriageService from triage.proto.
Proto-generated files (triage_pb2.py, triage_pb2_grpc.py) are created
at Docker build time via grpc_tools.protoc.
\"\"\"
import logging
from app.model.inference import predict

logger = logging.getLogger(__name__)

try:
    import triage_pb2 as pb2
    import triage_pb2_grpc as pb2_grpc

    class MLTriageServicer(pb2_grpc.MLTriageServiceServicer):
        def Predict(self, request, context):
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
            return pb2.PredictResponse(
                risk_score=result["risk_score"],
                priority_level=result["priority_level"],
                predicted_disease=result["predicted_disease"],
                model_version=result["model_version"],
            )

    add_MLTriageServiceServicer_to_server = pb2_grpc.add_MLTriageServiceServicer_to_server

except ImportError:
    logger.warning("Proto-generated files not found — run protoc first.")

    class MLTriageServicer:
        pass

    def add_MLTriageServiceServicer_to_server(servicer, server):
        pass
"""),

    # ── app/routes/predict.py ─────────────────────────────────────────────────
    ("app/routes/predict.py", """\
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
"""),

    # ── app/schemas/predict.py ────────────────────────────────────────────────
    ("app/schemas/predict.py", """\
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
"""),

    # ── app/utils/preprocessing.py ────────────────────────────────────────────
    ("app/utils/preprocessing.py", """\
import numpy as np
from typing import List, Dict

SYMPTOM_TYPES = [
    "fever", "cough", "fatigue", "shortness_of_breath",
    "headache", "diarrhea", "vomiting", "rash",
    "joint_pain", "chest_pain", "sore_throat", "runny_nose",
]

GENDER_MAP = {"MALE": 0, "FEMALE": 1, "OTHER": 2}


def build_feature_vector(age: int, gender: str, symptoms: List[Dict]) -> np.ndarray:
    \"\"\"
    Build a fixed-length (14,) float32 feature vector.
    Layout: [age_norm, gender_enc, symptom_0..11_severity_norm]
    \"\"\"
    features = [
        min(age / 100.0, 1.0),
        GENDER_MAP.get(gender.upper(), 2) / 2.0,
    ]

    symptom_map: Dict[str, int] = {}
    for s in symptoms:
        stype = s.get("symptom_type", s.get("type", "")).lower().replace(" ", "_")
        symptom_map[stype] = max(symptom_map.get(stype, 0), s.get("severity", 0))

    for stype in SYMPTOM_TYPES:
        features.append(symptom_map.get(stype, 0) / 5.0)

    return np.array(features, dtype=np.float32).reshape(1, -1)
"""),

    # ── app/model/inference.py ────────────────────────────────────────────────
    ("app/model/inference.py", """\
import logging
import joblib
import numpy as np
from pathlib import Path

from app.utils.preprocessing import build_feature_vector
from app.config.settings import settings

logger = logging.getLogger(__name__)

MODEL_VERSION = "1.0.0-lr-mvp"
_model = None


def load_model():
    global _model
    model_path = Path(settings.model_path)
    if model_path.exists():
        _model = joblib.load(model_path)
        logger.info("Model loaded from %s", model_path)
    else:
        logger.warning("No model found at %s — training bootstrap model", model_path)
        _model = _train_bootstrap()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(_model, model_path)
        logger.info("Bootstrap model saved to %s", model_path)


def _train_bootstrap():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    np.random.seed(42)
    n = 2000
    ages    = np.random.randint(1, 90, n) / 100.0
    genders = np.random.randint(0, 3, n) / 2.0
    symps   = np.random.dirichlet(np.ones(12), size=n)
    X = np.column_stack([ages, genders, symps])
    risk = (symps[:, 0] > 0.5).astype(int) + (symps[:, 1] > 0.5).astype(int) + (symps.sum(axis=1) > 3).astype(int)
    y = np.where(risk >= 2, 2, np.where(risk == 1, 1, 0))

    model = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500, random_state=42))])
    model.fit(X, y)
    logger.info("Bootstrap model accuracy: %.2f", model.score(X, y))
    return model


def predict(patient_id: str, age: int, gender: str, district: str, symptoms: list) -> dict:
    global _model
    if _model is None:
        load_model()

    features  = build_feature_vector(age, gender, symptoms)
    proba     = _model.predict_proba(features)[0]
    label_idx = int(np.argmax(proba))
    risk_score = float(proba[2])

    priority_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}

    return {
        "risk_score":        round(risk_score, 4),
        "priority_level":    priority_map[label_idx],
        "predicted_disease": _cluster_disease(symptoms),
        "model_version":     MODEL_VERSION,
    }


def _cluster_disease(symptoms: list) -> str:
    types = {s.get("symptom_type", s.get("type", "")).lower() for s in symptoms}
    if {"fever", "cough", "shortness_of_breath"} & types:
        return "Respiratory Infection"
    if {"fever", "rash", "joint_pain"} & types:
        return "Suspected Arboviral Disease"
    if {"diarrhea", "vomiting"} & types:
        return "Gastrointestinal Illness"
    if {"fever", "headache", "fatigue"} & types:
        return "Febrile Illness"
    if len(types) >= 4:
        return "Multi-symptom Syndrome"
    return "Undetermined"
"""),

    # ── training/__init__.py ──────────────────────────────────────────────────
    ("training/__init__.py", ""),
    ("training/scripts/__init__.py", ""),
    ("training/evaluation/__init__.py", ""),

    # ── training/train.py ─────────────────────────────────────────────────────
    ("training/train.py", """\
\"\"\"
epiguard-ai — Main training entry point.
Run via:  python -m training.train
Or:       docker-compose --profile train run --rm model-trainer
\"\"\"
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("═══ epiguard-ai training started ═══")

    # Import here so settings are loaded first
    from training.scripts.build_dataset import build_dataset
    from training.scripts.train_model   import train_and_save
    from training.evaluation.evaluate   import evaluate_and_report

    logger.info("Step 1/3 — Building dataset")
    X_train, X_test, y_train, y_test = build_dataset()

    logger.info("Step 2/3 — Training model")
    model = train_and_save(X_train, y_train)

    logger.info("Step 3/3 — Evaluating model")
    evaluate_and_report(model, X_test, y_test)

    logger.info("═══ Training complete — epiguard-ai.pkl saved ═══")


if __name__ == "__main__":
    main()
"""),

    # ── training/scripts/build_dataset.py ────────────────────────────────────
    ("training/scripts/build_dataset.py", """\
\"\"\"
Builds a training dataset from:
  1. PostgreSQL triage_results + symptoms tables (real data — when available)
  2. Synthetic fallback if DB is empty or unreachable
\"\"\"
import logging
import numpy as np
from sklearn.model_selection import train_test_split
from app.config.settings import settings
from app.utils.preprocessing import build_feature_vector, SYMPTOM_TYPES

logger = logging.getLogger(__name__)


def build_dataset(test_size: float = 0.2, random_state: int = 42):
    \"\"\"Returns X_train, X_test, y_train, y_test as numpy arrays.\"\"\"
    try:
        X, y = _load_from_postgres()
        if len(X) < 100:
            raise ValueError(f"Only {len(X)} samples in DB — using synthetic data")
        logger.info("Loaded %d real samples from PostgreSQL", len(X))
    except Exception as e:
        logger.warning("DB load failed (%s) — falling back to synthetic dataset", e)
        X, y = _generate_synthetic(n=3000)

    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def _load_from_postgres():
    \"\"\"Load and featurise real patient + triage data from the EpiGuard DB.\"\"\"
    import psycopg2
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )
    cur = conn.cursor()
    cur.execute(\"\"\"
        SELECT p.age, p.gender,
               array_agg(s.symptom_type ORDER BY s.symptom_type) AS types,
               array_agg(s.severity     ORDER BY s.symptom_type) AS severities,
               tr.priority_level
        FROM patients p
        JOIN symptoms s         ON s.patient_id  = p.id
        JOIN triage_results tr  ON tr.patient_id = p.id
        GROUP BY p.id, p.age, p.gender, tr.priority_level
    \"\"\")
    rows = cur.fetchall()
    conn.close()

    label_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    X, y = [], []
    for age, gender, types, severities, priority in rows:
        symptoms = [{"symptom_type": t, "severity": s} for t, s in zip(types, severities)]
        X.append(build_feature_vector(age, gender, symptoms).flatten())
        y.append(label_map.get(priority, 0))

    return np.array(X), np.array(y)


def _generate_synthetic(n: int = 3000):
    \"\"\"Generate a synthetic training set when no real data is available.\"\"\"
    np.random.seed(42)
    ages    = np.random.randint(1, 90, n) / 100.0
    genders = np.random.randint(0, 3, n) / 2.0
    symps   = np.random.dirichlet(np.ones(len(SYMPTOM_TYPES)), size=n)
    X = np.column_stack([ages, genders, symps])
    risk = (
        (symps[:, 0] > 0.5).astype(int) +
        (symps[:, 1] > 0.5).astype(int) +
        (symps.sum(axis=1) > 3).astype(int)
    )
    y = np.where(risk >= 2, 2, np.where(risk == 1, 1, 0))
    logger.info("Generated %d synthetic samples | class dist: %s", n, np.bincount(y).tolist())
    return X, y
"""),

    # ── training/scripts/train_model.py ───────────────────────────────────────
    ("training/scripts/train_model.py", """\
\"\"\"
Trains the epiguard-ai model and saves it as epiguard-ai.pkl.
Supports MODEL_TYPE env: logistic_regression | random_forest | xgboost
\"\"\"
import logging
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from app.config.settings import settings

logger = logging.getLogger(__name__)


def train_and_save(X_train, y_train):
    model_type = settings.model_type
    logger.info("Training model type: %s", model_type)

    clf = _build_classifier(model_type)
    model = Pipeline([("scaler", StandardScaler()), ("clf", clf)])
    model.fit(X_train, y_train)

    model_path = Path(settings.model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info("Model saved → %s", model_path)

    return model


def _build_classifier(model_type: str):
    if model_type == "logistic_regression":
        return LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
    if model_type == "random_forest":
        return RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced", n_jobs=-1)
    if model_type == "xgboost":
        try:
            from xgboost import XGBClassifier
            return XGBClassifier(n_estimators=200, random_state=42, eval_metric="mlogloss", use_label_encoder=False)
        except ImportError:
            logger.warning("xgboost not installed — falling back to random_forest")
            return RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    raise ValueError(f"Unknown model_type: {model_type}")
"""),

    # ── training/evaluation/evaluate.py ──────────────────────────────────────
    ("training/evaluation/evaluate.py", """\
\"\"\"
Evaluates trained model and writes a metrics report to training_reports/.
\"\"\"
import json
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    roc_auc_score,
)

logger = logging.getLogger(__name__)
REPORT_DIR = Path("training_reports")


def evaluate_and_report(model, X_test, y_test):
    REPORT_DIR.mkdir(exist_ok=True)

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    accuracy  = accuracy_score(y_test, y_pred)
    roc_auc   = roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
    cm        = confusion_matrix(y_test, y_pred).tolist()
    clf_report = classification_report(
        y_test, y_pred,
        target_names=["LOW", "MEDIUM", "HIGH"],
        output_dict=True,
    )

    logger.info("Accuracy : %.4f", accuracy)
    logger.info("ROC AUC  : %.4f", roc_auc)
    logger.info("\\nClassification Report:\\n%s",
                classification_report(y_test, y_pred, target_names=["LOW", "MEDIUM", "HIGH"]))

    report = {
        "timestamp":             datetime.utcnow().isoformat(),
        "accuracy":              round(accuracy, 4),
        "roc_auc_weighted":      round(roc_auc, 4),
        "confusion_matrix":      cm,
        "classification_report": clf_report,
    }

    report_path = REPORT_DIR / f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2))
    logger.info("Report saved → %s", report_path)

    return report
"""),

    # ── tests/__init__.py ─────────────────────────────────────────────────────
    ("tests/__init__.py", ""),
    ("tests/unit/__init__.py", ""),
    ("tests/integration/__init__.py", ""),

    # ── tests/unit/test_preprocessing.py ─────────────────────────────────────
    ("tests/unit/test_preprocessing.py", """\
import numpy as np
from app.utils.preprocessing import build_feature_vector, SYMPTOM_TYPES


def test_feature_vector_shape():
    symptoms = [{"symptom_type": "fever", "severity": 3}]
    vec = build_feature_vector(30, "MALE", symptoms)
    assert vec.shape == (1, 14), f"Expected (1, 14), got {vec.shape}"


def test_feature_vector_normalised():
    symptoms = [{"symptom_type": "fever", "severity": 5}]
    vec = build_feature_vector(100, "FEMALE", symptoms)
    assert (vec >= 0).all() and (vec <= 1).all(), "All values must be in [0, 1]"


def test_unknown_symptom_is_zero():
    symptoms = [{"symptom_type": "unknown_symptom_xyz", "severity": 4}]
    vec = build_feature_vector(25, "MALE", symptoms)
    # All symptom slots should be 0 since none match known types
    assert vec[0, 2:].sum() == 0.0


def test_empty_symptoms():
    vec = build_feature_vector(40, "OTHER", [])
    assert vec.shape == (1, 14)
"""),

    # ── tests/unit/test_inference.py ──────────────────────────────────────────
    ("tests/unit/test_inference.py", """\
from app.model.inference import predict, load_model


def test_predict_returns_valid_structure():
    load_model()
    result = predict(
        patient_id="test-001",
        age=35,
        gender="MALE",
        district="Gasabo",
        symptoms=[
            {"symptom_type": "fever",  "severity": 4},
            {"symptom_type": "cough",  "severity": 3},
        ],
    )
    assert "risk_score"        in result
    assert "priority_level"    in result
    assert "predicted_disease" in result
    assert "model_version"     in result
    assert 0.0 <= result["risk_score"] <= 1.0
    assert result["priority_level"] in ("LOW", "MEDIUM", "HIGH")


def test_high_severity_not_low():
    load_model()
    result = predict(
        patient_id="test-002",
        age=60,
        gender="FEMALE",
        district="Kicukiro",
        symptoms=[
            {"symptom_type": "fever",                "severity": 5},
            {"symptom_type": "cough",                "severity": 5},
            {"symptom_type": "shortness_of_breath",  "severity": 5},
            {"symptom_type": "fatigue",              "severity": 5},
        ],
    )
    assert result["priority_level"] != "LOW", "Severe multi-symptom case should not be LOW"
"""),

    # ── tests/integration/test_api.py ─────────────────────────────────────────
    ("tests/integration/test_api.py", """\
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "up"


def test_predict_endpoint():
    payload = {
        "patient_id": "test-uuid-001",
        "age": 28,
        "gender": "FEMALE",
        "district": "Gasabo",
        "symptoms": [
            {"symptom_type": "fever", "severity": 3},
            {"symptom_type": "cough", "severity": 2},
        ],
    }
    response = client.post("/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score"     in data
    assert "priority_level" in data
    assert data["priority_level"] in ("LOW", "MEDIUM", "HIGH")


def test_predict_invalid_severity():
    payload = {
        "patient_id": "test-uuid-002",
        "age": 28,
        "gender": "MALE",
        "district": "Kigali",
        "symptoms": [{"symptom_type": "fever", "severity": 10}],  # invalid — max is 5
    }
    response = client.post("/ml/predict", json=payload)
    assert response.status_code == 422
"""),

    # ── monitoring/prometheus.yml ─────────────────────────────────────────────
    ("monitoring/prometheus.yml", """\
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: epiguard-ai
    static_configs:
      - targets: ['epiguard-ai:8000']
    metrics_path: /metrics
"""),

    # ── scripts/init.sql placeholder ─────────────────────────────────────────
    ("scripts/init.sql", """\
-- EpiGuard PostgreSQL schema
-- Full schema lives in the main epiguard repo scripts/init.sql
-- This file is used for the epiguard-ai standalone dev environment

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE gender_type    AS ENUM ('MALE', 'FEMALE', 'OTHER');
CREATE TYPE priority_level AS ENUM ('LOW', 'MEDIUM', 'HIGH');

CREATE TABLE IF NOT EXISTS patients (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    age          INT          NOT NULL,
    gender       gender_type  NOT NULL,
    district     VARCHAR(50)  NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS symptoms (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id   UUID         NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    symptom_type VARCHAR(50)  NOT NULL,
    severity     INT          NOT NULL CHECK (severity >= 1 AND severity <= 5),
    recorded_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS triage_results (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id       UUID           NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_score       DECIMAL(5,4)   NOT NULL,
    priority_level   priority_level NOT NULL,
    predicted_disease VARCHAR(100),
    created_at       TIMESTAMP      NOT NULL DEFAULT NOW()
);
"""),

    # ── scripts/seed_training_data.sql placeholder ────────────────────────────
    ("scripts/seed_training_data.sql", """\
-- Seed synthetic training data for local dev
-- Replace with real anonymised clinic data when available
-- No names, no PII — age + gender + district + symptoms only
"""),

    # ── .env.example ─────────────────────────────────────────────────────────
    (".env.example", """\
# ── Server ──────────────────────────────────────────────────
HTTP_PORT=8000
GRPC_PORT=50051
LOG_LEVEL=INFO

# ── Model ───────────────────────────────────────────────────
MODEL_TYPE=logistic_regression

# ── Database ────────────────────────────────────────────────
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=epiguard
POSTGRES_USER=epiguard
POSTGRES_PASSWORD=your_strong_password_here

# ── Redis ───────────────────────────────────────────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_strong_redis_password_here

# ── Jupyter ─────────────────────────────────────────────────
JUPYTER_TOKEN=your_jupyter_token_here

# ── Monitoring ──────────────────────────────────────────────
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_grafana_password_here
"""),

    # ── data/.gitkeep (keeps folder in git despite being gitignored) ──────────
    ("data/raw/.gitkeep", ""),
    ("data/processed/.gitkeep", ""),
    ("data/synthetic/.gitkeep", ""),
    ("notebooks/eda/.gitkeep", ""),
    ("notebooks/experiments/.gitkeep", ""),
    ("notebooks/evaluation/.gitkeep", ""),
    ("training_reports/.gitkeep", ""),
    ("app/model/artefacts/.gitkeep", ""),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════════

def init(base: Path):
    print(f"\n{BOLD}EpiGuard — epiguard-ai folder initialiser{RESET}")
    print(f"Target: {BLUE}{base.resolve()}{RESET}\n")

    # ── Create directories ────────────────────────────────────────────────────
    log_section("Creating directories")
    for d in DIRECTORIES:
        target = base / d
        if target.exists():
            log_skip(d)
        else:
            target.mkdir(parents=True, exist_ok=True)
            log_create(d, "dir")

    # ── Create files ──────────────────────────────────────────────────────────
    log_section("Creating files")
    for rel_path, content in FILES:
        target = base / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            log_skip(rel_path)
        else:
            target.write_text(content, encoding="utf-8")
            log_create(rel_path, "file")

    # ── Summary ───────────────────────────────────────────────────────────────
    created_dirs  = sum(1 for d in DIRECTORIES if (base / d).exists())
    created_files = sum(1 for f, _ in FILES if (base / f).exists())

    print(f"\n{BOLD}{GREEN}✓ Done!{RESET}")
    print(f"  {GREEN}{created_dirs}{RESET} directories  |  {GREEN}{created_files}{RESET} files")
    print(f"\n{BOLD}Next steps:{RESET}")
    print(f"  1. cp .env.example .env  {YELLOW}# then fill in your values{RESET}")
    print(f"  2. docker-compose --profile dev up")
    print(f"  3. open http://localhost:8000/docs")
    print(f"  4. docker-compose --profile train run --rm model-trainer\n")


if __name__ == "__main__":
    # Allow an optional target directory as argument, default to current dir
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    init(target)