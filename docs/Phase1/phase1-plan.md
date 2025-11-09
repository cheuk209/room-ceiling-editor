# Phase 1: Core Data Models - Your Tasks

## Overview
- **Goal**: Create foundational data structures for ceiling grids and components
- **Time Budget**: 30 minutes

## Key Points
- Create essential data models using Pydantic
- Implement core grid functionality
- Set up basic project structure
- Define model interfaces
- Create sample data

---

### Task 1.1: Set Up Basic Project Structure

Create the following directories and files:

```
src/
├── __init__.py
├── pipeline/
│   ├── __init__.py
│   └── data_models.py
└── models/
    ├── __init__.py
    └── base.py

data/
├── input/
│   └── sample_grid.json
└── output/
    └── .gitkeep
```

---

### Task 1.2: Define Data Models in `src/pipeline/data_models.py`

Using Pydantic, create these classes:

#### `ComponentType` (Enum)
- **Values**: light, air_supply, air_return, smoke_detector, empty, invalid

#### `Cell` (BaseModel)
- **Fields**:
  - `row: int`
  - `col: int`
  - `type: ComponentType`
  - `metadata: Optional[Dict[str, Any]]` (for future extensibility)

#### `Grid` (BaseModel)
- **Fields**:
  - `grid_id: str`
  - `rows: int`
  - `cols: int`
  - `cells: List[Cell]`
- **Methods to implement**:
  - `get_cell(row: int, col: int) -> Optional[Cell]` - Get cell at position
  - `set_cell(row: int, col: int, cell_type: ComponentType) -> None` - Update cell
  - `count_components(component_type: ComponentType) -> int` - Count specific component type
  - `to_dict() -> dict` - Serialize to dictionary (use Pydantic's built-in)

#### `ModelResult` (BaseModel)
- **Fields**:
  - `model_name: str`
  - `grid: Grid`
  - `score: float` (0.0 to 1.0, higher is better)
  - `execution_time_ms: float`
  - `metadata: Optional[Dict[str, Any]]`

---

### Task 1.3: Create Base Model Interface in `src/models/base.py`

Create an abstract base class for all ML models:

#### `BaseMLModel` (ABC)
- **Abstract methods**:
  - `def run(self, input_grid: Grid) -> ModelResult` - Execute model
  - `def get_name(self) -> str` - Return model name
- **Optional helper methods**:
  - `def _calculate_score(self, grid: Grid) -> float` - Scoring logic (can be overridden)
  - `def _validate_placement(self, grid: Grid) -> bool` - Check if placement is valid

**Hints**:
- Use `from abc import ABC, abstractmethod`
- Think about what information every model needs to return
- Score should reflect "quality" of the placement (you'll define what that means)

---

### Task 1.4: Create Sample Input Data `data/input/sample_grid.json`

Create a 5x5 empty grid JSON file that represents a room ceiling:

**Requirements**:
- 25 cells total (5 rows × 5 columns)
- Most cells should be "empty" (available for placement)
- Include 2-3 "invalid" cells (e.g., structural beams, corners)
- Use zero-indexed positions (row 0-4, col 0-4)

**Example structure** (don't copy exactly, create your own layout):
```json
{
  "grid_id": "room-001",
  "rows": 5,
  "cols": 5,
  "cells": [
    {"row": 0, "col": 0, "type": "empty", "metadata": null},
    {"row": 0, "col": 1, "type": "invalid", "metadata": {"reason": "structural_beam"}},
    ...
  ]
}
```

---

### Task 1.5: Create `requirements.txt`

Add these core dependencies:
- `pydantic>=2.0`
- `pydantic-settings`
- Any other libraries you think you'll need for data models

---

## Acceptance Criteria (How You'll Know You're Done)

**Must Have**:
- ✅ All Pydantic models have type hints
- ✅ Grid can be created from the JSON file
- ✅ `Grid.get_cell()` and `Grid.set_cell()` work correctly
- ✅ `BaseMLModel` is abstract (can't instantiate directly)
- ✅ Sample grid JSON loads without errors

---

## Validation Test (Run This)

Create a quick test script to validate:

```python
# test_phase1.py
from src.pipeline.data_models import Grid, ComponentType
import json

# Load sample grid
with open('data/input/sample_grid.json', 'r') as f:
    data = json.load(f)

# Create Grid object
grid = Grid(**data)

# Test methods
print(f"Grid ID: {grid.grid_id}")
print(f"Dimensions: {grid.rows}x{grid.cols}")
print(f"Total cells: {len(grid.cells)}")
print(f"Empty cells: {grid.count_components(ComponentType.empty)}")

# Test get/set
cell = grid.get_cell(0, 0)
print(f"Cell at (0,0): {cell.type if cell else 'None'}")

grid.set_cell(0, 0, ComponentType.light)
print(f"After update: {grid.get_cell(0, 0).type}")

print("✅ Phase 1 Complete!")
```

---

## Tips & Common Pitfalls

### Pydantic Tips:
- Use `Field()` for validation (e.g., `score: float = Field(ge=0.0, le=1.0)`)
- Use `model_validator` for cross-field validation if needed
- Pydantic v2 uses `model_dump()` instead of `dict()`

### Design Tips:
- Keep it simple - don't over-engineer
- Add docstrings to your classes (good practice for reviews)
- Think about immutability - should `Grid` be mutable?

### Time Management:
- If you're stuck on a method for >5 mins, implement a simple version and move on
- You can always refine later
