# Phase 3 - Implementation Plan: Observability

**Status:** 📝 PLANNING
**Estimated Time:** ~1 hour (minimal approach for demo)
**Dependencies:** Phase 2 complete ✅

---

## 🎯 Phase 3 Objectives

Add lightweight observability to the ML pipeline:

1. **Structured Logging** - Console logs for key pipeline events
2. **Prometheus Instrumentation** - Code instrumented with prometheus-client
3. **Metrics Endpoint** - FastAPI `/metrics` endpoint (no Prometheus server)
4. **PipelineRunner** - Centralized observability via wrapper pattern
5. **Airflow Integration Ready** - Works with Airflow's built-in logging/metrics

---

## 🎯 Design Philosophy: Minimal But Production-Ready

### Why This Approach?

**The Problem:**
This is a **demo/take-home assignment**, not a production deployment. We need to show we understand observability without overengineering.

**The Solution: Option B - Lightweight Prometheus**

✅ **What we're doing:**
- Instrument application code with `prometheus-client`
- Create `/metrics` endpoint (can curl to see metrics)
- Console logs for human readability during demo
- PipelineRunner wraps models (separation of concerns)
- No Prometheus/Grafana servers (can add later in docker-compose)

✅ **Why this approach wins:**

**1. Demonstrates DevOps Skills:**
- Shows you know how to instrument applications
- Shows you understand Prometheus metrics (Counter, Histogram, Gauge)
- Shows you know about /metrics endpoint conventions

**2. Works With Airflow:**
- Airflow captures console logs automatically (viewable in UI)
- Airflow has built-in metrics via StatsD (task duration, success/failure)
- Our custom metrics complement Airflow (business logic vs orchestration)
- Can emit to Airflow's StatsD if needed: `from airflow.stats import Stats`

**3. Keeps It Simple:**
- No extra servers to run for basic demo
- Reviewers can `curl http://localhost:8000/metrics` to see metrics
- Console logs are immediately readable (no log parsing needed)
- Fast implementation (~1 hour vs 2.5 hours)

**4. Production-Ready Foundation:**
- Code is instrumented correctly
- Easy to add Prometheus server later (just docker-compose)
- Easy to switch logs to JSON (one config change)
- Follows industry best practices

**5. Avoids Redundancy:**
- Airflow already provides: task duration, success/failure, DAG metrics
- We add: model-specific metrics (confidence, component counts, selection)
- No overlap, complementary systems

### What We're NOT Doing (And Why)

❌ **No Prometheus Server:** Can add in Phase 5 (docker-compose), not needed for demo
❌ **No Grafana Dashboards:** Overkill for demo, shows in /metrics endpoint instead
❌ **No JSON Logs:** Console logs easier to read during demo, can switch to JSON later
❌ **No Distributed Tracing:** Out of scope for MVP demo

### Comparison: Our Approach vs Alternatives

| Approach | Pros | Cons | Our Choice |
|----------|------|------|------------|
| **Airflow Only** | Simplest, all-in-one | Doesn't show Prometheus knowledge | ❌ |
| **Full Prometheus Stack** | Complete monitoring | Overkill for demo, complex setup | ❌ |
| **Lightweight Prometheus** | Shows skills, works with Airflow, simple | Metrics not visualized (yet) | ✅ |

---

## 📊 What is Observability?

Observability answers 3 key questions for production systems:

1. **What happened?** → Logs (events, errors, context)
2. **How is it performing?** → Metrics (latency, throughput, errors)
3. **Why did it happen?** → Traces (request flow) - *Not in Phase 3 scope*

**For ML pipelines specifically:**
- Which model was selected and why? (confidence scores)
- How long did each model take to run? (latency)
- How many components were placed? (output quality)
- Did any models fail? (error rate)

---

## 🔍 Part 1: Minimal Console Logging with `structlog`

### Why Structured Logging (Even for Console)?

**Traditional logging:**
```python
print(f"Model {model_name} completed")
# ❌ No context, no structured fields
```

**Structured logging (our approach):**
```python
logger.info("model_execution_complete", model=model_name, confidence=confidence, duration_ms=execution_time*1000)
# Output: [info] model_execution_complete    model=light_model_a_dense confidence=0.8650 duration_ms=0.42
# ✅ Structured fields, colored console output, readable
# ✅ Can switch to JSON later with one config change
```

