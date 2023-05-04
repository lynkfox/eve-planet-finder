from __future__ import annotations
from data.planetaryResources import RawResources, ResourceNameMap
from models.map import *
from buildMapData import LoadPickles
from typing import Tuple, List, Set

JUMP_DISTANCE_WEIGHT = 1
MULTIPLE_PLANETS_WEIGHT = 0.01
MULTIPLE_PLANET_TYPES = 0.1

MAX_JUMPS = 5
RawResourcesDesired = [
    ResourceNameMap["Aqueous Liquids"],
    ResourceNameMap["Autotrophs"],
    ResourceNameMap["Base Metals"],
    ResourceNameMap["Carbon Compounds"],
    ResourceNameMap["Felsic Magma"],
    ResourceNameMap["Micro-Organisms"],
    ResourceNameMap["Noble Gas"],
    ResourceNameMap["Noble Metals"],
    ResourceNameMap["Non-CS Crystals"],
    ResourceNameMap["Suspended Plasma"],
    ResourceNameMap["Planktic Colonies"],
    ResourceNameMap["Reactive Gas"]
]



def CalculateCloseness(resources_desired:List[PIMaterial], max_jumps:int, map_data:AllData)-> Any:
    

    resources_desired = [map_data.RawResources[resource] for resource in resources_desired]
        

    planets_to_search_for = ConsolidatePlanetTypes(resources_desired)

    system_values = {}
    for systemId, system in map_data.Systems.items():
        closest_planets = {}
        system_values[systemId] = { "ClosestPlanets": closest_planets}
        for planet_type in planets_to_search_for:
            CheckNextSystem(system, 0, max_jumps, planet_type, None, [], closest_planets)
   
        surrounding_systems, system_weight = CalculateSystemWeight(closest_planets, max_jumps)
        system_values[systemId]["Weight"] = system_weight
        system_values[systemId]["Surrounding Systems"] = surrounding_systems
    return system_values


def CalculateSystemWeight(closest_planets: Dict[str, List[PotentialSite]], max_jumps:int)->Tuple[Dict[str, Dict[str, any]], int]:
    system_weights = {}
    for planet_type, potential_sites in closest_planets.items():
        for site in potential_sites:
            jumps_value = max_jumps-site.JumpsFromSource*JUMP_DISTANCE_WEIGHT
            number_of_planets = len(site.Planets)*MULTIPLE_PLANETS_WEIGHT
            
            other_planet_types = 0.0
            if site.SystemName in system_weights.keys():
                other_planet_types = len(system_weights[site.SystemName]["Planet Types"])*MULTIPLE_PLANET_TYPES
                
                system_weights[site.SystemName]["Planet Types"].append(planet_type)
                system_weights[site.SystemName]["Weight"] = jumps_value+number_of_planets+other_planet_types
            else:
                system_weight = {
                    "Planet Types":[planet_type],
                    "Weight": jumps_value+number_of_planets+other_planet_types,
                    "Jumps Away": site.JumpsFromSource,
                    "System Name": site.SystemName
                }
                system_weights[site.SystemName]=system_weight
        
        if len(potential_sites)==0:
            system_weights[site.SystemName]["Weight"] += -1

    running_total = 0.0
    for system in system_weights.values():
        running_total += system["Weight"]

    return system_weights, running_total


        


    


def CheckNextSystem(system:System, total_jumps: int, max_jumps:int, searching_for: PlanetType, origin_system:System, systems_already_searched: List[str], viable_planets: Dict[str, List[PotentialSite]])->Dict[str, List[PotentialSite]]:
    
    # if we've hit our max jumps, time to stop searching
    if total_jumps >= max_jumps:
        return viable_planets

    # Have we already visited this node? if so break out. If not, add it to the list of already searched.
    if system.Name in systems_already_searched:
        return viable_planets
    else:
        systems_already_searched.append(system.Name)


    # loop over every planet, seeing if it matches the type searched for
    for planet in system.Planets:
        if planet.Type == searching_for:
            new_system = PotentialSite(
                SystemName=system.Name,
                SystemId=system.Id,
                Planets=[planet],
                PlanetType=planet.Type,
                JumpsFromSource=total_jumps
            )
            
            # viable_planets is empty, be sure to initialize it. Since we may have many sites at the same distance for the same planet, its a list of sites
            if searching_for.Name not in viable_planets.keys():
                viable_planets[searching_for.Name] = [new_system]

            else:
                # get a tuple of the systems so far discovered and their index in the viable_planets[planet_type] list
                systems_found_so_far = [(site.SystemName, index) for index, site in enumerate(viable_planets[searching_for.Name])]

                # check to see if the given system has already been recorded
                index = [value[1] for value in systems_found_so_far if value[0] == system.Name]

                # if so add to the planets for the PotentialSite
                if len(index)>0:
                    viable_planets[searching_for.Name][index[0]].Planets.append(planet)
                else: # add the system anew
                    
                    viable_planets[searching_for.Name].append(new_system)




    # Get the smallest JumpsFromSource in the list - this will *probably* be one we just found, this also catches if 
    # in a system with no viable planets but have already found a closer system 
    
    closest_found = min([site.JumpsFromSource for site in viable_planets.get(searching_for.Name, [])], default=999999)
    if closest_found <= total_jumps:
        return viable_planets

    else:
        # make sure we dont go back the way we came, otherwise loop over every link and head on out to search again.
        for next_system in system.Links:
            if next_system == origin_system:
                continue

            return CheckNextSystem(next_system, total_jumps=total_jumps+1, max_jumps=max_jumps, searching_for=searching_for, origin_system=system, systems_already_searched=systems_already_searched, viable_planets=viable_planets)


def ConsolidatePlanetTypes(resources_desired:List[PIMaterial])->List[PlanetType]:
    unique_planet_types = []
    planet_types_already_chosen = []
    for resource in resources_desired:
        for planet_type in resource.OnTypes:
            if planet_type.Name not in planet_types_already_chosen:
                planet_types_already_chosen.append(planet_type.Name)
                unique_planet_types.append(planet_type)
    
    return unique_planet_types


if __name__ == "__main__":
    map_data = LoadPickles(regions=False, constellations=False)
    CalculateCloseness(RawResourcesDesired, MAX_JUMPS, map_data)