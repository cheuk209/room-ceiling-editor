# Mock Models Explained (For ML Beginners)

Let me break this down step-by-step with great patience, because this is actually a **crucial concept** to understand.

---

## The Core Misunderstanding

You're thinking:
> "If I don't know what the model should output, how can I mock it?"

But here's the key insight:

**For this takehome, YOU get to decide what reasonable outputs look like!**

Let me explain why...

---

## What Is This Assignment Really Testing?

### They're NOT Testing:
- ❌ Can you train an ML model?
- ❌ Do you know TensorFlow/PyTorch?
- ❌ Can you achieve 95% accuracy?
- ❌ Do you understand neural networks?

### They ARE Testing:
- ✅ Can you build a **pipeline** that orchestrates multiple models?
- ✅ Can you handle **parallel execution**?
- ✅ Can you implement **model selection logic**?
- ✅ Do you understand **MLOps infrastructure**?
- ✅ Can you add **monitoring and observability**?

**The actual predictions don't matter at all!**

---

## The Restaurant Analogy

Imagine you're being hired as a **restaurant manager** (not a chef).

### Bad Approach (What You're Worried About):
```
"To show I can manage a restaurant, I need to:
1. Go to culinary school (4 years)
2. Learn to make perfect risotto
3. Master molecular gastronomy
4. Create a Michelin-star menu
THEN I can show I can manage the restaurant"
```

**This is crazy!** You'd never finish the interview.

### Good Approach (What You Should Do):
```
"To show I can manage a restaurant, I will:
1. Simulate a restaurant with fake food orders
2. Show how I coordinate the kitchen staff
3. Demonstrate my ordering system
4. Show how I handle busy vs slow periods
5. Display my inventory management

I'll use TOY FOOD (plastic models) because the FOOD ISN'T 
THE POINT - the MANAGEMENT SYSTEM is!"
```

**For your takehome:**
- Real ML models = Being a world-class chef
- Mock models = Using toy food to demonstrate management
- The interview = Testing your management skills, not cooking

---

## How To Think About The Problem

### The Assignment Says:

> "We have a machine learning pipeline that supports multiple models 
> that take the input ceiling grid data and use multiple machine 
> learning models to generate the result."

**Translation:**
```
Input: Ceiling grid (5x5 array of cells)
        ↓
Process: Some models place lights on it
        ↓
Output: Grid with lights placed
```

### You Don't Need To Know The "Right" Answer!

**Here's why:** There IS no single "right" answer for ceiling design!

Think about it:
- Different architects design differently
- Different building codes have different requirements
- Different aesthetic preferences exist

**So you just make up reasonable rules!**

---

## Step-by-Step: Creating Your Mock Models

### Step 1: Understand The Input

```python
# Input: A ceiling grid (simple 2D array)
grid = [
    [0, 0, 0, 0, 0],  # 0 = valid ceiling tile
    [0, 0, 0, 0, 0],
    [0, -1, 0, 0, 0], # -1 = invalid (e.g., structural beam)
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
# Grid is 5x5, each cell is 1 meter
```

### Step 2: Understand The Output

```python
# Output: Positions where lights should go
output = {
    "lights": [
        {"position": [0, 0], "type": "LED"},
        {"position": [0, 3], "type": "LED"},
        {"position": [3, 0], "type": "LED"},
        {"position": [3, 3], "type": "LED"},
    ],
    "confidence": 0.85  # How confident is this model?
}
```

### Step 3: Invent Simple Rules

**You just make up rules that sound reasonable!**

**Model A: "Uniform Grid Pattern"**
```python
def light_placement_model_a(grid):
    """
    Strategy: Place lights in a uniform grid pattern.
    Rule: One light every 3 meters (every 3 cells).
    """
    lights = []
    rows = len(grid)
    cols = len(grid[0])
    
    # Place light every 3 cells
    for row in range(0, rows, 3):
        for col in range(0, cols, 3):
            # Skip if this cell is invalid
            if grid[row][col] != -1:
                lights.append({
                    "position": [row, col],
                    "type": "LED"
                })
    
    return {
        "lights": lights,
        "confidence": 0.85,  # Just pick a number!
        "model": "uniform_grid"
    }
```