### Implementation Strategy

**1. Install `structlog`:**
```bash
uv add structlog colorama  # colorama for colored console output
```

**2. Create minimal logging configuration:**
`src/utils/logging_config.py` with:
- **Console renderer** with colors (human-readable)
- Timestamp processor
- Log level indicators
- Ready to switch to JSON if needed

**3. What to log (MINIMAL):**

Since this is a demo, we only log key events:

**Must log:**
- ✅ Pipeline start/end
- ✅ Model execution complete (with confidence, duration)
- ✅ Model selection (which model won)

**Skip:**
- ❌ Model execution start (too verbose)
- ❌ Cell-level operations (too detailed)
- ❌ Internal state changes (unnecessary)

**Log levels:**
- `INFO` - All normal operations
- `WARNING` - Only if confidence < 0.4 (unusually low)
- `ERROR` - Model execution failures

### Expected Log Output Example

```
[2025-11-09 10:30:45] [info] pipeline_start                 grid_id=sample_001
[2025-11-09 10:30:45] [info] parallel_stage_complete        models_run=3 best_model=light_model_a_dense confidence=0.8650
[2025-11-09 10:30:45] [info] model_execution_complete       model=air_supply_model components_placed=5 confidence=0.9174 duration_ms=0.32
[2025-11-09 10:30:45] [info] model_execution_complete       model=smoke_detector_model components_placed=5 confidence=0.8818 duration_ms=0.28
[2025-11-09 10:30:45] [info] pipeline_complete              total_duration_ms=2.15 lights=31 air_supply=5 smoke_detectors=5
```

**Benefits for demo:**
- Immediately readable (reviewers can scan it)
- Airflow will capture this output automatically
- Can switch to JSON for production with config change
- Shows you understand structured logging principles

---

## 📈 Part 2: Lightweight Prometheus Instrumentation

### Why Prometheus Client (Without Server)?

**The Goal:** Instrument our code to emit metrics, create `/metrics` endpoint

**What we're doing:**
- ✅ Install `prometheus-client` Python library
- ✅ Instrument pipeline with 4-5 key metrics
- ✅ Create FastAPI `/metrics` endpoint
- ✅ Reviewers can `curl http://localhost:8000/metrics` to see metrics

**What we're NOT doing (yet):**
- ❌ Running Prometheus server (can add in Phase 5)
- ❌ Grafana dashboards (overkill for demo)
- ❌ Complex metric cardinality (keep labels simple)

**Why this approach:**
- Shows you know how to instrument applications (DevOps skill)
- Shows you understand Prometheus metrics format
- Works with Airflow (Airflow can also emit metrics)
- Easy to add Prometheus server later (just docker-compose)

### Metric Types to Implement

**1. Counter - Counts that only increase**
```python
from prometheus_client import Counter

model_executions_total = Counter(
    'ml_model_executions_total',
    'Total number of model executions',
    ['model_name', 'stage']
)

# Usage:
model_executions_total.labels(model='light_model_a_dense', stage='parallel').inc()
```

**2. Histogram - Distribution of values**
```python
from prometheus_client import Histogram

model_execution_duration_seconds = Histogram(
    'ml_model_execution_duration_seconds',
    'Model execution time in seconds',
    ['model_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Usage:
with model_execution_duration_seconds.labels(model='light_model_a_dense').time():
    result = model.run(grid)
```

**3. Gauge - Value that can go up or down**
```python
from prometheus_client import Gauge

model_confidence_score = Gauge(
    'ml_model_confidence_score',
    'Confidence score of model output',
    ['model_name']
)

# Usage:
model_confidence_score.labels(model='light_model_a_dense').set(0.8650)
```

**4. Counter for component placements**
```python
components_placed_total = Counter(
    'ml_components_placed_total',
    'Total number of components placed',
    ['component_type', 'model_name']
)

# Usage:
components_placed_total.labels(component='light', model='light_model_a_dense').inc(30)
```

### Metrics to Track (MINIMAL SET)

For this demo, we'll track **5 essential metrics only:**

**1. Model Executions (Counter)**
```python
ml_model_executions_total{model_name="light_model_a_dense"} 1.0
```
Tracks how many times each model has run.

