import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.models.anomaly_detector import AnomalyDetector
from src.models.risk_scorer import RiskScorer


def test_anomaly_detector_train_and_predict(tmp_path):
    df = generate_ambulance_batch(n=200)
    model_dir = tmp_path / "models"
    detector = AnomalyDetector(model_dir=model_dir)
    detector.train(df)

    out = detector.predict(df.iloc[:5])
    assert "is_anomaly" in out
    assert "anomaly_score" in out
    assert "confidence" in out
    assert out["confidence"].between(0.0, 1.0).all()


def test_risk_scorer_scores():
    df = generate_ambulance_batch(n=3)
    scored = RiskScorer.score(df)
    assert "mews_score" in scored
    assert "shock_index" in scored
