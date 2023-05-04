from __future__ import annotations
from dataclasses import dataclass, field
from data.planetaryResources import RawResources, ResourceNameMap
from models.map import *
from buildMapData import LoadPickles
from typing import Tuple, List, Dict, Union

JUMP_DISTANCE_WEIGHT = 1000
MULTIPLE_PLANETS_WEIGHT = 10
MULTIPLE_PLANET_TYPES_WEIGHT = 100
MISSING_PLANET_TYPE_WEIGHT = -1

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

@dataclass
class PlanetsInfo():
    Type: str
    Total: int
    Names: List[str]

    def __add__(self, right_hand: PlanetsInfo) -> bool:
        # if isinstance(right_hand, PlanetsInfo):
        #     raise ValueError(f"Cannot add type {type(right_hand)} to type PlanetsInfo")

        new_info = self
        new_info.Total += right_hand.Total
        new_info.Names.extend(right_hand.Names)
        return new_info
        

@dataclass
class WeightFactor():
    JumpsFromSource: int
    Planets: Dict[str, PlanetsInfo]
    SystemName: str
    Weight: int = field(kw_only=False, default=0)
    Audit: List[str] = field(kw_only=False, default_factory=list)

    def __post_init__(self):
        self.Audit.append(f"Audit For {self.SystemName}")

    def CalculateWeight(self, max_jumps:int) -> int:
        jump_weight = (max_jumps-self.JumpsFromSource)*JUMP_DISTANCE_WEIGHT
        planet_type_weight = len(self.Planets)*MULTIPLE_PLANET_TYPES_WEIGHT
        total_planets = sum([planets.Total for planets in self.Planets.values()])
        total_planets_weight = total_planets*MULTIPLE_PLANETS_WEIGHT

        self.Weight = jump_weight+planet_type_weight+total_planets_weight

        self.Audit.append(f"Calculating Weight vvvv")
        self.Audit.append(f"\tJumpWeight {jump_weight} | MaxJumps {max_jumps} | FromSource {self.JumpsFromSource} ")
        self.Audit.append(f"\tMultTypeWeight {planet_type_weight} | TotalTypes {len(self.Planets)}")
        self.Audit.append(f"\tTotalPlanetsWeight {total_planets_weight} | Total Planets {total_planets}")
        self.Audit.append(f"Calculating Weight ^^^^")

        return self.Weight

    def PenalizeForMissingType(self, planet_type):
        self.Weight += MISSING_PLANET_TYPE_WEIGHT
        self.Audit.append(f"----Applying MISSING_PLANET_TYPE_WEIGHT for {planet_type}")
        self.Audit.append(f"----New Weight: {self.Weight}")
    
    def AddAdditionalPlanetType(self, planet_type, planets:List[Planet]):
        if planet_type in self.Planets.keys():
            self.Planets[planet_type].Total += len(planets)
            self.Planets[planet_type].Names.extend([planet.Name for planet in planets])
        else:
            self.Planets[planet_type] = PlanetsInfo(
                planet_type, len(planets), [planet.Name for planet in planets]
            )
        

    def __add__(self, right_hand:WeightFactor)->WeightFactor:
        # if isinstance(right_hand, WeightFactor):
        #     raise ValueError(f"Cannot add type {type(right_hand)} to type WeightFactor ")
        
        new_factor =  WeightFactor(
            SystemName=self.SystemName,
            Planets=self.Planets,
            JumpsFromSource=self.JumpsFromSource if self.JumpsFromSource < right_hand.JumpsFromSource else right_hand.JumpsFromSource,
            Weight=self.Weight+right_hand.Weight,
            Audit=self.Audit
        )

        for key, value in right_hand.Planets.items():
            if key in new_factor.Planets.keys():
                new_factor.Planets[key] += value
            else:
                new_factor.Planets[key] = value

        return new_factor

    def __eq__(self, __o: Union[WeightFactor, str]) -> bool:
        if isinstance(__o, WeightFactor):
            return self.SystemName == __o.SystemName
        elif isinstance(__o, str):
            return self.SystemName == __o
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.SystemName)


@dataclass
class SystemTotalWeight():
    SystemName: str
    TotalWeight: int
    PotentialSites: List[WeightFactor]


def CalculateCloseness(resources_desired:List[PIMaterial], max_jumps:int, map_data:AllData)-> Dict[str, SystemTotalWeight]:
    

    resources_desired = [map_data.RawResources[resource] for resource in resources_desired]
        

    planets_to_search_for = ConsolidatePlanetTypes(resources_desired)

    system_values = {}
    for systemId, system in map_data.Systems.items():
        if len(system.Links) == 0:
            continue
        closest_planets = {}
        for planet_type in planets_to_search_for:
            CheckNextSystem(system, 0, max_jumps, system.Name, planet_type, None, [], closest_planets)
   
        surrounding_systems, total_weight = CalculateSystemWeight(closest_planets, max_jumps)
        system_weight = SystemTotalWeight(
            system.Name,
            total_weight,
            surrounding_systems
        )
        system_values[systemId] = system_weight
    return system_values