**2. Model Duration (Histogram)**
```python
ml_model_execution_duration_seconds_bucket{model_name="light_model_a_dense",le="0.01"} 1.0
ml_model_execution_duration_seconds_sum{model_name="light_model_a_dense"} 0.00042
ml_model_execution_duration_seconds_count{model_name="light_model_a_dense"} 1.0
```
Tracks model execution time distribution.

**3. Model Confidence (Gauge)**
```python
ml_model_confidence_score{model_name="light_model_a_dense"} 0.8650
```
Tracks latest confidence score (useful for monitoring degradation).

**4. Model Selection (Counter)**
```python
ml_model_selected_total{model_name="light_model_a_dense"} 1.0
```
Tracks which models get selected (for A/B testing analysis).

**5. Components Placed (Counter)**
```python
ml_components_placed_total{component_type="light"} 31.0
ml_components_placed_total{component_type="air_supply"} 5.0
```
Tracks output quality (how many components placed).

**That's it!** 5 metrics demonstrate you understand Prometheus without overengineering.

### Implementation Strategy

**1. Install prometheus-client:**
```bash
uv add prometheus-client
```

**2. Create metrics module:**
`src/utils/metrics.py` with:
- All metric definitions
- Helper functions for recording metrics
- Metric registry

**3. Create metrics server (optional for demo):**
`src/api/metrics_endpoint.py`:
- FastAPI endpoint at `/metrics`
- Exposes Prometheus metrics in text format
- Can be scraped by Prometheus server

**4. Add metrics collection to models:**
- Wrap `run()` method with timing
- Record confidence scores
- Count component placements
- Track errors

---

## 🏗️ Implementation Steps (Simplified)

### Step 1: Install Dependencies (~2 min)
```bash
uv add structlog colorama prometheus-client fastapi uvicorn
```

### Step 2: Create Logging Configuration (~10 min)
**File:** `src/utils/logging_config.py`

**Requirements:**
- Configure structlog with **console renderer** (colored output)
- Add timestamp, log level processors
- Simple `get_logger()` function
- ~30 lines of code

### Step 3: Create Metrics Module (~15 min)
**File:** `src/utils/metrics.py`

**Requirements:**
- Define 5 Prometheus metrics (as listed above)
- Simple, no helper functions needed
- ~40 lines of code

### Step 4: Create Pipeline Runner (~20 min)
**File:** `src/pipeline/runner.py` (new)

**Requirements:**
- PipelineRunner class with logging + metrics
- `run_parallel_stage()` - Runs 3 light models, selects best
- `run_sequential_stage()` - Runs air supply, then smoke detector
- Logs key events (minimal)
- Records metrics for all executions
- ~80 lines of code

**Example structure:**
```python
class PipelineRunner:
    def __init__(self):
        self.logger = get_logger()

    def run_parallel_stage(self, models: list[BaseMLModel], grid: Grid) -> ModelResult:
        """Run multiple models, select best, log + track metrics."""
        results = []
        for model in models:
            result = model.run(grid)
            # Log completion
            self.logger.info("model_complete", model=result.model_name, confidence=result.confidence)
            # Track metrics
            MODEL_EXECUTIONS.labels(model_name=result.model_name).inc()
            MODEL_DURATION.labels(model_name=result.model_name).observe(result.execution_time)
            results.append(result)

        best = max(results, key=lambda r: r.confidence)
        MODEL_SELECTED.labels(model_name=best.model_name).inc()
        self.logger.info("model_selected", model=best.model_name, confidence=best.confidence)
        return best
```

**Note:** Models stay unchanged! Observability is in the runner only.

### Step 5: Create Metrics Endpoint (~10 min)
**File:** `src/api/metrics_endpoint.py`

**Requirements:**
- FastAPI app with `/metrics` endpoint
- Expose Prometheus metrics in text format
- ~15 lines of code

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
def health():
    return {"status": "healthy"}
```

### Step 6: Create Demo Script (~10 min)
**File:** `examples/run_observable_pipeline.py`

**Requirements:**
- Imports PipelineRunner
- Runs full 3-stage pipeline
- Logs output to console (colored, readable)
- Prints message: "Metrics available at http://localhost:8000/metrics"
- ~50 lines of code

### Step 7: Update Tests (Optional, ~5 min)
**File:** `tests/test_observable_pipeline.py`

**Requirements:**
- Run pipeline via PipelineRunner
- Verify it completes successfully
- Check that metrics are recorded
- Simple smoke test

---

## 🧪 Testing Strategy

### Unit Tests
- Test logging configuration (JSON/console format)
- Test metric definitions (correct types, labels)
- Test helper functions

### Integration Tests
- Run pipeline with observability enabled
- Verify logs contain expected fields
- Verify metrics are incremented correctly
- Test error scenarios (logs + metrics)

### Manual Verification
```bash
# Run pipeline with JSON logs
python3 examples/run_observable_pipeline.py

