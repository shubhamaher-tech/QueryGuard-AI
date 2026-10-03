#!/usr/bin/env python3
"""
CLI script to train the GNN bottleneck classifier for QueryGuard AI.
Usage:
    python scripts/train_gnn_model.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from app.ml.train_gnn import train_gnn_model
from app.ml.model_registry import model_registry

def main():
    parser = argparse.ArgumentParser(description="Train QueryGuard GNN Bottleneck Classifier")
    parser.add_argument("--model-version", default="gnn_bottleneck_v2", help="Model version (e.g. gnn_bottleneck_v2)")
    parser.add_argument("--dataset-version", default="v2_synthetic_tpch_postgres", help="Dataset version (e.g. v2_synthetic_tpch_postgres)")
    parser.add_argument("--epochs", type=int, default=40, help="Training epochs")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate")
    args = parser.parse_args()

    print("=" * 70)
    print("QueryGuard AI: GNN Bottleneck Classifier Training")
    print(f"Model Version:   {args.model_version}")
    print(f"Dataset Version: {args.dataset_version}")
    print("Architecture:    2-layer GraphSAGE/GCN + Mean/Max Readout + MLP")
    print("Dataset:         Synthetic & TPC-H Sanitized Plan Graphs (Zero Raw SQL / Literals)")
    print("=" * 70)

    try:
        metrics = train_gnn_model(
            model_version=args.model_version,
            dataset_version=args.dataset_version,
            epochs=args.epochs,
            lr=args.lr
        )
        model_registry.reload()

        print("\n[TRAINING COMPLETE]")
        print(f"Model Version: {metrics.model_version}")
        print(f"Dataset:       {metrics.dataset_version}")
        print(f"Total Graphs:  {metrics.total_samples} (Train: {metrics.train_samples}, Val: {metrics.val_samples}, Test: {metrics.test_samples})")
        print(f"Test Accuracy: {metrics.accuracy * 100:.1f}%")
        print(f"Macro F1:      {metrics.macro_f1:.3f}")
        print("\nPer-Class Performance:")
        for label, m in metrics.per_class_metrics.items():
            print(f"  • {label:30s} | P: {m.precision:.2f} | R: {m.recall:.2f} | F1: {m.f1_score:.2f} | Support: {m.support}")

        print(f"\nArtifacts saved to: {model_registry.model_dir}")
        print("Disclaimer: Experimental POC trained on synthetic & benchmark plans only.")
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
