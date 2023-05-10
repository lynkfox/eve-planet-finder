from buildMapData import AllData
from calculate.planetary_industry import *
from display.build_node_graphs import *
from display.graph_values import *


def BuildLocalPIMap():
    all_data = AllData(skip_build=True)
    calculator = PlanetaryIndustryWeightFactor()
