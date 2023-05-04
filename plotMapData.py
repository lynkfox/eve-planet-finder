from buildMapData import *
from models.map import AllData, System
from models.common import Universe
from calculateCloseness import *

import plotly.graph_objects as go
import networkx as nx

POSITION_RELATIVE=1

INCLUDE_PLANET_NAMES = False

def DisplayMap():
    all_data = LoadPickles(regions=False, constellations=False)

    systemWeights = CalculateCloseness(RawResourcesDesired, 1, all_data)

    systemMap = nx.Graph()

    not_done_flag = True
    display_results = not not_done_flag

    node_x = []
    node_y = []
    node_names = []
    edge_x = []
    edge_y = []
    node_weight = []
    node_text = []
    top_weight = 0
    top_system = []
    top_values = {}
    for system in all_data.Systems.values():

        if system.Position.Universe == Universe.WORMHOLE:
            continue

        if len(system.Links) == 0:
            continue

        systemMap.add_node(system.Name)
        node_names.append(system.Name)
        node_x.append(system.Position.X/POSITION_RELATIVE)
        node_y.append(system.Position.Y/POSITION_RELATIVE)
        weight = systemWeights[system.Id].TotalWeight
        if weight == 1220 and not_done_flag:
            for pot_site in systemWeights[system.Id].PotentialSites:
                for entry in pot_site.Audit:
                    print(entry)
            not_done_flag=False
        if weight > top_weight:
            top_weight = weight
            top_system = [system.Name]
            top_values = {system.Name: systemWeights[system.Id].PotentialSites}

        elif weight == top_weight:
            top_system.append(system.Name)
            top_values = {**top_values, **{system.Name: systemWeights[system.Id].PotentialSites}}

        node_weight.append(weight)
        node_text.append(f"{system.Name}: {weight}")


        for destination in system.Links:
            systemMap.add_edge(system.Name, destination.Name)
            edge_x.append(system.Position.X/POSITION_RELATIVE)
            edge_x.append(destination.Position.X/POSITION_RELATIVE)
            edge_x.append(None)
            edge_y.append(system.Position.Y/POSITION_RELATIVE)
            edge_y.append(destination.Position.Y/POSITION_RELATIVE)
            edge_y.append(None)
        



    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')


    node_trace = go.Scatter(
        x=node_x, y=node_y,
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
    
    

    node_trace.marker.color = node_weight
    node_trace.text = node_text

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

    del all_data

    if display_results:
        print(f"=======Top Systems=======")
        print(f"     {top_system}")
        print(f"Closest Systems:")
        for key, source_system in top_values.items():
            systems = sorted(source_system, key=lambda d: d.JumpsFromSource)

            for sys in systems:
                print(f"\n>>>>>__________ {key} __________<<<<<<")
                print(f"\t- Jumps away:                {sys.JumpsFromSource}")
                planet_types = " | ".join([key for key in sys.Planets.keys() if key!= "PlanetNames"])
                print(f"\t- Planet Types Available:    {planet_types}")
                if INCLUDE_PLANET_NAMES:
                    for planetInfo in sys.Planets.values():
                        print(f"\t\t== {planetInfo.Type}")
                        print(f"\t\t --> {', '.join(planetInfo.Names)}")




if __name__ == "__main__":
    DisplayMap()