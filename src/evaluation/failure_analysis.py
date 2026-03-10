"""Failure mode analysis for ambulance monitoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FailureMode:
    name: str
    description: str
    mitigation: str


def get_common_failure_modes() -> list[FailureMode]:
    return [
        FailureMode(
            name="Sensor dropout",
            description="Data streams include long gaps or repeated values due to sensor disconnection.",
            mitigation="Implement missing-data detection and fallback to prior state, flag low SQI and require manual review.",
        ),
        FailureMode(
            name="Motion artifacts",
            description="High frequency noise from movement causing invalid spikes in vitals.",
            mitigation="Use SQI-based gating and median filtering to suppress transient spikes.",
        ),
        FailureMode(
            name="Model drift",
            description="Anomaly detector thresholds become stale as patient population or device calibration changes.",
            mitigation="Periodically retrain on recent clean data and implement drift monitoring.",
        ),
        FailureMode(
            name="Over-alerting",
            description="False positives lead to alarm fatigue in clinical staff.",
            mitigation="Combine anomaly scores with clinical risk rules and enforce alert cooldowns.",
        ),
    ]
