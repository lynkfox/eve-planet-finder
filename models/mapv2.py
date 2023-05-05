from __future__ import annotations
from dataclasses import dataclass, field, InitVar
from typing import Any, Dict, List
from functools import cached_property
from models.common import Position, Universe
from data.planetaryResources import RAW_RESOURCE_TO_TYPE
import re

ALL_COMMODITIES: List[Commodity] = []
ALL_PLANET_TYPES: List[PlanetType] = []
ALL_PLANETS: List[Planet] = []
ALL_STARGATES: List[Stargate] = []
ALL_SYSTEMS: List[System] = []
ALL_CONSTELLATIONS: List[Constellation] = []
ALL_REGIONS: List[Region] = []
MISSING = "ThisValueIsMissing"

@dataclass
class iStaticDataExport():
    properties: InitVar[Dict[str, Any]]
    Name: str = field(kw_only=True, default=None)
    Id: int = field(kw_only=True, default=0)

    def __hash__(self):
        return hash(self.Name, self.Id)
    
    def __eq__(self, __o):
        if isinstance(__o, Commodity):
            return self.Name == __o.Name and self.Id == __o.Id
        return False

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling """
        return (self.Name, self.Id)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id = state


        
@dataclass
class Commodity(iStaticDataExport):

    Tier: int = field(kw_only=True, default=1)
    Ingredient_Ids: List[int] = field(kw_only=True, default_factory=list)


    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["nameID"]["en"]
            for resourceID, resource in properties["types"].items():
                if resource["isInput"]:
                    self.Ingredient_Ids.append(resourceID)
                else:
                    self.Id = resourceID

        ALL_COMMODITIES.append(self)
    
    @cached_property
    def Ingredient_Names(self) -> List[str]:
        return [ingredient.Name for ingredient in ALL_COMMODITIES if ingredient.Id in self.Ingredient_Ids]

    
    def GetIngredients(self, cache:bool=False) -> List[Commodity]:
        ingredients = [ingredient for ingredient in ALL_COMMODITIES if ingredient.Id in self.Ingredient_Ids]
        if cache:
            self.Ingredients = ingredients
        return ingredients

    def __repr__(self) -> str:
        return f"Commodity( Name={self.Name}, Id={self.Id}, Tier={self.Tier}, Ingredients={self.IngredientNames} )"

    def __getstate__(self):
        return (self.Name, self.Id, self.Tier, self.Ingredient_Ids)

    def __setstate__(self, state):
        self.Name, self.Id, self.Tier, self.Ingredient_Ids = state


@dataclass
class PlanetType(iStaticDataExport):

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["nameID"]
            self.Id = properties["type_id"]

        ALL_PLANET_TYPES.append(self)

    @cached_property
    def RawResources_Ids(self) -> List[int]:
        return [key for key, value in RAW_RESOURCE_TO_TYPE if self.Id in value]
    
    @cached_property
    def RawResources_Names(self)->List[Commodity]:
        return [ingredient.Name for ingredient in ALL_COMMODITIES if ingredient.Id in self.RawResources_Ids]
            
    @cached_property
    def RawResources(self)->List[Commodity]:
        return [ingredient for ingredient in ALL_COMMODITIES if ingredient.Id in self.RawResources_Ids]
    
    

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

        ALL_PLANETS.append(self)

    
    @cached_property
    def Type_Name(self)->str:
        return next((pt.Name for pt in ALL_PLANET_TYPES if pt.Id == self.Type_Id), None)

    @cached_property
    def RawResource_Ids(self)-> List[int]:
        return self.GetType().RawResources_Ids

    @cached_property
    def RawResource_Names(self)->List[int]:
        return self.GetType().RawResources_Names

    def GetType(self, cache:bool=False) -> PlanetType:
        planet_type = next((pt for pt in ALL_PLANET_TYPES if pt.Id == self.Type_Id), None)
        if cache:
            self.Type = planet_type
        return planet_type

    def GetSystem(self, cache:bool=False) -> System:
        system = next((sys for sys in ALL_SYSTEMS if sys.Id == self.System_Id), None)
        if cache:
            self.System = system
        return system

    def __getstate__(self):
        return (self.Name, self.Id, self.System_Id, self.Type_Id)

    def __setstate__(self, state):
        self.Name, self.Id, self.System_Id, self.Type_Id = state


@dataclass
class Stargate(iStaticDataExport):
    DestinationSystem_Id: int = field(kw_only=True, default=0)
    OriginSystem_Id: int = field(kw_only=True, default=0)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["stargate_id"]
            self.OriginSystem_Id = properties["system_id"]
            self.DestinationSystem_Id = properties["destination"]["system_id"]

            ALL_STARGATES.append(self)
    
    @cached_property
    def DestinationSystem_Name(self) -> str:
        return next((sys.Name for sys in ALL_SYSTEMS if sys.Id == self.DestinationSystem_Id), None)

    @cached_property
    def DestinationSystem_Position(self)-> Position:
        return next((sys.Position for sys in ALL_SYSTEMS if sys.Id == self.DestinationSystem_Id), None)
    
    @cached_property
    def OriginSystem_Name(self)->str:
        return next((sys.Name for sys in ALL_SYSTEMS if sys.Id == self.OriginSystem_Id), None)

    @cached_property
    def OriginSystem_Position(self)-> Position:
        return next((sys.Position for sys in ALL_SYSTEMS if sys.Id == self.OriginSystem_Id), None)

    def GetDestinationSystem(self, cache:bool=False)-> System:
        destination =  next((sys for sys in ALL_SYSTEMS if sys.Id == self.DestinationSystem_Id), None)
        if cache:
            self.Destination = destination
        return destination

    def GetOriginSystem(self, cache:bool=False)-> System:
        destination =  next((sys for sys in ALL_SYSTEMS if sys.Id == self.OriginSystem_Id), None)
        if cache:
            self.Origin = destination
        return destination

    def __getstate__(self):
        return (self.Name, self.Id, self.DestinationSystem_Id, self.OriginSystem_Id)

    def __setstate__(self, state):
        self.Name, self.Id, self.DestinationSystem_Id, self.OriginSystem_Id = state

@dataclass
class System(iStaticDataExport):
    Position: Position = field(kw_only=True, default=None)
    Security_Status: float = field(kw_only=True, default=1.0)
    Planet_Ids: List[int] = field(kw_only=True, default_factory=list)
    LinkedSystem_Ids: List[int] = field(kw_only=True, default_factory=list)
    Constellation_Id: int = field(kw_only=True, default=0)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["system_id"]
            self.Planet_Ids = properties.get("planets", []) 
            self.LinkedSystem_Ids = properties.get("stargates", [])
            self.Security_Status = properties["security_status"]
            self.Constellation_Id = properties["constellation_id"]

            self.Position = Position(
                X=properties["position"]["x"],
                Y=properties["position"]["y"],
                Z=properties["position"]["z"],
                Universe=Universe.WORMHOLE if (re.match(r"J\d{6}", self.Name) is not None or self.Name in ["Thera", "J1226-0"]) else Universe.EDEN
            )

        if re.match(r"AD\d{3}$", self.Name) is not None or re.match(r"V-(\d{3})$", self.Name) is not None:
            ALL_SYSTEMS.append(self)

    @cached_property
    def LinkedSystem_Names(self)->List[str]:
        return [sys.name for sys in ALL_SYSTEMS if sys.id in self.LinkedSystem_Ids]

    @cached_property
    def Planet_Names(self)->List[str]:
        return [planet.name for planet in ALL_PLANETS if planet.id in self.Planet_Ids]

    @cached_property
    def Constellation_Name(self) -> int:
        return next((constellation.Name for constellation in ALL_CONSTELLATIONS if self.Id in constellation.System_Ids), None)
    
    def GetLinkedSystems(self, cache:bool=False) -> List[System]:
        systems =  [sys for sys in ALL_SYSTEMS if sys.id in self.LinkedSystem_Ids]
        if cache:
            self.Systems = systems
        
        return systems
        
    def GetPlanets(self, cache: bool=False) -> List[Planet]:
        planets = [planet for planet in ALL_PLANETS if planet.id in self.Planet_Ids]
        if cache:
            self.Planets=planets
        return planets

    def GetConstellation(self, cache: bool=False)-> Constellation:
        constellation = next((constellation for constellation in ALL_CONSTELLATIONS if self.Id in constellation.System_Ids), None)
        if cache:
            self.Constellation = constellation
        return constellation
    
    def __getstate__(self):
        return (self.Name, self.Id, self.Planet_Ids, self.LinkedSystem_Ids, self.Security_Status, self.Position, self.Constellation_Id)

    def __setstate__(self, state):
        self.Name, self.Id, self.Planet_Ids, self.LinkedSystem_Ids, self.Security_Status, self.Position, self.Constellation_Id  = state


@dataclass
class Constellation (iStaticDataExport):
    System_Ids:List[int] = field(kw_only=True, default_factory=list)
    Region_Id:int = field(kw_only=True, default=0)
    Position: Position = field(kw_only=True, default=None)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["constellation_id"]
            self.System_Ids = properties.get("systems", []) 
            self.Region_Id = properties["region_id"]

            self.Position = Position(
                X=properties["position"]["x"],
                Y=properties["position"]["y"],
                Z=properties["position"]["z"],
                Universe=Universe.EDEN
            )

        if re.match(r"ADC\d{2}", self.Name) is not None or re.match(r"VC-\d{3}", self.Name) is not None:
            ALL_CONSTELLATIONS.append(self)

    @cached_property
    def Region_Name(self)->str:
        return next((region.Name for region in ALL_REGIONS if self.id in region.Constellation_Ids), None)

    @cached_property
    def System_Ids(self)->List[int]:
        return [sys.id for sys in ALL_SYSTEMS if self.Id == sys.Constellation_Id]

    @cached_property
    def System_Names(self)->List[str]:
        return [sys.Name for sys in ALL_SYSTEMS if self.Id == sys.Constellation_Id]

    def GetRegion(self, cache:bool=False)->Region:
        region = next((region for region in ALL_REGIONS if self.id in region.Constellation_Ids), None)
        if cache:
            self.Region = region
        return region

    def GetSystems(self, cache:bool=False)->List[System]:
        systems = [sys for sys in ALL_SYSTEMS if self.Id == sys.Constellation_Id]
        if cache:
            self.Systems = systems
        
        return systems

    def __getstate__(self):
        return (self.Name, self.Id, self.System_Ids, self.Position, self.Region_Id )

    def __setstate__(self, state):
        self.Name, self.Id, self.System_Ids, self.Position, self.Region_Id  = state

@dataclass
class Region (iStaticDataExport):
    Constellation_Ids: list[int]  = field(kw_only=True, default_factory=list)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["name"]
            self.Id = properties["region_id"]
            self.Constellation_Ids = properties.get("constellations", [])


        if re.match(r"ADR\d{2}", self.Name) is not None or re.match(r"VR-\d{2}", self.Name) is not None:
            ALL_REGIONS.append(self)

    @cached_property
    def Constellation_Name(self)-> str:
        return next((constellation.Name for constellation in ALL_CONSTELLATIONS if self.Id == constellation.Region_id), None)

    def GetConstellations(self, cache:bool=False)->List[Constellation]:
        constellations = [constellation for constellation in ALL_CONSTELLATIONS if self.Id == constellation.Region_id]
        if cache:
            self.Constellations = constellations
        return constellations

    def __getstate__(self):
        return (self.Name, self.Id, self.Constellation_Ids, self.Position)

    def __setstate__(self, state):
        self.Name, self.Id, self.Constellation_Ids, self.Position  = state
