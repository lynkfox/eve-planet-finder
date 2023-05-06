from buildMapData import *
from models.common import Universe, WeightMethod, DECIMAL_FORMAT
from models.mapv2 import *
from calculate.search_map import WeightCalculator
from calculate.planetary_industry import PlanetaryIndustryWeightFactor, PlanetaryIndustryResult
from itertools import chain

import plotly.graph_objects as go
import networkx as nx
from time import perf_counter
from alive_progress import alive_bar

POSITION_RELATIVE=1

INCLUDE_PLANET_NAMES = False

COMMODITY_TO_TRACK = "Integrity Response Drones"

USE_CACHE = True

WEIGHTING_METHOD = WeightMethod.AVERAGE

DISPLAY_RESULTS = True
class GraphValues():
    def __init__(self) -> None:
        self.node_x = []
        self.node_y = []
        self.node_names = []
        self.edge_x = []
        self.edge_y = []
        self.node_weight = []
        self.node_text = []
        self.top_weight = 0
        self.top_system = []
        self.top_values = {}

def DisplayMap():
    all_data = AllData(skip_build=True)

    raw_resource_ids = next(commodity for commodity in all_data.Commodities if commodity.Name == COMMODITY_TO_TRACK).GetRawResourceIds(cache=USE_CACHE)

    systemMap = nx.Graph()

    

    calculator = WeightCalculator(
        WeightFactors=PlanetaryIndustryWeightFactor(
            PlanetTypesDesired=[ptype.Id for ptype in all_data.Planet_Types if len(set(ptype.RawResources_Ids).intersection(set(raw_resource_ids))) > 0]
        ),
        WeightResults=PlanetaryIndustryResult,
        MaxJumps=5
    )

    graph_values=GraphValues()
    
    start = perf_counter()
    counter = 0

    with alive_bar( all_data.TotalEdenSystems, title_length=40 ) as bar:

        for system in all_data.Systems:


            if system.Position.Universe == Universe.WORMHOLE:
                continue

            if len(system.Stargate_Ids) == 0:
                continue

            bar.title(f'Analyzing "{system.Constellation_Name}" in the "{system.GetConstellation().Region_Name}" Region')


            system_weight, _ = calculator.Run(system, method=WEIGHTING_METHOD)
            

            systemMap.add_node(system.Name)
            graph_values.node_names.append(system.Name)
            graph_values.node_x.append(system.Position.X/POSITION_RELATIVE)
            graph_values.node_y.append(system.Position.Y/POSITION_RELATIVE)

            graph_values.node_weight.append(system_weight)
            graph_values.node_text.append(f"{system.Name} - {system_weight}")

            for destination in system.GetLinkedSystems():
                systemMap.add_edge(system.Name, destination.Name)
                graph_values.edge_x.append(system.Position.X/POSITION_RELATIVE)
                graph_values.edge_x.append(destination.Position.X/POSITION_RELATIVE)
                graph_values.edge_x.append(None)
                graph_values.edge_y.append(system.Position.Y/POSITION_RELATIVE)
                graph_values.edge_y.append(destination.Position.Y/POSITION_RELATIVE)
                graph_values.edge_y.append(None)
            
            bar()
        


    edge_trace = go.Scatter(
        x=graph_values.edge_x, y=graph_values.edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')


    node_trace = go.Scatter(
        x=graph_values.node_x, y=graph_values.node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='More PI Planets, Closer',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
    
    

    node_trace.marker.color = graph_values.node_weight
    node_trace.text = graph_values.node_text

    top_system = [all_data.GetSystem(key).Name for key in calculator.TopDetails.keys()]
    top_weight = calculator.TopWeight

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title=f'<br>Eve Online System Map - Weighted by Closeness for all PI for {COMMODITY_TO_TRACK}<br>{top_system} with weight of {top_weight}',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    fig.show()

    

    if DISPLAY_RESULTS:
        print(f"=======Top Systems=======")
        print(f"     {top_system}")
        
        for key, value in calculator.TopDetails.items():
            print(all_data.GetSystem(key).Name)
            for entry in value.values():
                print(entry)




if __name__ == "__main__":
    DisplayMap()