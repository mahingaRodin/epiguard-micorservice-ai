import numpy as np
from typing import List, Dict

SYMPTOM_TYPES = [
    "fever", "cough", "fatigue", "shortness_of_breath",
    "headache", "diarrhea", "vomiting", "rash",
    "joint_pain", "chest_pain", "sore_throat", "runny_nose",
]

GENDER_MAP = {"MALE": 0, "FEMALE": 1, "OTHER": 2}


def build_feature_vector(age: int, gender: str, symptoms: List[Dict]) -> np.ndarray:
    """
    Build a fixed-length (14,) float32 feature vector.
    Layout: [age_norm, gender_enc, symptom_0..11_severity_norm]
    """
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
