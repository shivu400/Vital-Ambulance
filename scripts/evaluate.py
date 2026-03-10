"""Evaluation script for the Smart Ambulance anomaly detection pipeline.

Run with:
    python -m scripts.evaluate

Outputs a metrics report to reports/metrics.json and a markdown summary to
reports/metrics_report.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make sure project root is on sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.models.anomaly_detector import AnomalyDetector
from src.models.risk_scorer import RiskScorer
from src.preprocessing.artifact_detector import apply_artifact_filter

MODEL_DIR = project_root / "models"
REPORTS_DIR = project_root / "reports"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    far       = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # false alert rate

    return {
        "true_positives":  tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives":  tn,
        "precision":  round(precision, 4),
        "recall":     round(recall, 4),
        "f1_score":   round(f1, 4),
        "false_alert_rate": round(far, 4),
    }


def _alert_latency(timestamps: pd.Series, is_anomaly: pd.Series, scenario: pd.Series) -> float:
    """Average seconds from start of distress/critical phase to first correct alert."""
    latencies = []
    df = pd.DataFrame({"ts": pd.to_datetime(timestamps), "alert": is_anomaly, "sc": scenario})

    for phase in ["distress", "critical"]:
        phase_df = df[df["sc"] == phase].sort_values("ts")
        if phase_df.empty:
            continue
        phase_start = phase_df["ts"].iloc[0]
        alerted = phase_df[phase_df["alert"]]
        if alerted.empty:
            latencies.append(float((phase_df["ts"].iloc[-1] - phase_start).total_seconds()))
        else:
            latencies.append(float((alerted["ts"].iloc[0] - phase_start).total_seconds()))

    return round(float(np.mean(latencies)) if latencies else 0.0, 2)


# ---------------------------------------------------------------------------
# Failure case analysis
# ---------------------------------------------------------------------------

def _analyse_failure_cases(df: pd.DataFrame, y_pred: np.ndarray) -> list[dict]:
    """Identify and describe concrete failure cases from the eval run."""
    cases = []
    labels = df["label"].values

    # Case 1 – False negatives in critical phase
    critical_mask = (df["scenario"] == "critical").values
    critical_fn = (critical_mask & (labels == 1) & (y_pred == 0))
    if critical_fn.sum() > 0:
        sample = df[critical_fn].iloc[0]
        cases.append({
            "case": "False Negative in Critical Phase",
            "n_occurrences": int(critical_fn.sum()),
            "example_vitals": {k: round(float(sample[k]), 2) for k in ["hr", "spo2", "sbp", "rr"]},
            "what_failed": "Detector scored pattern as normal despite critical-level vitals.",
            "why": "Ensemble threshold was calibrated on normal-phase data; some critical patterns "
                   "still fall within the isolation forest decision boundary when only one vital "
                   "is severely abnormal.",
            "improvement": "Add rolling-window trend features (e.g., 10-second rate-of-change) "
                           "so gradual deterioration is captured even when individual values are "
                           "borderline.",
        })

    # Case 2 – False positives from motion artifacts
    normal_mask = (df["scenario"] == "normal").values
    high_motion_mask = (df.get("motion", pd.Series(0, index=df.index)) > 0.6).values
    motion_fp = (normal_mask & high_motion_mask & (y_pred == 1))
    if motion_fp.sum() > 0:
        sample = df[motion_fp].iloc[0]
        cases.append({
            "case": "False Positive from Motion Artifact",
            "n_occurrences": int(motion_fp.sum()),
            "example_vitals": {k: round(float(sample[k]), 2) for k in ["hr", "spo2", "motion"]},
            "what_failed": "Alert fired on a normal patient during a vehicle bump.",
            "why": "SpO2 and HR were transiently inflated/deflated by motion artifacts before "
                   "artifact filtering was applied, pushing the combined score past the threshold.",
            "improvement": "Gate alerts on SQI: suppress anomaly flag when hr_sqi or spo2_sqi < 0.5. "
                           "Additionally apply artifact cleaning before passing data to the detector.",
        })

    # Case 3 – False positives in normal phase without high motion
    normal_no_motion_fp = (normal_mask & ~high_motion_mask & (y_pred == 1) & (labels == 0))
    if normal_no_motion_fp.sum() > 0:
        sample = df[normal_no_motion_fp].iloc[0]
        cases.append({
            "case": "Over-alerting on Normal Phase (Non-motion FP)",
            "n_occurrences": int(normal_no_motion_fp.sum()),
            "example_vitals": {k: round(float(sample[k]), 2) for k in ["hr", "spo2", "sbp", "rr"]},
            "what_failed": "Detector triggered on a normal patient with no obvious artifact.",
            "why": "Gaussian noise in the generator occasionally pushes multiple vitals to their "
                   "plausible extremes simultaneously, creating a rare but valid-looking anomalous "
                   "multi-variate pattern.",
            "improvement": "Require co-occurrence: only alert if anomaly is flagged in >=2 "
                           "consecutive windows AND MEWS >= 2 simultaneously (alert hysteresis).",
        })

    return cases


# ---------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------

def run_evaluation(model_dir: Path = MODEL_DIR, n_eval: int = 1800, seed: int = 99) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating evaluation dataset …")
    df = generate_ambulance_batch(n=n_eval, seed=seed)  # different seed from training

    print("Loading models …")
    detector = AnomalyDetector(model_dir=model_dir)
    detector.load()
    scorer = RiskScorer()

    print("Running artifact filter …")
    df_clean = apply_artifact_filter(df)

    print("Running inference …")
    # Use cleaned vitals for inference
    infer_cols = ["hr", "spo2", "sbp", "dbp", "rr", "temp"]
    infer_df = df_clean[[f"{c}_clean" for c in infer_cols]].rename(
        columns={f"{c}_clean": c for c in infer_cols}
    )
    y = detector.predict(infer_df)
    scored = scorer.score(infer_df)

    y_true = df["label"].values
    y_pred = y["is_anomaly"].values.astype(int)

    metrics = _compute_metrics(y_true, y_pred)
    latency = _alert_latency(df["timestamp"], y["is_anomaly"], df["scenario"])
    metrics["alert_latency_seconds"] = latency

    per_phase = {}
    for phase in ["normal", "distress", "critical"]:
        mask = (df["scenario"] == phase).values
        pm = _compute_metrics(y_true[mask], y_pred[mask])
        per_phase[phase] = pm

    failure_cases = _analyse_failure_cases(df_clean.assign(motion=df["motion"]), y_pred)

    report = {
        "overall": metrics,
        "per_phase": per_phase,
        "failure_cases": failure_cases,
        "eval_samples": len(df),
        "eval_seed": seed,
    }

    # Save JSON
    with open(REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save markdown summary
    md = _render_markdown(metrics, per_phase, failure_cases, len(df))
    with open(REPORTS_DIR / "metrics_report.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("\n=== Evaluation Complete ===")
    print(f"  Precision  : {metrics['precision']:.3f}")
    print(f"  Recall     : {metrics['recall']:.3f}")
    print(f"  F1-Score   : {metrics['f1_score']:.3f}")
    print(f"  False Alert Rate: {metrics['false_alert_rate']:.3f}")
    print(f"  Alert Latency   : {latency:.1f}s")
    print(f"\nReports saved to {REPORTS_DIR}/")


def _render_markdown(metrics: dict, per_phase: dict, failure_cases: list, n: int) -> str:
    lines = [
        "# Smart Ambulance – Alert Quality Metrics Report\n",
        f"Evaluation set: **{n} samples** (separate seed from training)\n",
        "## Overall Metrics\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Precision | {metrics['precision']:.3f} |",
        f"| Recall | {metrics['recall']:.3f} |",
        f"| F1-Score | {metrics['f1_score']:.3f} |",
        f"| False Alert Rate | {metrics['false_alert_rate']:.3f} |",
        f"| Alert Latency (s) | {metrics['alert_latency_seconds']:.1f} |",
        f"| True Positives | {metrics['true_positives']} |",
        f"| False Positives | {metrics['false_positives']} |",
        f"| False Negatives | {metrics['false_negatives']} |",
        "",
        "### Error Acceptability in an Ambulance Context",
        "- **False negatives (missed anomalies)** are the most dangerous failure: a critical "
        "event goes undetected, delaying intervention. Target recall >= 0.85.",
        "- **False positives (over-alerting)** cause alarm fatigue but are tolerable if the "
        "false alert rate stays below ~15%. We prioritise recall over precision.",
        "",
        "## Per-Phase Metrics\n",
        "| Phase | Precision | Recall | F1 | False Alert Rate |",
        "|-------|-----------|--------|----|-----------------|",
    ]
    for phase, m in per_phase.items():
        lines.append(
            f"| {phase.capitalize()} | {m['precision']:.3f} | {m['recall']:.3f} | "
            f"{m['f1_score']:.3f} | {m['false_alert_rate']:.3f} |"
        )

    lines += ["", "## Failure Case Analysis\n"]
    for i, case in enumerate(failure_cases, 1):
        lines += [
            f"### Case {i}: {case['case']}",
            f"**Occurrences:** {case['n_occurrences']}",
            f"**Example vitals:** {case['example_vitals']}",
            f"**What failed:** {case['what_failed']}",
            f"**Why:** {case['why']}",
            f"**Improvement:** {case['improvement']}",
            "",
        ]

    return "\n".join(lines)


if __name__ == "__main__":
    run_evaluation()
