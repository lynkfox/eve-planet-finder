from dataclasses import dataclass, field
from functools import cached_property
from typing import Dict, List

import numpy

from buildMapData import AllData


@dataclass
class CalculatedMapData:
    all_data: AllData = field(kw_only=True, default=None)

    def __post_init__(self):
        self.all_data = AllData(skip_build=True)
        self.all_data.PopulateFromPickles()

    @cached_property
    def TotalPlanets(self) -> int:
        return len(self.all_data.Planets)

    @cached_property
    def TotalSystems(self) -> int:
        return len(self.all_data.Systems)

    @cached_property
    def PlanetIdsByTypeIds(self) -> Dict[int, List[int]]:
        return {
            planet_type.Id: [planet.Id for planet in self.all_data.Planets if planet.Type_Id == planet_type.Id]
            for planet_type in self.all_data.Planet_Types
        }

    @cached_property
    def PlanetTypeAmounts(self) -> Dict[int, int]:
        return {key: len(value) for key, value in self.PlanetIdsByTypeIds.items()}

    @cached_property
    def PlanetTypesPercentage(self) -> Dict[int, float]:
        return {key: value / self.TotalPlanets for key, value in self.PlanetTypeAmounts.items()}

    @cached_property
    def AveragePlanetsPerSystem(self) -> float:
        return numpy.average([len(sys.Planet_Ids) for sys in self.all_data.Systems])

    @cached_property
    def MeanPlanetsPerSystem(self) -> float:
        return numpy.mean([len(sys.Planet_Ids) for sys in self.all_data.Systems])

    @cached_property
    def AveragePlanetTypeBySystem(self) -> Dict[int, float]:
        return {
            planet_type.Id: numpy.average(
                [
                    len([planet.Type_Id for planet in sys.GetPlanets() if planet.Type_Id == planet_type.Id])
                    / len(sys.Planet_Ids)
                    for sys in self.all_data.Systems
                ]
            )
            for planet_type in self.all_data.Planet_Types
        }

    @cached_property
    def MeanPlanetTypeBySystem(self) -> Dict[int, float]:
        return {
            planet_type.Id: numpy.mean(
                [
                    len([planet.Type_Id for planet in sys.GetPlanets() if planet.Type_Id == planet_type.Id])
                    / len(sys.Planet_Ids)
                    for sys in self.all_data.Systems
                ]
            )
            for planet_type in self.all_data.Planet_Types
        }
