# Quick Start Guide

## Prerequisites

- Docker Desktop installed
- Docker Compose V2
- 4GB+ RAM available
- Ports 8080 and 5432 available

## Start the Stack

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait ~30 seconds for initialization
# Watch logs:
docker-compose logs -f airflow-init

# 3. Access Airflow UI
open http://localhost:8080

# Login credentials:
# Username: admin
# Password: admin
```

## Trigger the Pipeline

1. Go to http://localhost:8080
2. Find DAG: `ceiling_grid_pipeline`
3. Click the "Play" button (▶️) to trigger
4. Watch all 4 tasks turn green:
   - Light placement (parallel models)
   - Air supply placement
   - Smoke detector placement
   - **Visualization generation**
5. Click on tasks to view structured logs!

## View the Results

After the pipeline completes, open the interactive visualization:

```bash
# The latest visualization (always points to most recent run)
open data/output/grid_visualization_latest.html

# Or view all historical runs
ls -lh data/output/grid_visualization_*.html
```

This shows the grid at each stage with color-coded components!

**Note:** Each pipeline run creates a unique HTML file (with run_id), plus a "latest" copy for easy access.

## View Logs

```bash
# All services
docker-compose logs -f

# Just webserver
docker-compose logs -f airflow-webserver

# Just scheduler
docker-compose logs -f airflow-scheduler
```

## Stop the Stack

```bash
# Stop (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Troubleshooting

**Port 8080 already in use:**
```bash
# Check what's using it
lsof -i :8080

# Kill it or change port in docker-compose.yml
```

**Permission issues:**
```bash
# Fix permissions
sudo chown -R $(id -u):$(id -g) logs/
```

**DAG not showing up:**
```bash
# Check DAG is valid
docker-compose exec airflow-webserver airflow dags list

# Force refresh
docker-compose restart airflow-scheduler
```

## What's Running

- **Airflow Webserver** - http://localhost:8080 (UI)
- **Airflow Scheduler** - Background task runner
- **PostgreSQL** - localhost:5432 (Airflow metadata)

## Next Steps

After seeing it work:
- Check Phase 4 completion summary for architecture details
- See DEPLOYMENT.md for production considerations
- Review logs to see structured logging from Phase 3!