def CalculateSystemWeight(closest_planets: Dict[str, List[PotentialSite]], max_jumps:int)->Tuple[List[WeightFactor], int]:
    system_weights:List[WeightFactor] = []
    for planet_type, potential_sites in closest_planets.items():
        for site in potential_sites:

            if site.Planets is None:
                continue
            site_weight = WeightFactor(
                JumpsFromSource=site.JumpsFromSource,
                Planets={planet_type: PlanetsInfo(
                    planet_type,
                    len(site.Planets),
                    [planet.Name for planet in site.Planets]
                )},
                SystemName=site.SystemName,
            )


            if site_weight not in system_weights:
                system_weights.append(site_weight)

            else:
                existing, existing_idx = FindExistingWeightFactor(system_weights, site_weight)
                existing += site_weight
                system_weights[existing_idx] = existing
        
        if len(potential_sites)==0:
            existing, existing_idx = FindExistingWeightFactor(system_weights, site.SystemName)
            existing.PenalizeForMissingType(planet_type)
            system_weights[existing_idx] = existing

    running_total = sum([system.CalculateWeight(max_jumps) for system in system_weights])

    return system_weights, running_total

def FindExistingWeightFactor(system_weights, site):
    for idx, system in enumerate(system_weights):
        if system == site:
            existing = system
            existing_idx = idx

    return existing, existing_idx


        


    


def CheckNextSystem(system:System, total_jumps: int, max_jumps:int, source_system_name:str, searching_for_planet_type: PlanetType, previous_system:System, systems_already_searched: List[str], viable_planets: Dict[str, List[PotentialSite]])->Dict[str, List[PotentialSite]]:
    
    # if we've hit our max jumps, time to stop searching
    if total_jumps >= max_jumps:
        return viable_planets

    # Have we already visited this node? if check if we are closer or further away. If not, add it to the list of already searched.
    if system.Name in [system[0] for system in systems_already_searched]:
        if total_jumps >= [system[1] for system in systems_already_searched if system[0]==system.Name]:
            return viable_planets
        else:
            pass
    else:
        systems_already_searched.append((system.Name, total_jumps))


    # loop over every planet, seeing if it matches the type searched for
    for planet in system.Planets:
        if planet.Type == searching_for_planet_type:
            new_site = PotentialSite(
                SystemName=system.Name,
                SystemId=system.Id,
                Planets=[planet],
                PlanetType=planet.Type,
                JumpsFromSource=total_jumps,
                SourceSystemName=source_system_name
            )

            # if this is the first entry for a planet of type searching_for, then be sure to initialize that key
            if searching_for_planet_type.Name not in viable_planets.keys():
                viable_planets[searching_for_planet_type.Name] = [new_site]
                print(f"found sites for: {viable_planets.keys()} ")

            # else, check to see if the site already exists in that key's list of sites, and if not add it.
            elif new_site.SystemName not in [existing_system.SystemName for existing_system in viable_planets[searching_for_planet_type.Name]]:
                viable_planets[searching_for_planet_type.Name].append(new_site)
                print(f"+++++new site for {searching_for_planet_type.Name}")
    


            # otherwise, find the existing site, add to it, and replace it. This can happen if there is multiple paths to the same system from the source.
            else:
                # find an existing record of the system
                index, existing = [(index, system) for index, system in enumerate(viable_planets[searching_for_planet_type.Name])][0]

                # add thew new planets
                existing += new_site
                # replace
                viable_planets[searching_for_planet_type.Name][index] = existing


    # Get the smallest JumpsFromSource in the list - this will *probably* be one we just found, this also catches if 
    # in a system with no viable planets but have already found a closer system 
    
    closest_found = min([site.JumpsFromSource for site in viable_planets.get(searching_for_planet_type.Name, [])], default=999999)
    if closest_found <= total_jumps:
        return viable_planets

    else:
        # make sure we dont go back the way we came, otherwise loop over every link and head on out to search again.
        for next_system in system.Links:
            if next_system == previous_system:
                continue

            return CheckNextSystem(next_system, total_jumps=total_jumps+1, max_jumps=max_jumps,source_system_name=source_system_name, searching_for_planet_type=searching_for_planet_type, previous_system=system, systems_already_searched=systems_already_searched, viable_planets=viable_planets)


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