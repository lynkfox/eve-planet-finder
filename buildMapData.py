import codecs
from functools import cached_property
from pickle import dump, load
from time import perf_counter
from typing import Any, TYPE_CHECKING, Union

import yaml
from alive_progress import alive_bar

from data.planetaryResources import *
from models.common import *
from models.map.common import MapClient

if TYPE_CHECKING:
    from models.map.commodity import Commodity
    from models.map.galaxy import Constellation, Region
    from models.map.planet import Planet, PlanetType
    from models.map.system import Stargate, System

data_files = {
    "data/regions.en-us.yaml": Region,
    "data/constellations.en-us.yaml": Constellation,
    "data/systems.en-us.yaml": System,
    "data/stargates.en-us.yaml": Stargate,
    "data/planets.en-us.yaml": Planet,
    "data/planetTypes.yaml": PlanetType,
    "data/planetSchematics.yaml": Commodity,
}


def LoadYaml(file_name: str) -> Any:
    with codecs.open(file_name, "r", encoding="utf-8", errors="ignore") as fdata:
        return yaml.safe_load(fdata)


def CreateMaps(data, obj, client) -> dict:
    if isinstance(data, list):
        for item in list:
            obj(properties=item, client=client)
    else:
        for value in data.values():
            obj(properties=value, client=client)


class AllData:
    def __init__(self, skip_build: bool = False) -> None:
        self.MapClient = MapClient()
        self.PickleAttributes = [
            "Commodities",
            "Planet_Types",
            "Planets",
            "Stargates",
            "Systems",
            "Constellations",
            "Regions",
        ]
        if skip_build:
            self.PopulateFromPickles()
        else:
            BuildMapData(self.MapClient)

        self.SetAllData()

    def SetAllData(self):
        self.Commodities = self.MapClient.ALL_COMMODITIES
        self.Planet_Types = self.MapClient.ALL_PLANET_TYPES
        self.Planets = self.MapClient.ALL_PLANETS
        self.Stargates = self.MapClient.ALL_STARGATES
        self.Systems = self.MapClient.ALL_SYSTEMS
        self.Constellations = self.MapClient.ALL_CONSTELLATIONS
        self.Regions = self.MapClient.ALL_REGIONS

    def GetCommodity(self, value: Union[str, int]) -> Commodity:
        if isinstance(value, str):
            return next(commodity for commodity in self.Commodities.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Commodities[value]

    def GetPlanetType(self, value: Union[str, int]) -> PlanetType:
        if isinstance(value, str):
            return next(commodity for commodity in self.PlanetTypes.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Planet_Types[value]

    def GetPlanet(self, value: Union[str, int]) -> Planet:
        if isinstance(value, str):
            return next(commodity for commodity in self.Planets.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Planets[value]

    def GetStargate(self, value: Union[str, int]) -> Stargate:
        if isinstance(value, str):
            return next(commodity for commodity in self.Stargates.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Stargates[value]

    def GetSystem(self, value: Union[str, int]) -> System:
        if isinstance(value, str):
            return next(commodity for commodity in self.Systems.values if commodity.Name == value)
        if isinstance(value, int):
            return self.Systems[value]

    def GetConstellation(self, value: Union[str, int]) -> Constellation:
        if isinstance(value, str):
            return next(commodity for commodity in self.Constellations.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Constellations[value]

    def GetRegion(self, value: Union[str, int]) -> Region:
        if isinstance(value, str):
            return next(commodity for commodity in self.Regions.values() if commodity.Name == value)
        if isinstance(value, int):
            return self.Regions[value]

    @cached_property
    def TotalEdenSystems(self) -> int:
        return len(
            [
                sys.Id
                for sys in self.Systems.values()
                if sys.Position.Universe == Universe.EDEN and len(sys.LinkedSystem_Ids) > 0
            ]
        )

    def PickleAll(self):
        print("Picking Data")
        for attribute in self.PickleAttributes:
            with open(f"data/pickled_{attribute.lower()}", "wb") as pickleFile:
                print(f"Pickling {attribute} data")
                dump(getattr(self, attribute), pickleFile)
        print("Data Pickled")

    def PopulateFromPickles(self):
        print("Loading Pickled Map Data")
        for attribute in self.PickleAttributes:
            pickle_file_path = f"data/pickled_{attribute.lower()}"
            with open(pickle_file_path, "rb") as pickleFile:
                un_pickled_data = load(pickleFile)
                for item in un_pickled_data.values():
                    item.client = self.MapClient
                setattr(self.MapClient, f"ALL_{attribute.upper()}", un_pickled_data)

        print("Map Data Loaded")


def BuildMapData(client: MapClient):

    with alive_bar(len(data_files), title_length=40) as bar:
        for key, value in data_files.items():
            bar.title(f"Processing {key}")
            yamlFile = LoadYaml(key)
            CreateMaps(yamlFile, value, client)

            bar()

        for value in RawResources:
            Commodity(properties=value, client=client)


if __name__ == "__main__":
    data = AllData()
    data.PickleAll()
