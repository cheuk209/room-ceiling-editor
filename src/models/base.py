from abc import ABC, abstractmethod
from src.pipeline.data_models import Grid, ModelResult


class BaseMLModel(ABC):
    """Abstract base class defining the ML model interface.

    All ML models in the pipeline must inherit from this class and implement
    the required abstract methods.
    """

    @abstractmethod
    def run(self, input_grid: Grid) -> ModelResult:
        """Execute model inference on the input grid.

        Args:
            input_grid: The ceiling grid to process

        Returns:
            ModelResult containing the modified grid, confidence score,
            and execution metadata
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique identifier for this model.

        Returns:
            String identifier (e.g., 'light_model_a_dense')
        """
        pass