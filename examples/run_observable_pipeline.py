#!/usr/bin/env python3
"""
Observable ML Pipeline Demo

Demonstrates the complete pipeline with structured logging and Prometheus metrics:
- Stage 1: Parallel light placement models (3 models, select best)
- Stage 2: Sequential air supply placement
- Stage 3: Sequential smoke detector placement

Logs are output to console with structured fields.
Metrics can be viewed by running the metrics endpoint:
    uvicorn src.api.metrics_endpoint:app --port 8000
    Then visit: http://localhost:8000/metrics
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.light_models import LightModelA, LightModelB, LightModelC
from src.models.air_supply_model import AirSupplyModel
from src.models.smoke_detector_model import SmokeDetectorModel
from src.pipeline.data_models import Grid
from src.pipeline.runner import PipelineRunner


def main():
    print("=" * 80)
    print("OBSERVABLE ML PIPELINE DEMO - Phase 3")
    print("=" * 80)
    print()

    # Load input grid
    grid_path = project_root / "data" / "input" / "sample_grid.json"
    with open(grid_path, 'r') as f:
        grid_data = json.load(f)
    input_grid = Grid(**grid_data)

    print(f"Loaded grid: {input_grid.grid_id} ({input_grid.width}x{input_grid.height})")
    print()
    print("=" * 80)
    print("PIPELINE EXECUTION (Watch the structured logs below)")
    print("=" * 80)
    print()

    # Initialize models
    light_models = [LightModelA(), LightModelB(), LightModelC()]
    air_supply_model = AirSupplyModel()
    smoke_detector_model = SmokeDetectorModel()

    # Create pipeline runner (with observability)
    runner = PipelineRunner()

    # Run full pipeline
    final_result = runner.run_full_pipeline(
        light_models=light_models,
        air_supply_model=air_supply_model,
        smoke_detector_model=smoke_detector_model,
        input_grid=input_grid
    )

    # Display final results
    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print()

    final_counts = final_result.grid.count_components()
    from src.pipeline.data_models import ComponentType

    print("Component Breakdown:")
    for component_type in [ComponentType.LIGHT, ComponentType.AIR_SUPPLY,
                          ComponentType.SMOKE_DETECTOR, ComponentType.EMPTY,
                          ComponentType.INVALID]:
        count = final_counts.get(component_type, 0)
        print(f"  {component_type.value:20} : {count:3}")

    print()
    print("=" * 80)
    print("METRICS ENDPOINT")
    print("=" * 80)
    print()
    print("Prometheus metrics have been collected!")
    print("To view them, run in a separate terminal:")
    print()
    print("  cd src")
    print("  uv run python api/metrics_endpoint.py")
    print()
    print("Then visit:")
    print("  http://localhost:8000/  (All Prometheus metrics)")
    print()
    print("You'll see metrics like:")
    print("  - ml_model_executions_total")
    print("  - ml_model_execution_duration_seconds")
    print("  - ml_model_confidence_score")
    print("  - ml_model_selected_total")
    print("  - ml_components_placed_total")
    print()
    print("=" * 80)
    print("✅ PHASE 3 COMPLETE - Observability Working!")
    print("=" * 80)


if __name__ == "__main__":
    main()
