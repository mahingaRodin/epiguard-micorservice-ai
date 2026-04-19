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
