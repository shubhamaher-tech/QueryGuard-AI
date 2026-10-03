#!/usr/bin/env python3
"""
CLI script to evaluate the trained GNN bottleneck classifier for QueryGuard AI.
Usage:
    python scripts/evaluate_gnn_model.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.evaluate_gnn import get_latest_evaluation
from app.ml.model_registry import model_registry

def main():
    print("=" * 70)
    print("QueryGuard AI: GNN Bottleneck Classifier Evaluation")
    print("Truthfulness: Experimental classifier trained on synthetic plans only.")
    print("=" * 70)

    metrics = get_latest_evaluation()
    if not metrics:
        print("\n[NOTICE] No trained model metadata found. Please run training script first:")
        print("    python scripts/train_gnn_model.py")
        sys.exit(0)

    print(f"\nModel Version:    {metrics.model_version}")
    print(f"Dataset Version:  {metrics.dataset_version}")
    print(f"Trained At:       {metrics.trained_at}")
    print(f"Sample Count:     {metrics.total_samples} (Test Split: {metrics.test_samples})")
    print(f"Test Accuracy:    {metrics.accuracy * 100:.1f}%")
    print(f"Macro F1 Score:   {metrics.macro_f1:.3f}")

    print("\nPer-Class Breakdown:")
    for label, m in metrics.per_class_metrics.items():
        print(f"  • {label:30s} | Precision: {m.precision:.2f} | Recall: {m.recall:.2f} | F1: {m.f1_score:.2f} | Count: {m.support}")

    print("\nConfusion Matrix:")
    header = " " * 32 + " ".join(f"[{i}]" for i in range(len(metrics.classes)))
    print(header)
    for i, row in enumerate(metrics.confusion_matrix):
        row_str = " ".join(f"{val:3d}" for val in row)
        print(f"[{i}] {metrics.classes[i]:27s}: {row_str}")

if __name__ == "__main__":
    main()
