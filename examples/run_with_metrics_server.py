#!/usr/bin/env python3
"""
Run Observable Pipeline + Start Metrics Server

This script:
1. Runs the ML pipeline (collecting metrics)
2. Starts the metrics HTTP server
3. Keeps server running so you can view metrics

Usage:
    cd src && uv run python ../examples/run_with_metrics_server.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from prometheus_client import start_http_server
import time


def main():
    print("=" * 80)
    print("STEP 1: RUNNING ML PIPELINE")
    print("=" * 80)
    print()

    # Run the pipeline (this will populate metrics)
    from examples.run_observable_pipeline import main as run_pipeline
    run_pipeline()

    print()
    print("=" * 80)
    print("STEP 2: STARTING METRICS SERVER")
    print("=" * 80)
    print()

    port = 8000
    print(f"Starting metrics server on port {port}...")
    print()
    print("View your metrics at:")
    print(f"  http://localhost:{port}/")
    print()
    print("You'll see metrics like:")
    print("  - ml_model_executions_total")
    print("  - ml_model_execution_duration_seconds")
    print("  - ml_model_confidence_score")
    print("  - ml_model_selected_total")
    print("  - ml_components_placed_total")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    # Start metrics server
    start_http_server(port)

    # Keep server running
    try:
        print("✅ Metrics server running...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down metrics server...")
        print("Goodbye!")


if __name__ == "__main__":
    main()
