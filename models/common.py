from dataclasses import dataclass, field
from enum import Enum

DECIMAL_FORMAT = "{:.1f}"


class Universe(Enum):
    EDEN = 1
    WORMHOLE = 2
    JOVIAN = 3


class SecurityStatus(Enum):
    HIGH_SEC = 1
    LOW_SEC = 2
    NULL_SEC = 3


class WeightMethod(Enum):
    AVERAGE = 1
    TOTAL = 2


@dataclass
class Position:
    X: float
    Y: float
    Z: float
    Universe: Universe


@dataclass
class iWeightFactor:
    """interface for WeightFactors in the WeightCalculator

    Child classes should include anything in their attributes that is used in weight calculation that remains constant and doesn't change when moving
    to another node.
    """

    def DetermineSystemWeight(self, system, jumps_from_source):
        """
        Does the actual calculation of weight of a given system. Implemented in child classes.
        In order to work with WeightCalculator class, should maintain the same number of arguments in roughly the same order, but
        ignoring one or another as necessary is possible.

        :param system(System): The system being weighted.
        :param jumps_from_source(int): The jumps from the system being checked for radial proximity searches
        """
        raise NotImplementedError


@dataclass
class iWeightResult:
    """interface for Weight Results in the Weight Calculator"""

    WeightFactors: iWeightFactor = field(init=True)
    SortValue: int = field(init=False)

    def Populate(self, current_system, origin_system, jumps_from_source: int, weight: float):
        """Method to populate the details of the Child WeightResult class
        must return Self
        """
        raise NotImplementedError

    def Html(self) -> str:
        """Convert the str __repr__ of this object to HTML"""
        raise NotImplementedError
