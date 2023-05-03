from __future__ import annotations
from dataclasses import dataclass, field
from models.common import *
from typing import Any

class iStaticDataExport():
    def Update(self)-> int:
        return NotImplementedError

    def Link(self):
        return NotImplementedError


@dataclass
class PIMaterial(iStaticDataExport):
    Name: str = field(init=False, default="")
    Tier: int = field(init=False, default=0)
    OnTypes: list[PlanetType] = field(init=False, default_factory=list)
    Ingredients: list[PIMaterial] =field(init=False, default_factory=list) 
    Products: list[PIMaterial] = field(init=False, default_factory=list)

    


@dataclass
class PlanetType(iStaticDataExport):
    Name: str = field(init=False, default="")
    TypeId: int = field(init=False, default=0)
    PlanetaryIndustryMaterials: list[PIMaterial] = field(init=False, default_factory=list)

    def Update(self, planetType:Any) -> int:
        self.Name = planetType["name"]
        self.TypeId = planetType["type_id"]
        self.PlanetaryIndustryMaterials = []
        return self.TypeId

@dataclass
class Planet(iStaticDataExport):
    Name: str = field(init=False, default="")
    PlanetId: int = field(init=False, default=0)
    System: System = field(init=False, default=None)
    Type: PlanetType = field(init=False, default=None)

    def Update(self, system: Any)-> int:
        self.Name = system["name"]
        self.PlanetId = system["planet_id"]
        self.SystemId = system["system_id"]
        self._pre_type = system["type_id"] 
        return self._pre_type

    def Link(self, planetTypes: dict):
        self.Type = planetTypes[f"{self._pre_type}"]

@dataclass
class Stargate(iStaticDataExport):
    Name: str = field(init=False, default="")
    StargateId: int = field(init=False, default=0)
    DestinationSystem: System = field(init=False, default=None)

    def Update(self, stargate: Any)-> int:
        self.Name = stargate["name"]
        self.StargateId = stargate["stargate_id"]
        self._pre_destination_id = stargate["destination"]["system_id"]
        return self.StargateId

    def Link(self, systems: dict):
        self.DestinationSystem = systems[f"{self._pre_destination_id}"]

@dataclass
class System(iStaticDataExport):
    Name: str = field(init=False, default="")
    SystemId: int = field(init=False, default=0)
    Planets: list[Planet]  = field(init=False, default_factory=list)
    Position: Position = field(init=False, default=None)
    Links: list[System]  = field(init=False, default_factory=list)

    def Update(self, system: Any) ->int:
        self.Name = system["name"]
        self.SystemId = system["system_id"]
        self.Planets = []
        self._pre_planets = system.get("planets")
        self.Links = []
        self._pre_links = system.get("stargates")
        self.Position = Position(
            X=system["position"]["x"],
            Y=system["position"]["y"],
            Z=system["position"]["z"],
            Universe=Universe.WORMHOLE if self.Name.startswith("J") and self.Name[1].isdigit() else Universe.EDEN
        )

        return self.SystemId

    def Link(self, stargates=None, planets=None):
        if stargates and self._pre_links is not None:
            
            for stargate_id in self._pre_links:
                self.Links.append(stargates[f"{stargate_id}"].DestinationSystem)
        if planets and self._pre_planets is not None:
            for planet_data in self._pre_planets:
                planet_id = planet_data.get('planet_id')
                if planet_id is not None:
                    self.Planets.append(planets[f"{planet_id}"])


@dataclass
class Constellation(iStaticDataExport):
    ConstellationId: int = field(init=False, default=0)
    Name: str = field(init=False, default="")
    Systems: list[System]  = field(init=False, default_factory=list)

    def Update(self, constellation: Any) -> int:
        self.ConstellationId = constellation["constellation_id"]
        self.Name = constellation["name"]
        self.Systems = []
        self._pre_systems = constellation["systems"]
        return self.ConstellationId

    def Link(self, systems:dict ):
        for system_id in self._pre_systems:
            self.Systems.append(systems[f"{system_id}"])

@dataclass
class Region(iStaticDataExport):
    RegionId: int = field(init=False, default=0)
    Name: str = field(init=False, default="")
    Constellations: list[Constellation]  = field(init=False, default_factory=list)

    def Update(self, region:Any)-> int:
        self.Name = region["name"]
        self.RegionId = region["region_id"]
        self.Constellations = []
        self._pre_constellations = region["constellations"]
        return self.RegionId

    def Link(self, constellations:dict):

        for constellation_id in self._pre_constellations:
            self.Constellations.append(constellations[f"{constellation_id}"])
    

