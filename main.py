from alive_progress import alive_bar

from buildMapData import AllData
from calculate.full_map_values import CalculatedMapData
from calculate.planetary_industry import PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from models.common import Universe, WeightMethod

if __name__ == "__main__":
    data = AllData(skip_build=True)

    commodity = data.GetCommodity("Organic Mortar Applicators")
    value = commodity.PlanetTypePermutations
    print(value)

    # with alive_bar(data.TotalEdenSystems, title_length=47) as bar:
    #     for system in data.Systems.values():
    #         bar.title(f'{system.Name}#{system.Id}')
    #         system_commodities = system.SingleSystemCommodities
    #         bar()
