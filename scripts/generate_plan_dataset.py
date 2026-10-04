#!/usr/bin/env python3
"""
CLI script to generate synthetic plan graph dataset for QueryGuard AI.
Usage:
    python scripts/generate_plan_dataset.py --samples-per-class 20
"""

import sys
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.dataset_generator import dataset_generator

def main():
    parser = argparse.ArgumentParser(description="QueryGuard AI Plan Graph Dataset Generator")
    parser.add_argument(
        "--samples-per-class", "--samples",
        type=int,
        default=20,
        help="Target sanitized plan graph samples per bottleneck class (default: 20)"
    )
    parser.add_argument(
        "--dataset-version",
        default="v2_synthetic_tpch_postgres",
        help="Dataset version identifier (default: v2_synthetic_tpch_postgres)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("QueryGuard AI: Plan Graph Dataset Generator")
    print(f"Target Samples/Class: {args.samples_per_class}")
    print(f"Dataset Version:      {args.dataset_version}")
    print("Privacy: ZERO raw SQL, literals, or customer records persisted.")
    print("=" * 70)

    result = dataset_generator.generate_dataset(
        min_samples_per_class=args.samples_per_class,
        dataset_version=args.dataset_version
    )
    print(f"\n[SUCCESS] Generated {result.total_graphs_generated} sanitized plan graphs.")
    print(f"Dataset Version: {result.dataset_version}")
    print(f"Artifacts Path: {result.artifacts_directory}")
    print("\nClass Distribution:")
    for label, count in result.label_distribution.items():
        print(f"  • {label:30s}: {count} samples")

if __name__ == "__main__":
    main()
