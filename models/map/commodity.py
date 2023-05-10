from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import product
from typing import Any, Dict, List, TYPE_CHECKING, Union

from pandas import DataFrame

from data.planetaryResources import *
from models.common import PITier
from models.map.common import iStaticDataExport, MapClient

if TYPE_CHECKING:
    from models.map.planet import PlanetType


@dataclass
class Commodity(iStaticDataExport):
    """
    Planetary Industry Parts
    """

    Tier: PITier = field(kw_only=True, default=PITier.RAW)
    Ingredient_Ids: List[int] = field(kw_only=True, default_factory=list)

    def __post_init__(self, properties: Dict[str, Any]):
        if properties is not None:
            self.Name = properties["nameID"]["en"]
            for resourceID, resource in properties["types"].items():
                if resource["isInput"]:
                    self.Ingredient_Ids.append(resourceID)
                else:
                    self.Id = resourceID

            self._determineTier()

        self.client.ALL_COMMODITIES[self.Id] = self

    @cached_property
    def PlanetType_Ids(self) -> Union[Dict[int, List[int]], List[int]]:
        """
        If the resource is a P0 category (PITier.RAW) then return a list of the planet types ids needed.
        Otherwise returns a map of RawResource.Id: [PlanetType.Id]

        This does not keep track of Duplicates!
        """
        if self.Tier == PITier.RAW:
            return [ptype.Id for ptype in self.PlanetTypes]

        return {key: resource.PlanetType_Ids for key, resource in self.RawResources.items()}

    @cached_property
    def PlanetTypes(self) -> Union[Dict[int, List[PlanetType]], List[PlanetType]]:
        """
        If the resource is a P0 category (PITier.RAW) then return a list of the planet types needed.
        Otherwise returns a map of RawResource.Id: [PlanetType] for each P0 resource needed.

        This does not keep track of Duplicates!
        """
        if self.Tier == PITier.RAW:
            return [self.client.ALL_PLANET_TYPES[ptype_id] for ptype_id in RAW_RESOURCE_TO_TYPE[self.Id]]

        if self.Tier == PITier.BASIC:
            return [ptype.Id for ptype in self.client.ALL_COMMODITIES[self.Ingredient_Ids[0]]]

        return {key: resource.PlanetTypes for key, resource in self.RawResources.items()}

    @cached_property
    def Ingredient_Names(self) -> List[str]:
        return [self.client.ALL_COMMODITIES[ingr_id].Name for ingr_id in self.Ingredient_Ids]

    @cached_property
    def Ingredients(self) -> Dict[int, Commodity]:
        """
        Returns a map of Commodity.Id:Commodity for each resource used to add to this.
        """
        return {ingr_id: self.client.ALL_COMMODITIES[ingr_id] for ingr_id in self.Ingredient_Ids}

    @cached_property
    def RawResources_Ids(self) -> List[int]:
        """
        Returns a list of Commodity.Id for all the P0 commodities that ultimately make up this  resource.

        This value IGNORES DUPLICATES that may occur in the chain. For a complete map that does not ignore duplicates, use
        self.ProductionChainIngredients
        """
        return self.RawResources.keys()

    @cached_property
    def RawResources(self) -> Dict[int, Commodity]:
        """
        Returns a map of Commodity.Id: Commodity for all the P0 commodities that ultimately make up this  resource.

        This value IGNORES DUPLICATES that may occur in the chain. For a complete map that does not ignore duplicates, use
        self.ProductionChainIngredients
        """
        temp = {}

        for ingredient in self.Ingredients.values():
            if ingredient.Tier > 0:
                temp = {**temp, **ingredient.RawResources}
            else:
                return {ingredient.Id: ingredient}

        return temp

    @cached_property
    def ProductionChainIngredients(self) -> Dict[PITier, List[Commodity]]:
        tmp = {}

        tmp.setdefault(self.Tier, []).append(self)
        for ingredient in self.Ingredients.values():
            if ingredient.Tier == PITier.RAW:
                tmp.setdefault(ingredient.Tier, []).append(ingredient)

            else:
                otherChain = ingredient.ProductionChainIngredients

                for key, value in otherChain.items():
                    tmp.setdefault(key, []).extend(value)

        return tmp

    @cached_property
    def ProductionChainRawResources(self) -> List[Commodity]:
        """
        Returns a list, duplicities included, of all the raw resources that would be needed to produce this commodity.
        """
        tmp = []
        for value in self.ProductionChainIngredients[PITier.RAW]:

            tmp.append(value)

        return tmp

    @cached_property
    def PlanetTypePermutationsDF(self) -> DataFrame:
        return DataFrame([sorted(v) for v in self.PlanetTypePermutations])

    @cached_property
    def PlanetTypePermutations(self) -> List[list]:

        if self.Tier == PITier.BASIC:
            return [ptypeid.PlanetType_Ids for ptypeid in self.RawResources.values()][0]

        ingredients = []

        for ingredient in self.Ingredients.values():
            if self.Tier == PITier.ADVANCED and ingredient.Tier == PITier.BASIC:
                values = ingredient.PlanetTypePermutations
                values = [[ptype_id] for ptype_id in values]
                ingredients.append(values)
            else:
                ingredients.append(ingredient.PlanetTypePermutations)
        # ingredients = [ingredient.PlanetTypePermutations for ingredient in self.Ingredients.values()]
        all_combinations = product(*ingredients)

        return self._flatten(all_combinations, self.Tier.value)

    def _flatten(self, all_combinations, tier):
        if not isinstance(all_combinations, list):
            all_combinations = list(all_combinations)

        if isinstance(all_combinations[0], int):
            return all_combinations

        else:
            tmp = []
            for value in all_combinations:
                sub_value = self._flatten(value, tier - 1)
                if tier < self.Tier:
                    tmp.extend(sub_value)
                else:
                    tmp.append(sub_value)

            return tmp

    def _determineTier(self):

        if self.Name in AdvancedCommodities:
            self.Tier = PITier.ADVANCED
        if self.Name in SpecializedCommodities:
            self.Tier = PITier.SPECIALIZED
        if self.Name in RefinedCommodities:
            self.Tier = PITier.REFINED
        if self.Name in BasicCommodities:
            self.Tier = PITier.BASIC

    def __repr__(self) -> str:
        return f"Commodity( Name={self.Name}#{self.Id}, Tier={self.Tier}, Ingredients={self.Ingredient_Names} )"

    def __getstate__(self):
        return (self.Name, self.Id, self.Tier, self.Ingredient_Ids)

    def __setstate__(self, state):
        self.Name, self.Id, self.Tier, self.Ingredient_Ids = state
