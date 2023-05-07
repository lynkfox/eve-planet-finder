from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from pickle import dump, load
from typing import Any, Dict, List, Union

from models.common import *


class iStaticDataExport:
    def Update(self) -> int:
        """Returns the ID of the static data object to be used as a key in a dict.

        Returns -1 if we want to ignore this entry in the SDE for some reason.
        """
        return NotImplementedError

    def Link(self, mapLink: Any):
        """Links up this object with id's in one of its link lists to ids in the mapLink (usually a dict)"""
        return NotImplementedError

    def to_dict(self):
        """Used to convert into a dict for json purposes or data_frame purposes."""
        output = {}
        for key, value in self.__dict__:

            if not key.starswith("_"):
                if isinstance(value, list):
                    continue
                output[key] = value
            else:
                if key.startswith("_pre"):
                    output[key] = value
                continue
        return output


@dataclass
class PotentialSite:
    SystemName: str
    SystemId: int
    Planets: List[Planet]
    PlanetType: PlanetType
    JumpsFromSource: int
    SourceSystemName: str

    def __eq__(self, __o: Union[PotentialSite, Any]) -> bool:
        if isinstance(__o, str):
            return self.SystemName == __o

        if isinstance(__o, int):
            return self.SystemId == __o

        if isinstance(__o, list):
            system_names = [site.SystemName for site in __o]
            system_ids = [site.SystemId for site in __o]

            return self.SystemId in system_ids and self.SystemName in system_names

        return self.SystemId == __o.SystemId and self.SystemName == __o.SystemName

    def __hash__(self) -> int:
        return hash(self.SystemName + str(self.SystemId))

    def __add__(self, right_hand: PotentialSite) -> PotentialSite:
        new_site = PotentialSite(
            SystemName=self.SystemName,
            SystemId=self.SystemId,
            PlanetType=self.PlanetType,
            JumpsFromSource=self.JumpsFromSource
            if self.JumpsFromSource >= right_hand.JumpsFromSource
            else right_hand.JumpsFromSource,
            SourceSystemName=self.SourceSystemName,
            Planets=self.Planets.extend(right_hand.Planets),
        )
        return new_site


@dataclass
class AllData:
    Regions: Dict[int, Region] = field(kw_only=True, default_factory=dict)
    Constellations: Dict[int, Constellation] = field(kw_only=True, default_factory=dict)
    Systems: Dict[int, System] = field(kw_only=True, default_factory=dict)
    Stargates: Dict[int, Stargate] = field(kw_only=True, default_factory=dict)
    Planets: Dict[int, Planet] = field(kw_only=True, default_factory=dict)
    PlanetTypes: Dict[int, PlanetType] = field(kw_only=True, default_factory=dict)
    RawResources: Dict[int, PIMaterial] = field(kw_only=True, default_factory=dict)
    Commodities: Dict[int, PIMaterial] = field(kw_only=True, default_factory=dict)

    def _getDispatch(self):
        return {
            "Regions": self.Regions,
            "Constellations": self.Constellations,
            "Systems": self.Systems,
            "Stargates": self.Stargates,
            "Planets": self.Planets,
            "PlanetTypes": self.PlanetTypes,
            "RawResources": self.RawResources,
            "Commodities": self.Commodities,
        }

    def PickleData(self):
        print("Picking Data")
        dispatch = self._getDispatch()
        for key, value in dispatch.items():
            with open(f"data/pickled_{key.lower()}", "wb") as pickleFile:
                print(f"Pickling {key} data")
                dump(value, pickleFile)
        print("Data Pickled")

    def PopulateFromPickles(self) -> AllData:
        output = {}
        print("Loading Pickled Data")
        dispatch = self._getDispatch()
        for key in dispatch.keys():
            with open(f"data/pickled_{key.lower()}", "rb") as pickleFile:
                output[key] = load(pickleFile)
        print("Data Loaded")

        return AllData(**output)


@dataclass
class PIMaterial(iStaticDataExport):
    Name: str = field(kw_only=True, default=0)
    Tier: int = field(kw_only=True, default=0)
    Id: int = field(kw_only=True, default=0)
    OnTypes: list[PlanetType] = field(kw_only=True, default_factory=list)
    Ingredients: list[PIMaterial] = field(kw_only=True, default_factory=list)
    Products: list[PIMaterial] = field(kw_only=True, default_factory=list)
    _pre_types: list[int] = field(kw_only=True, default_factory=list)
    _pre_ingredients: list[int] = field(kw_only=True, default_factory=list)
    _pre_products: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, schematic: Any) -> int:
        self.Name = schematic["nameID"]["en"]
        self._pre_ingredients = []
        self._pre_products = []
        for resourceID, resource in schematic["types"].items():
            if resource["isInput"]:
                self._pre_ingredients.append(resourceID)
            else:
                self.Id = resourceID

        return self.Id

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

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id, self._pre_ingredients, self._pre_products, self._pre_types)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_ingredients, self._pre_products, self._pre_types = state
        self.Ingredients = []
        self.Products = []
        self.OnTypes = []


@dataclass
class PlanetType(iStaticDataExport):
    Name: str = field(init=False, default="")
    Id: int = field(init=False, default=0)
    PlanetaryIndustryMaterials: list[PIMaterial] = field(init=False, default_factory=list)

    def Update(self, planetType: Any) -> int:
        self.Name = planetType["name"]
        self.Id = planetType["type_id"]
        self.PlanetaryIndustryMaterials = []
        return self.Id

    def Link(self, planetaryMaterials: dict):
        for value in planetaryMaterials.values():
            if self.Id in value._pre_types:
                self.PlanetaryIndustryMaterials.append(value)

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id = state
        self.PlanetaryIndustryMaterials = []


