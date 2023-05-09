from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, TYPE_CHECKING

from data.planetaryResources import *
from models.common import PITier, Position, Universe
from models.map.common import iStaticDataExport, MapClient

if TYPE_CHECKING:
    from models.map.commodity import Commodity
    from models.map.planet import Planet, PlanetType


@dataclass
class Stargate(iStaticDataExport):
    DestinationSystem_Id: int = field(kw_only=True, default=0)
    DestinationName: str = field(kw_only=True, default="")
    OriginSystem_Id: int = field(kw_only=True, default=0)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["stargate_id"]
            self.OriginSystem_Id = properties["system_id"]
            self.DestinationSystem_Id = properties["destination"]["system_id"]
            self.DestinationSystem_Name = self.Name.replace("Stargate (", "")[:-1]

            self.client.ALL_STARGATES[self.Id] = self

    @cached_property
    def DestinationSystem(self) -> System:
        return self.client.ALL_SYSTEMS[self.DestinationSystem_Id]

    @cached_property
    def OriginSystem(self) -> System:
        return self.client.ALL_SYSTEMS[self.OriginSystem_Id]

    @cached_property
    def OriginSystem_Name(self) -> str:
        return self.client.ALL_SYSTEMS[self.OriginSystem_Id].Name

    def __getstate__(self):
        return (self.Name, self.Id, self.DestinationSystem_Id, self.OriginSystem_Id, self.DestinationSystem_Name)

    def __setstate__(self, state):
        self.Name, self.Id, self.DestinationSystem_Id, self.OriginSystem_Id, self.DestinationSystem_Name = state

    def __repr__(self) -> str:
        return f"Stargate( Name={self.Name}#{self.Id}, Origin={self.OriginSystem_Name}#{self.OriginSystem_Id}, Destination={self.DestinationSystem_Name}#{self.DestinationSystem_Id} )"


