from __future__ import annotations

from copy import deepcopy
from typing import List

import networkx as nx
import plotly.graph_objects as go
from distinctipy import distinctipy

from buildMapData import *
from logic.get_anoikis_data import GetAnokisData
from map.formatting import *
from models.common import Universe
from models.map import *

PICKLE_GRAPH_DATA = True  # If True will cause the simulation to be run and any existing pickled data to be overwritten!
# if False, it will attempt to load the data from the pickled data
PICKLE_FILE_PATH = f"data/pickled_graph_general".replace(" ", "_").lower()


def constellation_system_name(system: System):
    return f"{system.GetConstellation().Name}: {system.Name}"


def build_edge_text_point(start: System, destination: System, dotlan_layout: bool):
    system_position = start.Dotlan.Position if dotlan_layout else start.Position
    destination_system_position = destination.Dotlan.Position if dotlan_layout else destination.Position
    start_position = (
        system_position.X / X_POSITION_RELATIVE,
        system_position.Y / Y_POSITION_RELATIVE,
        system_position.Z / Z_POSITION_RELATIVE,
    )
    destination_position = (
        destination_system_position.X / X_POSITION_RELATIVE,
        destination_system_position.Y / Y_POSITION_RELATIVE,
        destination_system_position.Z / Z_POSITION_RELATIVE,
    )
    x = (start_position[0] + destination_position[0]) / 2
    y = (start_position[1] + destination_position[1]) / 2
    z = (start_position[2] + destination_position[2]) / 2

    if system_position.X < destination_system_position.X:
        name = f"{start.Name} > {destination.Name}"

    else:
        name = f"{destination.Name} > {start.Name}"

    return EdgeText(x, y, z, name)


