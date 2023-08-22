from buildMapData import AllData
from calculate.full_map_values import CalculatedMapData
from calculate.planetary_industry import PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from logic.fuzzwork_history import get_historical_fuzzworks, get_market_history
from models.common import WeightMethod

if __name__ == "__main__":

    get_historical_fuzzworks(starting=122331)
    # result = get_market_history(122298)
    # derived_data = CalculatedMapData()
    print("wee")
