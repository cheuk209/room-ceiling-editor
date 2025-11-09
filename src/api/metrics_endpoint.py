"""Simple HTTP metrics endpoint for Prometheus scraping.

Exposes Prometheus metrics using built-in prometheus_client HTTP server.
Uses simple HTTP server instead of FastAPI to avoid dependency conflicts with Airflow.

Usage:
    python src/api/metrics_endpoint.py

Then visit: http://localhost:8000/
"""

from prometheus_client import start_http_server
import time


def main():
    """Start Prometheus metrics HTTP server."""
    port = 8000
    print("=" * 80)
    print("PROMETHEUS METRICS SERVER")
    print("=" * 80)
    print()
    print(f"Starting metrics server on port {port}...")
    print()
    print("Metrics endpoint:")
    print(f"  http://localhost:{port}/")
    print()
    print("Note: All metrics are exposed at the root path")
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    # Start Prometheus HTTP server (serves metrics at /)
    start_http_server(port)

    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down metrics server...")


if __name__ == "__main__":
    main()
