"""Observable pipeline runner for ML models.

Orchestrates model execution with structured logging and Prometheus metrics.
Separates observability concerns from model logic.
"""

import time
from typing import List

from src.models.base import BaseMLModel
from src.pipeline.data_models import Grid, ModelResult, ComponentType
from src.utils.logging_config import get_logger
from src.utils.metrics import (
    MODEL_EXECUTIONS,
    MODEL_DURATION,
    MODEL_CONFIDENCE,
    MODEL_SELECTED,
    COMPONENTS_PLACED
)


class PipelineRunner:

    def __init__(self):
        self.logger = get_logger("pipeline")

    def run_parallel_stage(
        self,
        models: List[BaseMLModel],
        input_grid: Grid,
        stage_name: str = "parallel_execution"
    ) -> ModelResult:
        """Run multiple models in parallel pipeline stage."""
        self.logger.info(
            "parallel_stage_start",
            stage=stage_name,
            num_models=len(models),
            grid_id=input_grid.grid_id
        )

        results = []
        for model in models:
            # Execute model
            result = model.run(input_grid)
            results.append(result)

            # Track metrics
            MODEL_EXECUTIONS.labels(model_name=result.model_name).inc()
            MODEL_DURATION.labels(model_name=result.model_name).observe(result.execution_time)
            MODEL_CONFIDENCE.labels(model_name=result.model_name).set(result.confidence)

            # Log completion
            self.logger.info(
                "model_execution_complete",
                model=result.model_name,
                confidence=round(result.confidence, 4),
                duration_ms=round(result.execution_time * 1000, 2),
                stage=stage_name
            )

        # Select best model based on confidence
        best_result = max(results, key=lambda r: r.confidence)

        # Track selection
        MODEL_SELECTED.labels(model_name=best_result.model_name).inc()

        # Log selection
        self.logger.info(
            "model_selected",
            selected_model=best_result.model_name,
            confidence=round(best_result.confidence, 4),
            candidate_models=len(results)
        )

        # Track components from best model
        counts = best_result.grid.count_components()
        for component_type, count in counts.items():
            if count > 0 and component_type not in [ComponentType.EMPTY, ComponentType.INVALID]:
                COMPONENTS_PLACED.labels(component_type=component_type.value).inc(count)

        return best_result

    def run_sequential_stage(
        self,
        model: BaseMLModel,
        input_grid: Grid,
        stage_name: str = "sequential_execution"
    ) -> ModelResult:
        """Run a single model in sequential pipeline stage.

        Args:
            model: Model to execute
            input_grid: Input grid (may contain components from previous stages)
            stage_name: Name of this pipeline stage for logging

        Returns:
            ModelResult from the model
        """
        model_name = model.get_name()

        self.logger.info(
            "sequential_stage_start",
            stage=stage_name,
            model=model_name,
            grid_id=input_grid.grid_id
        )

        # Execute model
        result = model.run(input_grid)

        # Track metrics
        MODEL_EXECUTIONS.labels(model_name=result.model_name).inc()
        MODEL_DURATION.labels(model_name=result.model_name).observe(result.execution_time)
        MODEL_CONFIDENCE.labels(model_name=result.model_name).set(result.confidence)

        # Track components placed (delta from input)
        input_counts = input_grid.count_components()
        output_counts = result.grid.count_components()

        for component_type, output_count in output_counts.items():
            input_count = input_counts.get(component_type, 0)
            delta = output_count - input_count
            if delta > 0:
                COMPONENTS_PLACED.labels(component_type=component_type.value).inc(delta)

        # Log completion
        self.logger.info(
            "model_execution_complete",
            model=result.model_name,
            confidence=round(result.confidence, 4),
            duration_ms=round(result.execution_time * 1000, 2),
            components_placed=sum(
                output_counts.get(ct, 0) - input_counts.get(ct, 0)
                for ct in [ComponentType.LIGHT, ComponentType.AIR_SUPPLY,
                          ComponentType.AIR_RETURN, ComponentType.SMOKE_DETECTOR]
            ),
            stage=stage_name
        )

        return result

    def run_full_pipeline(
        self,
        light_models: List[BaseMLModel],
        air_supply_model: BaseMLModel,
        smoke_detector_model: BaseMLModel,
        input_grid: Grid
    ) -> ModelResult:
        """Run complete 3-stage pipeline with observability.

        Args:
            light_models: List of light placement models (parallel execution)
            air_supply_model: Air supply placement model
            smoke_detector_model: Smoke detector placement model
            input_grid: Empty input grid

        Returns:
            Final ModelResult with all components placed
        """
        start_time = time.time()

        self.logger.info(
            "pipeline_start",
            grid_id=input_grid.grid_id,
            grid_size=f"{input_grid.width}x{input_grid.height}"
        )

        # Stage 1: Parallel light placement
        light_result = self.run_parallel_stage(
            light_models,
            input_grid,
            stage_name="parallel_light_placement"
        )

        # Stage 2: Sequential air supply
        air_result = self.run_sequential_stage(
            air_supply_model,
            light_result.grid,
            stage_name="sequential_air_supply"
        )

        # Stage 3: Sequential smoke detector
        final_result = self.run_sequential_stage(
            smoke_detector_model,
            air_result.grid,
            stage_name="sequential_smoke_detector"
        )

        # Pipeline complete
        total_duration = time.time() - start_time
        final_counts = final_result.grid.count_components()

        self.logger.info(
            "pipeline_complete",
            grid_id=input_grid.grid_id,
            total_duration_ms=round(total_duration * 1000, 2),
            lights=final_counts.get(ComponentType.LIGHT, 0),
            air_supply=final_counts.get(ComponentType.AIR_SUPPLY, 0),
            smoke_detectors=final_counts.get(ComponentType.SMOKE_DETECTOR, 0),
            empty=final_counts.get(ComponentType.EMPTY, 0)
        )

        return final_result
