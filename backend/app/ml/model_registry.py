"""
QueryGuard AI - GNN Model Registry & Lifecycle Manager.

Manages model loading, status introspection, and graceful fallback when
ML dependencies or checkpoints are missing.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from app.ml.schemas import GNNStatusResponse
from app.ml.labels import BOTTLENECK_CLASSES

logger = logging.getLogger("queryguard.ml.model_registry")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "models"
DEFAULT_DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "plan_graph_dataset"

class GNNModelRegistry:
    def __init__(self, model_dir: Optional[Path] = None, dataset_dir: Optional[Path] = None):
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.dataset_dir = dataset_dir or DEFAULT_DATASET_DIR
        self.model_version = "gnn_bottleneck_v1"
        self._model = None
        self._metadata: Optional[Dict[str, Any]] = None
        self.confidence_threshold = 0.65
        self._load_model()

    def _has_dependencies(self) -> bool:
        try:
            import torch
            import sklearn
            return True
        except ImportError:
            return False

    def _load_model(self):
        """Safely load model weights and metadata if present."""
        metadata_path = self.model_dir / f"{self.model_version}.metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except Exception as e:
                logger.debug(f"Failed to read metadata json: {e}")

        if not self._has_dependencies():
            logger.info("ML dependencies (torch, sklearn) not installed. GNN will operate in fallback mode.")
            self._model = None
            return

        model_path = self.model_dir / f"{self.model_version}.pt"

        if not model_path.exists() or not metadata_path.exists():
            logger.info(f"GNN model artifact not found at {model_path}. Model status: NOT_TRAINED.")
            self._model = None
            self._metadata = None
            return

        try:
            import torch
            from app.ml.train_gnn import PlanGNNClassifier
            from app.ml.feature_encoder import NODE_FEATURE_DIM

            with open(metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            model = PlanGNNClassifier(in_dim=NODE_FEATURE_DIM, hidden_dim=64, num_classes=len(BOTTLENECK_CLASSES))
            state_dict = torch.load(model_path, map_location="cpu")
            model.load_state_dict(state_dict)
            model.eval()
            self._model = model
            logger.info(f"Loaded GNN model {self.model_version} successfully.")
        except Exception as e:
            logger.warning(f"Failed to load GNN model artifact: {e}")
            self._model = None
            self._metadata = None

    def reload(self):
        """Reload model from disk after training."""
        self._load_model()

    def is_available(self) -> bool:
        return self._model is not None and self._has_dependencies()

    def get_model(self):
        return self._model

    def get_status(self) -> GNNStatusResponse:
        """Inspect status of GNN model and plan dataset."""
        deps_installed = self._has_dependencies()
        available = self.is_available()

        dataset_count = 0
        label_dist: Dict[str, int] = {}
        summary_path = self.dataset_dir / "summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                    dataset_count = s_data.get("total_graphs", 0)
                    label_dist = s_data.get("label_distribution", {})
            except Exception:
                pass

        accuracy = None
        macro_f1 = None
        trained_at = None
        if self._metadata:
            accuracy = self._metadata.get("accuracy")
            macro_f1 = self._metadata.get("macro_f1")
            trained_at = self._metadata.get("trained_at")

        return GNNStatusResponse(
            model_available=available,
            ml_dependencies_installed=deps_installed,
            model_version=self.model_version,
            dataset_version=(self._metadata.get("dataset_version", "v1_synthetic") if self._metadata else "v1_synthetic"),
            dataset_graph_count=dataset_count,
            label_distribution=label_dist,
            accuracy=accuracy,
            macro_f1=macro_f1,
            trained_at=trained_at,
            confidence_threshold=self.confidence_threshold,
            disclaimer=(
                "GNN bottleneck classifier — experimental, trained only on synthetic sanitized benchmark plans."
            ),
        )

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Enumerates trained model checkpoints and their evaluation metrics."""
        models = []
        if not self.model_dir.exists():
            return models
        for meta_file in sorted(self.model_dir.glob("*.metadata.json")):
            m_id = meta_file.name.replace(".metadata.json", "")
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                models.append({
                    "model_version": m_id,
                    "dataset_version": data.get("dataset_version", "unknown"),
                    "accuracy": data.get("accuracy"),
                    "macro_f1": data.get("macro_f1"),
                    "trained_at": data.get("trained_at"),
                    "is_active": m_id == self.model_version
                })
            except Exception:
                models.append({"model_version": m_id, "is_active": m_id == self.model_version})
        return models

    def set_active_model(self, model_version: str) -> bool:
        """Switches active model checkpoint."""
        self.model_version = model_version
        self._load_model()
        return self.is_available()

# Module singleton
model_registry = GNNModelRegistry()
ModelRegistry = GNNModelRegistry

