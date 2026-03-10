"""FastAPI dependencies for model loading and health checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models.anomaly_detector import AnomalyDetector
from src.models.risk_scorer import RiskScorer


_detector: AnomalyDetector | None = None
_scorer: RiskScorer | None = None


def get_detector(model_dir: str | Path = "models") -> AnomalyDetector:
    """Return a singleton detector instance (lazy-loaded)."""

    global _detector
    if _detector is None:
        model_path = Path(model_dir)
        detector = AnomalyDetector(model_dir=model_path)
        try:
            detector.load()
        except Exception:
            # If models not trained yet, we still return a detector object to avoid 500s.
            pass
        _detector = detector

    return _detector


def get_scorer() -> RiskScorer:
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer


def is_model_ready(model_dir: str | Path = "models") -> bool:
    model_path = Path(model_dir)
    return (
        (model_path / "isolation_forest.pkl").exists()
        and (model_path / "ocsvm.pkl").exists()
        and (model_path / "detector_meta.json").exists()
    )


def load_input(payload: dict | pd.DataFrame) -> pd.DataFrame:
    """Normalize/validate in a single place.

    Accepts either a dict (from a request payload) or a DataFrame.
    """

    if isinstance(payload, dict):
        df = pd.DataFrame([payload])
    else:
        df = payload.copy()

    return df.reset_index(drop=True)
