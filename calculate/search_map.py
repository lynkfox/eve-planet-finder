from models.mapv2 import *
from models.common import WeightMethod
from calculate.planetary_industry import *
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class WeightCalculator():
    """
    Generic Calculator for calculating System Weights around a specific origin system.

    :param WeightFactors(iWeightFactor): The Weighting class that contains the factors to weigh against and any other necessary values to perform the evaluation.
    :param WeightResults(object): The Weighting Results class that contains a Populate method and the values for each individual system that is part of the overall weight.
    :param MaxJumps(int, 3): The maximum number of jumps to check around the OriginSystem (which is 0)
    :param CACHE_EXPENSIVE_CALLS(bool, default: False):  If false, will perform expensive calculations in func calls like System.GetLinkedSystems() everytime, otherwise will cache the responses.
        NOTE: Its useful to leave this False while Debugging, so as not to overwhelm the debugger with looped/recursive Object<->Object relationships

    :attributes TopWeight(float): The highest weight discovered
    :attributes TopDetails(Dict[int, Dict[int, int]]) Dictionary of all the top weights - originSystemId:{systemId: weight}


    :method Run() - Run the calculations
    
    """
    # Init Values
    WeightFactors: iWeightFactor
    WeightResults: object
    MaxJumps:int = field(kw_only=True, default=3)
    CACHE_EXPENSIVE_CALLS: bool = field(kw_only=True, default=False)
    # Attributes
    TopWeight: float = field(init=False, default=0)
    TopDetails: Dict[int, Dict[int, int]] = field(init=False, default=dict)

    # Internal Use 
    _origin_system: System = field(init=False, default=None)
    _results: Dict[int, Any] = field(init=False, default_factory=dict)
    _systemIdsAlreadySearched: Dict[int, int] = field(init=False, default_factory=dict)
    """
        _systemIdsAlreadySearched is a dict of SystemId: JumpsFromSource. This allows finding an already searched system 
            that is less jumps away from the origin than currently remembered.
    """
    
    
    def __post_init__(self):
        # Ensure the max jumps are the same, if the WeightFactors uses MaxJumps
        if hasattr(self.WeightFactors, "MaxJumps"):
            self.WeightFactors.MaxJumps = self.MaxJumps

    
    def Run(self, origin_system: System, method: WeightMethod = WeightMethod.AVERAGE) -> Tuple[int, Dict[int, Any]]:
        """ Runs the Calculations for Weighing each System within MaxJumps from the origin_system
        
        :param origin_system(System): The starting point to search MaxJumps away from.
        :param method(WeightMethod, Default:AVERAGE): How the weight is returned

        :return weight(int): The weight for the system, with the given method.
        :return results(Dict[int, int]): a dictionary of SystemIds and their weights.
        """
        # clear the results
        self.Clear()
        self._origin_system = origin_system

        # weigh the origin system with None as Previous and 0 as current_jumps
        self._checkNextSystem(origin_system, None, 0)


        raw_weight = [w.Weight for w in self._results.values()]
        match method:
            case WeightMethod.AVERAGE:
                weight = numpy.floor(numpy.average(raw_weight)*10)/100
            case WeightMethod.TOTAL:   
                weight = numpy.floor(numpy.sum(raw_weight)*10)/100
            case _:
                weight = raw_weight

        self._recordTopValues(weight, origin_system.Id)
        
        self.Clear()

        return weight, self._results

    def Clear(self):
        """ Used to Clear the saved values (but not the State of all Run() Calls) between Run() calls"""
        self._results = {}
        self._systemIdsAlreadySearched = {}
        self._origin_system = None


    def ClearAll(self):
        """ Used to Clear the state of all Run() calls, to reuse the same Calculator object"""
        self.TopWeight = 0
        self.TopDetails = {}
        self._results = {}
        self._systemIdsAlreadySearched = {}
        self._origin_system = None
        
    def _recordTopValues(self, weight:float, origin_system_id: int):
        """
        Stateful method. This records the top responses (and all of them in ties) for every call of Run() on a given calculator.
        """
        if weight > self.TopWeight:
            self.TopWeight = weight
            self.TopDetails = {origin_system_id: self._results}

        if weight == self.TopWeight:
            self.TopDetails[origin_system_id] = dict(sorted(self._results.items(), key=lambda x:x[1].SortValue))

        
    

    def _checkNextSystem(self, target_sys: System, previous_system_id: int, current_jumps:int):
        """
        Recursive function to check all new destinations from a source system, and give their weight.

        :param target_sys(System): The system being evaluated.
        :param previous_system_id(int): The System.Id of the system this function was called from.
        :param current_jumps(int): how many jumps away from the origin system this system is.
        """

        # if we've exceeded our jumps, cut out
        if current_jumps > self.MaxJumps:
            return
        
        # if the system has already been searched AND the total jumps to get from origin to here by another path is less than this path, cut out
        if target_sys.Id in self._systemIdsAlreadySearched.keys() and self._systemIdsAlreadySearched[target_sys.Id] < current_jumps:
            return
        
        # save the current jumps to get to this path for the above
        self._systemIdsAlreadySearched[target_sys.Id] = current_jumps
        
        # save the result from weighing this system. Its OK to overwrite if we already searched this system, because current_jumps will be different
        weight, weight_values = self.WeightFactors.DetermineSystemWeight(
            target_sys,
            current_jumps)

        results = self.WeightResults(self.WeightFactors)

        self._results[target_sys.Id] = results.Populate(
            target_sys,
            self._origin_system,
            current_jumps,
            (weight, weight_values) 
        )

        # loop over all the system linked to this one
        for new_target_system in target_sys.GetLinkedSystems(cache=self.CACHE_EXPENSIVE_CALLS):
            # ignore the one we came from
            if new_target_system.Id == previous_system_id:
                continue
            
            # repeat all of the above, shifting target_sys to the previous and incrementing the jump counter.
            self._checkNextSystem(new_target_system, target_sys.Id, current_jumps+1)

        return
            


