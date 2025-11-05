from abc import ABC, abstractmethod
from src.pipeline.data_models import Grid, ModelResult

class BaseMLModel(ABC):
    @abstractmethod
    def predict(self, grid: Grid) -> ModelResult:
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        pass