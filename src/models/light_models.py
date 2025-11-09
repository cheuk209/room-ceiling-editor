"""Light placement models for ceiling grid component placement."""

import time
import random
from abc import abstractmethod

from src.models.base import BaseMLModel
from src.pipeline.data_models import Grid, ModelResult, ComponentType


class LightPlacementModel(BaseMLModel):
    """Abstract base class for light placement models using Template Method pattern."""

    MIN_LIGHT_SPACING = 2  # Minimum distance between lights (Manhattan distance)

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

    def _is_valid_light_position(self, grid: Grid, x: int, y: int) -> bool:
        """
        Check if a position is valid for placing a light.

        A position is valid if there are no other lights within MIN_LIGHT_SPACING
        distance (Manhattan distance).
        """
        for cell in grid.cells:
            if cell.component == ComponentType.LIGHT:
                # Calculate Manhattan distance
                distance = abs(cell.x - x) + abs(cell.y - y)
                if distance < self.MIN_LIGHT_SPACING:
                    return False
        return True

    def _calculate_confidence(self, grid: Grid) -> float:
        """
        Calculate confidence based on light spacing quality.

        Rewards sparser, well-distributed placements with higher confidence.
        """
        counts = grid.count_components()
        total_cells = grid.width * grid.height
        lights = counts.get(ComponentType.LIGHT, 0)

        if lights == 0:
            return 0.0

        light_ratio = lights / total_cells if total_cells > 0 else 0

        # Calculate average spacing between lights (higher is better)
        avg_spacing = self._calculate_average_spacing(grid)

        # Base score favors sparse placements (10-20% coverage is ideal)
        if 0.10 <= light_ratio <= 0.20:
            base_score = 0.90
        elif 0.08 <= light_ratio <= 0.25:
            base_score = 0.75
        elif 0.05 <= light_ratio <= 0.30:
            base_score = 0.60
        else:
            base_score = 0.40

        # Bonus for good spacing (normalized by grid size)
        spacing_factor = min(avg_spacing / (grid.width + grid.height) * 2, 0.15)

        confidence = base_score + spacing_factor + random.uniform(-0.03, 0.03)
        return max(0.0, min(1.0, confidence))

    def _calculate_average_spacing(self, grid: Grid) -> float:
        """Calculate average minimum distance between lights."""
        light_positions = [
            (cell.x, cell.y)
            for cell in grid.cells
            if cell.component == ComponentType.LIGHT
        ]

        if len(light_positions) <= 1:
            return float(grid.width + grid.height)  # Max possible spacing

        total_min_distance = 0
        for i, (x1, y1) in enumerate(light_positions):
            min_distance = float('inf')
            for j, (x2, y2) in enumerate(light_positions):
                if i != j:
                    distance = abs(x1 - x2) + abs(y1 - y2)
                    min_distance = min(min_distance, distance)
            total_min_distance += min_distance

        return total_min_distance / len(light_positions)


class LightModelA(LightPlacementModel):
    """Dense light placement model - tries to place lights but respects spacing."""

    def __init__(self):
        self.placement_probability = 0.50  # Higher attempt rate
        self.strategy = "dense"

    def get_name(self) -> str:
        return "light_model_a_dense"

    def _place_lights(self, grid: Grid) -> None:
        """Place lights with spacing constraint - denser than sparse model."""
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                if random.random() < self.placement_probability:
                    # Only place if position is valid (respects spacing)
                    if self._is_valid_light_position(grid, cell.x, cell.y):
                        cell.component = ComponentType.LIGHT


class LightModelB(LightPlacementModel):
    """Sparse light placement model - prioritizes spacing quality."""

    def __init__(self):
        self.placement_probability = 0.25  # Lower attempt rate for sparse result
        self.strategy = "sparse"

    def get_name(self) -> str:
        return "light_model_b_sparse"

    def _place_lights(self, grid: Grid) -> None:
        """Place lights sparsely with strict spacing - should get high confidence."""
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                if random.random() < self.placement_probability:
                    # Only place if position is valid (respects spacing)
                    if self._is_valid_light_position(grid, cell.x, cell.y):
                        cell.component = ComponentType.LIGHT


class LightModelC(LightPlacementModel):
    """Balanced light placement model (modified checkerboard with spacing)."""

    def __init__(self):
        self.strategy = "balanced"

    def get_name(self) -> str:
        return "light_model_c_balanced"

    def _place_lights(self, grid: Grid) -> None:
        """Place lights in a balanced pattern with spacing constraint."""
        # Use a modified checkerboard pattern with spacing of 3
        for cell in grid.cells:
            if cell.component == ComponentType.EMPTY:
                # Pattern: every 3rd cell in both x and y
                if cell.x % 3 == 0 and cell.y % 3 == 0:
                    if self._is_valid_light_position(grid, cell.x, cell.y):
                        cell.component = ComponentType.LIGHT
