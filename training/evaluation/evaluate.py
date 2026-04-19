"""
Evaluates trained model and writes a metrics report to training_reports/.
"""
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
    logger.info("\nClassification Report:\n%s",
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
