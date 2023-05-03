from models.common import *
from models.map import *
import yaml
from typing import Any
from pathlib import Path
import codecs
from time import perf_counter

DECIMAL_FORMAT = "{:.3f}"
Regions = {}
Constellations = {}
Systems = {}
Stargates = {}
Planets = {}
PlanetTypes = {}

def LoadYaml(file_name: str)->Any:
    with codecs.open(file_name, 'r', encoding='utf-8', errors='ignore') as fdata:
        return yaml.safe_load(fdata)

def CreateMaps(file_path, obj) -> dict:
    yamlFile = LoadYaml(file_path)
    output = {}

    for key, value in yamlFile.items():
        newValue = obj()
        newValue.Update(value)
        output[key] = newValue

    return output


def LinkMaps(data, insert_data):
    for value in data.values():
        value.Link(insert_data)

if __name__ == "__main__":
    start_first = perf_counter()
    Regions = CreateMaps("data/regions.en-us.yaml", Region)
    print(f"Regions Loaded in {DECIMAL_FORMAT.format(perf_counter()-start_first)} seconds")
    start = perf_counter()
    Constellations = CreateMaps("data/constellations.en-us.yaml", Constellation)
    print(f"Constellations Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()
    Systems = CreateMaps("data/systems.en-us.yaml", System)
    print(f"Systems Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()
    Stargates = CreateMaps("data/stargates.en-us.yaml", Stargate)
    print(f"Stargates Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()
    Planets = CreateMaps("data/planets.en-us.yaml", Planet)
    print(f"Planets Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()
    PlanetTypes = CreateMaps("data/planetTypes.yaml", PlanetType)
    print(f"Planet Types Loaded in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()

    LinkMaps(Regions, Constellations)
    print(f"Constellations Linked to Regions in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()

    LinkMaps(Constellations, Systems)
    print(f"Systems linked to Constellations in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()

    LinkMaps(Stargates, Systems)
    print(f"Stargates linked to Systems in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()

    start = perf_counter()
    LinkMaps(Planets, PlanetTypes)
    print(f"Planet Types linked to Planets in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")

    for system in Systems.values():
        system.Link(planets=Planets)
        

    print(f"Planets linked to Systems in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    start = perf_counter()
    for system in Systems.values():
        system.Link(stargates=Stargates)

    print(f"Systems linked to each other in {DECIMAL_FORMAT.format(perf_counter()-start)} seconds")
    
    
    print(f"All data loaded: total time = {DECIMAL_FORMAT.format(perf_counter()-start_first)} seconds")