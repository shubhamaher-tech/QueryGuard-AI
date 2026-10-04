"""
QueryGuard AI - Graph Neural Network (GNN) Classifier & Training Engine.

Trains a lightweight GraphSAGE/GCN model on sanitized execution plan graphs.
Uses pure PyTorch message passing for maximum reproducibility, CPU efficiency,
and zero external compiled C++ dependencies.

Truthfulness Statement:
GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans.
Rule-based diagnosis remains the authoritative recommendation source.
"""

import os
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

from app.ml.labels import (
    BOTTLENECK_CLASSES,
    LABEL_TO_ID,
    ID_TO_LABEL,
    LABEL_METADATA,
)
from app.ml.schemas import GNNEvaluationMetrics, PerClassMetric
from app.ml.feature_encoder import NODE_FEATURE_DIM

logger = logging.getLogger("queryguard.ml.train_gnn")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "models"
DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "plan_graph_dataset" / "dataset.json"

class GraphConvLayer(nn.Module):
    """
    Lightweight Graph Convolutional Layer (GraphSAGE-style aggregation).
    h_v = ReLU(W_self * h_v + W_neigh * mean_{u in N(v)}(h_u))
    """
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.linear_self = nn.Linear(in_features, out_features, bias=True)
        self.linear_neigh = nn.Linear(in_features, out_features, bias=False)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        x: [N, in_features]
        edge_index: [2, E] where edge_index[0] is source and edge_index[1] is target
        """
        num_nodes = x.size(0)
        h_self = self.linear_self(x)

        if edge_index.size(1) == 0:
            return F.relu(h_self)

        src, dst = edge_index[0], edge_index[1]
        # Aggregate neighbor messages into target nodes
        messages = x[src]  # [E, in_features]
        aggregated = torch.zeros(num_nodes, x.size(1), device=x.device, dtype=x.dtype)
        # Count incoming degrees for mean pooling
        degree = torch.zeros(num_nodes, 1, device=x.device, dtype=x.dtype)
        
        aggregated.index_add_(0, dst, messages)
        degree.index_add_(0, dst, torch.ones(src.size(0), 1, device=x.device, dtype=x.dtype))
        degree = torch.clamp(degree, min=1.0)
        mean_neighbors = aggregated / degree

        h_neigh = self.linear_neigh(mean_neighbors)
        return F.relu(h_self + h_neigh)

class PlanGNNClassifier(nn.Module):
    """
    Graph Neural Network for execution plan bottleneck classification.
    """
    def __init__(self, in_dim: int = NODE_FEATURE_DIM, hidden_dim: int = 64, num_classes: int = len(BOTTLENECK_CLASSES)):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.node_encoder = nn.Linear(in_dim, hidden_dim)
        self.conv1 = GraphConvLayer(hidden_dim, hidden_dim)
        self.conv2 = GraphConvLayer(hidden_dim, hidden_dim)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(0.2)

        # Global readout: Mean + Max pooling -> hidden_dim * 2
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes)
        )

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Input single plan graph:
        x: [N, in_dim]
        edge_index: [2, E]
        Output: logits [1, num_classes]
        """
        h = F.relu(self.node_encoder(x))
        h1 = self.norm1(self.conv1(h, edge_index))
        h2 = self.norm2(self.conv2(h1, edge_index))
        h2 = self.dropout(h2)

        # Global graph readout
        mean_pool = torch.mean(h2, dim=0, keepdim=True)  # [1, hidden_dim]
        max_pool, _ = torch.max(h2, dim=0, keepdim=True)  # [1, hidden_dim]
        graph_repr = torch.cat([mean_pool, max_pool], dim=1)  # [1, hidden_dim * 2]

        logits = self.classifier(graph_repr)
        return logits

