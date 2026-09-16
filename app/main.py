from pathlib import Path
from py_compile import main

import numpy as np
import pandas as pd
from fastapi import FastAPI


app = FastAPI(
    title="Climate Commons API",
    version="0.1.0",
    description="Screen-reader-first climate data reporting API.",
)

DATA_PATH = Path("data_fixtures/gistemp_sample.csv")


def load_climate_data() -> pd.DataFrame:
    data = pd.read_csv(DATA_PATH)

    required_columns = {"year", "anomaly_c"}
    if not required_columns.issubset(data.columns):
        raise ValueError("The CSV must contain year and anomaly_c columns.")

    data["year"] = pd.to_numeric(data["year"], errors="raise").astype(int)
    data["anomaly_c"] = pd.to_numeric(
        data["anomaly_c"],
        errors="raise",
    )

    if data["year"].duplicated().any():
        raise ValueError("The CSV contains duplicate years.")

    return data.sort_values("year").reset_index(drop=True)


def five_year_average(data: pd.DataFrame) -> float:
    return float(data["anomaly_c"].tail(5).mean())


def trend_c_per_decade(data: pd.DataFrame) -> float:
    slope_c_per_year, _ = np.polyfit(
        data["year"],
        data["anomaly_c"],
        1,
    )
    return float(slope_c_per_year * 10)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/report")
def climate_report() -> dict[str, object]:
    data = load_climate_data()
    latest = data.iloc[-1]
    trend = trend_c_per_decade(data)

    if trend > 0:
        interpretation = (
            "The annual global temperature anomaly increased over "
            "this sample period."
        )
    elif trend < 0:
        interpretation = (
            "The annual global temperature anomaly decreased over "
            "this sample period."
        )
    else:
        interpretation = (
            "The annual global temperature anomaly was flat over "
            "this sample period."
        )

    return {
        "source": "Local development fixture based on NASA GISTEMP-style data",
        "coverage_start_year": int(data["year"].min()),
        "coverage_end_year": int(data["year"].max()),
        "observation_count": int(len(data)),
        "latest_year": int(latest["year"]),
        "latest_anomaly_c": float(latest["anomaly_c"]),
        "latest_five_year_average_c": round(five_year_average(data), 3),
        "trend_c_per_decade": round(trend, 3),
        "interpretation": interpretation,
    }

