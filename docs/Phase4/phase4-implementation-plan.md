# Phase 4 - Implementation Plan: Production Deployment

**Status:** 📝 PLANNING
**Estimated Time:** ~2-2.5 hours
**Approach:** Combined Airflow + Docker Compose deployment
**Dependencies:** Phase 3 complete ✅

---

## 🎯 Phase 4 Objectives

Build a complete, production-ready deployment stack:

1. **Airflow DAG** - Orchestrate the ML pipeline with task dependencies
2. **Docker Compose** - Multi-service stack (Airflow + PostgreSQL + Pipeline)
3. **One-Command Demo** - `docker-compose up` = everything works
4. **Reviewer-Ready** - Easy to run, impressive to see, well-documented

---

## 🏗️ Architecture Overview

### The Complete Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐      ┌────────────────────┐        │
│  │  Airflow Webserver │      │  Airflow Scheduler │        │
│  │  (Port 8080)       │◄────►│  (Background)      │        │
│  │                    │      │                    │        │
│  │  - DAG UI          │      │  - Runs DAGs       │        │
│  │  - Task Logs       │      │  - Task Queue      │        │
│  └────────┬───────────┘      └──────────┬─────────┘        │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
│                          ▼                                   │
│                ┌──────────────────┐                          │
│                │   PostgreSQL     │                          │
│                │   (Port 5432)    │                          │
│                │                  │                          │
│                │  - Airflow DB    │                          │
│                │  - Task State    │                          │
│                └──────────────────┘                          │
│                                                               │
│  ┌────────────────────────────────────────────────┐         │
│  │         Pipeline Service (Optional)             │         │
│  │         (Port 8000)                             │         │
│  │                                                  │         │
│  │  - Metrics HTTP Endpoint (/metrics)            │         │
│  │  - Prometheus scraping target                  │         │
│  └────────────────────────────────────────────────┘         │
│                                                               │
│  ┌────────────────────────────────────────────────┐         │
│  │         Prometheus (Optional, commented)        │         │
│  │         (Port 9090)                             │         │
│  │                                                  │         │
│  │  - Scrapes pipeline metrics                    │         │
│  │  - Query interface                             │         │
│  └────────────────────────────────────────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Philosophy

**Minimal but Complete:**
- ✅ Airflow with LocalExecutor (no Redis/Celery complexity)
- ✅ PostgreSQL (Airflow metadata)
- ✅ Pipeline code mounted as volume (easy development)
- ✅ Prometheus optional (can enable later)

**Reviewer Experience:**
```bash
docker-compose up
# Wait 30 seconds
# Visit http://localhost:8080
# See DAG, trigger run, watch logs
# Done! ✅
```

---

## 📋 What We'll Build

### 1. Airflow DAG (`dags/ceiling_grid_pipeline_dag.py`)

**Structure:**
```python
DAG: ceiling_grid_pipeline
├── Task: run_parallel_light_models
│   ├── Executes: LightModelA, LightModelB, LightModelC
│   ├── Selects: Best model based on confidence
│   └── Duration: ~1s
│
├── Task: run_air_supply_placement
│   ├── Depends on: run_parallel_light_models
│   ├── Executes: AirSupplyModel
│   └── Duration: ~0.5s
│
└── Task: run_smoke_detector_placement
    ├── Depends on: run_air_supply_placement
    ├── Executes: SmokeDetectorModel
    └── Duration: ~0.5s

Total Duration: ~2s
Schedule: @daily (or manual trigger for demo)
```

**Key Features:**
- Uses PipelineRunner (observability built-in!)
- XCom for passing grid between tasks
- Structured logs visible in Airflow UI
- Task dependencies enforce sequential execution

### 2. Docker Compose (`docker-compose.yml`)

**Services:**

#### `postgres` (Airflow Metadata)
- Image: `postgres:13`
- Port: 5432
- Volume: PostgreSQL data
- Environment: Airflow database credentials

#### `airflow-init` (One-time Setup)
- Initializes Airflow database
- Creates admin user
- Runs once, then exits

