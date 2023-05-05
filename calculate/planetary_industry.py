from models.mapv2 import *
from models.common import SecurityStatus, iWeightFactor
from typing import List, Union
from dataclasses import dataclass, field
import numpy


@dataclass
class PlanetaryIndustryWeightFactor(iWeightFactor):
    """"
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


    def DetermineSystemWeight(self, system: System, jumps_from_source: int) -> int:
        jump_value = self._calculateJumpValue(jumps_from_source)
        diversity_value = self._calculateDiversityValue(system.Planet_Ids)
        density_value = self._calculateDensityValue(system.Planet_Ids)
        security_value = self._calculateSecurityStatusWeight(system.Security_Status)

        return jump_value+diversity_value+density_value+security_value

    def _calculateSecurityStatusWeight(self, system_security: float)->float:
        adjusted_security = numpy.floor(system_security*10)

        match self.SecurityPreference:
            case SecurityStatus.HIGH_SEC:
                pass
            case SecurityStatus.LOW_SEC:
                if adjusted_security < 5 and adjusted_security > 0:
                    adjusted_security +=5
                elif adjusted_security >= 5:
                    adjusted_security -= 5
            case SecurityStatus.NULL_SEC:
                adjusted_security = -adjusted_security
                
        return adjusted_security/10 * self.SecurityWeight

    def _calculateDensityValue(self, system_planet_ids: List[int])->Union[int, float]:
        density_data = [ptype for ptype in system_planet_ids if ptype in self.PlanetTypesDesired]
        density_counts = [density_data.count(ptype) for ptype in system_planet_ids]
        
        if self.UseAverageDensity:
            # use floor(average*100)/1000 in order to round down to 2 decimal places.
            density_value = numpy.floor((numpy.average(density_counts)*100))/1000

        else:
            density_value = numpy.sum(density_counts)

        return density_value * self.TypeDensityWeight

    def _calculateDiversityValue(self, system_planet_ids: List[int])->int:
        return len({ptype for ptype in system_planet_ids if ptype in self.PlanetTypesDesired}) * self.TypeDiversityWeight

    def _calculateJumpValue(self, jumps_from_source:int)->int:
        return (self.MaxJumps-jumps_from_source) * self.JumpWeight