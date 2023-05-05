from buildMapData import *
from models.common import Universe
from models.mapv2 import *
#from calculateCloseness import *

import plotly.graph_objects as go
import networkx as nx

POSITION_RELATIVE=1

INCLUDE_PLANET_NAMES = False

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

    #systemWeights = CalculateCloseness(RawResourcesDesired, 1, all_data)

    systemMap = nx.Graph()

    not_done_flag = True
    display_results = not not_done_flag

    graph_values=GraphValues()
    
    for system in all_data.Systems:

        if system.Position.Universe == Universe.WORMHOLE:
            continue

        if len(system.Stargate_Ids) == 0:
            continue

        systemMap.add_node(system.Name)
        graph_values.node_names.append(system.Name)
        graph_values.node_x.append(system.Position.X/POSITION_RELATIVE)
        graph_values.node_y.append(system.Position.Y/POSITION_RELATIVE)
        # weight = systemWeights[system.Id].TotalWeight
        # if weight == 1220 and not_done_flag:
        #     for pot_site in systemWeights[system.Id].PotentialSites:
        #         for entry in pot_site.Audit:
        #             print(entry)
        #     not_done_flag=False
        # if weight > top_weight:
        #     top_weight = weight
        #     top_system = [system.Name]
        #     top_values = {system.Name: systemWeights[system.Id].PotentialSites}

        # elif weight == top_weight:
        #     top_system.append(system.Name)
        #     top_values = {**top_values, **{system.Name: systemWeights[system.Id].PotentialSites}}

        # graph_values.node_weight.append(weight)
        graph_values.node_text.append(f"{system.Name}")


        for destination in system.GetLinkedSystems():
            systemMap.add_edge(system.Name, destination.Name)
            graph_values.edge_x.append(system.Position.X/POSITION_RELATIVE)
            graph_values.edge_x.append(destination.Position.X/POSITION_RELATIVE)
            graph_values.edge_x.append(None)
            graph_values.edge_y.append(system.Position.Y/POSITION_RELATIVE)
            graph_values.edge_y.append(destination.Position.Y/POSITION_RELATIVE)
            graph_values.edge_y.append(None)
        



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

    top_system =""
    top_weight = ""

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title=f'<br>Eve Online System Map - Weighted by Closeness for all PI for Integrity Response Drones<br>{top_system} with weight of {top_weight}',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="Python code: <a href='https://plotly.com/ipython-notebooks/network-graphs/'> https://plotly.com/ipython-notebooks/network-graphs/</a>",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    fig.show()

    

    # if display_results:
    #     print(f"=======Top Systems=======")
    #     print(f"     {top_system}")
    #     print(f"Closest Systems:")
    #     for key, source_system in top_values.items():
    #         systems = sorted(source_system, key=lambda d: d.JumpsFromSource)

    #         for sys in systems:
    #             print(f"\n>>>>>__________ {key} __________<<<<<<")
    #             print(f"\t- Jumps away:                {sys.JumpsFromSource}")
    #             planet_types = " | ".join([key for key in sys.Planets.keys() if key!= "PlanetNames"])
    #             print(f"\t- Planet Types Available:    {planet_types}")
    #             if INCLUDE_PLANET_NAMES:
    #                 for planetInfo in sys.Planets.values():
    #                     print(f"\t\t== {planetInfo.Type}")
    #                     print(f"\t\t --> {', '.join(planetInfo.Names)}")




if __name__ == "__main__":
    DisplayMap()