#### `airflow-webserver` (UI)
- Image: `apache/airflow:2.8.1-python3.11`
- Port: 8080
- Depends on: postgres, airflow-init
- Volumes: DAGs folder, src code
- Command: `airflow webserver`

#### `airflow-scheduler` (Task Runner)
- Image: `apache/airflow:2.8.1-python3.11`
- Depends on: postgres, airflow-init
- Volumes: DAGs folder, src code
- Command: `airflow scheduler`

#### `pipeline-metrics` (Optional)
- Custom image with our code
- Port: 8000
- Serves /metrics endpoint
- Lightweight, runs continuously

#### `prometheus` (Optional, Commented Out)
- Image: `prom/prometheus`
- Port: 9090
- Scrapes pipeline-metrics
- Can enable by uncommenting

### 3. Dockerfile (`Dockerfile`)

**Purpose:** Package our pipeline code

**Strategy:** Extend official Airflow image
```dockerfile
FROM apache/airflow:2.8.1-python3.11

# Install our dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy our code
COPY src/ /opt/airflow/src/
COPY data/ /opt/airflow/data/

# Set Python path
ENV PYTHONPATH="/opt/airflow:${PYTHONPATH}"
```

**Why extend Airflow image?**
- Already has Python + Airflow
- No need to install Airflow separately
- Just add our dependencies

### 4. Environment Configuration (`.env`)

**Purpose:** Externalize configuration

**Contents:**
```bash
# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True

# PostgreSQL
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# Pipeline Configuration
GRID_INPUT_PATH=/opt/airflow/data/input/sample_grid.json
```

---

## 🔧 Implementation Steps

### Step 1: Create Airflow DAG (~30 min)

**File:** `dags/ceiling_grid_pipeline_dag.py`

**Requirements:**
- Import PipelineRunner, models
- Define DAG with @daily schedule
- Create 3 PythonOperator tasks
- Use XCom to pass grid between tasks
- Set task dependencies

**Key Code:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_parallel_light_models(**context):
    """Task 1: Run parallel light models, select best."""
    from src.pipeline.runner import PipelineRunner
    from src.models.light_models import LightModelA, LightModelB, LightModelC
    from src.pipeline.data_models import Grid
    import json

    # Load grid
    with open('/opt/airflow/data/input/sample_grid.json') as f:
        grid_data = json.load(f)
    input_grid = Grid(**grid_data)

    # Run parallel stage
    runner = PipelineRunner()
    light_models = [LightModelA(), LightModelB(), LightModelC()]
    result = runner.run_parallel_stage(light_models, input_grid, "parallel_light_placement")

    # Push to XCom
    context['task_instance'].xcom_push(key='grid_after_lights', value=result.grid.model_dump())
    return f"Selected {result.model_name} with confidence {result.confidence:.4f}"

def run_air_supply_placement(**context):
    """Task 2: Run air supply placement."""
    # Pull from XCom, run sequential stage, push to XCom
    ...

def run_smoke_detector_placement(**context):
    """Task 3: Run smoke detector placement."""
    # Pull from XCom, run sequential stage, done
    ...

with DAG(
    'ceiling_grid_pipeline',
    default_args=default_args,
    description='ML Pipeline for Ceiling Grid Component Placement',
    schedule_interval='@daily',
    start_date=datetime(2025, 11, 9),
    catchup=False,
    tags=['ml', 'pipeline', 'demo'],
) as dag:

    task1 = PythonOperator(
        task_id='run_parallel_light_models',
        python_callable=run_parallel_light_models,
    )

    task2 = PythonOperator(
        task_id='run_air_supply_placement',
        python_callable=run_air_supply_placement,
    )

    task3 = PythonOperator(
        task_id='run_smoke_detector_placement',
        python_callable=run_smoke_detector_placement,
    )

    task1 >> task2 >> task3  # Task dependencies
