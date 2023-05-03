from dataclasses import dataclass
from enum import Enum

class Universe(Enum):
    EDEN=1
    WORMHOLE=2
    
@dataclass
class Position():
    X: float
    Y: float
    Z: float
    Universe: Universe
    



