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

def get_latest_evaluation(model_dir: Optional[Path] = None) -> Optional[GNNEvaluationMetrics]:
    """Load latest evaluation metrics from metadata.json."""
    m_dir = model_dir or DEFAULT_MODEL_DIR
    metadata_file = m_dir / "gnn_bottleneck_v1.metadata.json"
    if not metadata_file.exists():
        return None
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return GNNEvaluationMetrics(**data)
    except Exception:
        return None
