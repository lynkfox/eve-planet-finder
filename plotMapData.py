from buildMapData import *
from models.map import AllData, System
from models.common import Universe

import plotly.graph_objects as go
import networkx as nx

POSITION_RELATIVE=100000000

def DisplayMap():
    all_data = AllData().PopulateFromPickles()

    systemMap = nx.Graph()

    node_x = []
    node_y = []
    node_names = []
    for system in all_data.Systems.values():
        if system.Position.Universe == Universe.WORMHOLE:
            continue
        systemMap.add_node(system.Name)
        node_names.append(system.Name)
        node_x.append(system.Position.X/POSITION_RELATIVE)
        node_y.append(system.Position.Y/POSITION_RELATIVE)

    edge_x = []
    edge_y = []
    LinkMaps(all_data.Stargates, all_data.Systems)
    LinkMaps(all_data.Systems, all_data.Stargates)
    for system in all_data.Systems.values():
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
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(systemMap.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append(node_names[node])

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>Network graph made with Python',
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


if __name__ == "__main__":
    DisplayMap()