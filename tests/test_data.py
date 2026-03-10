import pandas as pd

from src.data.generator import generate_ambulance_batch
from src.data.validator import validate_vitals


def test_generate_and_validate():
    df = generate_ambulance_batch(n=10)
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 10
    validate_vitals(df)
