"""Data validation utilities for ambulance telemetry."""

from __future__ import annotations

from typing import Mapping

import pandas as pd


REQUIRED_COLUMNS = ["timestamp", "hr", "spo2", "sbp", "dbp", "rr", "temp"]


def validate_vitals(df: pd.DataFrame) -> None:
    """Validate that incoming telemetry meets basic quality expectations.

    Raises:
        ValueError: If the DataFrame is missing required columns or contains invalid values.
    """

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("NaN values found in required columns")

    if (df["hr"] <= 0).any() or (df["spo2"] <= 0).any():
        raise ValueError("Invalid vital values: hr and spo2 must be positive")

    # Basic bounds
    bounds: Mapping[str, tuple[float, float]] = {
        "hr": (20, 250),
        "spo2": (50, 100),
        "sbp": (40, 250),
        "dbp": (20, 160),
        "rr": (4, 60),
        "temp": (30.0, 43.0),
    }

    for col, (low, high) in bounds.items():
        if ((df[col] < low) | (df[col] > high)).any():
            raise ValueError(f"Values out of bounds for {col}: expected {low}-{high}")


def validate_request(data: dict) -> None:
    """Validate a single request payload as in the API."""

    df = pd.DataFrame([data])
    validate_vitals(df)
