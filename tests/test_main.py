from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_loads():
    response = client.get("/")

    assert response.status_code == 200
    assert "Climate Commons" in response.text
    assert 'src="/static/app.js"' in response.text


def test_report_uses_nasa_gistemp_data():
    response = client.get("/report")
    report = response.json()

    assert response.status_code == 200
    assert report["source"] == (
        "NASA GISS Surface Temperature Analysis (GISTEMP v4)"
    )
    assert report["coverage_start_year"] == 1880
    assert report["coverage_end_year"] >= 2024
    assert report["observation_count"] > 100
    assert report["latest_year"] >= 2024


def test_report_contains_climate_metrics():
    response = client.get("/report")
    report = response.json()

    assert isinstance(report["latest_anomaly_c"], float)
    assert isinstance(report["latest_five_year_average_c"], float)
    assert isinstance(report["trend_c_per_decade"], float)
    assert report["trend_c_per_decade"] > 0
    assert "increased" in report["interpretation"].lower()

def test_report_rejects_reversed_year_range():
    response = client.get(
        "/report?start_year=2025&end_year=1980"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "start_year must be earlier than or equal to end_year."
        )
    }


def test_report_requires_at_least_five_observations():
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
