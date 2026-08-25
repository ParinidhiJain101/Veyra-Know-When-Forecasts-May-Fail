"""Tests for POST /v1/predict endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_predict_valid_location_accepted(client: TestClient):
    """Test that POST /v1/predict accepts a valid location with HTTP 200."""
    response = client.post("/v1/predict", json={"location": "London"})
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "London"


def test_predict_bust_probability_is_null_when_model_unavailable(client: TestClient):
    """Test that bust_probability is strictly null (None) while model is unavailable."""
    response = client.post("/v1/predict", json={"location": "Tokyo"})
    assert response.status_code == 200
    data = response.json()
    assert data["bust_probability"] is None
    assert data["risk_level"] is None


def test_predict_abstain_is_true_when_model_unavailable(client: TestClient):
    """Test that abstain flag is True while model is unavailable."""
    response = client.post("/v1/predict", json={"location": "Paris"})
    assert response.status_code == 200
    data = response.json()
    assert data["abstain"] is True


def test_predict_trust_state_is_unavailable(client: TestClient):
    """Test that trust_state is UNAVAILABLE while model is unavailable."""
    response = client.post("/v1/predict", json={"location": "Berlin"})
    assert response.status_code == 200
    data = response.json()
    assert data["trust_state"] == "UNAVAILABLE"


def test_predict_model_not_ready_in_reason_codes(client: TestClient):
    """Test that MODEL_NOT_READY is present in reason_codes list."""
    response = client.post("/v1/predict", json={"location": "New York"})
    assert response.status_code == 200
    data = response.json()
    assert "MODEL_NOT_READY" in data["reason_codes"]


def test_predict_with_optional_target_date(client: TestClient):
    """Test prediction request with an optional target_date provided."""
    response = client.post(
        "/v1/predict",
        json={"location": "Sydney", "target_date": "2026-09-01"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Sydney"
    assert data["abstain"] is True
    assert data["bust_probability"] is None


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {},  # Missing location
        {"location": ""},  # Empty string
        {"location": "   "},  # Whitespace only
        {"location": None},  # Null location
    ],
)
def test_predict_invalid_request_rejected(client: TestClient, invalid_payload: dict):
    """Test that invalid/empty requests are rejected with HTTP 422 Unprocessable Entity."""
    response = client.post("/v1/predict", json=invalid_payload)
    assert response.status_code == 422
