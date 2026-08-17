import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "up"
    assert data["model_loaded"] is True


def test_predict_endpoint(client):
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
    assert "risk_score" in data
    assert "priority_level" in data
    assert data["priority_level"] in ("LOW", "MEDIUM", "HIGH")


def test_predict_invalid_severity(client):
    payload = {
        "patient_id": "test-uuid-002",
        "age": 28,
        "gender": "MALE",
        "district": "Kigali",
        "symptoms": [{"symptom_type": "fever", "severity": 10}],  # invalid — max is 5
    }
    response = client.post("/ml/predict", json=payload)
    assert response.status_code == 422
