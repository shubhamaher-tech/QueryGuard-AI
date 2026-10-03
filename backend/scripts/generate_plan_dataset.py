#!/usr/bin/env python3
"""
CLI script to generate synthetic plan graph dataset for QueryGuard AI.
Usage:
    python scripts/generate_plan_dataset.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.dataset_generator import dataset_generator

def main():
    print("=" * 70)
    print("QueryGuard AI: Plan Graph Dataset Generator")
    print("Privacy: ZERO raw SQL, literals, or customer records persisted.")
    print("=" * 70)

    result = dataset_generator.generate_dataset()
    print(f"\n[SUCCESS] Generated {result.total_graphs_generated} sanitized plan graphs.")
    print(f"Dataset Version: {result.dataset_version}")
    print(f"Artifacts Path: {result.artifacts_directory}")
    print("\nClass Distribution:")
    for label, count in result.label_distribution.items():
        print(f"  • {label:30s}: {count} samples")

if __name__ == "__main__":
    main()
