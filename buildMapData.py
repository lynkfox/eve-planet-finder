import codecs
from functools import cached_property
from pickle import dump, load
from time import perf_counter
from typing import Any, Union

import yaml
from alive_progress import alive_bar

import models.map as mapData
from data.planetaryResources import *
from models.common import *

data_files = {
    "data/regions.en-us.yaml": mapData.Region,
    "data/constellations.en-us.yaml": mapData.Constellation,
    "data/systems.en-us.yaml": mapData.System,
    "data/stargates.en-us.yaml": mapData.Stargate,
    "data/planets.en-us.yaml": mapData.Planet,
    "data/planetTypes.yaml": mapData.PlanetType,
    "data/planetSchematics.yaml": mapData.Commodity,
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
        self.MapClient = mapData.MapClient()
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

    def GetCommodity(self, value: Union[str, int]) -> mapData.Commodity:
        if isinstance(value, str):
            return next(commodity for commodity in self.Commodities if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Commodities if commodity.Id == value)

    def GetPlanetType(self, value: Union[str, int]) -> mapData.PlanetType:
        if isinstance(value, str):
            return next(commodity for commodity in self.PlanetTypes if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.PlanetTypes if commodity.Id == value)

    def GetPlanet(self, value: Union[str, int]) -> mapData.Planet:
        if isinstance(value, str):
            return next(commodity for commodity in self.Planets if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Planets if commodity.Id == value)

    def GetStargate(self, value: Union[str, int]) -> mapData.Stargate:
        if isinstance(value, str):
            return next(commodity for commodity in self.Stargates if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Stargates if commodity.Id == value)

    def GetSystem(self, value: Union[str, int]) -> mapData.System:
        if isinstance(value, str):
            return next(commodity for commodity in self.Systems if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Systems if commodity.Id == value)

    def GetConstellation(self, value: Union[str, int]) -> mapData.Constellation:
        if isinstance(value, str):
            return next(commodity for commodity in self.Constellations if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Constellations if commodity.Id == value)

    def GetRegion(self, value: Union[str, int]) -> mapData.Region:
        if isinstance(value, str):
            return next(commodity for commodity in self.Regions if commodity.Name == value)
        if isinstance(value, int):
            return next(commodity for commodity in self.Regions if commodity.Id == value)

    @cached_property
    def TotalEdenSystems(self) -> int:
        return len(
            [sys.Id for sys in self.Systems if sys.Position.Universe == Universe.EDEN and len(sys.LinkedSystem_Ids) > 0]
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
                for item in un_pickled_data:
                    item.client = self.MapClient
                setattr(self.MapClient, f"ALL_{attribute.upper()}", un_pickled_data)

        print("Map Data Loaded")


def BuildMapData(client: mapData.MapClient):

    with alive_bar(title_length=40) as bar:
        for key, value in data_files.items():
            bar.title(f"Processing {key}")
            yamlFile = LoadYaml(key)
            CreateMaps(yamlFile, value, client)

            bar()

        for value in RawResources:
            mapData.Commodity(properties=value, client=client)


if __name__ == "__main__":
    data = AllData()
    data.PickleAll()
