"""Unit tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError
from backend.app.schemas.health import HealthResponse
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    ReasonCode,
    RiskLevel,
    TrustState,
)


def test_health_response_defaults():
    """Test default values of HealthResponse schema."""
    resp = HealthResponse()
    assert resp.status == "ok"
    assert resp.service == "forecast-bust-sentinel"
    assert resp.version == "0.1.0"


def test_prediction_request_valid():
    """Test valid PredictionRequest creation."""
    req = PredictionRequest(location="San Francisco", target_date="2026-09-10")
    assert req.location == "San Francisco"
    assert req.target_date == "2026-09-10"


def test_prediction_request_empty_location_raises():
    """Test that empty string or whitespace raises ValidationError."""
    with pytest.raises(ValidationError):
        PredictionRequest(location="")

    with pytest.raises(ValidationError):
        PredictionRequest(location="   ")


def test_prediction_response_defaults():
    """Test PredictionResponse defaults for unavailable state."""
    resp = PredictionResponse(location="Mumbai")
    assert resp.location == "Mumbai"
    assert resp.bust_probability is None
    assert resp.risk_level is None
    assert resp.trust_state == TrustState.UNAVAILABLE
    assert resp.abstain is True
    assert resp.reason_codes == [ReasonCode.MODEL_NOT_READY.value]
    assert resp.model_version is None
    assert resp.data_version is None


def test_prediction_response_json_serialization():
    """Test that PredictionResponse serializes properly to dict and JSON."""
    resp = PredictionResponse(location="Paris")
    data = resp.model_dump()
    assert data["location"] == "Paris"
    assert data["bust_probability"] is None
    assert data["trust_state"] == "UNAVAILABLE"
    assert data["abstain"] is True