**Model B: "Perimeter Focus"**
```python
def light_placement_model_b(grid):
    """
    Strategy: Focus lights near walls/edges.
    Rule: Place lights 1 meter from edges.
    """
    lights = []
    rows = len(grid)
    cols = len(grid[0])
    
    # Place lights near edges
    for row in [1, rows-2]:  # Second row from top/bottom
        for col in range(1, cols, 2):  # Every other column
            if grid[row][col] != -1:
                lights.append({
                    "position": [row, col],
                    "type": "LED"
                })
    
    for col in [1, cols-2]:  # Second column from left/right
        for row in range(1, rows, 2):  # Every other row
            if grid[row][col] != -1:
                lights.append({
                    "position": [row, col],
                    "type": "LED"
                })
    
    return {
        "lights": lights,
        "confidence": 0.78,  # Different confidence
        "model": "perimeter_focus"
    }
```

**Model C: "Center-Heavy"**
```python
def light_placement_model_c(grid):
    """
    Strategy: More lights in the center of the room.
    Rule: Denser placement in middle third of grid.
    """
    lights = []
    rows = len(grid)
    cols = len(grid[0])
    
    center_start_row = rows // 3
    center_end_row = 2 * rows // 3
    center_start_col = cols // 3
    center_end_col = 2 * cols // 3
    
    for row in range(rows):
        for col in range(cols):
            if grid[row][col] == -1:
                continue
                
            # In center area: place more lights
            if (center_start_row <= row <= center_end_row and 
                center_start_col <= col <= center_end_col):
                # Every other cell in center
                if (row + col) % 2 == 0:
                    lights.append({
                        "position": [row, col],
                        "type": "LED"
                    })
            else:
                # Outside center: place fewer lights
                if (row % 3 == 0 and col % 3 == 0):
                    lights.append({
                        "position": [row, col],
                        "type": "LED"
                    })
    
    return {
        "lights": lights,
        "confidence": 0.92,  # Highest confidence
        "model": "center_heavy"
    }
```

---

## Why These Mocks Are Perfectly Fine

### 1. **They Have Different Behaviors**
```
Model A: Uniform grid    → 4 lights evenly spaced
Model B: Perimeter focus → 12 lights near edges
Model C: Center-heavy    → 9 lights, more in middle
```

This demonstrates your pipeline can handle **different model outputs**!

### 2. **They Have Different "Confidences"**
```
Model A: 0.85
Model B: 0.78
Model C: 0.92  ← "Best" model
```

This lets you demonstrate **model selection logic**!

### 3. **They Simulate Real ML Model Behavior**

Real ML models:
- Take time to run → Add `time.sleep(random.uniform(0.1, 0.5))`
- Return predictions → Your mocks do this
- Have confidence scores → Your mocks have this
- Can fail sometimes → You can randomly raise exceptions

```python
import time
import random

def light_placement_model_a(grid):
    # Simulate inference time
    time.sleep(random.uniform(0.1, 0.5))
    
    # Simulate occasional failures (5% of the time)
    if random.random() < 0.05:
        raise RuntimeError("Model inference failed - GPU out of memory")
    
    # Your mock logic here
    lights = [...]
    
    return {
        "lights": lights,
        "confidence": 0.85,
        "model": "uniform_grid"
    }
```

**From your pipeline's perspective, this is IDENTICAL to a real ML model!**

---

## The "I Don't Know The Right Answer" Problem

### You're Thinking:
> "But I don't know the CORRECT way to place lights!"

### The Truth:
**Neither do the interviewers, and it doesn't matter!**

**They're not going to:**
- ❌ Check if your light placement is "correct"
- ❌ Validate against building codes
- ❌ Compare to real architectural designs
- ❌ Care about the actual positions

**They're going to check:**
- ✅ Does your pipeline run multiple models in parallel?
- ✅ Does it select between them?
- ✅ Does it handle failures gracefully?
- ✅ Is it well-monitored?
- ✅ Is the code clean and well-structured?

---

## Visual Example: What Happens When Pipeline Runs