def train_gnn_model(
    dataset_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    model_version: str = "gnn_bottleneck_v1",
    dataset_version: str = "v1_synthetic",
    epochs: int = 40,
    lr: float = 0.005,
    random_seed: Optional[int] = None,
) -> GNNEvaluationMetrics:
    """
    Train PlanGNNClassifier on sanitized plan dataset and persist artifacts.
    Supports versioned models (e.g. gnn_bottleneck_v1, gnn_bottleneck_v2).
    """
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, confusion_matrix

    actual_seed = random_seed if random_seed is not None else (int(datetime.datetime.utcnow().timestamp()) % 1000 + 7)
    torch.manual_seed(actual_seed)
    np.random.seed(actual_seed)


    dataset_file = dataset_path or DEFAULT_DATASET_PATH
    out_dir = output_dir or DEFAULT_MODEL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_file.exists():
        raise FileNotFoundError(f"Plan dataset not found at {dataset_file}. Run dataset generator first.")

    with open(dataset_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    if len(records) < 10:
        raise ValueError(f"Dataset too small for training ({len(records)} samples). Generate at least 100 samples.")

    # Parse into tensors and labels
    samples = []
    labels = []
    for r in records:
        x = torch.tensor(r["node_features"], dtype=torch.float32)
        edge_index = torch.tensor(r["edge_index"], dtype=torch.long)
        y = LABEL_TO_ID.get(r["label"], 0)
        samples.append((x, edge_index))
        labels.append(y)

    indices = list(range(len(samples)))
    train_idx, test_idx = train_test_split(indices, test_size=0.30, random_state=random_seed, stratify=labels)
    val_idx, test_idx = train_test_split(test_idx, test_size=0.50, random_state=random_seed, stratify=[labels[i] for i in test_idx])

    train_data = [(samples[i], labels[i]) for i in train_idx]
    val_data = [(samples[i], labels[i]) for i in val_idx]
    test_data = [(samples[i], labels[i]) for i in test_idx]

    model = PlanGNNClassifier(in_dim=NODE_FEATURE_DIM, hidden_dim=64, num_classes=len(BOTTLENECK_CLASSES))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    best_val_loss = float("inf")
    best_weights = None

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        np.random.shuffle(train_data)

        for (x, edge_index), y in train_data:
            optimizer.zero_grad()
            logits = model(x, edge_index)
            target = torch.tensor([y], dtype=torch.long)
            loss = criterion(logits, target)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for (x, edge_index), y in val_data:
                logits = model(x, edge_index)
                target = torch.tensor([y], dtype=torch.long)
                loss = criterion(logits, target)
                val_loss += loss.item()

        avg_val_loss = val_loss / max(1, len(val_data))
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    # Load best weights
    if best_weights:
        model.load_state_dict(best_weights)

    # Final Test Set Evaluation
    model.eval()
    test_preds = []
    test_targets = []
    with torch.no_grad():
        for (x, edge_index), y in test_data:
            logits = model(x, edge_index)
            pred = torch.argmax(logits, dim=1).item()
            test_preds.append(pred)
            test_targets.append(y)

    acc = float(accuracy_score(test_targets, test_preds))
    macro_f1 = float(f1_score(test_targets, test_preds, average="macro", zero_division=0))
    conf_mat = confusion_matrix(test_targets, test_preds, labels=list(range(len(BOTTLENECK_CLASSES)))).tolist()

    precision, recall, f1, support = precision_recall_fscore_support(
        test_targets, test_preds, labels=list(range(len(BOTTLENECK_CLASSES))), zero_division=0
    )

    per_class_metrics: Dict[str, PerClassMetric] = {}
    for i, label in enumerate(BOTTLENECK_CLASSES):
        per_class_metrics[label] = PerClassMetric(
            precision=float(precision[i]),
            recall=float(recall[i]),
            f1_score=float(f1[i]),
            support=int(support[i]),
        )

    metrics = GNNEvaluationMetrics(
        model_version=model_version,
        dataset_version=dataset_version,
        total_samples=len(samples),
        train_samples=len(train_data),
        val_samples=len(val_data),
        test_samples=len(test_data),
        accuracy=acc,
        macro_f1=macro_f1,
        per_class_metrics=per_class_metrics,
        confusion_matrix=conf_mat,
        classes=BOTTLENECK_CLASSES,
        trained_at=datetime.datetime.utcnow().isoformat() + "Z",
        random_seed=actual_seed,
    )

    # Save model checkpoint
    model_path = out_dir / f"{model_version}.pt"
    torch.save(model.state_dict(), model_path)

    # Save metadata JSON
    metadata_path = out_dir / f"{model_version}.metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metrics.model_dump(), f, indent=2)

    logger.info(f"Model {model_version} saved to {model_path} with Test Accuracy: {acc:.3f}, Macro F1: {macro_f1:.3f}")
    return metrics
