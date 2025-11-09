from prometheus_client import Counter, Histogram, Gauge


# 1. Model Executions - How many times each model has run
MODEL_EXECUTIONS = Counter(
    'ml_model_executions_total',
    'Total number of model executions',
    ['model_name']
)

# 2. Model Duration - Execution time distribution
MODEL_DURATION = Histogram(
    'ml_model_execution_duration_seconds',
    'Model execution time in seconds',
    ['model_name'],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# 3. Model Confidence - Latest confidence score per model
MODEL_CONFIDENCE = Gauge(
    'ml_model_confidence_score',
    'Latest confidence score from model output',
    ['model_name']
)

# 4. Model Selection - Which models get selected in parallel execution
MODEL_SELECTED = Counter(
    'ml_model_selected_total',
    'Total number of times a model was selected as best',
    ['model_name']
)

# 5. Components Placed - Output quality tracking
COMPONENTS_PLACED = Counter(
    'ml_components_placed_total',
    'Total number of components placed by type',
    ['component_type']
)