```

### Step 2: Create Dockerfile (~15 min)

**File:** `Dockerfile`

**Requirements:**
- Extend apache/airflow:2.8.1-python3.11
- Copy requirements.txt and install
- Copy src/ and data/ directories
- Set PYTHONPATH

### Step 3: Create docker-compose.yml (~45 min)

**File:** `docker-compose.yml`

**Requirements:**
- Define 5 services (postgres, airflow-init, webserver, scheduler, pipeline-metrics)
- Configure volumes (dags, src, data, postgres data)
- Set environment variables
- Configure healthchecks
- Set depends_on for proper startup order

**Key Sections:**

**PostgreSQL:**
```yaml
postgres:
  image: postgres:13
  environment:
    POSTGRES_USER: airflow
    POSTGRES_PASSWORD: airflow
    POSTGRES_DB: airflow
  volumes:
    - postgres-db-volume:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD", "pg_isready", "-U", "airflow"]
    interval: 5s
    retries: 5
```

**Airflow Webserver:**
```yaml
airflow-webserver:
  image: apache/airflow:2.8.1-python3.11
  depends_on:
    postgres:
      condition: service_healthy
    airflow-init:
      condition: service_completed_successfully
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
  volumes:
    - ./dags:/opt/airflow/dags
    - ./src:/opt/airflow/src
    - ./data:/opt/airflow/data
  ports:
    - "8080:8080"
  command: airflow webserver
