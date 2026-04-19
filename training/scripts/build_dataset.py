"""
Builds a training dataset from:
  1. PostgreSQL triage_results + symptoms tables (real data — when available)
  2. Synthetic fallback if DB is empty or unreachable
"""
import logging
import numpy as np
from sklearn.model_selection import train_test_split
from app.config.settings import settings
from app.utils.preprocessing import build_feature_vector, SYMPTOM_TYPES

logger = logging.getLogger(__name__)


def build_dataset(test_size: float = 0.2, random_state: int = 42):
    """Returns X_train, X_test, y_train, y_test as numpy arrays."""
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
    """Load and featurise real patient + triage data from the EpiGuard DB."""
    import psycopg2
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT p.age, p.gender,
               array_agg(s.symptom_type ORDER BY s.symptom_type) AS types,
               array_agg(s.severity     ORDER BY s.symptom_type) AS severities,
               tr.priority_level
        FROM patients p
        JOIN symptoms s         ON s.patient_id  = p.id
        JOIN triage_results tr  ON tr.patient_id = p.id
        GROUP BY p.id, p.age, p.gender, tr.priority_level
    """)
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
    """Generate a synthetic training set when no real data is available."""
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
