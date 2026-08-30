"""
Veyra Evaluation & Generalization Framework.

Provides:
- LocationHeldOutSplitter: Location-held-out out-of-domain dataset splitting.
- ClimateHeldOutSplitter: Climate-held-out regime transfer dataset splitting.
- GeneralizationMetrics: Comprehensive classification, probabilistic, and risk-utility metrics.
- GeneralizationEvaluator: Out-of-domain evaluation and cross-validation orchestrator.
- GeneralizationResult: Structured result container.
- ProbabilityCalibrator, ReliabilityAnalyzer: Strict train-only calibration and reliability analysis.
- EmpiricalEvidenceEngine, EmpiricalExperimentManifest: Full empirical benchmark orchestration.
- FeatureNoveltyDetector: Leakage-safe feature-space novelty and OOD detector.
- UncertaintyDecomposer: Operational uncertainty decomposition (aleatoric vs epistemic vs instability vs horizon).
- HistoricalFailureRetriever: Leakage-safe historical analogue and failure pattern retrieval.
- ForecastRiskAttributionEngine: Deterministic, model-compatible feature risk attribution.
- LocationRegimeProfiler: Station and meteorological regime reliability profiles.
- RiskConfidenceEngine: Self-confidence and risk-confidence quantification.
- CompositeFailureExplanation, ForecastFailureExplainer: Master failure explanation pipeline.
"""

from evaluation.attribution import ForecastRiskAttributionEngine
from evaluation.calibration import ProbabilityCalibrator, ReliabilityAnalyzer
from evaluation.empirical_engine import EmpiricalEvidenceEngine, EmpiricalExperimentManifest
from evaluation.explanation_engine import ForecastFailureExplainer
from evaluation.explanation_schema import CompositeFailureExplanation
from evaluation.failure_patterns import HistoricalFailureRetriever
from evaluation.generalization import GeneralizationEvaluator, GeneralizationResult, compute_dataset_content_hash
from evaluation.metrics import GeneralizationMetrics
from evaluation.novelty import FeatureNoveltyDetector
from evaluation.profiles import LocationRegimeProfiler
from evaluation.risk_confidence import RiskConfidenceEngine
from evaluation.splits import ClimateHeldOutSplitter, HeldOutSplit, LocationHeldOutSplitter
from evaluation.uncertainty import UncertaintyDecomposer

__all__ = [
    "HeldOutSplit",
    "LocationHeldOutSplitter",
    "ClimateHeldOutSplitter",
    "GeneralizationMetrics",
    "GeneralizationEvaluator",
    "GeneralizationResult",
    "compute_dataset_content_hash",
    "ProbabilityCalibrator",
    "ReliabilityAnalyzer",
    "EmpiricalEvidenceEngine",
    "EmpiricalExperimentManifest",
    "FeatureNoveltyDetector",
    "UncertaintyDecomposer",
    "HistoricalFailureRetriever",
    "ForecastRiskAttributionEngine",
    "LocationRegimeProfiler",
    "RiskConfidenceEngine",
    "CompositeFailureExplanation",
    "ForecastFailureExplainer",
]