# Expected output:
# {"event": "pipeline_start", "timestamp": "...", ...}
# {"event": "model_execution_complete", "model": "light_model_a_dense", ...}
# ...

# Check metrics (if endpoint running)
curl http://localhost:8000/metrics
# Expected output:
# ml_model_executions_total{model_name="light_model_a_dense"} 1.0
# ml_model_confidence_score{model_name="light_model_a_dense"} 0.865
# ...
```

---

## 📦 File Structure After Phase 3

```
room-ceiling-editor/
├── src/
│   ├── models/
│   │   ├── base.py                   # UNCHANGED
│   │   ├── light_models.py           # UNCHANGED
│   │   ├── air_supply_model.py       # UNCHANGED
│   │   └── smoke_detector_model.py   # UNCHANGED
│   │
│   ├── pipeline/
│   │   ├── data_models.py            # UNCHANGED
│   │   └── runner.py                 # NEW: PipelineRunner (observability wrapper)
│   │
│   ├── utils/                        # NEW: Utilities folder
│   │   ├── __init__.py               # NEW
│   │   ├── logging_config.py         # NEW: Structlog console config (~30 lines)
│   │   └── metrics.py                # NEW: 5 Prometheus metrics (~40 lines)
│   │
│   └── api/                          # NEW: API folder
│       ├── __init__.py               # NEW
│       └── metrics_endpoint.py       # NEW: FastAPI /metrics endpoint (~15 lines)
│
├── examples/                         # NEW: Runnable demos
│   └── run_observable_pipeline.py    # NEW: Demo with logging + metrics (~50 lines)
│
├── tests/
│   ├── test_phase1.py                # UNCHANGED
│   ├── test_all_light_models.py      # UNCHANGED
│   └── test_full_pipeline.py         # UNCHANGED (can optionally add PipelineRunner test)
│
└── docs/
    └── Phase3/
        ├── phase3-implementation-plan.md   # This file
        └── phase3-completion-summary.md    # After completion

Total new code: ~235 lines across 6 new files
```

---

## 🎓 Design Decisions & Best Practices

### 1. Structured Logging vs. Print Statements

**Why structlog?**
- Industry standard (used by Airbnb, Stripe, etc.)
- JSON output for log aggregation (ELK, Datadog, Splunk)
- Contextual logging (bind context once, appears in all logs)
- Easy to filter/query

### 2. Prometheus vs. Other Metrics Systems

**Why Prometheus?**
- Open-source, widely adopted
- Pull-based (scrapes metrics endpoints)
- Integrates with Grafana for dashboards
- Built-in alerting

**Alternatives considered:**
- StatsD - Push-based, requires extra daemon
- CloudWatch - AWS-specific
- Custom metrics - Reinventing the wheel

### 3. Where to Add Observability?

**Option A: In models themselves**
- ✅ Each model logs/tracks itself
- ❌ Models become aware of observability (coupling)
- ❌ Harder to change observability strategy

**Option B: In pipeline runner/orchestrator**
- ✅ Separation of concerns (models stay simple)
- ✅ Centralized observability logic
- ✅ Easier to modify/extend
- ❌ Pipeline runner needs to inspect model internals

**Recommendation:** Option B (pipeline runner) for cleaner architecture

### 4. Log Levels Strategy

**INFO:** Normal operations
- Pipeline start/end
- Model execution complete
- Model selection

**WARNING:** Unexpected but recoverable
- Low confidence score (< 0.5)
- Few components placed (< expected)
- Missing optional fields

**ERROR:** Failures that affect output
- Model execution failure
- Invalid grid state
- Missing required data

**DEBUG:** Detailed trace (disabled by default)
- Cell-level operations
- Internal state changes

---

## 🔄 Integration with Future Phases

### Phase 4: Airflow DAG
```python
# Airflow can consume these logs/metrics
task = PythonOperator(
    task_id='run_light_models',
    python_callable=run_observable_pipeline
)
# Logs appear in Airflow UI
# Metrics tracked per DAG run
```

### Phase 5: Docker Deployment
```yaml
# docker-compose.yml
services:
  pipeline:
    # App with /metrics endpoint
  prometheus:
    # Scrapes pipeline:8000/metrics
  grafana:
    # Visualizes Prometheus metrics