```python
# Your pipeline
def run_pipeline(grid):
    # Stage 1: Run 3 models in parallel
    with ThreadPoolExecutor() as executor:
        future_a = executor.submit(light_model_a, grid)
        future_b = executor.submit(light_model_b, grid)
        future_c = executor.submit(light_model_c, grid)
        
        result_a = future_a.result()  # {"lights": [4 positions], "confidence": 0.85}
        result_b = future_b.result()  # {"lights": [12 positions], "confidence": 0.78}
        result_c = future_c.result()  # {"lights": [9 positions], "confidence": 0.92}
    
    # Stage 2: Select best
    best = max([result_a, result_b, result_c], key=lambda x: x['confidence'])
    # best = result_c (confidence 0.92)
    
    # Stage 3: Use those lights for next models
    air_supply = air_supply_model(grid, best['lights'])
    smoke = smoke_detector_model(grid, best['lights'])
    
    return combine(best, air_supply, smoke)
```

**What the interviewer sees:**
```
✅ Three models ran in parallel (can see in logs/metrics)
✅ Pipeline selected model C (confidence-based selection)
✅ Sequential execution happened correctly
✅ Error handling works
✅ Metrics are collected
✅ Code is clean
```

**What the interviewer doesn't care about:**
```
❌ Whether position [2, 3] is the "correct" spot for a light
❌ If this would pass building inspection
❌ Whether a real architect would approve
```

---

## Real-World Parallel: How Companies Actually Build ML Systems

### Phase 1: Rules-Based (Before ML Models Exist)
```python
def recommend_products(user):
    """No ML model yet - just rules!"""
    if user.age < 25:
        return ["trendy_item_1", "trendy_item_2"]
    else:
        return ["classic_item_1", "classic_item_2"]
```

**The API, infrastructure, monitoring, pipelines are built around this!**

### Phase 2: Simple ML (Months Later)
```python
def recommend_products(user):
    """Now we have a simple ML model"""
    return simple_ml_model.predict(user)
```

**The pipeline stays the same! Just swap the function!**

### Phase 3: Complex ML (Year Later)
```python
def recommend_products(user):
    """Now we have a complex deep learning model"""
    return complex_dl_model.predict(user)
```

**Pipeline STILL the same!**

---

## How To Write Your Mocks Without Knowing "Right" Answers

### Step 1: Define Reasonable Constraints

```python
# Some basic rules that sound reasonable:
CONSTRAINTS = {
    "min_distance_between_lights": 2,  # At least 2 meters apart
    "max_lights": 20,  # Don't place too many
    "avoid_corners": True,  # Don't put lights in corners
}
```

### Step 2: Create Different Strategies

```python
# Strategy 1: Sparse placement
def sparse_strategy(grid):
    # Place few lights, far apart
    pass

# Strategy 2: Dense placement  
def dense_strategy(grid):
    # Place many lights, close together
    pass

# Strategy 3: Balanced placement
def balanced_strategy(grid):
    # Middle ground
    pass
```

### Step 3: Just Implement Simple Logic!

```python
def light_placement_model_a(grid):
    """Mock model using simple rules"""
    lights = []
    
    # Rule: Place light every 3 cells, skip invalid cells
    for i in range(0, len(grid), 3):
        for j in range(0, len(grid[0]), 3):
            if grid[i][j] != -1:  # Not invalid
                lights.append({"position": [i, j], "type": "LED"})
    
    return {
        "lights": lights,
        "confidence": random.uniform(0.7, 0.95),  # Random confidence
        "model": "model_a"
    }
```

**Done! That's a perfectly valid mock!**

---

## The Key Insight

**In MLOps, the model is a black box:**

```python
# From the pipeline's perspective, these are IDENTICAL:

# Mock model
def model(input):
    # Simple rules
    return output

# Real ML model
def model(input):
    # Complex neural network with millions of parameters
    return output
```

**Both:**
- Take input ✅
- Return output ✅
- Have latency ✅
- Can fail ✅
- Need monitoring ✅

**Your pipeline doesn't care which one it is!**

---

## Practical Example: Complete Mock Models

