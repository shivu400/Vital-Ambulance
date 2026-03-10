import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.preprocessing.artifact_detector import apply_artifact_filter, vital_sqi


def test_artifact_filter_adds_clean_columns():
    df = generate_ambulance_batch(n=20)
    out = apply_artifact_filter(df)
    assert "hr_clean" in out.columns
    assert "spo2_clean" in out.columns


def test_vital_sqi_is_in_range():
    df = generate_ambulance_batch(n=10)
    out = vital_sqi(df)
    assert out.between(0, 1).all()
