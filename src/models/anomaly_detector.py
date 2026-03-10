"""Anomaly detection model.

Uses an explainable ensemble of Isolation Forest and OneClassSVM from scikit-learn.
The decision threshold is computed from the training distribution and persisted
alongside the model weights so that inference is deterministic and reproducible.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

# Feature columns used for anomaly detection
FEATURE_COLS = ["hr", "spo2", "sbp", "dbp", "rr", "temp"]


@dataclass
class AnomalyDetector:
    """Encapsulates an ensemble anomaly detector.

    This class is intentionally lightweight and transparent to avoid black-box
    behaviour.  The decision threshold is persisted so that inference results
    are reproducible across sessions.
    """

    model_dir: Path
    isolation: IsolationForest | None = field(default=None, init=False)
    ocsvm: OneClassSVM | None = field(default=None, init=False)
    _threshold: float | None = field(default=None, init=False)
    _score_std: float | None = field(default=None, init=False)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, data: pd.DataFrame) -> None:
        """Train anomaly detectors from clean vital sign data.

        The adaptive threshold (median − 1σ of the combined decision scores
        computed on training data) and the score standard deviation are both
        persisted so that inference is independent of any runtime statistics.
        """

        features = data[FEATURE_COLS].copy()

        self.isolation = IsolationForest(
            n_estimators=100, contamination=0.05, random_state=42
        )
        self.isolation.fit(features)

        self.ocsvm = OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
        self.ocsvm.fit(features)

        # Compute and persist the decision threshold from *training* scores
        iso_scores = self.isolation.decision_function(features)
        svm_scores = self.ocsvm.decision_function(features)
        combined = (iso_scores + svm_scores) / 2.0

        self._threshold = float(np.median(combined) - 1.0 * np.std(combined))
        self._score_std = float(np.std(combined))

        self._save()

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return anomaly score, boolean flags and confidence per row.

        Returns a DataFrame with columns:
        - anomaly_score : Combined decision-function value (higher = more normal).
        - is_anomaly    : True when score falls below the persisted threshold.
        - confidence    : [0, 1] confidence in the anomaly decision.
                          1 = maximally confident, 0 = right on the boundary.

        Windowing strategy
        ------------------
        This method operates on whatever window the caller supplies.  For
        real-time inference the caller (API / pipeline) passes a single row
        (1-second window).  For batch evaluation, a rolling window of N rows
        should be assembled upstream.  The combined score captures the joint
        Isolation Forest + OCSVM signal across all supplied rows simultaneously.
        """

        if self.isolation is None or self.ocsvm is None or self._threshold is None:
            self.load()

        features = data[FEATURE_COLS].copy()

        iso_score = self.isolation.decision_function(features)
        svm_score = self.ocsvm.decision_function(features)
        combined_score = (iso_score + svm_score) / 2.0

        is_anomaly = combined_score < self._threshold

        # Confidence = normalised distance from the decision boundary.
        # σ from training gives us a meaningful scale for distance.
        scale = self._score_std if self._score_std and self._score_std > 0 else 1.0
        distance = np.abs(combined_score - self._threshold) / scale
        confidence = np.clip(distance / 3.0, 0.0, 1.0)  # 3σ → confidence = 1.0

        return pd.DataFrame(
            {
                "anomaly_score": combined_score,
                "is_anomaly": is_anomaly,
                "confidence": confidence,
            }
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)

        with open(self.model_dir / "isolation_forest.pkl", "wb") as f:
            pickle.dump(self.isolation, f)

        with open(self.model_dir / "ocsvm.pkl", "wb") as f:
            pickle.dump(self.ocsvm, f)

        meta = {
            "threshold": self._threshold,
            "score_std": self._score_std,
            "feature_cols": FEATURE_COLS,
        }
        with open(self.model_dir / "detector_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

    def load(self) -> None:
        with open(self.model_dir / "isolation_forest.pkl", "rb") as f:
            self.isolation = pickle.load(f)

        with open(self.model_dir / "ocsvm.pkl", "rb") as f:
            self.ocsvm = pickle.load(f)

        meta_path = self.model_dir / "detector_meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            self._threshold = float(meta["threshold"])
            self._score_std = float(meta.get("score_std", 1.0))
        else:
            # Backwards-compatibility: derive threshold at load-time if no meta file
            self._threshold = None
            self._score_std = None
