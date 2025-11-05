from enum import Enum
from pydantic import BaseModel, Field, model_validator
from collections import Counter


class ComponentType(str, Enum):
    LIGHT = "light"
    AIR_SUPPLY = "air_supply"
    AIR_RETURN = "air_return"
    SMOKE_DETECTOR = "smoke_detector"
    EMPTY = "empty"
    INVALID = "invalid"

class Cell(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    component: ComponentType

class Grid(BaseModel):
    grid_id: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    cells: list[Cell]

    @model_validator(mode='after')
    def validate_grid(self) -> 'Grid':
        """Validate grid structure after all fields are set."""
        expected_cells = self.width * self.height
        if len(self.cells) != expected_cells:
            raise ValueError(
                f"Grid should have {expected_cells} cells "
                f"({self.width}x{self.height}), but has {len(self.cells)}"
            )

        for cell in self.cells:
            if not (0 <= cell.x < self.width):
                raise ValueError(
                    f"Cell x={cell.x} is out of bounds (must be 0-{self.width-1})"
                )
            if not (0 <= cell.y < self.height):
                raise ValueError(
                    f"Cell y={cell.y} is out of bounds (must be 0-{self.height-1})"
                )

        positions = {(cell.x, cell.y) for cell in self.cells}
        if len(positions) != len(self.cells):
            raise ValueError("Grid has duplicate cells at the same position")
        return self

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Retrieve a cell from the grid by its coordinates."""
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                return cell
        return None
    
    def set_cell(self, x: int, y: int, component: ComponentType) -> None:
        """
        Set or update a cell in the grid.
        """
        for cell in self.cells:
            if cell.x == x and cell.y == y:
                cell.component = component
                return
        self.cells.append(Cell(x=x, y=y, component=component))

    def count_components(self) -> dict[ComponentType, int]:
        """
        Count all component types in the grid.
        """
        return dict(Counter(cell.component for cell in self.cells))


class ModelResult(BaseModel):
    """
    We will have different model results, from different ML models.
    Once we get the results back, we will choose the best one based on confidence.
    """
    model_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    grid: Grid
    execution_time: float = Field(gt=0.0)  # in seconds