"""Smoke detector placement model for ceiling grid."""

import time
import random

from src.models.base import BaseMLModel
from src.pipeline.data_models import Grid, ModelResult, ComponentType


class SmokeDetectorModel(BaseMLModel):
    """Smoke detector placement model.

    Places smoke detectors at center and corners for maximum coverage.
    Only places on EMPTY cells to preserve existing components.
    """

    def __init__(self):
        self.strategy = "coverage_based"
        self.target_positions = [
            (5, 5),
            (0, 0), (9, 0),
            (0, 9), (9, 9),
            (5, 0), (5, 9),
        ]

    def run(self, input_grid: Grid) -> ModelResult:
        """Execute smoke detector placement."""
        start_time = time.time()
        output_grid = input_grid.model_copy(deep=True)

        placed_count = self._place_smoke_detectors(output_grid)
        confidence = self._calculate_confidence(placed_count)
        execution_time = time.time() - start_time

        return ModelResult(
            model_name=self.get_name(),
            confidence=confidence,
            grid=output_grid,
            execution_time=execution_time
        )

    def get_name(self) -> str:
        return "smoke_detector_model"

    def _place_smoke_detectors(self, grid: Grid) -> int:
        """Place smoke detectors, only on EMPTY cells."""
        placed_count = 0

        for x, y in self.target_positions:
            cell = grid.get_cell(x, y)
            if cell and cell.component == ComponentType.EMPTY:
                if random.random() < 0.75:
                    grid.set_cell(x, y, ComponentType.SMOKE_DETECTOR)
                    placed_count += 1

            if placed_count >= 5:
                break

        return placed_count

    def _calculate_confidence(self, placed_count: int) -> float:
        """Calculate confidence based on number of placements."""
        if 4 <= placed_count <= 6:
            base_score = 0.90
        elif 3 <= placed_count <= 7:
            base_score = 0.75
        elif 2 <= placed_count <= 8:
            base_score = 0.60
        else:
            base_score = 0.40

        confidence = base_score + random.uniform(-0.03, 0.03)
        return max(0.0, min(1.0, confidence))
