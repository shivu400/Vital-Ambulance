"""Evaluation metrics for clinical alerting."""

from __future__ import annotations

import pandas as pd


def compute_precision_at_recall(y_true: pd.Series, y_score: pd.Series, target_recall: float = 0.9) -> float:
    """Compute precision at a given recall level.

    This is a simplified implementation and assumes binary labels (0/1).
    """

    df = pd.DataFrame({"y_true": y_true, "y_score": y_score}).sort_values("y_score", ascending=False)
    df["tp"] = (df["y_true"] == 1).cumsum()
    df["fp"] = (df["y_true"] == 0).cumsum()
    df["recall"] = df["tp"] / df["y_true"].sum().replace(0, 1)
    df["precision"] = df["tp"] / (df["tp"] + df["fp"]).replace(0, 1)

    idx = df[df["recall"] >= target_recall].head(1)
    if idx.empty:
        return 0.0
    return float(idx["precision"].iloc[0])


def compute_latency(timestamps: pd.Series, alert_flags: pd.Series) -> float:
    """Compute average latency (seconds) between first abnormal measurement and alert."""

    if timestamps.empty:
        return 0.0

    df = pd.DataFrame({"ts": timestamps, "alert": alert_flags}).sort_values("ts")
    df["ts"] = pd.to_datetime(df["ts"])

    # Find first abnormal time (alert)
    if not df["alert"].any():
        return 0.0

    first_alert = df.loc[df["alert"]].iloc[0]["ts"]
    # assume the abnormal event begins at first record with alert
    delta = (first_alert - df.iloc[0]["ts"]).total_seconds()
    return float(delta)
