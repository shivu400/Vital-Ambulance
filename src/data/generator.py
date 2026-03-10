"""Synthetic ambulance telemetry generator.

Signal meanings
---------------
timestamp : UTC datetime
hr        : Heart rate (bpm). Normal 60–100.
spo2      : Peripheral oxygen saturation (%). Normal 95–100.
sbp       : Systolic blood pressure (mmHg). Normal 100–140.
dbp       : Diastolic blood pressure (mmHg). Normal 60–90.
rr        : Respiratory rate (breaths / min). Normal 12–20.
temp      : Core body temperature (°C). Normal 36.1–37.5.
motion    : Normalised vehicle + patient vibration magnitude (0–1). 0 = still,
            1 = severe turbulence / bumps. Used as an artifact confound.
scenario  : Phase label – 'normal', 'distress', or 'critical'.
label     : Ground-truth anomaly flag (0 = normal, 1 = true clinical anomaly).
            Motion-only artifacts are NOT labelled 1; they are confounds.

Assumptions / Limitations
--------------------------
* Data is fully synthetic. Physiological correlations between vitals are
  simplified (e.g. HR and RR co-vary slightly in distress).
* The motion signal drives artifact injection independently from true
  clinical anomalies to reflect real-world measurement noise.
* Sampling rate is 1 Hz (configurable via freq_seconds).
* A session runs for n seconds total, split into three equal phases unless
  phase_splits is supplied.
"""

from __future__ import annotations

import datetime
import random
from typing import Dict, List

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(value: float, low: float, high: float) -> float:
    return float(np.clip(value, low, high))


def _motion_signal(n: int, scenario: str, rng: np.random.Generator) -> np.ndarray:
    """Generate a motion/vibration magnitude trace.

    Ambulance drives are modelled as:
    - Low-frequency sinusoidal component (road rhythm)
    - Random bump transients (potholes / corners)
    - Slightly higher baseline motion in distress/critical due to faster driving
    """
    base = {"normal": 0.15, "distress": 0.25, "critical": 0.20}[scenario]
    t = np.linspace(0, 2 * np.pi * n / 10, n)
    sinusoidal = base * 0.4 * (np.sin(t) + 0.5 * np.sin(3 * t))

    # Random bump transients: sparse, high-amplitude spikes
    bumps = np.zeros(n)
    n_bumps = max(1, int(n * 0.03))
    bump_positions = rng.integers(0, n, size=n_bumps)
    for pos in bump_positions:
        width = rng.integers(2, 8)
        end = min(n, pos + width)
        bumps[pos:end] = rng.uniform(0.4, 0.9)

    motion = np.clip(base + sinusoidal + bumps + rng.normal(0, 0.02, n), 0, 1)
    return motion


# ---------------------------------------------------------------------------
# Per-scenario baseline vitals
# ---------------------------------------------------------------------------

_BASELINES: Dict[str, Dict[str, float]] = {
    "normal":   {"hr": 75,  "spo2": 98,  "sbp": 120, "dbp": 80,  "rr": 16,  "temp": 36.8},
    "distress": {"hr": 105, "spo2": 93,  "sbp": 105, "dbp": 70,  "rr": 22,  "temp": 37.3},
    "critical": {"hr": 130, "spo2": 88,  "sbp": 85,  "dbp": 60,  "rr": 28,  "temp": 38.0},
}

_RANGES = {
    "hr":   (30, 220),
    "spo2": (70, 100),
    "sbp":  (60, 220),
    "dbp":  (40, 130),
    "rr":   (5, 40),
    "temp": (34, 42),
}


def _generate_phase(
    scenario: str,
    n: int,
    rng: np.random.Generator,
    noise_scale: float,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Generate one scenario phase.  Returns (vitals_df, motion_array)."""

    baselines = _BASELINES[scenario]
    motion = _motion_signal(n, scenario, rng)

    data: Dict[str, List[float]] = {k: [] for k in baselines}

    for i in range(n):
        for key, base in baselines.items():
            noise = rng.normal(scale=noise_scale * base)
            value = base + noise

            # Motion-induced artifact injection (NOT labelled as true anomaly)
            if motion[i] > 0.6:
                if key == "spo2":
                    value -= rng.uniform(2, 8)   # motion-induced SpO2 artefact
                elif key == "hr":
                    value += rng.uniform(5, 20)  # bump-induced HR spike

            data[key].append(_normalize(value, *_RANGES[key]))

    df = pd.DataFrame(data)
    return df, motion


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_ambulance_batch(
    n: int = 1800,
    start_time: datetime.datetime | None = None,
    freq_seconds: int = 1,
    noise_scale: float = 0.03,
    phase_splits: tuple[float, float, float] | None = None,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Generate a realistic time-series of vital signs with motion artifacts.

    The session is divided into three phases:
    - **normal**   : Stable transport, vitals in normal range.
    - **distress** : Patient showing early deterioration (tachycardia, falling SpO2).
    - **critical** : Severe deterioration requiring immediate intervention.

    Args:
        n           : Total number of samples (seconds at 1 Hz). Default = 1800 (30 min).
        start_time  : UTC start timestamp. Defaults to now.
        freq_seconds: Sampling interval in seconds.
        noise_scale : Gaussian noise relative to each vital's baseline value.
        phase_splits: Fraction of total samples for (normal, distress, critical).
                      Must sum to 1.0. Default: (0.50, 0.30, 0.20).
        seed        : Random seed for reproducibility.

    Returns:
        DataFrame with columns: timestamp, hr, spo2, sbp, dbp, rr, temp,
        motion, scenario, label.
    """

    if phase_splits is None:
        phase_splits = (0.50, 0.30, 0.20)

    if abs(sum(phase_splits) - 1.0) > 1e-6:
        raise ValueError("phase_splits must sum to 1.0")

    if start_time is None:
        start_time = datetime.datetime.now(datetime.timezone.utc)

    rng = np.random.default_rng(seed)

    phase_ns = [max(1, int(n * f)) for f in phase_splits]
    # Adjust last phase to guarantee exactly n total samples
    phase_ns[-1] += n - sum(phase_ns)

    phases = ["normal", "distress", "critical"]
    all_dfs = []

    for scenario, phase_n in zip(phases, phase_ns):
        vitals_df, motion = _generate_phase(scenario, phase_n, rng, noise_scale)
        vitals_df["motion"] = motion
        vitals_df["scenario"] = scenario

        # Ground-truth label: distress and critical phases contain true anomalies.
        # Within distress, not every sample is anomalous (early warning signals).
        # Within critical, nearly all samples are anomalous.
        if scenario == "normal":
            labels = np.zeros(phase_n, dtype=int)
        elif scenario == "distress":
            # First half of distress is borderline – ~40% anomalous
            labels = (rng.random(phase_n) < 0.40).astype(int)
        else:  # critical
            labels = (rng.random(phase_n) < 0.90).astype(int)

        vitals_df["label"] = labels
        all_dfs.append(vitals_df)

    df = pd.concat(all_dfs, ignore_index=True)

    timestamps = [
        start_time + datetime.timedelta(seconds=i * freq_seconds)
        for i in range(len(df))
    ]
    df.insert(0, "timestamp", timestamps)

    return df
