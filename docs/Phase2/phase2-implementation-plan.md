# Phase 2 - Mock ML Models Implementation Plan

**Goal:** Implement mock ML models to demonstrate parallel and sequential pipeline execution patterns.

**Time Budget:** 1.5 - 2 hours

---

## Table of Contents
1. [Core Philosophy](#core-philosophy)
2. [Parallel Execution - Model Selection](#1-parallel-execution---model-selection)
3. [Sequential Execution - Pipeline Stages](#2-sequential-execution---pipeline-stages)
4. [Realistic Model Behavior](#3-realistic-model-behavior-simulation)
5. [Observability Design](#4-observability-design)
6. [Grid Constraints](#5-grid-constraints)
7. [Implementation Checklist](#implementation-checklist)
8. [Q&A - Your Questions Answered](#qa---your-questions-answered)

---

## Core Philosophy

### Key Insight: You Control the "Expected" Output

**Your Question:**
> "If I do not know what the expected output JSON for these grids, how should I write my mocks to fulfill this?"

**Answer:**
You're absolutely right - **there is no "expected" output!** This is a **mock/simulation**, not real ML.

**Your approach:**
1. **Define your own rules** - What makes a "good" light placement? You decide!
2. **Make models differ** - As long as Model A, B, C produce *different* results, you're demonstrating the pattern
3. **Consistency matters more than correctness** - Dense model should always place more lights than sparse model

**Example:**
- Dense model: "Place light with 40% probability on each empty cell"
- Sparse model: "Place light with 15% probability on each empty cell"
- Balanced model: "Place light on checkerboard pattern (x+y)%2==0"

**None of these is "correct"** - they're just **different strategies**. The point is demonstrating pipeline orchestration!

---

## 1. Parallel Execution - Model Selection

### Objective
Run 3 light placement models simultaneously, then select the best result.

### What to Build

#### **LightModelA - Dense Strategy**
```python
class LightModelA(BaseMLModel):
    """Dense placement: High coverage, many lights"""
    strategy = "dense"
    placement_probability = 0.40  # 40% of empty cells
```

#### **LightModelB - Sparse Strategy**
```python
class LightModelB(BaseMLModel):
    """Sparse placement: Minimal coverage, few lights"""
    strategy = "sparse"
    placement_probability = 0.15  # 15% of empty cells
```

#### **LightModelC - Balanced Strategy**
```python
class LightModelC(BaseMLModel):
    """Balanced placement: Checkerboard pattern"""
    strategy = "balanced"
    # Place lights where (x + y) % 2 == 0
```

### Execution Pattern

```
Input: Empty 10x10 Grid (93 empty cells)
          ↓
    ┌─────┴─────┬─────────┬─────────┐
    ↓           ↓         ↓         ↓
LightModelA  LightModelB  LightModelC  ← Run in PARALLEL
    ↓           ↓         ↓
Result A     Result B   Result C
confidence:  confidence: confidence:
  0.72         0.58       0.85
    │           │         │
    └─────┬─────┴─────────┘
          ↓
    Select Best (highest confidence)
          ↓
    Result C selected
```

### Success Criteria
- ✅ All 3 models process the same input grid
- ✅ Each produces measurably different outputs
- ✅ Different strategies yield different confidence scores
- ✅ Can select "best" result based on confidence

---

## 2. Sequential Execution - Pipeline Stages

### Objective
Build a multi-stage pipeline where each model depends on the previous stage's output.

### Pipeline Flow

```
10x10 Empty Grid
    ↓
┌───────────────────────────┐
│ STAGE 1: Light Placement  │  (Parallel)
└───────────────────────────┘
    ↓ (best model selected)
Grid with ~25 lights
    ↓
┌───────────────────────────┐
│ STAGE 2: Air Supply       │  (Sequential)
└───────────────────────────┘
    ↓
Grid with lights + 4-6 air supply points
    ↓
┌───────────────────────────┐
│ STAGE 3: Smoke Detectors  │  (Sequential)
└───────────────────────────┘
    ↓
Final Grid: lights + air supply + smoke detectors
```

### What to Build

#### **AirSupplyModel - Even Distribution**
```python
class AirSupplyModel(BaseMLModel):
    """Place air supply points at strategic positions for airflow"""
    # Strategy: Corners and edges
    # Only place on EMPTY cells (preserve existing lights)
```

**Placement logic:**
- Target positions: Near corners (1,1), (8,1), (1,8), (8,8)
- Check: Is cell EMPTY? If yes, place. If occupied (light/invalid), skip.

#### **SmokeDetectorModel - Coverage-Based**
```python
class SmokeDetectorModel(BaseMLModel):
    """Place smoke detectors for maximum coverage"""
    # Strategy: Center + corners
    # Coverage radius: ~3 cells
```

**Placement logic:**
- Target positions: Center (5,5), corners (0,0), (9,0), (0,9), (9,9)
- Check: Is cell EMPTY? If yes, place. If occupied, skip.

### Key Constraint: Preserve Previous Stages

**Critical rule:** Sequential models MUST NOT overwrite existing components!

```python
def _place_component(self, grid: Grid, positions: list, component_type: ComponentType):
    """Only place on EMPTY cells"""
    for x, y in positions:
        cell = grid.get_cell(x, y)
        if cell and cell.component == ComponentType.EMPTY:  # ← CHECK THIS!
            grid.set_cell(x, y, component_type)
```

### Success Criteria
- ✅ Models only place on EMPTY cells
- ✅ Each stage preserves previous placements
- ✅ Final grid has all component types (lights, air_supply, smoke_detector)

---

## 3. Realistic Model Behavior Simulation

### Your Question:
> "Confidence scoring -> how would I assign confidence scores to models when I am not in the best place to judge?"

### Answer: Define Simple Quality Heuristics

You don't need to be an expert! Just define **reasonable rules**:

### Confidence Scoring Formula

#### For Light Models:
```python
def _calculate_confidence(self, grid: Grid) -> float:
    """Score based on coverage percentage"""
    counts = grid.count_components()
    total_cells = grid.width * grid.height
    lights = counts.get(ComponentType.LIGHT, 0)

    # Calculate coverage
    light_ratio = lights / total_cells

    # Define "ideal" range (25-35% coverage)
    if 0.25 <= light_ratio <= 0.35:
        base_score = 0.90  # Near ideal
    elif 0.20 <= light_ratio <= 0.40:
        base_score = 0.75  # Acceptable
    elif 0.15 <= light_ratio <= 0.45:
        base_score = 0.60  # Okay
    else:
        base_score = 0.40  # Too sparse or too dense

    # Add randomness (±5%)
    import random
    confidence = base_score + random.uniform(-0.05, 0.05)

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))
```

**Why this works:**
- **Balanced model** (checkerboard ~25% coverage) → High confidence (~0.85)
- **Dense model** (~40% coverage) → Medium confidence (~0.70)
- **Sparse model** (~15% coverage) → Lower confidence (~0.55)

**Result:** Balanced model naturally wins most of the time!

#### For Sequential Models:
```python
def _calculate_confidence(self, grid: Grid) -> float:
    """Simpler: Did we place the expected number of components?"""
    counts = grid.count_components()
    placed = counts.get(ComponentType.AIR_SUPPLY, 0)

    # Expected: 4-6 air supply points
    if 4 <= placed <= 6:
        return random.uniform(0.85, 0.95)  # Success
    else:
        return random.uniform(0.50, 0.70)  # Suboptimal
```

### Non-Deterministic Behavior (Randomness)

**Why randomness?**
- Real ML models have stochastic behavior
- Makes logs/metrics more realistic
- Tests pipeline robustness

**How to add it:**
```python
# In placement logic
if random.random() < self.placement_probability:
    cell.component = ComponentType.LIGHT
```

**Result:** Running the same model twice produces similar but not identical results.

### Execution Time Simulation

**Option 1: Measure actual Python execution (Recommended for MVP)**
```python
import time

def run(self, input_grid: Grid) -> ModelResult:
    start_time = time.time()
    # ... do work ...
    execution_time = time.time() - start_time  # Real time in seconds
```

**Option 2: Add artificial delay (more realistic)**
```python
import time
import random

def run(self, input_grid: Grid) -> ModelResult:
    start_time = time.time()

    # Simulate model inference time (50-200ms)
    time.sleep(random.uniform(0.05, 0.20))

    # ... do work ...
    execution_time = time.time() - start_time
```

**Recommendation:** Start with Option 1 (real timing), add sleep if you want more dramatic timing differences.

### Success Criteria
- ✅ Confidence scores correlate with placement quality
- ✅ Running model twice produces different results (but similar patterns)
- ✅ Execution times are measurable and logged
- ✅ Each model has distinct characteristics

---

## 4. Observability Design

### Your Question:
> "Confidence scores are meaningful (How?)"

### Answer: Meaningful = Comparable & Actionable

**Meaningful confidence scores:**
1. **Comparable:** Model A (0.85) > Model B (0.72) → A is better
2. **Actionable:** Confidence < 0.5 → Flag for investigation
3. **Interpretable:** 0.85 means "25-35% light coverage, near ideal"

### Observability Checklist

#### ✅ Complete ModelResult
```python
ModelResult(
    model_name="light_model_c_balanced",      # ← Unique identifier
    confidence=0.85,                          # ← Quality metric
    grid=output_grid,                         # ← Full output
    execution_time=0.123                      # ← Performance metric
)
```

#### ✅ Grid State Inspection
```python
# After each model runs
counts = result.grid.count_components()
print(f"Model {result.model_name}:")
print(f"  - Lights: {counts.get(ComponentType.LIGHT, 0)}")
print(f"  - Empty: {counts.get(ComponentType.EMPTY, 0)}")
print(f"  - Confidence: {result.confidence:.2f}")
print(f"  - Time: {result.execution_time*1000:.2f}ms")
```

#### ✅ Model Comparison
```python
# Compare 3 parallel results
results = [result_a, result_b, result_c]
for r in sorted(results, key=lambda x: x.confidence, reverse=True):
    counts = r.grid.count_components()
    print(f"{r.model_name}: {r.confidence:.2f} ({counts[ComponentType.LIGHT]} lights)")

# Output:
# light_model_c_balanced: 0.87 (25 lights)
# light_model_a_dense: 0.71 (38 lights)
# light_model_b_sparse: 0.56 (14 lights)
```

### What This Enables (Future Phases)

**Phase 3 (Logging):**
```python
logger.info(
    "model_execution_complete",
    model=result.model_name,
    confidence=result.confidence,
    execution_time_ms=result.execution_time * 1000,
    lights_placed=counts[ComponentType.LIGHT]
)
```

**Phase 3 (Metrics):**
```python
# Prometheus metrics
model_confidence.set(result.confidence)
model_execution_time.observe(result.execution_time)
```

### Success Criteria
- ✅ Every model returns complete metadata
- ✅ Grid state is easily inspectable
- ✅ Model names are unique and descriptive
- ✅ Confidence scores enable comparison

---

## 5. Grid Constraints

### Your Question:
> "What are the grid constraints we have?"

### Answer: Physical Ceiling Constraints

Think of this as a **real ceiling** in a building:

### Constraint 1: Invalid Cells (Structural Obstacles)

**What they represent:**
- Structural beams
- Columns
- HVAC ducts
- Light fixtures (permanent)

**Rule:** **NEVER place any component on INVALID cells**

```python
def _can_place(self, cell: Cell) -> bool:
    """Check if we can place a component here"""
    return cell.component == ComponentType.EMPTY  # ← Only EMPTY allowed
```

### Constraint 2: No Overwrites (Sequential Stages)

**Rule:** Sequential models must **preserve existing components**

```python
# ❌ BAD - Overwrites existing light!
grid.set_cell(x, y, ComponentType.AIR_SUPPLY)

# ✅ GOOD - Check first
cell = grid.get_cell(x, y)
if cell.component == ComponentType.EMPTY:
    grid.set_cell(x, y, ComponentType.AIR_SUPPLY)
```

### Constraint 3: Logical Placement

**Not enforced by code, but makes sense:**

**Lights:**
- Coverage-based (illuminate the room)
- Reasonably spaced (not all clustered)

**Air Supply:**
- Edge/corner placement (ventilation inflow)
- Even distribution

**Smoke Detectors:**
- Coverage-based (detect smoke anywhere)
- Strategic positions (corners, center)

### Validation Helper

```python
def validate_placement(grid: Grid) -> bool:
    """Validate grid meets constraints"""
    for cell in grid.cells:
        # Check 1: No components on invalid cells
        if cell.component == ComponentType.INVALID:
            continue  # This is okay

        # In practice, your validator would check more rules
        # For MVP, the model logic handles this

    return True
```

### Success Criteria
- ✅ No components placed on INVALID cells
- ✅ Sequential models don't overwrite existing components
- ✅ Placement patterns are reasonable (visually inspectable)

---

## Implementation Checklist

### Phase 2A: Light Models (Parallel Execution)

- [ ] Create `src/models/light_models.py`
- [ ] Implement `LightModelA` (dense: 40% probability)
- [ ] Implement `LightModelB` (sparse: 15% probability)
- [ ] Implement `LightModelC` (balanced: checkerboard pattern)
- [ ] Each model implements `run()` and `get_name()`
- [ ] Each model calculates meaningful confidence scores
- [ ] Each model tracks execution time
- [ ] Test: All 3 models produce different results
- [ ] Test: Can select best model based on confidence

### Phase 2B: Component Models (Sequential Execution)

- [ ] Create `src/models/air_supply_model.py`
- [ ] Implement `AirSupplyModel` (corner/edge placement)
- [ ] Create `src/models/smoke_detector_model.py`
- [ ] Implement `SmokeDetectorModel` (coverage-based)
- [ ] Models only place on EMPTY cells
- [ ] Models preserve existing components
- [ ] Test: Sequential pipeline produces complete grid

### Phase 2C: Testing & Validation

- [ ] Create `tests/test_phase2.py`
- [ ] Test: Each model implements BaseMLModel
- [ ] Test: Models produce different outputs
- [ ] Test: Sequential models preserve placements
- [ ] Test: No invalid cell placements
- [ ] Test: Confidence scores are in [0.0, 1.0] range
- [ ] Test: ModelResult contains all required fields
- [ ] Manual test: Run full pipeline (lights → air → detectors)

### Phase 2D: Documentation

- [ ] Update project structure diagram
- [ ] Document model strategies
- [ ] Document confidence scoring logic
- [ ] Create phase2-completion-summary.md

---

## Q&A - Your Questions Answered

### Q1: "How do I know what the expected output should be?"

**A:** You don't need to! **You define the expected behavior** through your model strategies. As long as:
- Models produce different results
- Results are consistent with their strategy (dense = more lights)
- The pipeline works end-to-end

You've succeeded. This is a **demonstration**, not a prediction task.

---

### Q2: "Should I assign random confidence scores?"

**A:** **No** - Don't make them completely random. Use **heuristics**:

```python
# ❌ BAD - Completely random
confidence = random.uniform(0.0, 1.0)  # No meaning!

# ✅ GOOD - Based on quality metric
light_ratio = lights_placed / total_cells
if 0.25 <= light_ratio <= 0.35:
    confidence = 0.9 + random.uniform(-0.05, 0.05)  # Near ideal
else:
    confidence = 0.6 + random.uniform(-0.1, 0.1)   # Suboptimal
```

**Why?** Shows you understand model evaluation, not just randomness.

---

### Q3: "How do I make confidence scores meaningful?"

**A:** Make them **reflect placement quality**:

**For Light Models:**
- High confidence (0.8-0.95): Good coverage (25-35%)
- Medium confidence (0.6-0.8): Acceptable coverage
- Low confidence (<0.6): Too sparse or too dense

**For Sequential Models:**
- High confidence: Placed expected number of components
- Low confidence: Couldn't find enough empty cells

**Key:** Confidence should **correlate with something measurable**.

---

### Q4: "What constraints should models respect?"

**A:** Two main constraints:

1. **Never place on INVALID cells** (structural obstacles)
2. **Don't overwrite existing components** (in sequential stages)

**Implementation:**
```python
# Before placing
if cell.component == ComponentType.EMPTY:
    # Safe to place
    grid.set_cell(x, y, new_component)
```

---

### Q5: "How do I test if models work correctly?"

**A:** Multi-level testing:

**Unit Test (Per Model):**
```python
def test_light_model_a():
    grid = load_empty_grid()
    model = LightModelA()
    result = model.run(grid)

    assert result.model_name == "light_model_a_dense"
    assert 0.0 <= result.confidence <= 1.0
    assert result.execution_time > 0

    counts = result.grid.count_components()
    assert counts[ComponentType.LIGHT] > 0  # Placed some lights
```

**Integration Test (Full Pipeline):**
```python
def test_full_pipeline():
    grid = load_empty_grid()

    # Stage 1: Parallel light models
    results = [
        LightModelA().run(grid),
        LightModelB().run(grid),
        LightModelC().run(grid),
    ]
    best_light_result = max(results, key=lambda r: r.confidence)

    # Stage 2: Air supply
    air_result = AirSupplyModel().run(best_light_result.grid)

    # Stage 3: Smoke detectors
    final_result = SmokeDetectorModel().run(air_result.grid)

    # Validate
    counts = final_result.grid.count_components()
    assert counts[ComponentType.LIGHT] > 0
    assert counts[ComponentType.AIR_SUPPLY] > 0
    assert counts[ComponentType.SMOKE_DETECTOR] > 0
```

---

## Success Criteria for Phase 2

### Functional Requirements
- ✅ 3 light models produce different results
- ✅ Confidence scores reflect placement quality
- ✅ Sequential models preserve previous placements
- ✅ Full pipeline produces complete grid
- ✅ No invalid cell placements

### Code Quality
- ✅ All models implement BaseMLModel interface
- ✅ Code is DRY (helper methods for common logic)
- ✅ Clear docstrings explaining strategies
- ✅ Type hints on all methods

### Testing
- ✅ Unit tests for each model
- ✅ Integration test for full pipeline
- ✅ All tests passing

### Documentation
- ✅ Model strategies documented
- ✅ Confidence scoring explained
- ✅ Completion summary written

---

## Next Steps After Phase 2

Once Phase 2 is complete, you'll have:
- 5 working mock models
- Testable pipeline components
- Foundation for observability

**Then:**
- **Phase 3:** Add structured logging + Prometheus metrics
- **Phase 4:** Orchestrate with Airflow DAG
- **Phase 5:** Containerize with Docker Compose

---

**Ready to implement? Start with `LightModelA` and let me know when you want a review!** 🚀
