"""End-to-end training pipeline for the smart ambulance model."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path so this module can be executed as a script
# (e.g., `python src/pipeline/train.py`) without needing `python -m`.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.data.validator import validate_vitals
from src.models.anomaly_detector import AnomalyDetector


def run_training(
    model_dir: str | Path = "models",
    n_samples: int = 1800,
    random_seed: int = 42,
) -> None:
    """Train and persist models with synthetic ambulatory data.

    Training is intentionally performed on normal-phase data only so the
    detector learns a clean baseline distribution.  Distress and critical
    phase rows act as the labelled anomaly set used during evaluation.
    """

    Path(model_dir).mkdir(parents=True, exist_ok=True)

    df = generate_ambulance_batch(n=n_samples, seed=random_seed)

    # Train only on the clean normal phase
    train_df = df[df["scenario"] == "normal"].copy()
    validate_vitals(train_df)

    detector = AnomalyDetector(model_dir=Path(model_dir))
    detector.train(train_df)

    # Persist the full dataset (used by the evaluate script)
    df.to_parquet(Path(model_dir) / "training_data.parquet", index=False)

    print(f"Training complete. Models saved to {model_dir}")
    print(f"  Normal samples : {(df['scenario'] == 'normal').sum()}")
    print(f"  Distress samples: {(df['scenario'] == 'distress').sum()}")
    print(f"  Critical samples: {(df['scenario'] == 'critical').sum()}")


if __name__ == "__main__":
    # Allow running this file directly (e.g., python src/pipeline/train.py) by
    # ensuring the project root is on sys.path so `import src...` works.
    import sys

    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    run_training()