```

### Step 4: Create .env File (~5 min)

**File:** `.env`

**Requirements:**
- Airflow configuration
- PostgreSQL credentials
- Pipeline paths

### Step 5: Create Setup Script (~10 min)

**File:** `scripts/setup.sh`

**Requirements:**
- Install Docker + Docker Compose (instructions)
- Initialize .env if not exists
- Create necessary directories
- Provide usage instructions

### Step 6: Test Locally (~20 min)

**Steps:**
1. Build images: `docker-compose build`
2. Start stack: `docker-compose up`
3. Wait for Airflow to initialize (~30s)
4. Access UI: http://localhost:8080
5. Login: admin/admin
6. Trigger DAG manually
7. Watch task logs
8. Verify success

### Step 7: Create Quick Start Guide (~15 min)

**File:** `docs/DEPLOYMENT.md`

**Requirements:**
- Prerequisites (Docker, Docker Compose)
- Quick start commands
- Accessing services (URLs)
- Troubleshooting common issues
- How to view logs
- How to stop/restart services

---

## 🧪 Testing Strategy

### Local Testing (Before Docker)

**Test DAG Python Code:**
```bash
cd dags
python3 -c "
import sys
sys.path.insert(0, '..')
from ceiling_grid_pipeline_dag import run_parallel_light_models
# Mock context
context = {'task_instance': MockTI()}
result = run_parallel_light_models(**context)
print(result)
"
```

**Expected:** Should run without errors

### Docker Testing

**Test 1: Build**
```bash
docker-compose build
```
**Expected:** All images build successfully

**Test 2: Database Initialization**
```bash
docker-compose up postgres airflow-init
```
**Expected:** Database initialized, admin user created

**Test 3: Start Services**
```bash
docker-compose up -d
```
**Expected:** All services start, webserver healthy

**Test 4: Access Airflow UI**
```
Visit: http://localhost:8080
Login: admin / admin
```
**Expected:** DAG visible in UI

**Test 5: Trigger DAG**
```
Click "ceiling_grid_pipeline"
Click "Trigger DAG" button
```
**Expected:**
- All 3 tasks execute
- Logs show structured logging output
- All tasks succeed (green)

**Test 6: View Logs**
```
Click on each task
Click "Log" button
```
**Expected:** Structured logs visible with model names, confidence scores

**Test 7: Check Metrics (Optional)**
```
Visit: http://localhost:8000/
```
**Expected:** Prometheus metrics visible

---

## 📊 What to Show Reviewers

### The Demo Flow

**Step 1: Start Everything**
```bash
docker-compose up -d
```
*"I'm using Docker Compose to spin up the entire stack - Airflow, PostgreSQL, and our pipeline service. This demonstrates containerization and orchestration skills."*

**Step 2: Access Airflow UI**
```
Open browser: http://localhost:8080
Login: admin / admin
```
*"Here's the Airflow UI. You can see our DAG 'ceiling_grid_pipeline' with 3 tasks representing our pipeline stages."*

**Step 3: Show DAG Structure**
```
Click on "ceiling_grid_pipeline"
Click "Graph" view
```
*"The graph shows task dependencies: parallel light placement → sequential air supply → sequential smoke detectors. This enforces the execution order."*

**Step 4: Trigger DAG**
```
Click "Trigger DAG" button
Watch tasks turn from white → yellow → green
```
*"I'm triggering a manual run. You can see tasks executing in real-time. The parallel task runs first, then the sequential tasks."*

**Step 5: View Logs**
```
Click "run_parallel_light_models" task
Click "Log" button
```
*"Here are the structured logs from Phase 3. Airflow captures all stdout, so our structlog output appears here with model names, confidence scores, and execution times."*

**Step 6: Show Metrics (Optional)**
```
Open new tab: http://localhost:8000/
```
*"And here are the Prometheus metrics we instrumented in Phase 3. In production, Prometheus would scrape this endpoint for monitoring and alerting."*

**Step 7: Explain Production Readiness**
*"For production, I'd add:
- Celery executor for distributed task execution
- Redis for task queue
- External PostgreSQL (RDS)
- Grafana dashboards
- Alert rules in Prometheus
- But for this demo, LocalExecutor is sufficient and shows the core concepts."*

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] Airflow DAG defined with 3 tasks
- [ ] Task dependencies correct (parallel → air → smoke)
- [ ] XCom passes data between tasks
- [ ] docker-compose.yml with all services
- [ ] `docker-compose up` starts everything
- [ ] Airflow UI accessible at :8080
- [ ] DAG visible and triggerable
- [ ] All tasks execute successfully
- [ ] Logs visible in Airflow UI

### Code Quality
- [ ] DAG code is clean and documented
- [ ] Dockerfile follows best practices
- [ ] docker-compose.yml is well-structured
- [ ] Environment variables externalized
- [ ] No hardcoded credentials

### Documentation
- [ ] README with quick start
- [ ] DEPLOYMENT.md with detailed instructions
- [ ] Troubleshooting section
- [ ] Architecture diagram (optional)

### Reviewer Experience
- [ ] One command to start everything
- [ ] Works on first try (no manual setup)
- [ ] Clear what to click/view
- [ ] Logs are readable
- [ ] Easy to stop/restart

---

## 🚧 Known Challenges & Solutions

### Challenge 1: Airflow Initialization Delay

**Problem:** Airflow takes 20-30s to initialize database

**Solution:**
- Use `airflow-init` service with `depends_on`
- Add healthchecks to postgres
- Document expected wait time

### Challenge 2: Python Path Issues

**Problem:** Airflow can't find `src` module

**Solutions:**
- Mount src/ as volume
- Set PYTHONPATH in docker-compose
- Use absolute imports in DAG

### Challenge 3: File Permissions (Mac/Linux)

**Problem:** PostgreSQL volume permission issues

**Solution:**
- Use named volume (not bind mount)
- Let Docker manage permissions

### Challenge 4: Port Conflicts

**Problem:** Port 8080 or 5432 already in use

**Solution:**
- Check running services: `lsof -i :8080`
- Change ports in docker-compose if needed
- Document in troubleshooting

---

## 📁 File Structure After Phase 4

```
room-ceiling-editor/
├── dags/                             # NEW: Airflow DAGs
│   └── ceiling_grid_pipeline_dag.py  # NEW: Main pipeline DAG
│
├── src/
│   ├── models/                       # UNCHANGED
│   ├── pipeline/                     # UNCHANGED
│   ├── utils/                        # UNCHANGED
│   └── api/                          # UNCHANGED
│
├── data/
│   └── input/
│       └── sample_grid.json          # UNCHANGED
│
├── examples/                         # UNCHANGED
│
├── tests/                            # UNCHANGED
│
├── docs/
│   ├── Phase4/
│   │   ├── phase4-implementation-plan.md  # This file
│   │   └── phase4-completion-summary.md   # After completion
│   ├── DEPLOYMENT.md                 # NEW: Deployment guide
│   └── ... (Phase 1-3 docs)
│
├── scripts/                          # NEW: Utility scripts
│   └── setup.sh                      # NEW: Setup helper
│
├── docker-compose.yml                # NEW: Multi-service stack
├── Dockerfile                        # NEW: Pipeline image
├── .env                              # NEW: Environment config
├── .dockerignore                     # NEW: Docker build exclusions
└── README.md                         # UPDATED: Quick start

