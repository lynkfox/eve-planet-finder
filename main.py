from buildMapData import AllData
from calculate.full_map_values import CalculatedMapData
from calculate.planetary_industry import PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from logic.fuzzwork_history import get_historical_fuzzworks, get_market_history
from logic.get_dotlan_maps import *
from models.common import WeightMethod

if __name__ == "__main__":

    # with open("eden_svg.xml", "w") as file:
    #     soup = BeautifulSoup(get_region_map(), features="xml")
    #     soup.write(str(soup))

    all_data = AllData(skip_build=True, skip_dotlan_rebuild=False)

    # get_historical_fuzzworks(starting=122331)
    # # result = get_market_history(122298)
    # # derived_data = CalculatedMapData()
    # print("wee")
