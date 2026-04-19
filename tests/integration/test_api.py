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