```

---

## ✅ Design Decisions (Already Made)

Based on discussion, here's what we're implementing:

**1. Logging Format:** Console logs with colors (structlog + colorama)
- Human-readable for demo
- Airflow captures automatically
- Can switch to JSON later with config change

**2. Observability Location:** PipelineRunner wrapper pattern
- Models stay unchanged
- Observability in orchestration layer
- Clean separation of concerns

**3. Metrics Endpoint:** Yes - FastAPI `/metrics` endpoint
- Shows you know how to expose metrics
- Can curl it during demo
- No Prometheus server needed (yet)

**4. Log Verbosity:** Minimal
- Only key events (pipeline start, model complete, selection)
- No excessive detail (this is a demo!)
- Easy to scan and understand

**5. Metrics Scope:** 5 essential metrics
- Executions (Counter)
- Duration (Histogram)
- Confidence (Gauge)
- Selection (Counter)
- Components placed (Counter)

---

## 📊 Success Criteria

**Functional Requirements:**
- [ ] Structured JSON logs generated for all pipeline events
- [ ] Prometheus metrics collected for all models
- [ ] Metrics endpoint exposes data in Prometheus format
- [ ] Logs include timestamp, model name, confidence, execution time
- [ ] Metrics include counters, histograms, and gauges

**Code Quality:**
- [ ] Logging/metrics code is reusable and DRY
- [ ] No impact on model logic (separation of concerns)
- [ ] Easy to enable/disable observability
- [ ] Clear documentation on what's logged/tracked

**Testing:**
- [ ] Pipeline runs successfully with observability enabled
- [ ] Logs are valid JSON and parseable
- [ ] Metrics increment correctly
- [ ] Demo script showcases observability clearly

**Documentation:**
- [ ] Phase 3 completion summary created
- [ ] Log format documented
- [ ] Metrics definitions documented
- [ ] Examples of using logs/metrics

---

## 🎯 What Phase 3 Demonstrates to Reviewers

### DevOps Excellence
- ✅ Production observability practices
- ✅ Structured logging for log aggregation
- ✅ Prometheus metrics for monitoring
- ✅ Understanding of logging vs. metrics use cases

### MLOps Knowledge
- ✅ Tracking model performance (confidence, latency)
- ✅ Monitoring model selection decisions
- ✅ Output quality metrics (components placed)
- ✅ Foundation for A/B testing analysis

### Software Engineering
- ✅ Separation of concerns (observability separate from logic)
- ✅ Dependency injection (logger/metrics as utilities)
- ✅ Open/Closed principle (add observability without modifying models)
- ✅ Industry-standard tools (structlog, Prometheus)

---

## ⏱️ Time Estimate Breakdown

**Step-by-step:**
1. Install dependencies - 2 min
2. Create logging config (`logging_config.py`) - 10 min
3. Create metrics module (`metrics.py`) - 15 min
4. Create pipeline runner (`runner.py`) - 20 min
5. Create metrics endpoint (`metrics_endpoint.py`) - 10 min
6. Create demo script (`run_observable_pipeline.py`) - 10 min
7. Testing & verification - 5 min

**Total: ~1 hour** (72 minutes)

**Why so fast?**
- Minimal logging (no JSON complexity)
- Only 5 metrics (no complex helpers)
- PipelineRunner is straightforward wrapper
- Models unchanged (no refactoring)
- No Prometheus/Grafana servers to configure

---

## 🚀 Implementation Ready!

**All decisions made:**
- ✅ Console logging (minimal, colored)
- ✅ PipelineRunner wrapper pattern
- ✅ 5 essential Prometheus metrics
- ✅ FastAPI `/metrics` endpoint
- ✅ No Prometheus server (yet)

**Estimated time:** ~1 hour

**When ready, we'll implement in order:**
1. Dependencies installation
2. Logging config
3. Metrics module
4. PipelineRunner
5. Metrics endpoint
6. Demo script
7. Quick test

**Ready to start whenever you are!** 🚀
