"""Batch/online prediction utility."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.api.dependencies import get_detector, get_scorer, load_input


def run_predict(data: dict, model_dir: str | Path = "models") -> dict:
    detector = get_detector(model_dir=model_dir)
    scorer = get_scorer()

    df = load_input(data)
    y = detector.predict(df)
    scored = scorer.score(df)

    return {
        "is_anomaly": bool(y["is_anomaly"].iloc[0]),
        "anomaly_score": float(y["anomaly_score"].iloc[0]),
        "confidence": float(y["confidence"].iloc[0]),
        "mews_score": int(scored["mews_score"].iloc[0]),
        "shock_index": float(scored["shock_index"].iloc[0]),
        "clinical_risk": str(scored["clinical_risk"].iloc[0]),
    }


if __name__ == "__main__":
    # Allow running this file directly (python src/pipeline/predict.py)
    import sys

    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    example = {
        "timestamp": "2026-03-09T00:00:00Z",
        "hr": 80.0,
        "spo2": 98.0,
        "sbp": 120.0,
        "dbp": 80.0,
        "rr": 16.0,
        "temp": 36.8,
    }
    out = run_predict(example)
    print(out)
