from models.common import *
import models.mapv2 as mapData
from data.planetaryResources import *
import yaml
from typing import Any
import codecs
from time import perf_counter
from pickle import dump, load
from math import floor

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

def CreateMaps(data, obj) -> dict:

    tick = floor(len(data)/240)
    tock = 0
    for index in data:
        tock +=1
        obj(properties=data[index])
        if tick%tock == 0 :
            print(".", end="")
    
    

class AllData():
    def __init__(self) -> None:
        BuildMapData()
        self.SetAllData()

    def SetAllData(self):
        self.Commodities = mapData.ALL_COMMODITIES
        self.Planet_Types = mapData.ALL_PLANET_TYPES
        self.Planets = mapData.ALL_PLANETS
        self.Stargates = mapData.ALL_STARGATES
        self.Systems = mapData.ALL_SYSTEMS
        self.Constellations = mapData.ALL_CONSTELLATIONS
        self.Regions = mapData.ALL_REGIONS

        self.PickleAttributes = [
            "Commodities", "Planet_Types", "Planets", "Stargates", "Systems", "Constellations", "Regions"
        ]

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
            with open(f"data/pickled_{attribute.lower()}", "rb") as pickleFile:
                 setattr(mapData, attribute.upper(), load(pickleFile))
        print("Data Loaded")


def BuildMapData():
    start = perf_counter()
    for key, value in data_files.items():
        print(f"Processing {key}")
        start = perf_counter()
        yamlFile = LoadYaml(key)
        print(f"{key} loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

        start = perf_counter()
        CreateMaps(yamlFile, value)
        print(f"\n{len(yamlFile)} {key} entries converted in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    CreateMaps(RawResources, mapData.Commodity)
    

     

if __name__ == "__main__":
    AllData()
    AllData.PickleAll()

    

