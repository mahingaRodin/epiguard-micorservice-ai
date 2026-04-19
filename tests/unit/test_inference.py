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
