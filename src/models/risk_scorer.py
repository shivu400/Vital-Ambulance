"""Clinical risk scoring (MEWS, Shock Index, etc.)."""

from __future__ import annotations

import pandas as pd


def shock_index(hr: float, sbp: float) -> float:
    """Shock index (HR / SBP)."""

    if sbp <= 0:
        return float("inf")
    return hr / sbp


def mews_score(hr: float, sbp: float, rr: float, temp: float, spo2: float) -> int:
    """Calculate a simplified MEWS score."""

    score = 0

    # HR
    if hr <= 40:
        score += 2
    elif hr <= 50:
        score += 1
    elif hr <= 100:
        score += 0
    elif hr <= 110:
        score += 1
    elif hr <= 130:
        score += 2
    else:
        score += 3

    # SBP
    if sbp <= 70:
        score += 3
    elif sbp <= 80:
        score += 2
    elif sbp <= 100:
        score += 1
    elif sbp <= 200:
        score += 0
    else:
        score += 2

    # RR
    if rr <= 8:
        score += 2
    elif rr <= 14:
        score += 0
    elif rr <= 20:
        score += 1
    elif rr <= 30:
        score += 2
    else:
        score += 3

    # Temp
    if temp <= 35:
        score += 2
    elif temp <= 38.4:
        score += 0
    else:
        score += 2

    # SpO2
    if spo2 < 90:
        score += 3
    elif spo2 < 95:
        score += 1

    return score


class RiskScorer:
    """Wrapper for combined risk scoring."""

    @staticmethod
    def score(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["shock_index"] = out.apply(lambda r: shock_index(r["hr"], r["sbp"]), axis=1)
        out["mews_score"] = out.apply(
            lambda r: mews_score(r["hr"], r["sbp"], r["rr"], r["temp"], r["spo2"]),
            axis=1,
        )
        out["clinical_risk"] = out.apply(
            lambda r: "high" if (r["mews_score"] >= 5 or r["shock_index"] >= 0.9) else "normal",
            axis=1,
        )
        return out
