from __future__ import annotations

from typing import List

import networkx as nx
import plotly.graph_objects as go
from distinctipy import distinctipy

from buildMapData import *
from data.get_anoikis_data import GetAnokisData
from map.formatting import *
from models.common import Universe
from models.map import *

PICKLE_GRAPH_DATA = True  # If True will cause the simulation to be run and any existing pickled data to be overwritten!
# if False, it will attempt to load the data from the pickled data
PICKLE_FILE_PATH = f"data/pickled_graph_general".replace(" ", "_").lower()


def generate_distinct_colorings(keys: list) -> dict:
    colors = distinctipy.get_colors(len(keys))

    return dict(zip(keys, [distinctipy.get_hex(c) for c in colors]))


def constellation_system_name(system: System):
    return f"{system.GetConstellation().Name}: {system.Name}"


def build_edge_text_point(start: System, destination: System):
    start_position = (
        start.Position.X / X_POSITION_RELATIVE,
        start.Position.Y / Y_POSITION_RELATIVE,
        start.Position.Z / Z_POSITION_RELATIVE,
    )
    destination_position = (
        destination.Position.X / X_POSITION_RELATIVE,
        destination.Position.Y / Y_POSITION_RELATIVE,
        destination.Position.Z / Z_POSITION_RELATIVE,
    )
    x = (start_position[0] + destination_position[0]) / 2
    y = (start_position[1] + destination_position[1]) / 2
    z = (start_position[2] + destination_position[2]) / 2

    if start.Position.X < destination.Position.X:
        name = f"{start.Name} > {destination.Name}"

    else:
        name = f"{destination.Name} > {start.Name}"

    return EdgeText(x, y, z, name)


def QuickMap(
    all_data: AllData,
    include_universe: List[Universe] = [],
    formatting: iDisplayFormatting = DefaultFormatting,
    include_jump_names: bool = True,
):

    systemMap = nx.Graph()
    graph_values = GraphValues()
    existing_lines = []

    for system in all_data.Systems:
        if system.Position.Universe not in include_universe:
            continue

        systemMap.add_node(system.Name)
        graph_values.node_names.append(formatting.node_naming(system))
        graph_values.node_x.append(system.Position.X / X_POSITION_RELATIVE)
        graph_values.node_y.append(system.Position.Y / Y_POSITION_RELATIVE)
        graph_values.node_weight.append(formatting.node_coloring(system))
        if system.Position.Universe == Universe.EDEN:
            system.GetLinkedSystems()

            for destination in system.GetLinkedSystems():

                line = (destination.Name, system.Name)
                opposite = (system.Name, destination.Name)
                if line in existing_lines or opposite in existing_lines:
                    continue
                else:
                    existing_lines.append(line)
                    systemMap.add_edge(system.Name, destination.Name)
                    graph_values.edge_x.append(system.Position.X / X_POSITION_RELATIVE)
                    graph_values.edge_x.append(destination.Position.X / X_POSITION_RELATIVE)
                    graph_values.edge_x.append(None)
                    graph_values.edge_y.append(system.Position.Y / Y_POSITION_RELATIVE)
                    graph_values.edge_y.append(destination.Position.Y / Y_POSITION_RELATIVE)
                    graph_values.edge_y.append(None)
                    graph_values.edge_marker.append(build_edge_text_point(system, destination))

    color_coded_values = break_into_color_groups(formatting.color_map, graph_values)
    all_traces = []

    # System Connection Lines

    all_traces.append(
        go.Scatter(
            name="Connections",
            x=graph_values.edge_x,
            y=graph_values.edge_y,
            line=go.scatter.Line(width=0.5, color="#000"),
            hoverinfo="none",
            mode="lines",
        )
    )

    if include_jump_names:

        all_traces.append(
            go.Scatter(
                name="Connection Info",
                x=[node.x for node in graph_values.edge_marker],
                y=[node.y for node in graph_values.edge_marker],
                text=[node.text for node in graph_values.edge_marker],
                hoverinfo="text",
                mode="markers",
                marker=go.scatter.Marker(
                    symbol="diamond-tall",
                    opacity=0.3,
                    line=go.scatter.marker.Line(width=0.4, color="#777"),
                    size=8,
                    color="#A921E1",
                ),
            )
        )

    # Systems, color coded if weights given
    for key, value in color_coded_values.items():

        all_traces.append(
            go.Scatter(
                name=key,
                x=value.node_x,
                y=value.node_y,
                text=value.node_names,
                mode="markers",
                marker=go.scatter.Marker(
                    size=10,
                    autocolorscale=False,
                    color=value.node_weight,
                    line=go.scatter.marker.Line(width=2, color="black"),
                ),
            )
        )

    fig = go.Figure(
        data=all_traces,
        layout=go.Layout(
            title=f"Eve Online System Map for: {', '.join([uni.name for uni in include_universe])}",
            titlefont_size=16,
            showlegend=True,
            hovermode="closest",
            margin=go.layout.Margin(b=20, l=5, r=5, t=40),
            xaxis=go.layout.XAxis(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=go.layout.YAxis(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    fig.show()


def break_into_color_groups(color_groups: dict, graph_values: GraphValues):

    if len(color_groups) == 0:
        return {"Systems": graph_values}

    split_groups: Dict[str, GraphValues] = {}
    color_to_names = {v: k for k, v in color_groups.items()}
    for idx, weight in enumerate(graph_values.node_weight):

        if weight not in color_groups.values():
            individual_values = split_groups.setdefault("Other", GraphValues())

        else:
            name = color_to_names[weight]
            individual_values = split_groups.setdefault(name, GraphValues())

        individual_values.node_x.append(graph_values.node_x[idx]) if len(graph_values.node_x) > idx else None
        individual_values.node_y.append(graph_values.node_y[idx]) if len(graph_values.node_y) > idx else None
        individual_values.node_z.append(graph_values.node_z[idx]) if len(graph_values.node_z) > idx else None
        individual_values.node_names.append(graph_values.node_names[idx]) if len(
            graph_values.node_names
        ) > idx else None
        individual_values.node_custom_data.append(graph_values.node_custom_data[idx]) if len(
            graph_values.node_custom_data
        ) > idx else None
        individual_values.node_weight.append(graph_values.node_weight[idx]) if len(
            graph_values.node_weight
        ) > idx else None
        individual_values.node_text.append(graph_values.node_text[idx]) if len(graph_values.node_text) > idx else None

    return split_groups


if __name__ == "__main__":
    all_data = AllData(skip_build=True)

    AnokisData = GetAnokisData()
    static_types = list(set([system.statics for system in AnokisData]))
    WormholeStaticFormatting.color_map = generate_distinct_colorings(keys=static_types)
    WormholeStaticFormatting.anokis_map = {system.name: system for system in AnokisData}

    QuickMap(
        all_data, include_universe=[Universe.WORMHOLE], formatting=WormholeStaticFormatting, include_jump_names=False
    )

    print(WormholeClassFormatting.color_map)
