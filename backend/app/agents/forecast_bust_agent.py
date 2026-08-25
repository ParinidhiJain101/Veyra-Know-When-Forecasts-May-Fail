"""ForecastBustAgent Orchestration Layer.

Orchestrates:
Request -> Weather Data -> Feature Pipeline -> ML Model -> Safety/Abstention -> Response
"""
from typing import Optional
from backend.app.safety.abstention import SafetyAssessment, SafetyEvaluator
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.services.base import (
    BaseFeatureService,
    BaseModelService,
    BaseWeatherService,
    FeatureResult,
    ModelResult,
    WeatherDataResult,
)
from backend.app.services.feature_service import UnavailableFeatureService
from backend.app.services.model_service import UnavailableModelService
from backend.app.services.weather_service import UnavailableWeatherService


class ForecastBustAgent:
    """Orchestration agent for evaluating forecast bust likelihood.

    Coordinates data ingestion, feature generation, ML inference, and
    abstention/safety evaluation.
    """

    def __init__(
        self,
        weather_service: Optional[BaseWeatherService] = None,
        feature_service: Optional[BaseFeatureService] = None,
        model_service: Optional[BaseModelService] = None,
        safety_evaluator: Optional[SafetyEvaluator] = None,
    ):
        self.weather_service = weather_service or UnavailableWeatherService()
        self.feature_service = feature_service or UnavailableFeatureService()
        self.model_service = model_service or UnavailableModelService()
        self.safety_evaluator = safety_evaluator or SafetyEvaluator()

    def resolve_request(self, request: PredictionRequest) -> tuple[str, Optional[str]]:
        """Validate and resolve location and target date parameters."""
        return request.location.strip(), request.target_date

    def get_weather_data(
        self, location: str, target_date: Optional[str]
    ) -> WeatherDataResult:
        """Fetch weather and forecast atmospheric data."""
        return self.weather_service.fetch_forecast_data(location, target_date)

    def get_features(self, weather_data: WeatherDataResult) -> FeatureResult:
        """Extract engineered features from weather data."""
        return self.feature_service.extract_features(weather_data)

    def run_model(self, feature_result: FeatureResult) -> ModelResult:
        """Execute ML model inference for bust probability."""
        return self.model_service.predict(feature_result)

    def apply_safety(
        self,
        weather_result: WeatherDataResult,
        feature_result: FeatureResult,
        model_result: ModelResult,
    ) -> SafetyAssessment:
        """Evaluate safety, OOD, and abstention criteria."""
        return self.safety_evaluator.evaluate(
            weather_result, feature_result, model_result
        )

    def build_response(
        self,
        location: str,
        safety_assessment: SafetyAssessment,
        model_result: ModelResult,
        weather_result: WeatherDataResult,
    ) -> PredictionResponse:
        """Construct the final API response payload."""
        return PredictionResponse(
            location=location,
            bust_probability=safety_assessment.bust_probability,
            risk_level=safety_assessment.risk_level,
            trust_state=safety_assessment.trust_state,
            abstain=safety_assessment.abstain,
            reason_codes=safety_assessment.reason_codes,
            model_version=model_result.model_version,
            data_version=weather_result.data_version,
        )

    def analyze(self, request: PredictionRequest) -> PredictionResponse:
        """Main entry point orchestrating the end-to-end evaluation pipeline."""
        # 1. Resolve request
        location, target_date = self.resolve_request(request)

        # 2. Weather Data Collection
        weather_result = self.get_weather_data(location, target_date)

        # 3. Feature Engineering
        feature_result = self.get_features(weather_result)

        # 4. ML Model Prediction
        model_result = self.run_model(feature_result)

        # 5. Safety & Abstention Evaluation
        safety_assessment = self.apply_safety(
            weather_result, feature_result, model_result
        )

        # 6. Response Construction
        return self.build_response(
            location=location,
            safety_assessment=safety_assessment,
            model_result=model_result,
            weather_result=weather_result,
        )
