from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, TYPE_CHECKING

from data.planetaryResources import *
from models.common import PITier
from models.map.common import iStaticDataExport, MapClient

if TYPE_CHECKING:
    from models.map.commodity import Commodity
    from models.map.system import System


@dataclass
class PlanetType(iStaticDataExport):
    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"].replace("Planet", "").replace("(", "").replace(")", "").strip()
            self.Id = properties["type_id"]

        self.client.ALL_PLANET_TYPES[self.Id] = self

    @cached_property
    def RawResources_Ids(self) -> List[int]:
        return [key for key, value in RAW_RESOURCE_TO_TYPE.items() if self.Id in value]

    @cached_property
    def RawResources_Names(self) -> List[Commodity]:
        return [self.client.ALL_COMMODITIES[res_id].name for res_id in self.RawResources_Ids]

    @cached_property
    def RawResources(self) -> Dict[int, Commodity]:
        return {res_id: self.client.ALL_COMMODITIES[res_id] for res_id in self.RawResources_Ids}


@dataclass
class Planet(iStaticDataExport):
    Type_Id: int = field(kw_only=True, default=0)
    System_Id: int = field(kw_only=True, default=0)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["planet_id"]
            self.System_Id = properties["system_id"]
            self.Type_Id = properties["type_id"]

        self.client.ALL_PLANETS[self.Id] = self

    @cached_property
    def Type(self) -> PlanetType:
        return self.client.ALL_PLANET_TYPES[self.Type_Id]

    @cached_property
    def RawResource_Ids(self) -> List[int]:
        return self.client.ALL_PLANET_TYPES[self.Type_Id].RawResources_Ids

    @cached_property
    def RawResource_Names(self) -> List[int]:
        return self.client.ALL_PLANET_TYPES[self.Type_Id].RawResources_Names

    @cached_property
    def System(self) -> System:
        return self.client.ALL_SYSTEMS[self.System_Id]

    def __getstate__(self):
        return (self.Name, self.Id, self.System_Id, self.Type_Id)

    def __setstate__(self, state):
        self.Name, self.Id, self.System_Id, self.Type_Id = state

    def __repr__(self) -> str:
        return f"Planet( Name={self.Name}#{self.Id}, System={self.System.Name}#{self.System_Id} )"
