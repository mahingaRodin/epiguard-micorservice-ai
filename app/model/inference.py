import logging
import joblib
import numpy as np
from pathlib import Path

from app.utils.preprocessing import build_feature_vector
from app.config.settings import settings

logger = logging.getLogger(__name__)

MODEL_VERSION = "1.0.0-lr-mvp"
_model = None


def is_model_loaded() -> bool:
    return _model is not None


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

    # Ensure all three priority classes exist so predict_proba always returns 3 columns
    for label in (0, 1, 2):
        if label not in y:
            X = np.vstack([X, X[0:1]])
            y = np.append(y, label)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500, random_state=42)),
    ])
    model.fit(X, y)
    logger.info("Bootstrap model accuracy: %.2f", model.score(X, y))
    return model


def _priority_proba(model, features: np.ndarray) -> np.ndarray:
    """Map sklearn predict_proba output to fixed [LOW, MEDIUM, HIGH] probabilities."""
    proba = model.predict_proba(features)[0]
    classes = model.named_steps["clf"].classes_
    full = np.zeros(3, dtype=np.float64)
    for i, cls in enumerate(classes):
        idx = int(cls)
        if 0 <= idx < 3:
            full[idx] = proba[i]
    return full


def predict(patient_id: str, age: int, gender: str, district: str, symptoms: list) -> dict:
    global _model
    if _model is None:
        load_model()

    features = build_feature_vector(age, gender, symptoms)
    proba = _priority_proba(_model, features)
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
