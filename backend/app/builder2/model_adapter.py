"""Builder 2 HTTP Model Inference Adapter for Veyra.

Communicates with Builder 2's authoritative V2 ForecastIntelligenceService
over HTTP/REST (default: http://localhost:8001/api/forecast-risk).

Receives calibrated bust probabilities, operational risk tiers, reliability indices,
structural overconfidence, OOD scores, trajectory stability, analytical failure fingerprints,
and physical risk drivers from the V2 Champion LightGBM model.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import urllib.request
import urllib.error
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.schemas.prediction import ReasonCode
from backend.app.services.base import BaseModelService, FeatureResult, ModelResult

logger = logging.getLogger(__name__)


class Builder2ModelAdapter(BaseModelService):
    """Production model adapter communicating with Builder 2 V2 HTTP Service.

    Uses the verified veyra-v2-champion-lightgbm model with Platt Sigmoid calibration
    at the calibrated decision threshold of 0.060.

    When the Builder 2 service is unavailable or unconfigured, safely abstains with
    is_ready=False and status=MODEL_UNAVAILABLE without falling back to legacy models.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
        aggregation_method: str = "max",
    ):
        self.api_url = (api_url or settings.BUILDER2_API_URL or os.getenv("BUILDER2_URL", "http://localhost:8001")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.aggregation_method = aggregation_method
        self.model_version: str = "veyra-v2-champion-lightgbm"
        self.threshold: float = 0.060
        self.is_ready: bool = True

    def predict(self, feature_result: FeatureResult) -> ModelResult:
        """Compute calibrated forecast-bust probability via Builder 2 HTTP Service."""
        if not feature_result.is_ready or feature_result.error:
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.FEATURES_NOT_READY.value},
                error=feature_result.error or "Features not ready for model inference",
            )

        # Extract forecast matrix rows or standardized dataframe rows
        matrix_rows = (
            feature_result.metadata.get("forecast_dataframe_rows")
            or feature_result.metadata.get("feature_matrix_rows")
        )
        if matrix_rows and isinstance(matrix_rows, list):
            forecast_data = matrix_rows
        elif feature_result.features:
            forecast_data = [feature_result.features]
        else:
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.FEATURES_NOT_READY.value},
                error="FeatureResult contains no feature data",
            )

        location_id = feature_result.location or "delhi"
        payload = {
            "forecast_data": forecast_data,
            "location_id": location_id,
            "forecast_source": "NOAA_GEFS",
        }

        endpoint_url = f"{self.api_url}/api/forecast-risk"
        req_data = json.dumps(payload).encode("utf-8")
        http_req = urllib.request.Request(
            endpoint_url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "VeyraBuilder1/2.0"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(http_req, timeout=self.timeout_seconds) as response:
                if response.status != 200:
                    return ModelResult(
                        probability=None,
                        model_version=self.model_version,
                        is_ready=False,
                        metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                        error=f"Builder 2 HTTP service returned status {response.status}",
                    )
                resp_bytes = response.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))

            forecasts = resp_json.get("forecasts", [])
            if not forecasts:
                return ModelResult(
                    probability=None,
                    model_version=self.model_version,
                    is_ready=False,
                    metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                    error="Builder 2 returned zero forecast risk predictions",
                )

            probabilities = [f.get("bust_probability", 0.0) for f in forecasts]
            top_f = forecasts[0]

            if self.aggregation_method == "max":
                agg_prob = float(np.max(probabilities))
            else:
                agg_prob = float(np.mean(probabilities))

            # Strictly enforce probability bounds [0.0, 1.0]
            if not (0.0 <= agg_prob <= 1.0) or np.isnan(agg_prob) or np.isinf(agg_prob):
                return ModelResult(
                    probability=None,
                    model_version=self.model_version,
                    is_ready=False,
                    metadata={"status": ReasonCode.QC_FAILED.value},
                    error=f"Model computed invalid probability: {agg_prob}",
                )

            model_ver = resp_json.get("model_version", self.model_version)
            thresh = float(resp_json.get("decision_threshold", self.threshold))

            metadata: Dict[str, Any] = {
                "status": ReasonCode.SUCCESS.value,
                "model_version": model_ver,
                "decision_threshold": thresh,
                "risk_level": top_f.get("risk_level", "LOW"),
                "confidence_index": top_f.get("confidence_index", 100.0),
                "structural_overconfidence": top_f.get("structural_overconfidence", 0.0),
                "ood_score": top_f.get("ood_score", 0.0),
                "stability_index": top_f.get("stability_index", 100.0),
                "failure_fingerprint": top_f.get("failure_fingerprint", "NOMINAL"),
                "uncertainty_pct": top_f.get("uncertainty_pct", 3.37),
                "dominant_risk_drivers": top_f.get("dominant_risk_drivers", []),
                "backend_service": "Builder2_HTTP_V2",
            }

            return ModelResult(
                probability=round(agg_prob, 4),
                model_version=model_ver,
                is_ready=True,
                metadata=metadata,
            )

        except urllib.error.URLError as url_err:
            logger.error("Builder 2 HTTP connection error to %s: %s", endpoint_url, url_err)
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.MODEL_UNAVAILABLE.value},
                error=f"Builder 2 HTTP service unavailable at {self.api_url}: {url_err}",
            )
        except Exception as exc:
            logger.error("Builder 2 inference failed: %s", exc)
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                error=f"Builder 2 inference failed: {exc}",
            )
