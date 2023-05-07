from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Set, Tuple, Union

import numpy

import models.map as mapData
from models.common import DECIMAL_FORMAT, iWeightFactor, iWeightResult, SecurityStatus


@dataclass
class PlanetaryIndustryResult(iWeightResult):
    # WeightFactors: PlanetaryIndustryWeightFactor - defined on Parent Class
    # SortValue: Int - defined in Parent class
    System: mapData.System = field(init=False)
    PlanetIds: List[int] = field(init=False, default_factory=list)
    JumpsFromOrigin: int = field(init=False)
    OriginSystem: mapData.System = field(init=False)
    Weight: float = field(init=False)
    IndividualWeights: Tuple[float, float, float, float] = field(init=False)

    def Populate(
        self, current_system: mapData.System, origin_system: mapData.System, jumps_from_source: int, weight: tuple
    ) -> PlanetaryIndustryResult:
        self.System = current_system
        self.PlanetIds = current_system.Planet_Ids
        self.OriginSystem = origin_system
        self.JumpsFromOrigin = jumps_from_source
        self.Weight = weight[0]
        self.IndividualWeights = weight[1]
        self.SortValue = self.Weight

        return self

    def getSymbol(self, symbol: str, html: bool = False) -> str:
        symbolLibrary = {
            "TitlePrefix": ("<b>", ">>>>>__________ "),
            "TitleSuffix": ("</b>", " __________<<<<<"),
            "LevelOne": ("<br>&#8594;<i> ", "\n -> "),
            "LevelTwo": ("<br>  &#8618;<i> ", "\n   => "),
            "EndItalic": ("</i>", "*"),
            "NewLine": ("<br>", "\n"),
            "Italic": ("<i>", "*"),
        }

        return symbolLibrary[symbol][0] if html else symbolLibrary[symbol][1]

    def spacing(self, words: str, total_spacing: int) -> str:
        return f"{words}{''.join([' ' for _ in range(total_spacing-len(words))])}"

    def Html(self, html: bool = True, simple: bool = False) -> str:
        level_one_spacing = 30
        simple_spacing = 5
        planets = [
            planet
            for planet in self.System.GetPlanets(cache=True)
            if planet.Type_Id in self.WeightFactors.PlanetTypesDesired
        ]
        planet_counts = Counter([planet.GetType().Name for planet in planets])
        planet_types_sub_str = " | ".join(sorted([f"{key} x{value}" for key, value in planet_counts.items()]))

        if simple:
            system_name_str = f"{self.getSymbol('TitlePrefix',html=html)} {self.System.Name} (Jmp: {self.JumpsFromOrigin}) {self.getSymbol('TitleSuffix',html=html)}"
            weight_values_str = f" ".join(
                [
                    f"{self.getSymbol('Italic',html=html)}Weights: (T: {self.Weight}){self.getSymbol('EndItalic',html=html)}{self.getSymbol('NewLine',html=html)} "
                    f"{self.spacing('Jmp:', simple_spacing)}{DECIMAL_FORMAT.format(self.IndividualWeights[0])}",
                    f"{self.spacing('Div:', simple_spacing)}{DECIMAL_FORMAT.format(self.IndividualWeights[1])}",
                    f"{self.spacing('Sec:', simple_spacing)}{DECIMAL_FORMAT.format(self.IndividualWeights[3])}",
                    f"{self.spacing('Dns:', simple_spacing)}{DECIMAL_FORMAT.format(self.IndividualWeights[2])}",
                ]
            )

            return system_name_str + weight_values_str

        system_name_str = f"{self.getSymbol('TitlePrefix',html=html)}{self.System.Name} (Jumps: {self.JumpsFromOrigin}){self.getSymbol('TitleSuffix',html=html)}"
        system_weight_str = f"{self.getSymbol('LevelOne',html=html)}{self.spacing('Weight:', level_one_spacing)}{self.getSymbol('EndItalic',html=html)}{self.Weight}"
        weight_values_str = f"{self.getSymbol('LevelTwo',html=html)}Individual Weights:      Jumps: {self.getSymbol('EndItalic',html=html)}{DECIMAL_FORMAT.format(self.IndividualWeights[0])}, Diversity: {DECIMAL_FORMAT.format(self.IndividualWeights[1])}, Density: {DECIMAL_FORMAT.format(self.IndividualWeights[2])}, Security: {DECIMAL_FORMAT.format(self.IndividualWeights[3])}"
        planet_types_str = f"{self.getSymbol('LevelOne',html=html)}{self.spacing('Planet Types Available:', level_one_spacing)}{self.getSymbol('EndItalic',html=html)}{planet_types_sub_str}"

        return system_name_str + system_weight_str + weight_values_str + planet_types_str

    def __repr__(self) -> str:
        return self.Html(html=False)


