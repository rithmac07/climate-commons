from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_report_returns_expected_data():
    response = client.get("/report")
    report = response.json()

    assert response.status_code == 200
    assert report["coverage_start_year"] == 2015
    assert report["coverage_end_year"] == 2024
    assert report["observation_count"] == 10
    assert report["latest_year"] == 2024
    assert report["latest_anomaly_c"] == 1.28
    assert "latest_five_year_average_c" in report
    assert "trend_c_per_decade" in report
    assert "interpretation" in report


def test_report_shows_positive_sample_trend():
    response = client.get("/report")
    report = response.json()

    assert response.status_code == 200
    assert report["trend_c_per_decade"] > 0
    assert "increased" in report["interpretation"].lower()
