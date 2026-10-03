"""
QueryGuard AI - GNN Service Interface.

Provides a unified interface to the experimental GNN Bottleneck Classifier.
Truthfulness Statement:
Experimental GNN bottleneck classifier trained only on locally generated, sanitized synthetic PostgreSQL plan graphs.
It supports but does not replace rule-based diagnosis, HypoPG simulation, or DBA approval.
"""

from app.ml.inference import GNNInferenceService, gnn_inference_service
from app.ml.schemas import GNNInferenceResult, GNNStatusResponse, GNNEvaluationMetrics
from app.ml.model_registry import model_registry
from app.ml.evaluate_gnn import get_latest_evaluation

__all__ = [
    "GNNInferenceService",
    "gnn_inference_service",
    "model_registry",
    "get_latest_evaluation",
    "GNNInferenceResult",
    "GNNStatusResponse",
    "GNNEvaluationMetrics",
]
