from alive_progress import alive_bar

from buildMapData import AllData
from calculate.full_map_values import CalculatedMapData
from calculate.planetary_industry import PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from models.common import Universe, WeightMethod

if __name__ == "__main__":
    data = AllData(skip_build=True)

    with alive_bar(data.TotalEdenSystems, title_length=47) as bar:
        for system in data.Systems.values():
            if system.Position.Universe == Universe.WORMHOLE:
                continue
            if len(system.Stargate_Ids) == 0:
                continue

            system.SingleSystemCommodities
            bar.title(f'Analyzing "{system.Constellation_Name}" in the "{system.Region_Name}" Region')
            bar()
