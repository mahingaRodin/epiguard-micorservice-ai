"""
Trains the epiguard-ai model and saves it as epiguard-ai.pkl.
Supports MODEL_TYPE env: logistic_regression | random_forest | xgboost
"""
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
