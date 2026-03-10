"""Artifact detection demonstration – before vs after plots.

Run with:
    python -m scripts.artifact_demo

Generates plots showing the effect of artifact filtering on vital signs,
saved to reports/artifact_demo.png.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.preprocessing.artifact_detector import apply_artifact_filter

REPORTS_DIR = project_root / "reports"
OUTPUT_PATH = REPORTS_DIR / "artifact_demo.png"


def run_demo(seed: int = 42) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic data …")
    df = generate_ambulance_batch(n=600, seed=seed)  # 10-minute window for clear visualisation

    print("Applying artifact filter …")
    df_clean = apply_artifact_filter(df)

    # Focus on the first 300 seconds to show readable traces
    df = df.iloc[:300].copy()
    df_clean = df_clean.iloc[:300].copy()

    t = np.arange(len(df))

    # ------------------------------------------------------------------
    # Plot layout: 4 rows (HR, SpO2, SBP, Motion) × 2 cols (before/after)
    # ------------------------------------------------------------------
    signals = [
        ("hr",   "Heart Rate (bpm)",      "#e74c3c",  (30, 220)),
        ("spo2", "SpO₂ (%)",              "#3498db",  (70, 100)),
        ("sbp",  "Systolic BP (mmHg)",    "#2ecc71",  (60, 220)),
    ]

    fig = plt.figure(figsize=(14, 11))
    fig.patch.set_facecolor("#0f1117")
    fig.suptitle(
        "Artifact Detection – Before vs After Filtering",
        fontsize=15, fontweight="bold", color="white", y=0.98,
    )

    gs = gridspec.GridSpec(
        len(signals) + 1, 2,
        figure=fig,
        hspace=0.45, wspace=0.08,
        left=0.07, right=0.97, top=0.93, bottom=0.06,
    )

    axis_style = dict(facecolor="#1a1d27")
    label_kw = dict(color="white", fontsize=9)
    tick_kw = dict(colors="#aaaaaa", labelsize=8)

    for row, (col, ylabel, colour, (ylo, yhi)) in enumerate(signals):
        raw_vals   = df[col].values
        clean_vals = df_clean[f"{col}_clean"].values
        sqi_vals   = df_clean.get(f"{col}_sqi", pd.Series(np.ones(len(df_clean)))).iloc[:300].values

        # ---- BEFORE ----
        ax_b = fig.add_subplot(gs[row, 0], **axis_style)
        ax_b.plot(t, raw_vals, color=colour, linewidth=0.9, alpha=0.85)
        ax_b.set_ylabel(ylabel, **label_kw)
        ax_b.set_ylim(ylo, yhi)
        ax_b.tick_params(axis="both", **tick_kw)
        ax_b.spines[:].set_color("#333344")
        for spine in ax_b.spines.values():
            spine.set_linewidth(0.5)
        if row == 0:
            ax_b.set_title("BEFORE filtering", color="#aaaaaa", fontsize=10, pad=6)
        if row < len(signals) - 1:
            ax_b.set_xticklabels([])
        else:
            ax_b.set_xlabel("Time (s)", **label_kw)

        # Shade artifact windows (motion > 0.6)
        motion = df["motion"].values
        in_artifact = motion > 0.6
        # group consecutive artifact spans
        starts = np.where(np.diff(in_artifact.astype(int)) == 1)[0] + 1
        ends   = np.where(np.diff(in_artifact.astype(int)) == -1)[0] + 1
        if in_artifact[0]:
            starts = np.concatenate([[0], starts])
        if in_artifact[-1]:
            ends = np.concatenate([ends, [len(in_artifact)]])
        for s, e in zip(starts, ends):
            ax_b.axvspan(s, e, color="#e74c3c", alpha=0.15)

        # ---- AFTER ----
        ax_a = fig.add_subplot(gs[row, 1], **axis_style)
        ax_a.plot(t, raw_vals,   color=colour, linewidth=0.8, alpha=0.35, label="Raw")
        ax_a.plot(t, clean_vals, color="white", linewidth=0.9, alpha=0.9, label="Cleaned")
        ax_a.set_ylim(ylo, yhi)
        ax_a.yaxis.set_ticklabels([])
        ax_a.tick_params(axis="both", **tick_kw)
        ax_a.spines[:].set_color("#333344")
        for spine in ax_a.spines.values():
            spine.set_linewidth(0.5)
        if row == 0:
            ax_a.set_title("AFTER filtering", color="#aaaaaa", fontsize=10, pad=6)
            ax_a.legend(fontsize=7, loc="upper right",
                        facecolor="#1a1d27", edgecolor="#555555", labelcolor="white")
        if row < len(signals) - 1:
            ax_a.set_xticklabels([])
        else:
            ax_a.set_xlabel("Time (s)", **label_kw)

        # SQI colour overlay
        sqi_norm = np.clip(sqi_vals, 0, 1)
        for i in range(len(t) - 1):
            q = sqi_norm[i]
            # low SQI → reddish tint via alpha-filled span
            if q < 0.6:
                ax_a.axvspan(t[i], t[i + 1], color="#e74c3c", alpha=(1 - q) * 0.2)

    # ---- Motion signal (full width) ----
    ax_m = fig.add_subplot(gs[len(signals), :], facecolor="#1a1d27")
    motion_vals = df["motion"].values
    ax_m.fill_between(t, motion_vals, color="#f39c12", alpha=0.55, linewidth=0)
    ax_m.plot(t, motion_vals, color="#f39c12", linewidth=0.8)
    ax_m.axhline(0.6, color="#e74c3c", linewidth=0.8, linestyle="--", label="Artifact threshold (0.6)")
    ax_m.set_ylabel("Motion / Vibration", **label_kw)
    ax_m.set_xlabel("Time (s)", **label_kw)
    ax_m.set_ylim(0, 1.05)
    ax_m.tick_params(axis="both", **tick_kw)
    ax_m.spines[:].set_color("#333344")
    ax_m.legend(fontsize=7, loc="upper right",
                facecolor="#1a1d27", edgecolor="#555555", labelcolor="white")

    # ---- Scenario phase bands ----
    scenario_colours = {"normal": "#2ecc71", "distress": "#f39c12", "critical": "#e74c3c"}
    for ax in fig.get_axes():
        phase_prev = df["scenario"].iloc[0]
        s = 0
        for i, phase in enumerate(df["scenario"]):
            if phase != phase_prev or i == len(df) - 1:
                ax.axvspan(s, i, color=scenario_colours[phase_prev], alpha=0.04)
                s = i
                phase_prev = phase

    # Legend for scenario phases
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, alpha=0.5, label=p.capitalize())
                       for p, c in scenario_colours.items()]
    fig.legend(
        handles=legend_elements, loc="lower center", ncol=3,
        fontsize=8, facecolor="#1a1d27", edgecolor="#555555", labelcolor="white",
        bbox_to_anchor=(0.5, 0.005),
    )

    plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Plot saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run_demo()
