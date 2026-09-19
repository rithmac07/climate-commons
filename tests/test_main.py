import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_loads(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Climate Commons" in response.text


def test_report_uses_nasa_gistemp_data(client):
    response = client.get("/report")

    assert response.status_code == 200

    report = response.json()

    assert report["source"] == (
        "NASA GISS Surface Temperature Analysis (GISTEMP v4)"
    )
    assert report["coverage_start_year"] == 1880
    assert report["coverage_end_year"] == 2025
    assert report["latest_year"] == 2025


def test_report_contains_climate_metrics(client):
    response = client.get("/report")

    assert response.status_code == 200

    report = response.json()

    assert report["observation_count"] == 146
    assert report["latest_anomaly_c"] == 1.19
    assert report["trend_c_per_decade"] > 0
    assert "increased" in report["interpretation"]


def test_report_rejects_reversed_year_range(client):
    response = client.get(
        "/report?start_year=2025&end_year=1980"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "start_year must be earlier than or equal to end_year."
        )
    }


def test_report_requires_at_least_five_observations(client):
    response = client.get(
        "/report?start_year=2023&end_year=2025"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Choose a range containing at least five annual "
            "observations."
        )
    }


def test_observations_returns_annual_records(client):
    response = client.get("/observations")

    assert response.status_code == 200

    body = response.json()

    assert body["source"] == (
        "NASA GISS Surface Temperature Analysis (GISTEMP v4)"
    )
    assert len(body["observations"]) == 146
    assert body["observations"][0] == {
        "year": 1880,
        "anomaly_c": -0.18,
    }
    assert body["observations"][-1] == {
        "year": 2025,
        "anomaly_c": 1.19,
    }


def test_observations_filters_by_year_range(client):
    response = client.get(
        "/observations?start_year=1980&end_year=1984"
    )

    assert response.status_code == 200

    observations = response.json()["observations"]

    assert len(observations) == 5
    assert observations[0]["year"] == 1980
    assert observations[-1]["year"] == 1984


def test_observations_rejects_reversed_year_range(client):
    response = client.get(
        "/observations?start_year=2025&end_year=1980"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "start_year must be earlier than or equal to end_year."
        )
    }


def test_observations_rejects_year_before_dataset(client):
    response = client.get("/observations?start_year=1879")

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert errors[0]["loc"] == ["query", "start_year"]
    assert errors[0]["type"] == "greater_than_equal"


def test_report_rejects_year_after_dataset(client):
    response = client.get("/report?end_year=2026")

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert errors[0]["loc"] == ["query", "end_year"]
    assert errors[0]["type"] == "less_than_equal"
