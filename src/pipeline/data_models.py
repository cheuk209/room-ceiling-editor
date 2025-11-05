from enum import Enum

class ComponentType(str, Enum):
    LIGHT = "light"
    AIR_SUPPLY = "air_supply"
    AIR_RETURN = "air_return"
    SMOKE_DETECTOR = "smoke_detector"
    EMPTY = "empty"
    INVALID = "invalid" 