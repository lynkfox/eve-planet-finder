from __future__ import annotations
from dataclasses import dataclass, field, fields
from models.common import *
from typing import Any, Dict
from pickle import dump, load

class iStaticDataExport():
    def Update(self)-> int:
        return NotImplementedError

    def Link(self):
        return NotImplementedError

@dataclass
class AllData():
    Regions: Dict[int, Region] = field(kw_only=True, default_factory=dict)
    Constellations: Dict[int, Constellation] = field(kw_only=True, default_factory=dict)
    Systems: Dict[int, System] = field(kw_only=True, default_factory=dict)
    Stargates: Dict[int, Stargate] = field(kw_only=True, default_factory=dict)
    Planets: Dict[int, Planet] = field(kw_only=True, default_factory=dict)
    PlanetTypes: Dict[int, PlanetType] = field(kw_only=True, default_factory=dict)
    RawResources: Dict[int, PIMaterial] = field(kw_only=True, default_factory=dict)
    Commodities: Dict[int, PIMaterial] = field(kw_only=True, default_factory=dict)

    def __post_init__(self):
        self._dispatch_map = {
            "Regions": self.Regions,
            "Constellations": self.Constellations,
            "Systems": self.Systems,
            "Stargates": self.Stargates,
            "Planets": self.Planets,
            "PlanetTypes": self.PlanetTypes,
            "RawResources": self.RawResources,
            "Commodities": self.Commodities
        }
    
    def PickleData(self):
        print("Picking Data")
        for key, value in self._dispatch_map.items():
            with open(f"data/pickled_{key.lower()}", "wb") as pickleFile:
                dump(value, pickleFile)
        print("Data Pickled")

    def PopulateFromPickles(self):
        output ={}
        print("Loading Pickled Data")
        for key in self._dispatch_map.keys():
            with open(f"data/pickled_{key.lower()}", "rb") as pickleFile:
                 output[key]=load(pickleFile)
        print("Data Loaded")
        return AllData(**output)
    

@dataclass
class PIMaterial(iStaticDataExport):
    Name: str = field(kw_only=True, default=0)
    Tier: int = field(kw_only=True, default=0)
    ResourceId: int  = field(kw_only=True, default=0)
    OnTypes: list[PlanetType] = field(kw_only=True, default_factory=list)
    Ingredients: list[PIMaterial] =field(kw_only=True, default_factory=list) 
    Products: list[PIMaterial] = field(kw_only=True, default_factory=list)
    _pre_types: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, schematic: Any)-> int:
        self.Name = schematic["nameID"]["en"]
        self._pre_ingredients = []
        self._pre_products = []
        for resourceID, resource in schematic["types"].items():
            if resource["isInput"]:
                self._pre_ingredients.append(resourceID)
            else:
                self.ResourceId = resourceID

        return self.ResourceId

    def Link(self, linkMap: dict):
        for key, value in linkMap.items():
            if isinstance(value, PlanetType):
                for planet_type in self._pre_types:
                    self.OnTypes.append(linkMap[planet_type])
                return
            if isinstance(value, PIMaterial):
                for resource_id in self._pre_products:
                    if linkMap.get(f"{resource_id}") is not None:
                        self.Products.append(linkMap.get(resource_id))

                for resource_id in self._pre_ingredients:
                    if linkMap.get(f"{resource_id}") is not None:
                        self.Products.append(linkMap.get(resource_id))
            
                return




    


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
    
    def Link(self, planetaryMaterials: dict):
        for value in planetaryMaterials.values():
            if self.TypeId in value._pre_types:
                self.PlanetaryIndustryMaterials.append(value)

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
        return self.PlanetId

    def Link(self, planetTypes: dict):
        self.Type = planetTypes[self._pre_type]

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
        self.DestinationSystem = systems[self._pre_destination_id]

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

    def Link(self, linkMap: Any):
        for key, value in linkMap.items():
            if isinstance(value, Stargate) and self._pre_links is not None:
                
                for stargate_id in self._pre_links:
                    self.Links.append(linkMap[stargate_id].DestinationSystem)
                return

            if isinstance(value, Planet) and self._pre_planets is not None:
                for planet_data in self._pre_planets:
                    planet_id = planet_data.get('planet_id')
                    if planet_id is not None:
                        self.Planets.append(linkMap[planet_id])
                
                return


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
            self.Systems.append(systems[system_id])

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
            self.Constellations.append(constellations[constellation_id])
    

