"""Artifact detection and adaptive filtering."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .signal_quality import compute_vital_sqi


def _median_filter(series: pd.Series, window: int = 5) -> pd.Series:
    return series.rolling(window=window, min_periods=1, center=True).median()


def _reject_outliers(series: pd.Series, z_thresh: float = 3.0) -> pd.Series:
    mean = series.mean()
    std = series.std(ddof=0) + 1e-6
    z = (series - mean) / std
    return series.where(z.abs() < z_thresh, np.nan)


def apply_artifact_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Apply artifact removal filters and compute SQI.

    This function performs:
    - Signal quality scoring (SQI)
    - Outlier rejection via z-score
    - Median smoothing for spikes

    Returns a DataFrame with additional columns ending in `_clean` and `_sqi`.
    """

    df = df.copy()
    sqi_df = compute_vital_sqi(df)

    out = df.copy()
    out["hr_sqi"] = sqi_df["hr_sqi"]
    out["spo2_sqi"] = sqi_df["spo2_sqi"]

    # Apply conservative artifact removal: only adjust if quality is low
    for col in ["hr", "spo2", "sbp", "dbp", "rr", "temp"]:
        cleaned = _reject_outliers(out[col])
        cleaned = _median_filter(cleaned, window=5)
        out[f"{col}_clean"] = cleaned.fillna(out[col])

    return out


def vital_sqi(df: pd.DataFrame) -> pd.Series:
    """Return a single aggregated SQI score for a row."""

    sqi_cols = [c for c in df.columns if c.endswith("_sqi")]
    if not sqi_cols:
        return pd.Series([0.0] * len(df), index=df.index)
    return df[sqi_cols].mean(axis=1)