def QuickMap(
    all_data: AllData,
    include_universe: List[Universe] = [],
    formatting: iDisplayFormatting = DefaultFormatting,
    second_formatting: iDisplayFormatting = None,
    include_jump_names: bool = True,
    three_dimension: bool = False,
    dotlan_layout: bool = False,
):
    """
    see map.formatting.py for Formatting classes.  Second formatting will be "under" the standard formatting, useful for broader categories
    """
    three_dimension = not dotlan_layout
    graph_obj = go.scatter if not three_dimension else go.scatter3d
    scatter_obj = go.Scatter if not three_dimension else go.Scatter3d

    legend_order = {value: idx for idx, value in enumerate(sorted(formatting.color_map.keys()))}

    systemMap = nx.Graph()
    graph_values = GraphValues()
    existing_lines = []
    special_names = []
    special_weights = []

    for system in all_data.Systems:
        if system.Position.Universe not in include_universe:
            continue

        if system.Dotlan is None and dotlan_layout:
            print(f"Warning: Dotlan Postion data missing for: {system.Name} in {system.Region_Name}")
            continue

        system_position = system.Dotlan.Position if dotlan_layout else system.Position

        systemMap.add_node(system.Name)
        graph_values.node_x.append(system_position.X / X_POSITION_RELATIVE)
        graph_values.node_y.append(system_position.Y / Y_POSITION_RELATIVE)
        graph_values.node_z.append(system_position.Z / Z_POSITION_RELATIVE)
        graph_values.node_names.append(formatting.node_naming(system))
        graph_values.node_weight.append(formatting.node_coloring(system))
        if second_formatting is not None:
            special_names.append(second_formatting.node_naming(system))
            special_weights.append(second_formatting.node_coloring(system))

        if system.Position.Universe == Universe.EDEN:
            system.GetLinkedSystems()

            for destination in system.GetLinkedSystems():
                destination_position = destination.Dotlan.Position if dotlan_layout else destination.Position

                line = (destination.Name, system.Name)
                opposite = (system.Name, destination.Name)
                if line in existing_lines or opposite in existing_lines:
                    continue
                else:
                    existing_lines.append(line)
                    systemMap.add_edge(system.Name, destination.Name)
                    graph_values.connections.append(
                        Connection(
                            origin_x=system_position.X / X_POSITION_RELATIVE,
                            origin_y=system_position.Y / Y_POSITION_RELATIVE,
                            origin_z=system_position.Z / Z_POSITION_RELATIVE,
                            destination_x=destination_position.X / X_POSITION_RELATIVE,
                            destination_y=destination_position.Y / Y_POSITION_RELATIVE,
                            destination_z=destination_position.Z / Z_POSITION_RELATIVE,
                            origin_sys=system,
                            destination_sys=destination,
                        )
                    )

    all_traces = break_connections_into_color_groups(
        formatting.connection_grouping, scatter_obj, graph_obj, formatting.color_map, graph_values, three_dimension
    )

    # System Connection Lines

    if second_formatting is not None:
        new_graph = deepcopy(graph_values)
        new_graph.node_names = special_names
        new_graph.node_weight = special_weights
        all_traces.extend(break_into_color_groups(second_formatting, scatter_obj, new_graph, three_dimension))

    # Systems, color coded if weights given
    all_traces.extend(
        break_into_color_groups(formatting, scatter_obj, graph_values, three_dimension, legend_order=legend_order)
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

    return fig


def break_connections_into_color_groups(
    format_grouping: function,
    scatter_obj,
    graph_obj,
    color_groups: dict,
    graph_values: GraphValues,
    three_dimension: bool,
    legend_order: dict = None,
):
    if len(color_groups) == 0:
        return {"Connections": graph_values}

    all_edge_traces = []
    groupings = {}
    for connection in graph_values.connections:
        origin_region = format_grouping(connection.origin_sys)
        groupings.setdefault(origin_region, {}).setdefault("edge_x", []).extend(
            [connection.origin_x, connection.destination_x, None]
        )
        groupings[origin_region].setdefault("edge_y", []).extend([connection.origin_y, connection.destination_y, None])
        groupings[origin_region].setdefault("edge_z", []).extend([connection.origin_z, connection.destination_z, None])

        destination_region = format_grouping(connection.destination_sys)
        if origin_region != destination_region:
            groupings.setdefault(destination_region, {}).setdefault("edge_x", []).extend(
                [connection.origin_x, connection.destination_x, None]
            )
            groupings[destination_region].setdefault("edge_y", []).extend(
                [connection.origin_y, connection.destination_y, None]
            )
            groupings[destination_region].setdefault("edge_z", []).extend(
                [connection.origin_z, connection.destination_z, None]
            )

    for key in color_groups.keys():
        if key not in groupings.keys():
            continue
        grouping = groupings[key]
        edge_trace = scatter_obj(
            name=f"{key} Gates",
            x=grouping["edge_x"],
            y=grouping["edge_y"],
            line=graph_obj.Line(width=0.5, color="#000"),
            legendgroup=key,
            showlegend=False,
            hoverinfo="none",
            mode="lines",
        )
        if three_dimension:
            edge_trace.z = grouping["edge_z"]

        if legend_order is not None:
            edge_trace.legendrank = legend_order.get(key, 1000)

        all_edge_traces.append(edge_trace)
    return all_edge_traces


def break_into_color_groups(
    formatting: iDisplayFormatting,
    scatter_obj,
    graph_values: GraphValues,
    three_dimension: bool,
    legend_order: dict = None,
):

    if len(formatting.color_map) == 0:
        return {"Systems": graph_values}

    layer_traces = []
    split_groups: Dict[str, GraphValues] = {}
    color_to_names = {distinctipy.get_hex(v): k for k, v in formatting.color_map.items()}
    for idx, weight in enumerate(graph_values.node_weight):

        if weight not in color_to_names.keys() and weight not in formatting.color_map.values():
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

    for key, value in split_groups.items():

        layer = scatter_obj(
            name=key,
            x=value.node_x,
            y=value.node_y,
            text=value.node_names,
            mode="markers",
            legendgroup=key,
            opacity=formatting.opacity,
            marker=formatting.marker(value.node_weight, three_dimension),
        )
        if three_dimension:
            layer.z = value.node_z

        if legend_order is not None:
            layer.legendrank = legend_order.get(key, 1000)

        layer_traces.append(layer)

    return layer_traces


if __name__ == "__main__":
    all_data = AllData(skip_build=True)

    AnokisData = GetAnokisData(pickle_data=False)

    # WormholeWeatherFormatting.color_map = generate_distinct_colorings(keys=weather, existing=WormholeClassFormatting.color_map, pastel_factor=True)
    # RegionFormatting.color_map = generate_distinct_colorings(
    #     keys=[region.Name for region in all_data.Regions], existing=None, pastel_factor=True
    # )
    WormholeClassFormatting.anokis_map = {system.name: system for system in AnokisData}
    WormholeStaticFormatting.anokis_map = WormholeClassFormatting.anokis_map
    WormholeWeatherFormatting.anokis_map = WormholeClassFormatting.anokis_map

    figure = QuickMap(
        all_data,
        include_universe=[Universe.EDEN],
        formatting=RegionFormatting,
        second_formatting=None,
        include_jump_names=False,
        three_dimension=True,
        dotlan_layout=True,
    )

    # figure.write_html("docs/pre_rendered_maps/3D/wormhole_by_weather_and_class.html")

    # print(RegionFormatting.color_map)
