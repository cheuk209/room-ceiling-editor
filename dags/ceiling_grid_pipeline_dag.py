"""
Ceiling Grid ML Pipeline DAG

Orchestrates the complete ML pipeline with 4 stages:
1. Parallel: Run 3 light placement models, select best
2. Sequential: Air supply placement
3. Sequential: Smoke detector placement
4. Visualization: Generate interactive HTML showing all stages

The PipelineRunner handles all observability (logs + metrics),
so this DAG is just a thin orchestration layer.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json

# Default arguments for all tasks
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_parallel_light_models(**context):
    """
    Task 1: Parallel Light Placement

    Runs 3 light models in parallel, selects best based on confidence.
    PipelineRunner handles all logging and metrics.
    """
    from src.pipeline.runner import PipelineRunner
    from src.models.light_models import LightModelA, LightModelB, LightModelC
    from src.pipeline.data_models import Grid

    # Load input grid
    with open('/opt/airflow/data/input/sample_grid.json', 'r') as f:
        grid_data = json.load(f)
    input_grid = Grid(**grid_data)

    # Run parallel stage (PipelineRunner handles observability!)
    runner = PipelineRunner()
    light_models = [LightModelA(), LightModelB(), LightModelC()]
    result = runner.run_parallel_stage(
        light_models,
        input_grid,
        stage_name="parallel_light_placement"
    )

    # Push grid to XCom for next task
    context['ti'].xcom_push(key='grid_after_lights', value=result.grid.model_dump())

    # Return summary for Airflow UI
    counts = result.grid.count_components()
    from src.pipeline.data_models import ComponentType
    lights = counts.get(ComponentType.LIGHT, 0)

    return f"✅ Selected {result.model_name} | Confidence: {result.confidence:.4f} | Lights placed: {lights}"


def run_air_supply_placement(**context):
    """
    Task 2: Sequential Air Supply Placement

    Runs air supply model on grid from previous task.
    Preserves existing light placements.
    """
    from src.pipeline.runner import PipelineRunner
    from src.models.air_supply_model import AirSupplyModel
    from src.pipeline.data_models import Grid

    # Pull grid from previous task
    grid_data = context['ti'].xcom_pull(key='grid_after_lights', task_ids='run_parallel_light_models')
    input_grid = Grid(**grid_data)

    # Run sequential stage
    runner = PipelineRunner()
    air_model = AirSupplyModel()
    result = runner.run_sequential_stage(
        air_model,
        input_grid,
        stage_name="sequential_air_supply"
    )

    # Push grid to XCom for next task
    context['ti'].xcom_push(key='grid_after_air', value=result.grid.model_dump())

    # Return summary
    counts = result.grid.count_components()
    from src.pipeline.data_models import ComponentType
    air_supply = counts.get(ComponentType.AIR_SUPPLY, 0)

    return f"✅ Air supply placed: {air_supply} | Confidence: {result.confidence:.4f}"


def run_smoke_detector_placement(**context):
    """
    Task 3: Sequential Smoke Detector Placement

    Runs smoke detector model on grid from previous task.
    Preserves existing light and air supply placements.
    """
    from src.pipeline.runner import PipelineRunner
    from src.models.smoke_detector_model import SmokeDetectorModel
    from src.pipeline.data_models import Grid, ComponentType

    # Pull grid from previous task
    grid_data = context['ti'].xcom_pull(key='grid_after_air', task_ids='run_air_supply_placement')
    input_grid = Grid(**grid_data)

    # Run sequential stage
    runner = PipelineRunner()
    smoke_model = SmokeDetectorModel()
    result = runner.run_sequential_stage(
        smoke_model,
        input_grid,
        stage_name="sequential_smoke_detector"
    )

    # Push final grid to XCom for visualization task
    context['ti'].xcom_push(key='grid_final', value=result.grid.model_dump())

    # Return summary
    counts = result.grid.count_components()
    lights = counts.get(ComponentType.LIGHT, 0)
    air_supply = counts.get(ComponentType.AIR_SUPPLY, 0)
    smoke_detectors = counts.get(ComponentType.SMOKE_DETECTOR, 0)

    return (f"✅ Smoke detectors placed: {smoke_detectors} | "
            f"Total - Lights: {lights}, Air Supply: {air_supply}, Smoke: {smoke_detectors}")


def generate_visualization(**context):
    """
    Task 4: Generate HTML Visualization

    Creates an interactive HTML page showing the grid at each pipeline stage.
    Output saved to /opt/airflow/data/output/grid_visualization.html
    """
    from src.visualization.grid_renderer import GridHTMLRenderer
    from src.pipeline.data_models import Grid
    import os

    # Pull grids from all previous tasks
    grid_after_lights_data = context['ti'].xcom_pull(key='grid_after_lights', task_ids='run_parallel_light_models')
    grid_after_air_data = context['ti'].xcom_pull(key='grid_after_air', task_ids='run_air_supply_placement')
    grid_final_data = context['ti'].xcom_pull(key='grid_final', task_ids='run_smoke_detector_placement')

    # Load initial grid for comparison
    with open('/opt/airflow/data/input/sample_grid.json', 'r') as f:
        initial_grid_data = json.load(f)
    initial_grid = Grid(**initial_grid_data)

    # Reconstruct Grid objects from XCom data
    grid_after_lights = Grid(**grid_after_lights_data)
    grid_after_air = Grid(**grid_after_air_data)
    grid_final = Grid(**grid_final_data)

    # Prepare stages for visualization
    stages = [
        ("Initial Grid (Empty)", initial_grid),
        ("After Light Placement", grid_after_lights),
        ("After Air Supply Placement", grid_after_air),
        ("Final Grid (Complete)", grid_final),
    ]

    # Generate HTML visualization
    renderer = GridHTMLRenderer()
    output_dir = '/opt/airflow/data/output'
    os.makedirs(output_dir, exist_ok=True)

    # Include run_id in filename to keep historical versions
    run_id = context['run_id']
    output_filename = f'grid_visualization_{run_id}.html'
    output_path = os.path.join(output_dir, output_filename)

    # Also create a "latest" symlink for easy access
    latest_path = os.path.join(output_dir, 'grid_visualization_latest.html')

    renderer.render_pipeline_stages(stages, output_path)

    # Update latest symlink (copy the file, since symlinks might not work in all envs)
    import shutil
    shutil.copy2(output_path, latest_path)

    return f"✅ Visualization generated: {output_filename} (also saved as latest)"


# Define the DAG
with DAG(
    'ceiling_grid_pipeline',
    default_args=default_args,
    description='ML Pipeline for Ceiling Grid Component Placement',
    schedule_interval='@daily',  # Run daily, or trigger manually
    start_date=datetime(2025, 11, 9),
    catchup=False,  # Don't backfill past runs
    tags=['ml', 'pipeline', 'demo', 'mlops'],
) as dag:

    # Task 1: Parallel light placement
    task_parallel_lights = PythonOperator(
        task_id='run_parallel_light_models',
        python_callable=run_parallel_light_models,
        provide_context=True,
    )

    # Task 2: Sequential air supply
    task_air_supply = PythonOperator(
        task_id='run_air_supply_placement',
        python_callable=run_air_supply_placement,
        provide_context=True,
    )

    # Task 3: Sequential smoke detector
    task_smoke_detector = PythonOperator(
        task_id='run_smoke_detector_placement',
        python_callable=run_smoke_detector_placement,
        provide_context=True,
    )

    # Task 4: Generate HTML visualization
    task_visualization = PythonOperator(
        task_id='generate_visualization',
        python_callable=generate_visualization,
        provide_context=True,
    )

    # Define task dependencies (sequential pipeline with final visualization)
    task_parallel_lights >> task_air_supply >> task_smoke_detector >> task_visualization
