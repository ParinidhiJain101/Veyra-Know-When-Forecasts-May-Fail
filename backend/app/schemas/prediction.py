"""Prediction request and response schemas."""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TrustState(str, Enum):
    """Trust state of the forecast bust assessment."""

    UNAVAILABLE = "UNAVAILABLE"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MODERATE_CONFIDENCE = "MODERATE_CONFIDENCE"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    ABSTAINED = "ABSTAINED"


class RiskLevel(str, Enum):
    """Categorical risk level of forecast bust."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReasonCode(str, Enum):
    """Standardized reason codes explaining trust state and abstention."""

    MODEL_NOT_READY = "MODEL_NOT_READY"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    OOD_DETECTED = "OOD_DETECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    EXTREME_VOLATILITY = "EXTREME_VOLATILITY"
    SUCCESS = "SUCCESS"


class PredictionRequest(BaseModel):
    """Forecast bust prediction request payload."""

    location: str = Field(
        ...,
        min_length=1,
        description="Location name, city, or coordinates for forecast evaluation",
        examples=["London", "Tokyo", "New York"],
    )
    target_date: Optional[str] = Field(
        default=None,
        description="Optional target forecast date (ISO format YYYY-MM-DD)",
        examples=["2026-09-01"],
    )

    @field_validator("location")
    @classmethod
    def validate_location_not_blank(cls, v: str) -> str:
        """Ensure location is not just whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("location cannot be empty or whitespace only")
        return stripped


class PredictionResponse(BaseModel):
    """Forecast bust prediction response payload."""

    location: str = Field(
        ...,
        description="Location requested for forecast evaluation",
    )
    bust_probability: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated probability (0.0 - 1.0) of forecast bust. null when unavailable or abstained.",
    )
    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Categorical risk level for forecast failure",
    )
    trust_state: TrustState = Field(
        default=TrustState.UNAVAILABLE,
        description="Assessment of model reliability for this forecast instance",
    )
    abstain: bool = Field(
        default=True,
        description="Whether the sentinel abstains from making a prediction",
    )
    reason_codes: list[str] = Field(
        default_factory=lambda: [ReasonCode.MODEL_NOT_READY.value],
        description="List of reason codes explaining the prediction or abstention decision",
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Identifier of the ML model used, if available",
    )
    data_version: Optional[str] = Field(
        default=None,
        description="Identifier of the weather data pipeline version used, if available",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "location": "London",
                "bust_probability": None,
                "risk_level": None,
                "trust_state": "UNAVAILABLE",
                "abstain": True,
                "reason_codes": ["MODEL_NOT_READY"],
                "model_version": None,
                "data_version": None,
            }
        }
    }
