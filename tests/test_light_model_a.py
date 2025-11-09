#!/usr/bin/env python3
"""
Quick test script for LightModelA.

Run this to verify your implementation works before implementing B and C.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.light_models import LightModelA
from src.pipeline.data_models import Grid, ComponentType
import json


def test_light_model_a():
    """Test LightModelA implementation."""
    print("=" * 60)
    print("Testing LightModelA (Dense Strategy)")
    print("=" * 60)

    # Load empty grid
    with open('data/input/sample_grid.json', 'r') as f:
        grid_data = json.load(f)

    input_grid = Grid(**grid_data)

    print(f"\n📥 Input Grid:")
    counts = input_grid.count_components()
    print(f"   - Empty cells: {counts.get(ComponentType.EMPTY, 0)}")
    print(f"   - Invalid cells: {counts.get(ComponentType.INVALID, 0)}")

    # Run model
    print(f"\n🤖 Running LightModelA...")
    model = LightModelA()
    result = model.run(input_grid)

    # Display results
    print(f"\n✅ Model Execution Complete!")
    print(f"   - Model: {result.model_name}")
    print(f"   - Confidence: {result.confidence:.4f}")
    print(f"   - Execution time: {result.execution_time * 1000:.2f}ms")

    output_counts = result.grid.count_components()
    print(f"\n📊 Output Grid:")
    print(f"   - Lights placed: {output_counts.get(ComponentType.LIGHT, 0)}")
    print(f"   - Empty remaining: {output_counts.get(ComponentType.EMPTY, 0)}")
    print(f"   - Invalid cells: {output_counts.get(ComponentType.INVALID, 0)}")

    # Calculate coverage
    total_cells = result.grid.width * result.grid.height
    lights = output_counts.get(ComponentType.LIGHT, 0)
    coverage = (lights / total_cells) * 100
    print(f"   - Coverage: {coverage:.1f}%")

    # Validate
    print(f"\n🧪 Validation:")
    assert result.model_name == "light_model_a_dense", "❌ Wrong model name"
    print(f"   ✅ Model name correct")

    assert 0.0 <= result.confidence <= 1.0, "❌ Confidence out of range"
    print(f"   ✅ Confidence in valid range")

    assert result.execution_time > 0, "❌ Execution time not tracked"
    print(f"   ✅ Execution time tracked")

    assert lights > 0, "❌ No lights placed"
    print(f"   ✅ Lights were placed")

    # With spacing constraints, expect 10-25% coverage (sparser than before)
    assert 5 <= lights <= 30, f"❌ Unexpected number of lights: {lights}"
    print(f"   ✅ Light count reasonable for dense strategy (with spacing)")

    # Check no lights on invalid cells
    for cell in result.grid.cells:
        if cell.component == ComponentType.LIGHT:
            original_cell = input_grid.get_cell(cell.x, cell.y)
            assert original_cell.component != ComponentType.INVALID, \
                f"❌ Light placed on invalid cell at ({cell.x}, {cell.y})"
    print(f"   ✅ No lights on invalid cells")

    # Check spacing constraint (MIN_LIGHT_SPACING = 2)
    light_positions = [(c.x, c.y) for c in result.grid.cells if c.component == ComponentType.LIGHT]
    for i, (x1, y1) in enumerate(light_positions):
        for j, (x2, y2) in enumerate(light_positions):
            if i != j:
                distance = abs(x1 - x2) + abs(y1 - y2)
                assert distance >= 2, \
                    f"❌ Lights at ({x1},{y1}) and ({x2},{y2}) too close (distance={distance})"
    print(f"   ✅ All lights respect minimum spacing (≥2)")

    print(f"\n{'=' * 60}")
    print("🎉 All tests passed! LightModelA is working correctly.")
    print("=" * 60)
    print(f"\n💡 Next steps:")
    print(f"   1. Implement LightModelB (sparse: 15% probability)")
    print(f"   2. Implement LightModelC (balanced: checkerboard)")
    print(f"   3. Compare all three models")


if __name__ == "__main__":
    test_light_model_a()