Total new files: ~8
Total new code: ~300-400 lines
```

---

## ⏱️ Time Estimate Breakdown

1. **Create Airflow DAG** - 30 min
2. **Create Dockerfile** - 15 min
3. **Create docker-compose.yml** - 45 min
4. **Create .env file** - 5 min
5. **Create setup script** - 10 min
6. **Test locally** - 20 min
7. **Create deployment docs** - 15 min
8. **Fix issues & polish** - 20 min

**Total: ~2.5 hours**

**Why this is realistic:**
- Leveraging existing code (PipelineRunner, models)
- Using official Airflow image (don't build from scratch)
- LocalExecutor (simpler than Celery)
- No Kubernetes complexity

---

## 💡 Phase 4 Design Decisions

### Why LocalExecutor (Not CeleryExecutor)?

**LocalExecutor:**
- ✅ Simpler (no Redis, no workers)
- ✅ Sufficient for demo
- ✅ 3 services instead of 5+
- ✅ Still shows orchestration concepts

**CeleryExecutor:**
- Requires Redis
- Requires Celery workers
- Overkill for this demo
- Adds complexity without value for reviewers

**Decision:** LocalExecutor ✅

### Why XCom (Not Shared Volume)?

**XCom (Our Choice):**
- ✅ Native Airflow feature
- ✅ Shows understanding of Airflow
- ✅ Works with any executor
- ✅ Simple to implement

**Shared Volume:**
- Requires file I/O
- Harder to track data flow
- Not how Airflow is typically used

**Decision:** XCom ✅

### Why Not Kubernetes?

**Docker Compose (Our Choice):**
- ✅ Easy to run locally
- ✅ Reviewers can test easily
- ✅ Sufficient for demo
- ✅ Shows containerization skills

**Kubernetes:**
- Requires minikube/kind setup
- Complex for reviewers
- Overkill for take-home
- Shows off, not practical

**Decision:** Docker Compose ✅ (document K8s considerations)

---

## 🎓 What Phase 4 Demonstrates

### DevOps Skills
- ✅ **Docker** - Multi-stage builds, layer optimization
- ✅ **Docker Compose** - Multi-service orchestration
- ✅ **Airflow** - DAG design, task dependencies, XCom
- ✅ **Environment Management** - .env files, externalized config

### MLOps Skills
- ✅ **Pipeline Orchestration** - Task dependencies, retries
- ✅ **Observability Integration** - Logs in Airflow UI
- ✅ **Production Patterns** - Containerization, service separation

### Software Engineering
- ✅ **Infrastructure as Code** - Declarative docker-compose
- ✅ **Separation of Concerns** - DAG orchestration vs business logic
- ✅ **Documentation** - Deployment guides, troubleshooting

---

## 🚀 After Phase 4

**What's Working:**
- Complete ML pipeline
- Airflow orchestration
- Containerized deployment
- Observability (logs + metrics)
- One-command demo

**What's Left (Phase 5: Final Polish):**
- Comprehensive README
- Architecture diagram (optional)
- Video walkthrough (optional)
- Final testing on fresh machine

**Total Project:** 80-90% complete after Phase 4! 🎉

---

## ✅ Ready to Implement?

**Before we start:**
1. Review this plan
2. Ask any questions
3. Confirm you're ready

**When ready, we'll implement:**
1. Airflow DAG (30 min)
2. Docker setup (60 min)
3. Testing (20 min)
4. Documentation (15 min)

**Let's build this! 🚀**
