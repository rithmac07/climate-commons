from pathlib import Path
import pandas as pd
from app.analysis.validate import validate_annual_series

FIXTURE_PATH = Path("data_fixtures/gistemp_sample.csv")


def load_sample_gistemp() -> pd.DataFrame:
    raw_data = pd.read_csv(FIXTURE_PATH)
    return validate_annual_series(raw_data)
