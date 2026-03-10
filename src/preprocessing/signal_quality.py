"""Signal quality index (SQI) utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _scaled_var(series: pd.Series) -> float:
    return float(np.var(series) / (np.mean(series) + 1e-6))


def compute_signal_quality(series: pd.Series, min_expected: float, max_expected: float) -> float:
    """Compute a simple SQI between 0 (low quality) and 1 (high quality)."""

    if series.empty or series.isna().all():
        return 0.0

    mean = float(series.mean())
    std = float(series.std(ddof=0))

    # Score based on expected range and stability
    range_score = 1 - min(1, max(0, abs(mean - (min_expected + max_expected) / 2) / ((max_expected - min_expected) / 2)))
    stability_score = 1 - min(1, std / (abs(mean) + 1e-6))

    quality = max(0.0, min(1.0, (range_score + stability_score) / 2))
    return quality


def compute_vital_sqi(df: pd.DataFrame) -> pd.DataFrame:
    """Compute SQI for each vital sign in a DataFrame.

    Returns a DataFrame with additional columns: *<vital>_sqi.
    """

    out = df.copy()
    out["hr_sqi"] = out["hr"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 30, 220), raw=False
    )
    out["spo2_sqi"] = out["spo2"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 70, 100), raw=False
    )
    out["sbp_sqi"] = out["sbp"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 60, 220), raw=False
    )
    out["dbp_sqi"] = out["dbp"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 40, 130), raw=False
    )
    out["rr_sqi"] = out["rr"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 5, 40), raw=False
    )
    out["temp_sqi"] = out["temp"].rolling(window=5, min_periods=1).apply(
        lambda s: compute_signal_quality(s, 34, 42), raw=False
    )

    return out