@dataclass
class PlanetaryIndustryWeightFactor(iWeightFactor):
    """ "
    Container class for various Weighting in calculating the value of a System for Planetary Industry.

    All parameters accept negative numbers, reversing their effect (Negative JumpWeight means more jumps is preferred). 0 causes a particular weight to be ignored.

    All values are Ints in order to prevent floating point comparison issues.

    While you can use a float, doing so could make two systems that are otherwise equal have an arbitrary difference based on floating point comparison.

    :param PlanetTypesDesired(List[int], default:[]): A list of Planet Type Ids to search for.
    :param MaxJumps(Int, default: 3): How far from starting system (for calculating JumpWeight).
    :param JumpWeight(Int, default: 500): How much to value remaining jumps before maximum.
    :param TypeDiversityWeight(Int, default 100): How much to value multiple planet types.
    :param TypeDensityWeight(Int, default: 10): How much to value multiple planets of the same type.
    :param UseAverageDensity(Bool, default: True): Will take an average of the counts of each planet type to use against the weight, otherwise uses sum
        of all the planets that match a given type.
        NOTE: If UseAverageDensity is true, then the value is rounded *down* to 2 decimal places before being adjusted by weight.
    :param SecurityWeight(Int, default: 0) How much to weigh security status.
        NOTE: Security status is stored as a float with more than just the single visible digit in the overview. I am unsure if this has a meaning,
        so am rounding down to 1 digit to display/use the same number.
    :param SecurityPreference(Enum.SecurityStatus, default HIGH_SEC): Sets the preference for High, Low, Null. To ignore security status, set weight to 0.

    """

    PlanetTypesDesired: List[int] = field(kw_only=True, default_factory=list)
    MaxJumps: int = field(kw_only=True, default=3)
    JumpWeight: int = field(kw_only=True, default=500)
    TypeDiversityWeight: int = field(kw_only=True, default=100)
    TypeDensityWeight: int = field(kw_only=True, default=10)
    UseAverageDensity: bool = field(kw_only=True, default=True)
    SecurityWeight: int = field(kw_only=True, default=0)
    SecurityPreference: SecurityStatus = field(kw_only=True, default=SecurityStatus.HIGH_SEC)

    def DetermineSystemWeight(
        self, system: mapData.System, jumps_from_source: int
    ) -> Tuple[int, Tuple[int, int, int, int], Set[int]]:
        """
        Determines the Weight of hte system:
        Jumps from Source * JumpWeight
        Number of Different Types of Planets * TypeDiversityWeight
        Number of Planets that match the types * TypeDensityWeight
        Security Status * Security Weight(affected by SecurityPreference)

        returns: Total Weight, (Jump_Value, Diversity_Value, Density_Value, Security_Value), set(PlanetTypeIDsFound)
        """
        jump_value = self._calculateJumpValue(jumps_from_source)
        diversity_value = self._calculateDiversityValue(system.PlanetTypes_Ids)
        density_value = self._calculateDensityValue(system.PlanetTypes_Ids)
        security_value = self._calculateSecurityStatusWeight(system.Security_Status)
        planet_type_ids_found = self._determine_what_was_found(system.PlanetTypes_Ids)

        return (
            jump_value + diversity_value + density_value + security_value,
            (jump_value, diversity_value, density_value, security_value),
            planet_type_ids_found,
        )

    def _calculateSecurityStatusWeight(self, system_security: float) -> float:
        adjusted_security = numpy.floor(system_security * 10)

        match self.SecurityPreference:
            case SecurityStatus.HIGH_SEC:
                pass
            case SecurityStatus.LOW_SEC:
                if adjusted_security < 5 and adjusted_security > 0:
                    adjusted_security += 5
                elif adjusted_security >= 5:
                    adjusted_security -= 5
            case SecurityStatus.NULL_SEC:
                adjusted_security = -adjusted_security

        return adjusted_security / 10 * self.SecurityWeight

    def _calculateDensityValue(self, planet_type_ids: List[int]) -> Union[int, float]:
        density_data = [ptype for ptype in planet_type_ids if ptype in self.PlanetTypesDesired]
        density_counts = [density_data.count(ptype) for ptype in planet_type_ids]

        if self.UseAverageDensity:
            # use floor(average*100)/1000 in order to round down to 2 decimal places.
            density_value = numpy.floor((numpy.average(density_counts) * 100)) / 1000

        else:
            density_value = numpy.sum(density_counts)

        return density_value * self.TypeDensityWeight

    def _calculateDiversityValue(self, planet_type_ids: List[int]) -> int:
        return len({ptype for ptype in planet_type_ids if ptype in self.PlanetTypesDesired}) * self.TypeDiversityWeight

    def _calculateJumpValue(self, jumps_from_source: int) -> int:
        return (self.MaxJumps - jumps_from_source) * self.JumpWeight

    def _determine_what_was_found(self, planet_type_ids: List[int]) -> Set[int]:
        return set(self.PlanetTypesDesired).intersection(set(planet_type_ids))
