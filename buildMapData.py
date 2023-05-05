from models.common import *
import models.mapv2 as mapData
from data.planetaryResources import *
import yaml
from typing import Any, Dict, List
import codecs
from time import perf_counter
from pickle import dump, load
from math import floor
from functools import cached_property
import numpy
from dataclasses import dataclass, field

DECIMAL_FORMAT = "{:.3f}"


data_files = {
    "data/regions.en-us.yaml": mapData.Region,
    "data/constellations.en-us.yaml": mapData.Constellation,
    "data/systems.en-us.yaml": mapData.System,
    "data/stargates.en-us.yaml": mapData.Stargate,
    "data/planets.en-us.yaml": mapData.Planet,
    "data/planetTypes.yaml": mapData.PlanetType,
    "data/planetSchematics.yaml": mapData.Commodity,
}




def LoadYaml(file_name: str)->Any:
    with codecs.open(file_name, 'r', encoding='utf-8', errors='ignore') as fdata:
        return yaml.safe_load(fdata)

def CreateMaps(data, obj, client) -> dict:
    if isinstance(data, list):
        for item in list:
            obj(properties=item, client=client)
    else:
        for value in data.values():
            obj(properties=value, client=client)

    
    

class AllData():
    def __init__(self, skip_build:bool=False) -> None:
        self.MapClient = mapData.MapClient()
        self.PickleAttributes = [
            "Commodities", "Planet_Types", "Planets", "Stargates", "Systems", "Constellations", "Regions"
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

        

    def PickleAll(self):
        print("Picking Data")
        for attribute in self.PickleAttributes:
            with open(f"data/pickled_{attribute.lower()}", "wb") as pickleFile:
                print(f"Pickling {attribute} data")
                dump(getattr(self, attribute), pickleFile)
        print("Data Pickled")

    def PopulateFromPickles(self):
        print("Loading Pickled Data")
        for attribute in self.PickleAttributes:
            pickle_file_path = f"data/pickled_{attribute.lower()}"
            with open(pickle_file_path, "rb") as pickleFile:
                un_pickled_data=load(pickleFile)
                for item in un_pickled_data:
                    item.client=self.MapClient
                setattr(self.MapClient, f"ALL_{attribute.upper()}", un_pickled_data)
                 
        print("Data Loaded")

def BuildMapData(client: mapData.MapClient):
    first_start = perf_counter()
    for key, value in data_files.items():
        print(f"\n==== Processing {key} =====")
        start = perf_counter()
        yamlFile = LoadYaml(key)
        print(f"\t> {DECIMAL_FORMAT.format(perf_counter()-start)} seconds to load yaml file")

        start = perf_counter()
        CreateMaps(yamlFile, value, client)
        print(f"\t> {DECIMAL_FORMAT.format(perf_counter()-start)} seconds to convert {len(yamlFile)} entries")

    for value in RawResources:
        mapData.Commodity(properties=value, client=client)

    print(f"{DECIMAL_FORMAT.format(perf_counter()-first_start)} total run time.")
    

     

if __name__ == "__main__":
    data = AllData()
    data.PickleAll()

    