@dataclass
class System(iStaticDataExport):
    Position: Position = field(kw_only=True, default=None)
    Security_Status: float = field(kw_only=True, default=1.0)
    Planet_Ids: List[int] = field(kw_only=True, default_factory=list)
    Stargate_Ids: List[int] = field(kw_only=True, default_factory=list)
    Constellation_Id: int = field(kw_only=True, default=0)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["system_id"]
            self.Planet_Ids = [
                celestial.get("planet_id", None)
                for celestial in properties.get("planets", {})
                if celestial.get("planet_id", None) is not None
            ]
            self.Stargate_Ids = properties.get("stargates", [])
            self.Security_Status = properties["security_status"]
            self.Constellation_Id = properties["constellation_id"]

            # non accessible constellation, so dont add this system to the general list
            if self.Constellation_Id == 20000062:
                return

            self.Position = Position(
                X=properties["position"]["x"],
                Y=properties["position"]["y"],
                Z=properties["position"]["z"],
                Universe=Universe.WORMHOLE
                if (re.match(r"J\d{6}", self.Name) is not None or self.Name in ["Thera", "J1226-0"])
                else Universe.EDEN,
            )

        if re.match(r"AD\d{3}$", self.Name) is None and re.match(r"V-(\d{3})$", self.Name) is None:
            self.client.ALL_SYSTEMS[self.Id] = self

    @cached_property
    def LinkedSystem_Names(self) -> List[str]:
        return [self.client.ALL_STARGATES[sg_id].DestinationSystem_Name for sg_id in self.Stargate_Ids]

    @cached_property
    def LinkedSystem_Ids(self) -> List[int]:
        return [self.client.ALL_STARGATES[sg_id].DestinationSystem_Id for sg_id in self.Stargate_Ids]

    @cached_property
    def Stargates(self) -> Dict[int, Stargate]:
        return {sg_id: self.client.ALL_STARGATES[sg_id] for sg_id in self.Stargate_Ids}

    @cached_property
    def LinkedSystems(self) -> Dict[int, System]:
        return {
            self.client.ALL_STARGATES[sg_id].DestinationSystem_Id: self.client.ALL_STARGATES[sg_id].DestinationSystem
            for sg_id in self.Stargate_Ids
        }

    @cached_property
    def Planet_Names(self) -> List[str]:
        return [self.client.ALL_PLANETS[planet_id].Name for planet_id in self.Planet_Ids]

    @cached_property
    def Planets(self) -> Dict[int, Planet]:
        return {planet_id: self.client.ALL_PLANETS[planet_id] for planet_id in self.Planet_Ids}

    @cached_property
    def PlanetTypes(self) -> Dict[int, PlanetType]:
        return {planet_id: self.client.ALL_PLANETS[planet_id].PlanetType for planet_id in self.Planet_Ids}

    @cached_property
    def PlanetTypes_Ids(self) -> List[int]:
        return [self.client.ALL_PLANETS[planet_id].Type_Id for planet_id in self.Planet_Ids]

    @cached_property
    def PlanetTypes_Names(self) -> List[int]:
        return [self.client.ALL_PLANETS[planet_id].Type.Name for planet_id in self.Planet_Ids]

    @cached_property
    def Region_Name(self) -> str:
        return self.client.ALL_REGIONS[self.client.ALL_CONSTELLATIONS[self.Constellation_Id].Region_Id].Name

    @cached_property
    def Region_Id(self) -> int:
        return self.client.ALL_REGIONS[self.client.ALL_CONSTELLATIONS[self.Constellation_Id].Region_Id].Id

    @cached_property
    def Region(self) -> str:
        return self.client.ALL_REGIONS[self.client.ALL_CONSTELLATIONS[self.Constellation_Id].Region_Id]

    @cached_property
    def Constellation(self) -> Constellation:
        return self.client.ALL_CONSTELLATIONS[self.Constellation_Id]

    @cached_property
    def Constellation_Name(self) -> str:
        return self.client.ALL_CONSTELLATIONS[self.Constellation_Id].Name

    @cached_property
    def SingleSystemCommodities(self) -> Dict[PITier, List[int]]:
        tmp = {}
        reduced_items = [item for item in self.client.ALL_COMMODITIES.values()]  # if item.Tier != PITier.ADVANCED]
        combinations = {}
        number_of_planets = len(self.Planet_Ids)
        if number_of_planets >= 2:
            combinations[2] = permutations(self.PlanetTypes_Ids, 2)
        if number_of_planets >= 4:
            combinations[4] = permutations(self.PlanetTypes_Ids, 4)
        if number_of_planets >= 5:
            combinations[5] = permutations(self.PlanetTypes_Ids, 5)
        if number_of_planets >= 6:
            combinations[6] = permutations(self.PlanetTypes_Ids, 6)
        if number_of_planets >= 9:
            combinations[9] = permutations(self.PlanetTypes_Ids, 9)

        if number_of_planets >= 12:
            combinations[12] = permutations(self.PlanetTypes_Ids, 12)

        if number_of_planets >= 18:
            combinations[18] = permutations(self.PlanetTypes_Ids, 18)

        for key, value in combinations.items():
            tmp = []
            for item in value:
                tmp.append(hash(str(item)))
            combinations[key] = tmp

        temp = {}
        for commodity in reduced_items:
            number_of_commodity_planets = len(commodity.RawResources_Ids)
            if number_of_commodity_planets <= number_of_planets and number_of_commodity_planets > 1:
                for value in combinations[number_of_commodity_planets]:
                    if commodity.HashedPermutations.get(value, None) is not None:
                        temp.setdefault(commodity.Tier, []).append(commodity.Name)
                        break
            if number_of_commodity_planets == 1:
                if any(item in commodity.PlanetTypeId_Permutations[0] for item in self.PlanetTypes_Ids):
                    temp.setdefault(commodity.Tier, []).append(commodity.Name)
                    break

            # for set_of_planets in commodity.PlanetTypeId_Permutations:

            #     if commodity.Tier == PITier.RAW:
            #         if any( item in self.PlanetTypes_Ids for item in commodity.PlanetTypeId_Permutations):
            #             tmp.setdefault(commodity.Tier, []).append(commodity.Name)

            #     elif all( item in self.PlanetTypes_Ids for item in set_of_planets):
            #         tmp.setdefault(commodity.Tier, []).append(commodity.Name)

            #     break

        return temp

    def __getstate__(self):
        return (
            self.Name,
            self.Id,
            self.Planet_Ids,
            self.Stargate_Ids,
            self.Security_Status,
            self.Position,
            self.Constellation_Id,
        )

    def __setstate__(self, state):
        (
            self.Name,
            self.Id,
            self.Planet_Ids,
            self.Stargate_Ids,
            self.Security_Status,
            self.Position,
            self.Constellation_Id,
        ) = state

    def __repr__(self) -> str:
        return f"System( Name={self.Name}#{self.Id}, Universe={self.Position.Universe.name}, Constellation={self.Constellation_Name}#{self.Constellation_Id} )"
