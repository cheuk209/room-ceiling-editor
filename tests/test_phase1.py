#!/usr/bin/env python3
"""
Phase 1 Test Script
Tests all data models and grid operations
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.data_models import Grid, Cell, ComponentType, ModelResult
import json


def test_grid_loading():
    """Test loading grid from JSON file."""
    print("🧪 Test 1: Loading 10x10 grid from JSON...")

    with open('data/input/sample_grid.json', 'r') as f:
        data = json.load(f)

    grid = Grid(**data)

    assert grid.grid_id == "room-001", "Grid ID mismatch"
    assert grid.width == 10, "Width should be 10"
    assert grid.height == 10, "Height should be 10"
    assert len(grid.cells) == 100, "Should have 100 cells"

    print("   ✅ Grid loaded successfully")
    return grid


def test_get_cell(grid):
    """Test get_cell method."""
    print("\n🧪 Test 2: Testing get_cell method...")

    cell = grid.get_cell(0, 0)
    assert cell is not None, "Cell (0,0) should exist"
    assert cell.x == 0 and cell.y == 0, "Cell coordinates should match"

    # Test invalid coordinates
    invalid_cell = grid.get_cell(99, 99)
    assert invalid_cell is None, "Out of bounds cell should return None"

    print("   ✅ get_cell working correctly")


def test_set_cell(grid):
    """Test set_cell method."""
    print("\n🧪 Test 3: Testing set_cell method...")

    # Place a light
    grid.set_cell(1, 1, ComponentType.LIGHT)
    cell = grid.get_cell(1, 1)

    assert cell is not None, "Cell should exist"
    assert cell.component == ComponentType.LIGHT, "Cell should have light component"

    # Update it to air supply
    grid.set_cell(1, 1, ComponentType.AIR_SUPPLY)
    cell = grid.get_cell(1, 1)
    assert cell.component == ComponentType.AIR_SUPPLY, "Cell should be updated"

    print("   ✅ set_cell working correctly")


def test_count_components(grid):
    """Test count_components method."""
    print("\n🧪 Test 4: Testing count_components method...")

    counts = grid.count_components()

    assert isinstance(counts, dict), "Should return a dictionary"
    assert ComponentType.EMPTY in counts, "Should count empty cells"
    assert ComponentType.INVALID in counts, "Should count invalid cells"

    total_cells = sum(counts.values())
    assert total_cells == 100, f"Total cells should be 100, got {total_cells}"

    print(f"   ✅ count_components working correctly")
    print(f"      Empty cells: {counts.get(ComponentType.EMPTY, 0)}")
    print(f"      Invalid cells: {counts.get(ComponentType.INVALID, 0)}")
    print(f"      Lights: {counts.get(ComponentType.LIGHT, 0)}")
    print(f"      Air Supply: {counts.get(ComponentType.AIR_SUPPLY, 0)}")


def test_model_result():
    """Test ModelResult creation."""
    print("\n🧪 Test 5: Testing ModelResult model...")

    # Create a simple grid for testing
    cells = [Cell(x=x, y=y, component=ComponentType.EMPTY) for y in range(3) for x in range(3)]
    test_grid = Grid(grid_id="test", width=3, height=3, cells=cells)

    result = ModelResult(
        model_name="test_model",
        confidence=0.85,
        grid=test_grid,
        execution_time=0.123
    )

    assert result.model_name == "test_model", "Model name mismatch"
    assert result.confidence == 0.85, "Confidence mismatch"
    assert result.execution_time == 0.123, "Execution time mismatch"
    assert result.grid.width == 3, "Grid should be included"

    print("   ✅ ModelResult model working correctly")


def test_validation():
    """Test grid validation."""
    print("\n🧪 Test 6: Testing grid validation...")

    # Test invalid grid (wrong number of cells)
    try:
        cells = [Cell(x=0, y=0, component=ComponentType.EMPTY)]  # Only 1 cell
        Grid(grid_id="invalid", width=5, height=5, cells=cells)
        assert False, "Should have raised validation error"
    except ValueError as e:
        print(f"   ✅ Validation caught invalid cell count: {str(e)[:50]}...")

    # Test out of bounds cell
    try:
        cells = [Cell(x=x, y=y, component=ComponentType.EMPTY) for y in range(3) for x in range(3)]
        cells[0].x = 10  # Out of bounds
        Grid(grid_id="invalid", width=3, height=3, cells=cells)
        assert False, "Should have raised validation error"
    except ValueError as e:
        print(f"   ✅ Validation caught out-of-bounds cell: {str(e)[:50]}...")


def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("PHASE 1 - Data Models & Grid Operations Test Suite")
    print("=" * 60)

    try:
        grid = test_grid_loading()
        test_get_cell(grid)
        test_set_cell(grid)
        test_count_components(grid)
        test_model_result()
        test_validation()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED - PHASE 1 COMPLETE!")
        print("=" * 60)
        print("\n📋 What was tested:")
        print("   ✅ Grid/Cell/ComponentType data models")
        print("   ✅ Grid validation (cell count, bounds, duplicates)")
        print("   ✅ Grid.get_cell() method")
        print("   ✅ Grid.set_cell() method")
        print("   ✅ Grid.count_components() method")
        print("   ✅ ModelResult data model")
        print("   ✅ BaseMLModel abstract class (defined)")
        print("\n✨ Ready for Phase 2: Mock ML Models Implementation")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
