import codecs
import os
from functools import cached_property
from pickle import dump, load
from time import perf_counter
from typing import Any, Union

import yaml
from alive_progress import alive_bar

import logic.get_dotlan_maps as dotlan
import models.map as mapData
from logic.common import ProgressBar, try_parse
from logic.planetaryResources import *
from models.common import *
from models.third_party.dotlan import *

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
    def __init__(
        self, skip_build: bool = False, skip_dotlan_rebuild: bool = None, skip_dotlan_scrape: bool = None
    ) -> None:
        if skip_dotlan_rebuild is None:
            skip_dotlan_rebuild = skip_build

        if skip_dotlan_scrape is None:
            skip_dotlan_scrape = skip_build
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
        self.add_dotlan(skip_dotlan_rebuild, skip_dotlan_scrape)

    def add_dotlan(self, skip_build: bool, skip_scrape: bool):

        with alive_bar(len(dotlan.REGION_NAMES), title_length=40) as bar:
            dotlan.get_all_dotlan_data(
                self, build_data=not skip_build, progress_bar=ProgressBar(bar=bar), force_dotlan_scrape=not skip_scrape
            )

    def SetAllData(self):
        self.Commodities = self.MapClient.ALL_COMMODITIES
        self.Planet_Types = self.MapClient.ALL_PLANET_TYPES
        self.Planets = self.MapClient.ALL_PLANETS
        self.Stargates = self.MapClient.ALL_STARGATES
        self.Systems = self.MapClient.ALL_SYSTEMS
        self.Constellations = self.MapClient.ALL_CONSTELLATIONS
        self.Regions = self.MapClient.ALL_REGIONS

    def GetCommodity(self, value: Union[str, int]) -> mapData.Commodity:
        return next(item for item in self.Commodities if item.Name == value or item.Id == try_parse(int, value))

    def GetPlanetType(self, value: Union[str, int]) -> mapData.PlanetType:
        return next(item for item in self.PlanetTypes if item.Name == value or item.Id == try_parse(int, value))

    def GetPlanet(self, value: Union[str, int]) -> mapData.Planet:
        return next(item for item in self.Planets if item.Name == value or item.Id == try_parse(int, value))

    def GetStargate(self, value: Union[str, int]) -> mapData.Stargate:
        return next(item for item in self.Stargates if item.Name == value or item.Id == try_parse(int, value))

    def GetSystem(self, value: Union[str, int]) -> mapData.System:

        return next(item for item in self.Systems if item.Name == value or item.Id == try_parse(int, value))

    def GetConstellation(self, value: Union[str, int]) -> mapData.Constellation:
        return next(item for item in self.Constellations if item.Name == value or item.Id == try_parse(int, value))

    def GetRegion(self, value: Union[str, int]) -> mapData.Region:
        return next(item for item in self.Regions if item.Name == value or item.Id == try_parse(int, value))

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


def BuildMapData(client: mapData.MapClient, include_pi_data: bool = False):

    tasks = len(data_files)
    tasks += len(RawResources)
    os.system("cls" if os.name == "nt" else "clear")

    with alive_bar(tasks, title_length=40) as bar:
        for key, value in data_files.items():
            bar.title(f"Processing {key}")
            yamlFile = LoadYaml(key)
            CreateMaps(yamlFile, value, client)

            bar()

        for value in RawResources:
            bar.title(f"PI Calculations {value['nameID']['en']}")
            mapData.Commodity(properties=value, client=client)

            bar()


if __name__ == "__main__":
    data = AllData()
    # add_dotlan(data)
    data.PickleAll()
