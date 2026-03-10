"""Explainability helpers for predictions."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def explain_prediction(
    vitals: pd.Series, anomaly_score: float, is_anomaly: bool, risk_score: int
) -> Dict[str, str]:
    """Generate a lightweight explanation for a prediction."""

    reasons = []

    # Clinical rules
    if risk_score >= 5:
        reasons.append("MEWS indicates potential deterioration")

    if vitals.get("spo2", 100) < 92:
        reasons.append("Low oxygen saturation")

    if vitals.get("hr", 0) > 130:
        reasons.append("Tachycardia")

    # Anomaly explanation
    if is_anomaly:
        reasons.append("Pattern deviates from baseline (isolation forest + OCSVM)")

    if not reasons:
        reasons.append("Vitals within expected range and no detected anomalies")

    return {
        "reason": "; ".join(reasons),
        "anomaly_score": f"{anomaly_score:.3f}",
        "risk_score": str(risk_score),
    }
