from io import StringIO
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.gistemp import load_gistemp_annual_data


DATASET_SOURCE = "NASA GISS Surface Temperature Analysis (GISTEMP v4)"
DATASET_BASELINE = "1951-1980"
DATASET_START_YEAR = 1880
DATASET_END_YEAR = 2025
MINIMUM_REPORT_OBSERVATIONS = 5
MAXIMUM_OBSERVATION_LIMIT = DATASET_END_YEAR - DATASET_START_YEAR + 1
CACHE_CONTROL_HEADER = "public, max-age=3600"

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

OPENAPI_TAGS = [
    {
        "name": "Status",
        "description": "Service availability checks.",
    },
    {
        "name": "Dataset",
        "description": (
            "Source, baseline period, coverage, and unit information "
            "for the climate dataset."
        ),
    },
    {
        "name": "Observations",
        "description": (
            "Annual global temperature-anomaly observations in JSON "
            "and CSV formats."
        ),
    },
    {
        "name": "Reports",
        "description": (
            "Calculated climate metrics and plain-language "
            "interpretations for selected year ranges."
        ),
    },
]

CLIMATE_DATA = load_gistemp_annual_data()

app = FastAPI(
    title="Climate Commons API",
    version="0.8.0",
    description="Screen-reader-first climate data reporting API.",
    openapi_tags=OPENAPI_TAGS,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=[],
)


class HealthResponse(BaseModel):
    status: str


class DatasetMetadata(BaseModel):
    source: str
    baseline_period: str
    coverage_start_year: int
    coverage_end_year: int
    observation_count: int
    latest_year: int
    unit: str


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


class ClimateSummary(BaseModel):
    latest_year: int
    summary: str


def load_climate_data() -> pd.DataFrame:
    return CLIMATE_DATA.copy()


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


def limit_observations(
    data: pd.DataFrame,
    limit: Optional[int],
) -> pd.DataFrame:
    if limit is None:
        return data

    return data.head(limit)


def five_year_average(data: pd.DataFrame) -> float:
    return float(data["anomaly_c"].tail(5).mean())


def trend_c_per_decade(data: pd.DataFrame) -> float:
    slope_c_per_year, _ = np.polyfit(
        data["year"],
        data["anomaly_c"],
        1,
    )
    return float(slope_c_per_year * 10)


@app.get(
    "/",
    include_in_schema=False,
)
def homepage() -> FileResponse:
    return FileResponse("static/index.html")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Status"],
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/metadata",
    response_model=DatasetMetadata,
    tags=["Dataset"],
)
def dataset_metadata(response: Response) -> DatasetMetadata:
    response.headers["Cache-Control"] = CACHE_CONTROL_HEADER

    data = load_climate_data()

    return DatasetMetadata(
        source=DATASET_SOURCE,
        baseline_period=DATASET_BASELINE,
        coverage_start_year=int(data["year"].min()),
        coverage_end_year=int(data["year"].max()),
        observation_count=int(len(data)),
        latest_year=int(data["year"].max()),
        unit="degrees Celsius anomaly",
    )


@app.get(
    "/observations",
    response_model=ObservationsResponse,
    tags=["Observations"],
)
def climate_observations(
    response: Response,
    start_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
    end_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=MAXIMUM_OBSERVATION_LIMIT,
    ),
) -> ObservationsResponse:
    response.headers["Cache-Control"] = CACHE_CONTROL_HEADER

    data = select_observations(start_year, end_year)
    data = limit_observations(data, limit)

    observations = [
        Observation(
            year=int(row.year),
            anomaly_c=float(row.anomaly_c),
        )
        for row in data.itertuples(index=False)
    ]

    return ObservationsResponse(
        source=DATASET_SOURCE,
        observations=observations,
    )


@app.get(
    "/observations.csv",
    tags=["Observations"],
)
def climate_observations_csv(
    start_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
    end_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        le=MAXIMUM_OBSERVATION_LIMIT,
    ),
) -> StreamingResponse:
    data = select_observations(start_year, end_year)
    data = limit_observations(data, limit)

    csv_buffer = StringIO()
    data.to_csv(
        csv_buffer,
        columns=["year", "anomaly_c"],
        index=False,
    )

    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Cache-Control": CACHE_CONTROL_HEADER,
            "Content-Disposition": (
                'attachment; filename="gistemp_observations.csv"'
            ),
        },
    )


@app.get(
    "/report",
    response_model=ClimateReport,
    tags=["Reports"],
)
def climate_report(
    response: Response,
    start_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
    end_year: Optional[int] = Query(
        default=None,
        ge=DATASET_START_YEAR,
        le=DATASET_END_YEAR,
    ),
) -> ClimateReport:
    response.headers["Cache-Control"] = CACHE_CONTROL_HEADER

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


@app.get(
    "/summary",
    response_model=ClimateSummary,
    tags=["Reports"],
)
def climate_summary(response: Response) -> ClimateSummary:
    response.headers["Cache-Control"] = CACHE_CONTROL_HEADER

    data = load_climate_data()
    latest = data.iloc[-1]
    recent_average = five_year_average(data)
    trend = trend_c_per_decade(data)

    summary = (
        f"In {int(latest['year'])}, the global annual temperature "
        f"anomaly was {float(latest['anomaly_c']):.2f} degrees Celsius "
        f"relative to the {DATASET_BASELINE} baseline. Over the latest "
        f"five years, the average anomaly was {recent_average:.2f} "
        f"degrees Celsius. Across the full dataset, the trend was "
        f"{trend:.3f} degrees Celsius per decade."
    )

    return ClimateSummary(
        latest_year=int(latest["year"]),
        summary=summary,
    )
