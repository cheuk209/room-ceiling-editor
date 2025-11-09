#!/usr/bin/env python3
"""
Test all three light models and compare results.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.light_models import LightModelA, LightModelB, LightModelC
from src.pipeline.data_models import Grid, ComponentType
import json


def main():
    print("=" * 70)
    print("Testing All Light Models - Parallel Execution Simulation")
    print("=" * 70)

    # Load empty grid
    with open('data/input/sample_grid.json', 'r') as f:
        grid_data = json.load(f)
    input_grid = Grid(**grid_data)

    print(f"\n📥 Input Grid: {input_grid.width}x{input_grid.height}")
    counts = input_grid.count_components()
    print(f"   - Empty cells: {counts.get(ComponentType.EMPTY, 0)}")
    print(f"   - Invalid cells: {counts.get(ComponentType.INVALID, 0)}")

    # Run all three models (simulating parallel execution)
    print(f"\n🚀 Running 3 light models in parallel...")
    models = [
        LightModelA(),
        LightModelB(),
        LightModelC(),
    ]

    results = []
    for model in models:
        result = model.run(input_grid)
        results.append(result)
        print(f"   ✓ {result.model_name} completed in {result.execution_time*1000:.2f}ms")

    # Display comparison
    print(f"\n📊 Model Comparison:")
    print(f"{'Model':<30} {'Lights':<10} {'Coverage':<12} {'Confidence':<12}")
    print("-" * 70)

    total_cells = input_grid.width * input_grid.height
    for result in results:
        counts = result.grid.count_components()
        lights = counts.get(ComponentType.LIGHT, 0)
        coverage = (lights / total_cells) * 100

        print(f"{result.model_name:<30} {lights:<10} {coverage:<11.1f}% {result.confidence:<12.4f}")

    # Select best model
    best_result = max(results, key=lambda r: r.confidence)
    print(f"\n🏆 Best Model Selected: {best_result.model_name}")
    print(f"   - Confidence: {best_result.confidence:.4f}")
    print(f"   - Lights placed: {best_result.grid.count_components()[ComponentType.LIGHT]}")

    # Validation
    print(f"\n🧪 Validation:")
    assert len(results) == 3, "Should have 3 results"
    print(f"   ✅ All 3 models executed")

    # Check models produced different outputs
    light_counts = [r.grid.count_components()[ComponentType.LIGHT] for r in results]
    assert len(set(light_counts)) > 1, "Models should produce different results"
    print(f"   ✅ Models produced different results")

    # Check confidence scores vary
    confidences = [r.confidence for r in results]
    assert max(confidences) - min(confidences) > 0.1, "Confidence scores should vary"
    print(f"   ✅ Confidence scores vary meaningfully")

    print(f"\n{'=' * 70}")
    print("🎉 Phase 2A Complete - Light Models Working!")
    print("=" * 70)
    print(f"\n✨ Next: Implement sequential models (AirSupply, SmokeDetector)")


if __name__ == "__main__":
    main()
