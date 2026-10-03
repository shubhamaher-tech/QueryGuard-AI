"""
QueryGuard AI - Privacy-Preserving GNN Inference Engine.

Evaluates sanitized execution-plan graphs through the trained GNN model.
Guarantees:
- Never receives raw SQL or raw identifiers.
- Graceful fallback when model or ML dependencies are absent.
- Respects the 0.65 confidence threshold.
- Preserves deterministic rule engine authority.
"""

import logging
from typing import Dict, Any, List, Optional

from app.ml.labels import (
    BOTTLENECK_CLASSES,
    ID_TO_LABEL,
    LABEL_METADATA,
)
from app.ml.schemas import GNNInferenceResult, PredictionProbability
from app.ml.model_registry import model_registry
from app.ml.graph_builder import build_graph_from_plan_dict

logger = logging.getLogger("queryguard.ml.inference")

class GNNInferenceService:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def predict_plan(
        self,
        plan_dict: Optional[Dict[str, Any]] = None,
        rule_engine_label: Optional[str] = None,
        highlighted_node_indices: Optional[List[int]] = None,
        plan_data: Optional[Dict[str, Any]] = None,
    ) -> GNNInferenceResult:
        """
        Run GNN inference on a plan dictionary (either from plan_json or sanitized telemetry node tree).
        Input must already be sanitized or structural.
        """
        target_plan = plan_dict if plan_dict is not None else (plan_data or {})
        if not model_registry.is_available():
            return GNNInferenceResult(
                model_available=False,
                predicted_label=None,
                predicted_bottleneck=None,
                confidence=0.0,
                top_3_predictions=[],
                top_predictions=[],
                model_version=model_registry.model_version,
                dataset_version="v1_synthetic_postgres",
                is_low_confidence=True,
                confidence_threshold=self.confidence_threshold,
                rule_engine_label=rule_engine_label,
                rule_disagreement=False,
                agreement_status="MODEL_UNAVAILABLE",
                highlighted_node_indices=highlighted_node_indices or [],
                disclaimer=(
                    "Experimental GNN classifier: model artifact or ML dependencies not loaded. "
                    "Rule-based plan diagnosis remains active and authoritative."
                ),
            )

        try:
            import torch
            import torch.nn.functional as F

            model = model_registry.get_model()
            node_features, edge_index, node_operators, graph_features = build_graph_from_plan_dict(target_plan)

            x = torch.tensor(node_features, dtype=torch.float32)
            edge_idx = torch.tensor(edge_index, dtype=torch.long)

            with torch.no_grad():
                logits = model(x, edge_idx)
                probs = F.softmax(logits, dim=1).squeeze(0)

            # Top 3 predictions
            top_k_probs, top_k_indices = torch.topk(probs, min(3, len(BOTTLENECK_CLASSES)))
            top_3: List[PredictionProbability] = []
            for p, idx in zip(top_k_probs.tolist(), top_k_indices.tolist()):
                lbl = ID_TO_LABEL.get(idx, "UNKNOWN")
                sev = LABEL_METADATA.get(lbl, {}).get("severity", "MEDIUM")
                top_3.append(PredictionProbability(label=lbl, probability=round(p, 4), severity=sev))

            best_prob = float(top_k_probs[0].item())
            best_label = ID_TO_LABEL.get(int(top_k_indices[0].item()), "UNKNOWN")
            is_low_conf = best_prob < self.confidence_threshold

            # Check disagreement with rule engine
            rule_disagreement = False
            if rule_engine_label:
                # Normalize rule engine string (e.g. "Sequential Scan" vs "SEQ_SCAN_BOTTLENECK")
                rule_norm = rule_engine_label.upper().replace(" ", "_")
                if "SEQ" in rule_norm and "SEQ" not in best_label:
                    rule_disagreement = True
                elif "NEST" in rule_norm and "NEST" not in best_label:
                    rule_disagreement = True
                elif "SORT" in rule_norm and "SORT" not in best_label:
                    rule_disagreement = True

            # Highlight nodes (e.g. index 0 root or scan/sort operators)
            node_highlights = highlighted_node_indices or []
            if not node_highlights:
                # Default heuristic: highlight bottleneck nodes
                for i, op in enumerate(node_operators):
                    if "seq scan" in op.lower() or "sort" in op.lower() or "nested loop" in op.lower():
                        node_highlights.append(i)

            agreement_status = "AGREES_WITH_RULE_ENGINE"
            if is_low_conf:
                agreement_status = "LOW_CONFIDENCE"
            elif rule_disagreement:
                agreement_status = "DIFFERS_FROM_RULE_ENGINE"

            return GNNInferenceResult(
                model_available=True,
                predicted_label=best_label,
                predicted_bottleneck=best_label,
                confidence=round(best_prob, 4),
                top_3_predictions=top_3,
                top_predictions=top_3,
                model_version=model_registry.model_version,
                dataset_version="v1_synthetic_postgres",
                is_low_confidence=is_low_conf,
                confidence_threshold=self.confidence_threshold,
                rule_engine_label=rule_engine_label,
                rule_disagreement=rule_disagreement,
                agreement_status=agreement_status,
                highlighted_node_indices=node_highlights,
                disclaimer=(
                    "GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans. "
                    "Rule-based diagnosis remains the authoritative recommendation source. "
                    "Highlighted nodes are based on structural plan analysis. Full GNNExplainer attribution is future work."
                ),
            )

        except Exception as e:
            logger.warning(f"GNN inference execution failed: {e}")
            return GNNInferenceResult(
                model_available=False,
                predicted_label=None,
                predicted_bottleneck=None,
                confidence=0.0,
                top_3_predictions=[],
                top_predictions=[],
                model_version=model_registry.model_version,
                dataset_version="v1_synthetic_postgres",
                is_low_confidence=True,
                confidence_threshold=self.confidence_threshold,
                rule_engine_label=rule_engine_label,
                rule_disagreement=False,
                agreement_status="MODEL_UNAVAILABLE",
                disclaimer=f"Inference error: {e}. Falling back safely to deterministic rules.",
            )

# Module singleton
gnn_inference_service = GNNInferenceService()