@dataclass
class Planet(iStaticDataExport):
    Name: str = field(init=False, default="")
    Id: int = field(init=False, default=0)
    System: System = field(init=False, default=None)
    Type: PlanetType = field(init=False, default=None)
    _pre_system_id: list[int] = field(kw_only=True, default_factory=list)
    _pre_type: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, system: Any) -> int:
        self.Name = system["name"]
        self.Id = system["planet_id"]
        self._pre_system_id = system["system_id"]
        self._pre_type = system["type_id"]
        return self.Id

    def Link(self, linkMap: Any):
        for value in linkMap.values():
            if isinstance(value, PlanetType):
                self.Type = linkMap[self._pre_type]
                return
            if isinstance(value, System):
                self.System - linkMap(self._pre_system_id)
                return

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id, self._pre_system_id, self._pre_type)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_system_id, self._pre_type = state
        self.Type = None
        self.System = None


@dataclass
class Stargate(iStaticDataExport):
    Name: str = field(init=False, default="")
    Id: int = field(init=False, default=0)
    DestinationSystem: System = field(init=False, default=None)
    _pre_destination_id: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, stargate: Any) -> int:
        self.Name = stargate["name"]
        self.Id = stargate["stargate_id"]
        self._pre_destination_id = stargate["destination"]["system_id"]
        return self.Id

    def Link(self, systems: dict):
        self.DestinationSystem = systems[self._pre_destination_id]

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (
            self.Name,
            self.Id,
            self._pre_destination_id,
        )

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_destination_id = state
        self.DestinationSystem = None


@dataclass
class System(iStaticDataExport):
    Name: str = field(init=False, default="")
    Id: int = field(init=False, default=0)
    Planets: list[Planet] = field(init=False, default_factory=list)
    Position: Position = field(init=False, default=None)
    Links: list[System] = field(init=False, default_factory=list)
    SecurityStatus: float = field(init=False, default=0.0)
    _pre_planets: list[int] = field(kw_only=True, default_factory=list)
    _pre_links: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, system: Any) -> int:
        self.Name = system["name"]
        if re.match(r"AD\d{3}$", self.Name) is not None or re.match(r"V-(\d{3})$", self.Name) is not None:
            return -1
        self.Id = system["system_id"]
        self.SecurityStatus = system["security_status"]
        self.Planets = []
        self._pre_planets = system.get("planets")
        self.Links = []
        self._pre_links = system.get("stargates")

        self.Position = Position(
            X=system["position"]["x"],
            Y=system["position"]["y"],
            Z=system["position"]["z"],
            Universe=Universe.WORMHOLE
            if (re.match(r"J\d{6}", self.Name) is not None or self.Name in ["Thera", "J1226-0"])
            else Universe.EDEN,
        )

        return self.Id

    def Link(self, linkMap: Any):
        for key, value in linkMap.items():
            if isinstance(value, Stargate) and self._pre_links is not None:

                for stargate_id in self._pre_links:
                    self.Links.append(linkMap[stargate_id].DestinationSystem)
                return

            if isinstance(value, Planet) and self._pre_planets is not None:
                for planet_data in self._pre_planets:
                    planet_id = planet_data.get("planet_id")
                    if planet_id is not None:
                        self.Planets.append(linkMap[planet_id])

                return

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id, self._pre_planets, self._pre_links, self.Position)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_planets, self._pre_links, self.Position = state
        self.Planets = []
        self.Links = []


@dataclass
class Constellation(iStaticDataExport):
    Id: int = field(init=False, default=0)
    Name: str = field(init=False, default="")
    Systems: list[System] = field(init=False, default_factory=list)
    _pre_systems: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, constellation: Any) -> int:
        self.Id = constellation["constellation_id"]
        self.Name = constellation["name"]
        if re.match(r"ADC\d{2}", self.Name) is not None or re.match(r"VC-\d{3}", self.Name) is not None:
            return -1
        self.Systems = []
        self._pre_systems = constellation["systems"]
        return self.Id

    def Link(self, systems: dict):
        for system_id in self._pre_systems:
            self.Systems.append(systems[system_id])

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id, self._pre_systems)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_systems = state
        self.Systems = []


@dataclass
class Region(iStaticDataExport):
    Id: int = field(init=False, default=0)
    Name: str = field(init=False, default="")
    Constellations: list[Constellation] = field(init=False, default_factory=list)
    _pre_constellations: list[int] = field(kw_only=True, default_factory=list)

    def Update(self, region: Any) -> int:
        self.Name = region["name"]
        if re.match(r"ADR\d{2}", self.Name) is not None or re.match(r"VR-\d{2}", self.Name) is not None:
            return -1
        self.Id = region["region_id"]
        self.Constellations = []
        self._pre_constellations = region["constellations"]
        return self.Id

    def Link(self, constellations: dict):

        for constellation_id in self._pre_constellations:
            self.Constellations.append(constellations[constellation_id])

    def __getstate__(self):
        """Ignores the recursive object values of other objects in pickling"""
        return (self.Name, self.Id, self._pre_constellations)

    def __setstate__(self, state):
        """Sets the values from the pickle and sets other objects as empty list. Expects LinkMap to be run after"""
        self.Name, self.Id, self._pre_constellations = state
        self.Constellations = []
