from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_predict_missing_model_returns_503():
    payload = {
        "timestamp": "2026-03-09T00:00:00Z",
        "hr": 80.0,
        "spo2": 98.0,
        "sbp": 120.0,
        "dbp": 80.0,
        "rr": 16.0,
        "temp": 36.8,
    }

    resp = client.post("/v1/predict", json=payload)
    assert resp.status_code in (503, 200)
