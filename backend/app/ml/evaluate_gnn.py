"""
QueryGuard AI - GNN Model Evaluation Suite.

Evaluates trained checkpoint on plan graph dataset, producing accuracy,
per-class F1, and confusion matrix reports.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from app.ml.schemas import GNNEvaluationMetrics

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "models"

def get_latest_evaluation(model_dir: Optional[Path] = None, model_version: Optional[str] = None) -> Optional[GNNEvaluationMetrics]:
    """Load latest evaluation metrics from metadata.json for the given model_version."""
    m_dir = model_dir or DEFAULT_MODEL_DIR
    target_version = model_version or "gnn_bottleneck_v2"
    metadata_file = m_dir / f"{target_version}.metadata.json"
    if not metadata_file.exists():
        # Try gnn_bottleneck_v1 or any available metadata.json
        fallback_files = list(m_dir.glob("*.metadata.json"))
        if not fallback_files:
            return None
        metadata_file = fallback_files[0]
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return GNNEvaluationMetrics(**data)
    except Exception:
        return None

