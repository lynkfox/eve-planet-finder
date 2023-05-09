from __future__ import annotations

from dataclasses import dataclass, field, InitVar
from typing import Any, Dict, TYPE_CHECKING

from data.planetaryResources import *

if TYPE_CHECKING:
    from models.map.commodity import Commodity
    from models.map.galaxy import Constellation, Region
    from models.map.planet import Planet, PlanetType
    from models.map.system import Stargate, System


MISSING = "ThisValueIsMissing"


@dataclass
class MapClient:
    PLANET_TYPE_CONTAINS_RAW: Dict[int, Commodity] = field(init=False, default_factory=dict)
    ALL_COMMODITIES: Dict[int, Commodity] = field(init=False, default_factory=dict)
    ALL_PLANET_TYPES: Dict[int, PlanetType] = field(init=False, default_factory=dict)
    ALL_PLANETS: Dict[int, Planet] = field(init=False, default_factory=dict)
    ALL_STARGATES: Dict[int, Stargate] = field(init=False, default_factory=dict)
    ALL_SYSTEMS: Dict[int, System] = field(init=False, default_factory=dict)
    ALL_CONSTELLATIONS: Dict[int, Constellation] = field(init=False, default_factory=dict)
    ALL_REGIONS: Dict[int, Region] = field(init=False, default_factory=dict)
    BASIC_COMMODITIES: Dict[int, Commodity] = field(init=False, default_factory=dict)
    REFINED_COMMODITIES: Dict[int, Commodity] = field(init=False, default_factory=dict)
    SPECIALIZED_COMMODITIES: Dict[int, Commodity] = field(init=False, default_factory=dict)
    ADVANCED_COMMODITIES: Dict[int, Commodity] = field(init=False, default_factory=dict)


@dataclass
class iStaticDataExport:
    """
    Parent class to all SDE data models. Since they will all have a name and an ID, we can set these for some basic functionality.

    Mainly, hash and eq. Contains a primitive __getstate__ and __setstate__ for pickling but these should be redone for each
    """

    properties: InitVar[Dict[str, Any]]
    client: MapClient = field(init=True)
    Name: str = field(kw_only=True, default=None)
    Id: int = field(kw_only=True, default=0)

    def __hash__(self):
        return hash(self.Name, self.Id)

    def __eq__(self, __o):
        if type(self) == type(__o):
            return self.Name == __o.Name and self.Id == __o.Id
        return False

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id = state

    def __repr__(self) -> str:
        return f"{type(self)} ( Name={self.Name}#{self.Id} )"
