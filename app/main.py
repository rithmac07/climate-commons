from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.gistemp import load_gistemp_annual_data


app = FastAPI(
    title="Climate Commons API",
    version="0.3.0",
    description="Screen-reader-first climate data reporting API.",
)

DATASET_SOURCE = "NASA GISS Surface Temperature Analysis (GISTEMP v4)"
DATASET_START_YEAR = 1880
DATASET_END_YEAR = 2025
MINIMUM_REPORT_OBSERVATIONS = 5

app.mount("/static", StaticFiles(directory="static"), name="static")


class HealthResponse(BaseModel):
    status: str


class Observation(BaseModel):
    year: int
    anomaly_c: float


class ObservationsResponse(BaseModel):
    source: str
    observations: list[Observation]


class ClimateReport(BaseModel):
    source: str
    coverage_start_year: int
    coverage_end_year: int
    observation_count: int
    latest_year: int
    latest_anomaly_c: float
    latest_five_year_average_c: float
    trend_c_per_decade: float
    interpretation: str


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse("static/index.html")


def load_climate_data() -> pd.DataFrame:
    return load_gistemp_annual_data()


def select_observations(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    if start_year is not None and end_year is not None:
        if start_year > end_year:
            raise HTTPException(
                status_code=400,
                detail=(
                    "start_year must be earlier than or equal to end_year."
                ),
            )

    data = load_climate_data()

    if start_year is not None:
        data = data[data["year"] >= start_year]

    if end_year is not None:
        data = data[data["year"] <= end_year]

    if data.empty:
        raise HTTPException(
            status_code=400,
            detail="No observations were found for the selected year range.",
        )

    return data


def five_year_average(data: pd.DataFrame) -> float:
    return float(data["anomaly_c"].tail(5).mean())


def trend_c_per_decade(data: pd.DataFrame) -> float:
    slope_c_per_year, _ = np.polyfit(
        data["year"],
        data["anomaly_c"],
        1,
    )
    return float(slope_c_per_year * 10)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/observations", response_model=ObservationsResponse)
def climate_observations(
    start_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
        description=(
            "First year to include, from "
            f"{DATASET_START_YEAR} through {DATASET_END_YEAR}."
        ),
    ),
    end_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
        description=(
            "Last year to include, from "
            f"{DATASET_START_YEAR} through {DATASET_END_YEAR}."
        ),
    ),
) -> ObservationsResponse:
    data = select_observations(start_year, end_year)

    return ObservationsResponse(
        source=DATASET_SOURCE,
        observations=[
            Observation(
                year=int(row.year),
                anomaly_c=float(row.anomaly_c),
            )
            for row in data.itertuples(index=False)
        ],
    )


@app.get("/report", response_model=ClimateReport)
def climate_report(
    start_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
        description=(
            "First year to include in the report, from "
            f"{DATASET_START_YEAR} through {DATASET_END_YEAR}."
        ),
    ),
    end_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
        description=(
            "Last year to include in the report, from "
            f"{DATASET_START_YEAR} through {DATASET_END_YEAR}."
        ),
    ),
) -> ClimateReport:
    data = select_observations(start_year, end_year)

    if len(data) < MINIMUM_REPORT_OBSERVATIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Choose a range containing at least five annual "
                "observations."
            ),
        )

    latest = data.iloc[-1]
    trend = trend_c_per_decade(data)

    if trend > 0:
        interpretation = (
            "The global annual temperature anomaly increased across "
            "the selected period."
        )
    elif trend < 0:
        interpretation = (
            "The global annual temperature anomaly decreased across "
            "the selected period."
        )
    else:
        interpretation = (
            "The global annual temperature anomaly was flat across "
            "the selected period."
        )

    return ClimateReport(
        source=DATASET_SOURCE,
        coverage_start_year=int(data["year"].min()),
        coverage_end_year=int(data["year"].max()),
        observation_count=int(len(data)),
        latest_year=int(latest["year"]),
        latest_anomaly_c=float(latest["anomaly_c"]),
        latest_five_year_average_c=round(five_year_average(data), 3),
        trend_c_per_decade=round(trend, 3),
        interpretation=interpretation,
    )
