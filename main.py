from buildMapData import AllData
from calculate.full_map_values import CalculatedMapData
from calculate.planetary_industry import PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from models.common import WeightMethod

if __name__ == "__main__":
    data = AllData(skip_build=True)

    RawResourcesDesired = [
        "Aqueous Liquids",
        "Autotrophs",
        "Base Metals",
        "Carbon Compounds",
        "Felsic Magma",
        "Micro-Organisms",
        "Noble Gas",
        "Noble Metals",
        "Non-CS Crystals",
        "Suspended Plasma",
        "Planktic Colonies",
        "Reactive Gas",
    ]

    calculator = WeightCalculator(
        WeightFactors=PlanetaryIndustryWeightFactor(
            PlanetTypesDesired=[commodity.Id for commodity in data.Commodities if commodity.Name in RawResourcesDesired]
        ),
        MaxJumps=5,
    )

    weight, result = calculator.Run(data.Systems[0], WeightMethod.AVERAGE)
    # derived_data = CalculatedMapData()
    print("wee")
