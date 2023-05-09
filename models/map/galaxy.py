from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, TYPE_CHECKING

from models.common import PITier, Position, Universe
from models.map.common import iStaticDataExport, MapClient

if TYPE_CHECKING:
    from models.map.system import System


@dataclass
class Constellation(iStaticDataExport):
    System_Ids: List[int] = field(kw_only=True, default_factory=list)
    Region_Id: int = field(kw_only=True, default=0)
    Position: Position = field(kw_only=True, default=None)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["constellation_id"]
            self.System_Ids = properties.get("systems", [])
            self.Region_Id = properties["region_id"]

            # non accessible constellation
            if self.Id == 20000062:
                return

            self.Position = Position(
                X=properties["position"]["x"],
                Y=properties["position"]["y"],
                Z=properties["position"]["z"],
                Universe=Universe.EDEN,
            )

        if re.match(r"ADC\d{2}", self.Name) is None and re.match(r"VC-\d{3}", self.Name) is None:
            self.client.ALL_CONSTELLATIONS[self.Id] = self

    @cached_property
    def Region_Name(self) -> str:
        return self.client.ALL_REGIONS[self.Region_Id].Name

    @cached_property
    def Region(self) -> Region:
        return self.client.ALL_REGIONS[self.Region_Id]

    @cached_property
    def System_Names(self) -> List[str]:
        return [self.client.ALL_SYSTEMS[sys_id].Name for sys_id in self.System_Ids]

    @cached_property
    def Systems(self) -> Dict[int, System]:
        return {sys_id: self.client.ALL_SYSTEMS[sys_id] for sys_id in self.System_Ids}

    def __getstate__(self):
        return (self.Name, self.Id, self.System_Ids, self.Position, self.Region_Id)

    def __setstate__(self, state):
        self.Name, self.Id, self.System_Ids, self.Position, self.Region_Id = state

    def __repr__(self) -> str:
        return f"Constellation( Name={self.Name}#{self.Id}, Region={self.Region_Name}#{self.Region_Id} )"


@dataclass
class Region(iStaticDataExport):
    Constellation_Ids: list[int] = field(kw_only=True, default_factory=list)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["region_id"]
            self.Constellation_Ids = properties.get("constellations", [])

        if re.match(r"ADR\d{2}", self.Name) is None and re.match(r"VR-\d{2}", self.Name) is None:
            self.client.ALL_REGIONS[self.Id] = self

    @cached_property
    def Constellation_Names(self) -> List[str]:
        return [self.client.ALL_CONSTELLATIONS[const_id].Name for const_id in self.Constellation_Ids]

    @cached_property
    def Constellations(self) -> Dict[int, Constellation]:
        return {const_id: self.client.ALL_CONSTELLATIONS[const_id].Name for const_id in self.Constellation_Ids}

    def __getstate__(self):
        return (self.Name, self.Id, self.Constellation_Ids)

    def __setstate__(self, state):
        self.Name, self.Id, self.Constellation_Ids = state

    def __repr__(self) -> str:
        return f"Constellation( Name={self.Name}#{self.Id} )"
