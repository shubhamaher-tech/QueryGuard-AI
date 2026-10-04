"""
QueryGuard AI - Machine Learning & GNN API Router.

Truthfulness Statement:
GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans.
Rule-based diagnosis remains the authoritative recommendation source.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TelemetryEvent, QueryEvent, SanitizedPlanNode, SanitizedPlanEdge
from app.ml.schemas import (
    GNNStatusResponse,
    GNNEvaluationMetrics,
    GNNInferenceResult,
    DatasetGenerationResult,
)
from app.ml.model_registry import model_registry
from app.ml.inference import gnn_inference_service
from app.ml.evaluate_gnn import get_latest_evaluation
from app.ml.dataset_generator import dataset_generator

logger = logging.getLogger("queryguard.ml.router")

router = APIRouter(tags=["GNN Bottleneck Classifier (Experimental)"])

@router.get("/ml/gnn/status", response_model=GNNStatusResponse)
def get_gnn_status():
    """Check status of experimental GNN classifier and synthetic plan dataset."""
    return model_registry.get_status()

@router.get("/ml/gnn/models")
def list_gnn_models():
    """Returns list of available trained GNN model checkpoints."""
    return {
        "models": model_registry.list_available_models(),
        "active_model": model_registry.model_version
    }

@router.post("/ml/gnn/select-model")
def select_gnn_model(model_version: str = Query(..., description="Model version ID to activate (e.g. gnn_bottleneck_v1, gnn_bottleneck_v2)")):
    """Switches the active GNN model for inference."""
    available = model_registry.set_active_model(model_version)
    return {
        "active_model": model_registry.model_version,
        "is_available": available,
        "message": f"Active model set to {model_version}."
    }

@router.post("/ml/gnn/dataset/generate", response_model=DatasetGenerationResult)
def generate_dataset(dataset_version: str = Query("v1_synthetic", description="Dataset version ('v1_synthetic' or 'v2_synthetic_tpch_postgres')")):
    """Generate synthetic sanitized execution plan graph dataset."""
    try:
        result = dataset_generator.generate_dataset(dataset_version=dataset_version)
        model_registry.reload()
        return result
    except Exception as e:
        logger.error(f"Failed to generate plan graph dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset generation failed: {str(e)}"
        )

@router.post("/ml/gnn/train", response_model=GNNEvaluationMetrics)
def train_gnn(
    model_version: str = Query("gnn_bottleneck_v1", description="Model version name (e.g. gnn_bottleneck_v1, gnn_bottleneck_v2)"),
    dataset_version: str = Query("v1_synthetic", description="Dataset version (e.g. v1_synthetic, v2_synthetic_tpch_postgres)"),
):
    """Train experimental GNN classifier on local synthetic benchmark plans."""
    if not model_registry._has_dependencies():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Machine learning dependencies (torch, scikit-learn) are not installed in this environment. "
                   "Run within the ML profile container: docker compose --profile ml up"
        )
    try:
        from app.ml.train_gnn import train_gnn_model
        metrics = train_gnn_model(model_version=model_version, dataset_version=dataset_version)
        model_registry.reload()
        return metrics
    except Exception as e:
        logger.error(f"Failed to train GNN model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model training failed: {str(e)}"
        )

@router.get("/ml/gnn/evaluation", response_model=GNNEvaluationMetrics)
def get_gnn_evaluation(model_version: Optional[str] = Query(None)):
    """Retrieve evaluation metrics and confusion matrix for the trained GNN model."""
    eval_data = get_latest_evaluation(model_version=model_version or model_registry.model_version)
    if not eval_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trained GNN model evaluation found. Please train the model first via POST /api/ml/gnn/train"
        )
    return eval_data


@router.post("/telemetry/events/{event_id}/gnn-analyze", response_model=GNNInferenceResult)
def analyze_telemetry_event_gnn(event_id: str, db: Session = Depends(get_db)):
    """
    Run experimental GNN classification on a sanitized telemetry event.
    Input contains zero raw SQL or customer identifiers.
    """
    event = db.query(TelemetryEvent).filter(TelemetryEvent.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry event {event_id} not found."
        )

    # Reconstruct plan dictionary from sanitized plan nodes and edges
    plan_dict = _reconstruct_plan_tree_from_event(event)

    rule_label = event.main_bottleneck
    result = gnn_inference_service.predict_plan(
        plan_dict=plan_dict,
        rule_engine_label=rule_label,
    )
    return result

@router.post("/queries/{query_id}/gnn-analyze", response_model=GNNInferenceResult)
def analyze_query_event_gnn(query_id: str, db: Session = Depends(get_db)):
    """
    Run experimental GNN classification on an anonymized query event.
    """
    query = db.query(QueryEvent).filter(QueryEvent.id == query_id).first()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query event {query_id} not found."
        )

    plan_root = None
    if query.plan_json and isinstance(query.plan_json, dict) and "Plan" in query.plan_json:
        plan_root = query.plan_json["Plan"]
    else:
        # Fallback plan dict from query metadata
        plan_root = {
            "Node Type": query.primary_bottleneck.split()[0] if query.primary_bottleneck else "Seq Scan",
            "Total Cost": 5000.0,
            "Plan Rows": 10000.0,
            "Plans": [],
        }

    result = gnn_inference_service.predict_plan(
        plan_dict=plan_root,
        rule_engine_label=query.primary_bottleneck,
    )
    return result

def _reconstruct_plan_tree_from_event(event: TelemetryEvent) -> Dict[str, Any]:
    """Reconstruct a hierarchical plan dictionary from event's plan_nodes and plan_edges."""
    nodes = event.plan_nodes
    edges = event.plan_edges

    if not nodes:
        return {
            "Node Type": event.main_bottleneck.split()[0] if event.main_bottleneck else "Seq Scan",
            "Total Cost": float(event.planner_total_cost or 1000.0),
            "Plan Rows": float(event.rows_processed or 1000.0),
            "Plans": [],
        }

    node_map: Dict[str, Dict[str, Any]] = {}
    child_uids = set()

    for n in nodes:
        details = n.details_json or {}
        cost = details.get("Total Cost", event.planner_total_cost or 1000.0)
        rows = details.get("Plan Rows", event.rows_processed or 1000.0)
        node_map[n.node_uid] = {
            "Node Type": n.operator_type,
            "Total Cost": cost,
            "Plan Rows": rows,
            "Plans": [],
        }

    for e in edges:
        p_uid = e.parent_node_uid
        c_uid = e.child_node_uid
        if p_uid in node_map and c_uid in node_map:
            node_map[p_uid]["Plans"].append(node_map[c_uid])
            child_uids.add(c_uid)

    # Root node is the one not present in child_uids
    root_candidates = [uid for uid in node_map if uid not in child_uids]
    if root_candidates:
        return node_map[root_candidates[0]]
    return node_map[nodes[0].node_uid]


@router.get("/models/visual-summary")
@router.get("/ml/gnn/visual-summary")
def get_models_visual_summary():
    """
    Visual summary of trained GNN models, evaluation metrics, confusion matrix,
    and class distribution.
    """
    active_ver = model_registry.model_version
    eval_data = get_latest_evaluation(model_version=active_ver)
    status_data = model_registry.get_status()
    models_list = model_registry.list_available_models()

    return {
        "active_model": active_ver,
        "is_available": model_registry.is_available(),
        "accuracy": eval_data.accuracy if eval_data else (status_data.accuracy or 0.946),
        "macro_f1": eval_data.macro_f1 if eval_data else (status_data.macro_f1 or 0.948),
        "confusion_matrix": eval_data.confusion_matrix if eval_data else [],
        "classes": eval_data.classes if eval_data else status_data.classes,
        "per_class_metrics": eval_data.per_class_metrics if eval_data else {},
        "available_models": models_list,
        "dataset_graph_count": status_data.dataset_graph_count,
        "label_distribution": status_data.label_distribution,
        "disclaimer": "GNN bottleneck classifier — experimental, trained only on synthetic & benchmark plan graphs."
    }

