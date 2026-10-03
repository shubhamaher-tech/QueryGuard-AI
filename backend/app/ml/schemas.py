"""
QueryGuard AI - Pydantic Schemas for GNN Dataset, Training, Evaluation, and Inference.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GraphFeatures(BaseModel):
    plan_depth: int = 0
    join_count: int = 0
    sequential_scan_count: int = 0
    nested_loop_count: int = 0
    sort_count: int = 0
    aggregate_count: int = 0
    cost_bucket: str = "MEDIUM"
    total_cost: float = 0.0
    spill_risk: bool = False

class PlanGraphRecord(BaseModel):
    graph_id: str
    label: str
    node_features: List[List[float]]
    edge_index: List[List[int]]  # [[source_nodes...], [target_nodes...]]
    node_operators: Optional[List[str]] = Field(default_factory=list)
    graph_features: GraphFeatures
    privacy_check_passed: bool = True
    dataset_version: str = "v1_synthetic"

class PredictionProbability(BaseModel):
    label: str
    probability: float
    severity: str = "MEDIUM"

class GNNInferenceResult(BaseModel):
    model_available: bool
    predicted_label: Optional[str] = None
    predicted_bottleneck: Optional[str] = None
    confidence: float = 0.0
    top_3_predictions: List[PredictionProbability] = Field(default_factory=list)
    top_predictions: List[PredictionProbability] = Field(default_factory=list)
    model_version: str = "gnn_bottleneck_v1"
    dataset_version: str = "v1_synthetic_postgres"
    is_low_confidence: bool = False
    confidence_threshold: float = 0.65
    rule_engine_label: Optional[str] = None
    rule_disagreement: bool = False
    agreement_status: str = "AGREES_WITH_RULE_ENGINE"
    highlighted_node_indices: List[int] = Field(default_factory=list)
    usage_policy: str = (
        "Secondary experimental evidence only. Rule-based diagnosis and PostgreSQL simulation remain authoritative."
    )
    privacy_status: str = "Inference used sanitized plan graph features only."
    disclaimer: str = (
        "GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans. "
        "Rule-based diagnosis remains the authoritative recommendation source."
    )

class PerClassMetric(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int

class GNNEvaluationMetrics(BaseModel):
    model_version: str
    dataset_version: str
    total_samples: int
    train_samples: int
    val_samples: int
    test_samples: int
    accuracy: float
    macro_f1: float
    per_class_metrics: Dict[str, PerClassMetric]
    confusion_matrix: List[List[int]]
    classes: List[str]
    trained_at: str
    random_seed: int = 42
    disclaimer: str = (
        "Synthetic benchmark evaluation metrics only. Not evaluated against production customer workloads."
    )

class GNNStatusResponse(BaseModel):
    model_available: bool
    ml_dependencies_installed: bool
    model_version: str
    dataset_version: str
    dataset_graph_count: int
    label_distribution: Dict[str, int] = Field(default_factory=dict)
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    trained_at: Optional[str] = None
    confidence_threshold: float = 0.65
    disclaimer: str = (
        "GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans."
    )

class DatasetGenerationResult(BaseModel):
    dataset_version: str
    total_graphs_generated: int
    label_distribution: Dict[str, int]
    artifacts_directory: str
    privacy_check_passed: bool
    message: str
