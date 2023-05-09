from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from data.planetaryResources import *
from models.common import PITier
from models.map.common import iStaticDataExport, MapClient

if TYPE_CHECKING:
    from models.map.planet import Planet, PlanetType


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
    def PlanetType_Ids(self) -> List[int]:
        if self.Tier == PITier.RAW:
            return RAW_RESOURCE_TO_TYPE[self.Id]
        else:
            return []

    @cached_property
    def PlanetTypes(self) -> Dict[int, PlanetType]:
        if self.Tier == PITier.RAW:
            return {ptype_id: self.client.ALL_PLANET_TYPES[ptype_id] for ptype_id in RAW_RESOURCE_TO_TYPE[self.Id]}
        else:
            return []

    @cached_property
    def Ingredient_Names(self) -> List[str]:
        return [self.client.ALL_COMMODITIES[ingr_id].Name for ingr_id in self.Ingredient_Ids]

    @cached_property
    def Ingredients(self) -> Dict[int, Commodity]:
        return {ingr_id: self.client.ALL_COMMODITIES[ingr_id] for ingr_id in self.Ingredient_Ids}

    @cached_property
    def RawResources_Ids(self, cache: bool = True) -> List[int]:
        return [raw_id for raw_id in self.RawResources]

    @cached_property
    def RawResources(self) -> Dict[int, Commodity]:
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
    def PlanetTypeId_Permutations(self) -> List[Tuple[int]]:
        """
        All permutations of planet type ids that would let you produce this ingredient, assuming 1 planet per raw resource

        e.g.

        Consumer Electronics (tier: Specialized) needs Toxic Metals and Chiral Structures.
        Toxic metals can be produced on Ice, Lava, and Plasma. Chiral Structures can be produced on Lava and Plasma.
        Combinations of planet types that would allow you to produce Consumer Electronics in a single system would then be:
        (Ice, Lava), (Lava, Lava), (Plasma, Lava), (Plasma, Plasma)
        """

        # do the initial calculation for the lowest pont as a 2D Matrix
        if self.Tier == PITier.REFINED:
            planet_types_by_raw = {raw.Name: raw.PlanetTypes for raw in self.RawResources.values()}
            matrix_of_ids = []

            for value in planet_types_by_raw.values():
                matrix_of_ids.append([ptype.Id for ptype in value.values()])

            return list(product(*matrix_of_ids))
        elif self.Tier == PITier.BASIC:
            return [item.PlanetType_Ids for item in self.Ingredients.values()]
        elif self.Tier == PITier.RAW:
            return self.PlanetType_Ids
        else:
            tmp = []
            for ingredient in self.Ingredients.values():
                tmp.append(ingredient.PlanetTypeId_Permutations)

            return list(product(*tmp))

    @cached_property
    def HashedPermutations(self):
        return {hash(str(item)): item for item in self.PlanetTypeId_Permutations}

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
        return f"Commodity( Name={self.Name}#{self.Id}, Tier={self.Tier}, Ingredients={self.IngredientNames} )"

    def __getstate__(self):
        return (self.Name, self.Id, self.Tier, self.Ingredient_Ids)

    def __setstate__(self, state):
        self.Name, self.Id, self.Tier, self.Ingredient_Ids = state