```python
import time
import random

class LightPlacementModelA:
    """Mock model: Uniform grid pattern"""
    
    def predict(self, grid):
        # Simulate inference time (real models take time)
        time.sleep(random.uniform(0.1, 0.3))
        
        lights = []
        for i in range(0, len(grid), 3):
            for j in range(0, len(grid[0]), 3):
                if grid[i][j] != -1:
                    lights.append({
                        "position": [i, j],
                        "type": "LED",
                        "watts": 15
                    })
        
        return {
            "lights": lights,
            "confidence": 0.85,
            "model_name": "uniform_grid_v1",
            "inference_time_ms": random.uniform(100, 300)
        }


class LightPlacementModelB:
    """Mock model: Random placement with density control"""
    
    def predict(self, grid):
        time.sleep(random.uniform(0.15, 0.4))
        
        lights = []
        density = 0.3  # 30% of valid cells get lights
        
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] != -1 and random.random() < density:
                    lights.append({
                        "position": [i, j],
                        "type": "LED",
                        "watts": 15
                    })
        
        return {
            "lights": lights,
            "confidence": random.uniform(0.75, 0.95),  # Varies!
            "model_name": "random_density_v2",
            "inference_time_ms": random.uniform(150, 400)
        }


class LightPlacementModelC:
    """Mock model: Center-focused with edge illumination"""
    
    def predict(self, grid):
        time.sleep(random.uniform(0.2, 0.5))
        
        lights = []
        rows, cols = len(grid), len(grid[0])
        center_row, center_col = rows // 2, cols // 2
        
        # Place lights based on distance from center
        for i in range(rows):
            for j in range(cols):
                if grid[i][j] == -1:
                    continue
                
                distance_from_center = abs(i - center_row) + abs(j - center_col)
                
                # Higher probability near center
                probability = max(0.1, 1.0 - (distance_from_center / (rows + cols)))
                
                if random.random() < probability:
                    lights.append({
                        "position": [i, j],
                        "type": "LED",
                        "watts": 15
                    })
        
        return {
            "lights": lights,
            "confidence": 0.92,  # This model is more "confident"
            "model_name": "center_focus_v1",
            "inference_time_ms": random.uniform(200, 500)
        }
```

**Usage in pipeline:**
```python
# These work EXACTLY like real ML models from pipeline perspective!

model_a = LightPlacementModelA()
model_b = LightPlacementModelB()
model_c = LightPlacementModelC()

# Run in parallel
with ThreadPoolExecutor() as executor:
    future_a = executor.submit(model_a.predict, grid)
    future_b = executor.submit(model_b.predict, grid)
    future_c = executor.submit(model_c.predict, grid)
    
    results = [f.result() for f in [future_a, future_b, future_c]]

# Select best based on confidence
best = max(results, key=lambda x: x['confidence'])

print(f"Selected {best['model_name']} with confidence {best['confidence']}")
```

---

## What You Show In Your Demo

**README.md:**
```markdown
## Mock Models

For this MVP, I've implemented three mock light placement models
with different strategies:

1. **Uniform Grid Model**: Places lights in a regular grid pattern
2. **Random Density Model**: Probabilistic placement with configurable density
3. **Center Focus Model**: Higher density near room center

Each model simulates realistic ML model behavior:
- Variable inference latency (100-500ms)
- Confidence scores (0.75-0.95)
- Occasional failures for fault tolerance testing

In production, these would be replaced with trained models while
the pipeline infrastructure remains identical.
```

**Interviewer thinks:** 
✅ "They understand the separation of concerns between models and infrastructure"  
✅ "They know how to build around uncertain/evolving components"  
✅ "They're pragmatic about MVPs"

---

## Final Answer To Your Question

**Q: How do I write mocks when I don't know the expected output?**

**A: You make up reasonable rules! The actual output doesn't matter for this assignment.**

**What matters:**
1. Different models give different outputs (shows variety)
2. Models have confidence scores (enables selection)
3. Models simulate real behavior (latency, failures)
4. Your pipeline handles all of this correctly

**What doesn't matter:**
1. Whether the light positions are "correct"
2. If a real architect would approve
3. If it meets building codes
4. The accuracy of the predictions

**Remember:** You're being evaluated on **infrastructure skills**, not **ML model skills**.

---

Does this finally click? The key is: **you're building the restaurant management system, not becoming a chef!**