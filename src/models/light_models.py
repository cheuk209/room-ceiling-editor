"""Light placement models for ceiling grid component placement."""

import time
import random
from abc import abstractmethod

from src.models.base import BaseMLModel
from src.pipeline.data_models import Grid, ModelResult, ComponentType


class LightPlacementModel(BaseMLModel):
    """Abstract base class for light placement models using Template Method pattern."""

    def run(self, input_grid: Grid) -> ModelResult:
        """Execute light placement model."""
        start_time = time.time()
        output_grid = input_grid.model_copy(deep=True)

        self._place_lights(output_grid)
        confidence = self._calculate_confidence(output_grid)
        execution_time = time.time() - start_time

        return ModelResult(
            model_name=self.get_name(),
            confidence=confidence,
            grid=output_grid,
            execution_time=execution_time
        )

    @abstractmethod
    def _place_lights(self, grid: Grid) -> None:
        """Place lights on grid using model-specific strategy."""
        pass

    def _calculate_confidence(self, grid: Grid) -> float:
        """Calculate confidence based on light coverage percentage."""
        counts = grid.count_components()
        total_cells = grid.width * grid.height
        lights = counts.get(ComponentType.LIGHT, 0)

        light_ratio = lights / total_cells if total_cells > 0 else 0

        if 0.25 <= light_ratio <= 0.35:
            base_score = 0.90
        elif 0.20 <= light_ratio <= 0.40:
            base_score = 0.75
        elif 0.15 <= light_ratio <= 0.45:
            base_score = 0.60
        else:
            base_score = 0.40

        confidence = base_score + random.uniform(-0.05, 0.05)
        return max(0.0, min(1.0, confidence))


class LightModelA(LightPlacementModel):
    """Dense light placement model (40% probability)."""

    def __init__(self):
        self.placement_probability = 0.40
        self.strategy = "dense"

    def get_name(self) -> str:
        return "light_model_a_dense"

    def _place_lights(self, grid: Grid) -> None:
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                if random.random() < self.placement_probability:
                    cell.component = ComponentType.LIGHT


class LightModelB(LightPlacementModel):
    """Sparse light placement model (15% probability)."""

    def __init__(self):
        self.placement_probability = 0.15
        self.strategy = "sparse"

    def get_name(self) -> str:
        return "light_model_b_sparse"

    def _place_lights(self, grid: Grid) -> None:
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                if random.random() < self.placement_probability:
                    cell.component = ComponentType.LIGHT


class LightModelC(LightPlacementModel):
    """Balanced light placement model (checkerboard pattern)."""

    def __init__(self):
        self.strategy = "balanced"

    def get_name(self) -> str:
        return "light_model_c_balanced"

    def _place_lights(self, grid: Grid) -> None:
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                if (cell.x + cell.y) % 2 == 0:
                    cell.component = ComponentType.LIGHT
