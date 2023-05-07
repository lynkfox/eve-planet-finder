from dataclasses import dataclass, field
from typing import Dict, Tuple

from calculate.planetary_industry import *
from models.common import WeightMethod
from models.mapv2 import *


@dataclass
class WeightCalculator:
    """
    Generic Calculator for calculating System Weights around a specific origin system.

    :param WeightFactors(iWeightFactor): The Weighting class that contains the factors to weigh against and any other necessary values to perform the evaluation.
    :param WeightResults(object): The Weighting Results class that contains a Populate method and the values for each individual system that is part of the overall weight.
    :param MustFindTargets(Set[Any]): A set of values that must be found. The iWeightFactor.DetermineSystemWeight should return a set of any values that matched this as its 3rd value.
    :param MustFindPenalty(Int): A value that will be applied to any chain that does not find all the targets in MustFindTargets.
    :param MaxJumps(int, 3): The maximum number of jumps to check around the OriginSystem (which is 0)
    :param CACHE_EXPENSIVE_CALLS(bool, default: False):  If false, will perform expensive calculations in func calls like System.GetLinkedSystems() everytime, otherwise will cache the responses.
        NOTE: Its useful to leave this False while Debugging, so as not to overwhelm the debugger with looped/recursive Object<->Object relationships

    :attributes TopWeight(float): The highest weight discovered
    :attributes TopDetails(Dict[int, Dict[int, int]]) Dictionary of all the top weights - originSystemId:{systemId: weight}
    :attributes AllAuditLogs(Dict[int, List[str]]) All auditing logs run by this calculator, by organized by OriginSystem_Id of each Run command.

    :method Run() - Run the calculations
    :method GetAuditFor() - Get the Audit logs for a particular key in the AllAuditLogs

    """

    # Init Values
    WeightFactors: iWeightFactor
    WeightResults: iWeightResult
    MustFindTargets: Set[Any] = field(kw_only=True, default_factory=set)
    MaxJumps: int = field(kw_only=True, default=3)
    CACHE_EXPENSIVE_CALLS: bool = field(kw_only=True, default=False)
    # Attributes
    TopWeight: float = field(init=False, default=0)
    TopDetails: Dict[int, Dict[int, int]] = field(init=False, default=dict)
    AllAuditLogs: Dict[int, List[str]] = field(init=False, default_factory=dict)

    # Internal Use
    # Passing Origin System in through Run we can use the WeightResults.Populate() command to keep a record for each system
    # when running the Calculator as part of a loop
    _origin_system: System = field(init=False, default=None)
    # Similar to _origin_system, _results is for keeping track of a particular source node while using calculate in a loop
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

    def GetLogs(self, key) -> List[str]:
        if isinstance(key, str):
            key = int(key)
        return self.AllAuditLogs[key]

    def Run(self, origin_system: System, method: WeightMethod = WeightMethod.AVERAGE) -> Tuple[int, Dict[int, Any]]:
        """Runs the Calculations for Weighing each System within MaxJumps from the origin_system

        :param origin_system(System): The starting point to search MaxJumps away from.
        :param method(WeightMethod, Default:AVERAGE): How the weight is returned

        :return weight(int): The weight for the system, with the given method.
        :return results(Dict[int, int]): a dictionary of SystemIds and their weights.
        """
        # clear the results
        self.Clear()
        self._origin_system = origin_system
        self._add_log(f"==== New Run started for {origin_system.Name} ====")
        self._add_log(f" *** Expected Match Values: {self.MustFindTargets}")

        # weigh the origin system with None as Previous and 0 as current_jumps
        any_matches = self._checkNextSystem(origin_system, None, 0, set())

        if any_matches:
            raw_weight = [w.Weight for w in self._results.values()]
            match method:
                case WeightMethod.AVERAGE:
                    weight = numpy.floor(numpy.average(raw_weight) * 10) / 100
                case WeightMethod.TOTAL:
                    weight = numpy.floor(numpy.sum(raw_weight) * 10) / 100
                case _:
                    weight = raw_weight
            self._add_log(
                f"==== Run Complete: Raw Weight:{raw_weight} | Recorded Weight by {method.name}: {weight} ===="
            )
        else:
            weight = -1
            self._results = {}
            self._add_log(f"==== Run Complete: Not able to find complete match. Weight: -1 ====")

        self._results = dict(sorted(self._results.items(), key=lambda x: x[1].SortValue, reverse=True))
        self._recordTopValues(weight, origin_system.Id)

        return weight, self._results

    def Clear(self):
        """Used to Clear the saved values (but not the State of all Run() Calls) between Run() calls"""
        self._results = {}
        self._systemIdsAlreadySearched = {}
        self._origin_system = None

    def ClearAll(self):
        """Used to Clear the state of all Run() calls, to reuse the same Calculator object"""
        self.TopWeight = 0
        self.TopDetails = {}
        self.AllAuditLogs = {}
        self._results = {}
        self._systemIdsAlreadySearched = {}
        self._origin_system = None

    def _recordTopValues(self, weight: float, origin_system_id: int):
        """
        Stateful method. This records the top responses (and all of them in ties) for every call of Run() on a given calculator.
        """
        if weight > self.TopWeight:
            self.TopWeight = weight
            self.TopDetails = {origin_system_id: self._results}
            self._add_log("New Top Origin System (Previous Systems Removed)")
            self.AllAuditLogs[
                1
            ] = f"[TOP_SYSTEM] {self._origin_system.Name} is new top system with Weight {weight} (removed previous systems)"

        if weight == self.TopWeight:
            self.TopDetails[origin_system_id] = self._results
            self._add_log("Current Origin System matches Top Weight, adding to To Details")
            self.AllAuditLogs[
                1
            ] = f"[TOP_SYSTEM] {self._origin_system.Name} Matches current top weight ({weight}) (added details to existing)"

    def _add_log(self, message: str):
        """
        Adds an Audit log to the current origin system
        """
        if self.AllAuditLogs.get(self._origin_system.Id, None) is None:
            self.AllAuditLogs[self._origin_system.Id] = []
        prefix = f"[Run{len(self.AllAuditLogs.keys())}|{self._origin_system.Name}#{self._origin_system.Id}]"
        self.AllAuditLogs[self._origin_system.Id].append(prefix + message)

    def _checkNextSystem(
        self, current_sys: System, previous_system_id: int, current_jumps: int, current_matched_values: set
    ) -> Tuple[bool, set]:
        """
        Recursive function to check all new destinations from a source system, and give their weight.

        :param target_sys(System): The system being evaluated.
        :param previous_system_id(int): The System.Id of the system this function was called from.
        :param current_jumps(int): how many jumps away from the origin system this system is.
        :param current_matched_values(set): the values we have found in this particular chain.
        Returns true if all current_matched_values == self.MustFindTargets, indicating we can stop going down this chain.
        """
        logging_prefix = (
            f"Weighting [{current_sys.Name}#{current_sys.Id}@Jump-{current_jumps} From {previous_system_id}]"
        )

        self._add_log(f"{logging_prefix} Beginning Check of System")
        # if the system has already been searched AND the total jumps to get from origin to here by another path is less than this path, cut out
        if (
            current_sys.Id in self._systemIdsAlreadySearched.keys()
            and self._systemIdsAlreadySearched[current_sys.Id] < current_jumps
        ):
            self._add_log(f"{logging_prefix} has already been checked closer. Returning False.")
            return False

        # save the current jumps to get to this path for the above
        self._systemIdsAlreadySearched[current_sys.Id] = current_jumps

        # save the result from weighing this system. Its OK to overwrite if we already searched this system, because current_jumps will be different
        weight, weight_values, matched_values = self.WeightFactors.DetermineSystemWeight(current_sys, current_jumps)

        results = self.WeightResults(self.WeightFactors)

        self._results[current_sys.Id] = results.Populate(
            current_sys, self._origin_system, current_jumps, (weight, weight_values)
        )

        new_matched_values = current_matched_values.union(matched_values)

        self._add_log(f"{logging_prefix} Weight Values (J, Dv, Dns, sec) {weight_values}")
        self._add_log(f"{logging_prefix} Current Matched Values {new_matched_values}")

        # if we every meet everything in this chain we can just return - we don't need to search for more systems beyond.
        if new_matched_values == self.MustFindTargets:
            self._add_log(f"{logging_prefix} ***** Completes a path! Returning TRUE!!!! *****")
            return True
        elif current_jumps == self.MaxJumps:  # and hence, new_matched_values != self.MustFindTargets
            # we've reached the end of this chain. The chain to get here did not find everything, so its not worth keeping
            del self._results[current_sys.Id]
            self._add_log(
                f"{logging_prefix} Is Final System in Chain, still not all required values found. Returning False."
            )
            return False

        # We want to gather up all the children's responses as a list of True False.
        # Since the only way to return True is if all self.MustFindTargets have been found, then
        # an any(children_responses) would indicate that this particular system is potentially valuable.
        children_responses = []

        self._add_log(f"{logging_prefix} Now checking linked children.")
        # loop over all the system linked to this one
        for new_target_system in current_sys.GetLinkedSystems(cache=self.CACHE_EXPENSIVE_CALLS):
            # ignore the one we came from
            if new_target_system.Id == previous_system_id:
                continue

            # repeat all of the above, shifting target_sys to the previous and incrementing the jump counter.
            did_chain_find_everything = self._checkNextSystem(
                new_target_system, current_sys.Id, current_jumps + 1, new_matched_values
            )

            # if every chain originating from this particular child returns false, then no need to keep it around - dump it.
            # Since every parent will be doing this as well, then we eliminate all children who do not, in some way, contribute
            # to finding everything needed. And we remove their weights from the system.
            if not did_chain_find_everything and self._results.get(new_target_system.Id, None) is not None:
                del self._results[new_target_system.Id]
                self._add_log(
                    f"{logging_prefix} No children of this chain meet all targets. Deleting child #{new_target_system.Id}"
                )

            children_responses.append(did_chain_find_everything)

        # Finally, return True if any child (of any child further down the chain) has meet the requirements of "All Values Matched"
        return any(children_responses)
