"""
Builder 2 Model Inference Adapter for Veyra V2.

Adapts Veyra V2's ForecastIntelligenceService (LightGBM + Platt Sigmoid Calibration)
to conform to Builder 1's BaseModelService interface, supporting both in-process
execution and HTTP remote gateway execution.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

try:
    from backend.app.schemas.prediction import ReasonCode
except (ImportError, ModuleNotFoundError):
    from enum import Enum
    class ReasonCode(str, Enum):  # type: ignore
        SUCCESS = "SUCCESS"
        MODEL_NOT_READY = "MODEL_NOT_READY"
        MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
        FEATURES_NOT_READY = "FEATURES_NOT_READY"
        INTERNAL_ERROR = "INTERNAL_ERROR"
        QC_FAILED = "QC_FAILED"

from backend.app.services.base import BaseModelService, FeatureResult, ModelResult

logger = logging.getLogger(__name__)


class Builder2ModelAdapter(BaseModelService):
    """Production model adapter wrapping Veyra V2 ForecastIntelligenceService.

    Uses the verified veyra-v2-champion-lightgbm model with Platt Sigmoid calibration
    at the calibrated decision threshold of 0.060.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        model_dir: Optional[Union[str, Path]] = None,
        aggregation_method: str = "max",
        timeout_seconds: float = 10.0,
    ):
        self.api_url = (api_url or os.getenv("BUILDER2_API_URL") or os.getenv("BUILDER2_URL", "http://localhost:8001")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.aggregation_method = aggregation_method
        self.model_version: str = "veyra-v2-champion-lightgbm"
        self.threshold: float = 0.060
        self.is_ready: bool = True
        self.service = None

        # If HTTP URL is configured, use HTTP; otherwise fallback to local service if available
        if not self.api_url:
            self._initialize_local_service(model_dir)

    def _initialize_local_service(self, model_dir: Optional[Union[str, Path]] = None) -> None:
        """Attempt to load in-process V2 ForecastIntelligenceService."""
        try:
            from models.forecast_intelligence_service import ForecastIntelligenceService
            self.service = ForecastIntelligenceService(model_dir=model_dir)
            self.model_version = self.service.model_version
            self.threshold = float(self.service.operational_threshold)
            self.is_ready = True
            logger.info("Builder2ModelAdapter successfully loaded in-process V2 champion '%s'", self.model_version)
        except Exception as exc:
            logger.warning("Builder2ModelAdapter could not load in-process V2 artifacts: %s", exc)
            self.service = None
            self.is_ready = False

    def predict(self, feature_result: FeatureResult) -> ModelResult:
        """Compute calibrated forecast-bust probability using V2 champion (via HTTP or in-process)."""
        if not feature_result.is_ready or feature_result.error:
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.FEATURES_NOT_READY.value},
                error=feature_result.error or "Features not ready for model inference",
            )

        # Extract forecast rows
        forecast_rows = (
            feature_result.metadata.get("forecast_dataframe_rows")
            or feature_result.metadata.get("feature_matrix_rows")
        )
        if not forecast_rows:
            if feature_result.features:
                forecast_rows = [feature_result.features]
            else:
                return ModelResult(
                    probability=None,
                    model_version=self.model_version,
                    is_ready=False,
                    metadata={"status": ReasonCode.FEATURES_NOT_READY.value},
                    error="FeatureResult contains no feature data",
                )

        if self.api_url:
            return self._predict_http(forecast_rows, feature_result.location)
        elif self.service is not None:
            return self._predict_local(pd.DataFrame(forecast_rows))
        else:
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.MODEL_UNAVAILABLE.value},
                error="Builder 2 V2 model service is unavailable",
            )

    def _predict_http(self, forecast_rows: list, location: Optional[str]) -> ModelResult:
        location_id = location or "delhi"
        payload = {
            "forecast_data": forecast_rows,
            "location_id": location_id,
            "forecast_source": "NOAA_GEFS",
        }

        endpoint_url = f"{self.api_url}/api/forecast-risk"
        req_data = json.dumps(payload, default=str).encode("utf-8")
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

    def _predict_local(self, df_features: pd.DataFrame) -> ModelResult:
        try:
            results = self.service.evaluate_forecast(df_features)
            if not results:
                return ModelResult(
                    probability=None,
                    model_version=self.model_version,
                    is_ready=False,
                    metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                    error="V2 intelligence service returned zero results",
                )

            probabilities = [r.bust_probability for r in results]
            r_top = results[0]

            if self.aggregation_method == "max":
                agg_prob = float(np.max(probabilities))
            else:
                agg_prob = float(np.mean(probabilities))

            if not (0.0 <= agg_prob <= 1.0) or np.isnan(agg_prob) or np.isinf(agg_prob):
                return ModelResult(
                    probability=None,
                    model_version=self.model_version,
                    is_ready=False,
                    metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                    error=f"Model computed invalid probability: {agg_prob}",
                )

            metadata: Dict[str, Any] = {
                "status": ReasonCode.SUCCESS.value,
                "model_version": self.model_version,
                "decision_threshold": self.threshold,
                "risk_level": r_top.risk_level,
                "confidence_index": r_top.confidence_index,
                "structural_overconfidence": r_top.overconfidence_signal,
                "ood_score": r_top.ood_score,
                "stability_index": r_top.stability_index,
                "failure_fingerprint": r_top.provenance.get("failure_fingerprint", "NOMINAL"),
                "uncertainty_pct": r_top.provenance.get("prediction_uncertainty_pct", 3.37),
                "dominant_risk_drivers": [d.to_dict() for d in r_top.dominant_risk_drivers],
                "backend_service": "Builder2_Local_V2",
            }

            return ModelResult(
                probability=round(agg_prob, 4),
                model_version=self.model_version,
                is_ready=True,
                metadata=metadata,
            )
        except Exception as exc:
            logger.error("V2 local model inference failed: %s", exc)
            return ModelResult(
                probability=None,
                model_version=self.model_version,
                is_ready=False,
                metadata={"status": ReasonCode.INTERNAL_ERROR.value},
                error=f"Model inference failed: {exc}",
            )
