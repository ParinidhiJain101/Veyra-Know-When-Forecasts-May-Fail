"""
Veyra Evaluation & Generalization Framework.

Provides:
- LocationHeldOutSplitter: Location-held-out out-of-domain dataset splitting.
- ClimateHeldOutSplitter: Climate-held-out regime transfer dataset splitting.
- GeneralizationMetrics: Comprehensive classification, probabilistic, and risk-utility metrics.
- GeneralizationEvaluator: Out-of-domain evaluation and cross-validation orchestrator.
- GeneralizationResult: Structured result container.
"""

from evaluation.generalization import GeneralizationEvaluator, GeneralizationResult
from evaluation.metrics import GeneralizationMetrics
from evaluation.splits import ClimateHeldOutSplitter, HeldOutSplit, LocationHeldOutSplitter

__all__ = [
    "HeldOutSplit",
    "LocationHeldOutSplitter",
    "ClimateHeldOutSplitter",
    "GeneralizationMetrics",
    "GeneralizationEvaluator",
    "GeneralizationResult",
]
