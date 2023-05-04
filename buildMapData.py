from models.common import *
from models.map import *
from data.planetaryResources import *
import yaml
from typing import Any
import codecs
from time import perf_counter

DECIMAL_FORMAT = "{:.3f}"


all_map_data = AllData()

def LoadYaml(file_name: str)->Any:
    with codecs.open(file_name, 'r', encoding='utf-8', errors='ignore') as fdata:
        return yaml.safe_load(fdata)

def CreateMaps(file_path, obj) -> dict:
    yamlFile = LoadYaml(file_path)
    output = {}

    for key, value in yamlFile.items():
        newValue = obj()
        item_id = newValue.Update(value)
        if item_id == -1:
            continue
        if item_id is None:
            item_id = key
        if isinstance(item_id, str):
            item_id = int(item_id)
        output[item_id] = newValue

    return output


def LinkMaps(data, insert_data):
    for value in data.values():
        value.Link(insert_data)

def BuildMapData():
    start_first = perf_counter()
    all_map_data.Regions = CreateMaps("data/regions.en-us.yaml", Region)
    print(f"Regions Loaded in {DECIMAL_FORMAT.format(perf_counter()-start_first)} seconds")
    
    start = perf_counter()
    all_map_data.Constellations = CreateMaps("data/constellations.en-us.yaml", Constellation)
    print(f"Constellations Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    all_map_data.Systems = CreateMaps("data/systems.en-us.yaml", System)
    print(f"Systems Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    all_map_data.Stargates = CreateMaps("data/stargates.en-us.yaml", Stargate)
    print(f"Stargates Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    all_map_data.Planets = CreateMaps("data/planets.en-us.yaml", Planet)
    print(f"Planets Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    all_map_data.PlanetTypes = CreateMaps("data/planetTypes.yaml", PlanetType)
    print(f"Planet Types Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    start = perf_counter()
    all_map_data.Commodities = CreateMaps("data/planetSchematics.yaml", PIMaterial)
    print(f"Commodities Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    all_map_data.RawResources = RawResources

    print("\n=======All Data Loaded, starting links=========\n")

    LinkAllMaps(all_map_data)
    
    
    print(f"All data loaded: total time = {DECIMAL_FORMAT.format(perf_counter()-start_first)} seconds")

def LinkAllMaps(map_data: AllData, regions=True, constellations=True):
    if regions:
        start = perf_counter()
        LinkMaps(map_data.Regions, map_data.Constellations)
        print(f"Constellations Linked to Regions in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    if constellations:
        start = perf_counter()
        LinkMaps(map_data.Constellations, map_data.Systems)
        print(f"Systems linked to Constellations in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    LinkMaps(map_data.Stargates, map_data.Systems)
    print(f"Stargates linked to Systems in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    LinkMaps(map_data.Planets, map_data.PlanetTypes)
    print(f"Planet Types linked to Planets in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    start = perf_counter()
    LinkMaps(map_data.RawResources, map_data.PlanetTypes)
    LinkMaps(map_data.PlanetTypes, map_data.RawResources)
    print(f"Planet Types and Raw Resources linked in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    # start = perf_counter()
    # LinkMaps(RawResources, Commodities)
    # LinkMaps(Commodities, RawResources)
    # print(f"Commodity Production Chains Linked {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    LinkMaps(map_data.Systems, map_data.Planets)
    print(f"Planets linked to Systems in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    start = perf_counter()
    LinkMaps(map_data.Systems, map_data.Stargates)
    print(f"Systems linked to each other in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    return map_data

def PickleAll():
    all_map_data.PickleData()

def LoadPickles(regions=False, constellations=False)->AllData:
    all_map = AllData()
    all_map = all_map.PopulateFromPickles()
    return LinkAllMaps(all_map, regions=regions, constellations=constellations)
     

if __name__ == "__main__":
    BuildMapData()
    PickleAll()

    

