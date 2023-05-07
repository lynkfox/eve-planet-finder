import json
from pathlib import Path
from typing import List, Optional

import networkx as nx
import plotly.graph_objects as go
from alive_progress import alive_bar

from buildMapData import *
from calculate.planetary_industry import PlanetaryIndustryResult, PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from models.common import Universe, WeightMethod
from models.mapv2 import *

X_POSITION_RELATIVE = 1
Y_POSITION_RELATIVE = 1

INCLUDE_PLANET_NAMES = False

COMMODITY_TO_TRACK = "Integrity Response Drones"

MAX_JUMPS = 3

WEIGHTING_METHOD = WeightMethod.AVERAGE

USE_CACHE = True

SAVE_AUDIT_LOGS = True

DISPLAY_RESULTS = True

PICKLE_GRAPH_DATA = True  # If True will cause the simulation to be run and any existing pickled data to be overwritten!
# if False, it will attempt to load the data from the pickled data
PICKLE_FILE_PATH = f"data/pickled_graph_{COMMODITY_TO_TRACK}".replace(" ", "_").lower()


class GraphValues:
    """
    Struct for holding various graph data.
    """

    def __init__(self) -> None:
        self.node_x = []
        self.node_y = []
        self.node_z = []
        self.node_names = []
        self.node_custom_data = []
        self.edge_x = []
        self.edge_y = []
        self.edge_z = []
        self.node_weight = []
        self.node_text = []
        self.top_weight = 0
        self.top_system = []
        self.top_values = {}
        self.top_system_x = []
        self.top_system_y = []
        self.top_system_z = []
        self.top_system_text = []
        self.top_system_hover_extra = []
        self.save_top_details = None
        self.save_top_weight = None
        self.logs = None


def DisplayMap():
    all_data = AllData(skip_build=True)

    raw_resource_ids = next(
        commodity for commodity in all_data.Commodities if commodity.Name == COMMODITY_TO_TRACK
    ).GetRawResourceIds(cache=USE_CACHE)
    planet_types_needed = [
        ptype
        for ptype in all_data.Planet_Types
        if len(set(ptype.RawResources_Ids).intersection(set(raw_resource_ids))) > 0
    ]
    systemMap = nx.Graph()

    calculator = WeightCalculator(
        WeightFactors=PlanetaryIndustryWeightFactor(
            PlanetTypesDesired=[ptype.Id for ptype in planet_types_needed],
            JumpWeight=50,
            TypeDensityWeight=50,
            TypeDiversityWeight=25,
            SecurityWeight=50,
            SecurityPreference=SecurityStatus.HIGH_SEC,
        ),
        WeightResults=PlanetaryIndustryResult,
        MaxJumps=MAX_JUMPS,
        MustFindTargets=set([ptype.Id for ptype in planet_types_needed]),
    )

    graph_values = GraphValuesFactory(calculator)

    if len(graph_values.node_names) == 0:  # basically, if there has not yet been any data loaded into the graph values
        GenerateGraphValues(all_data, systemMap, calculator, graph_values)

    if PICKLE_GRAPH_DATA:
        with open(PICKLE_FILE_PATH, "wb") as pickleFile:
            graph_values.logs = calculator.AllAuditLogs
            print(f"Pickling {COMMODITY_TO_TRACK} graph data")
            dump(graph_values, pickleFile)

    top_results_trace = BuildNodesTrace(
        graph_values.top_system_x,
        graph_values.top_system_y,
        graph_values.top_system_text,
        graph_values.top_system_hover_extra,
        "<b>%{text}</b><br><i>%{customdata[0]}, %{customdata[1]}<br>%{customdata[2]}<extra></extra>",
        go.scatter.Marker(symbol="star-diamond", size=25, color="crimson"),
    )

    edge_trace = BuildEdgeTrace(graph_values.edge_x, graph_values.edge_y)

    systems_trace = BuildNodesTrace(
        graph_values.node_x,
        graph_values.node_y,
        graph_values.node_text,
        graph_values.node_custom_data,
        "".join(
            [
                "<b>%{text}</b> | Weight: <i>%{customdata[0]:.2f}</i>",
                "<br>%{customdata[1]}</i>, %{customdata[2]}</i>",
                "<br>%{customdata[3]}" "<extra></extra>",
            ]
        ),
    )

    fig = go.Figure(
        data=[edge_trace, systems_trace, top_results_trace],
        layout=go.Layout(
            title=f"<br>Eve Online System Map - Planetary Industry - Weighted by Minimal Jumps from source, Max Diversity of Planet Types",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=go.layout.Margin(b=20, l=5, r=5, t=40),
            annotations=[
                go.layout.Annotation(
                    text=f'<b>{COMMODITY_TO_TRACK}:</b><br>| {" | ".join(sorted([ptype.Name for ptype in planet_types_needed]))} |',
                    showarrow=True,
                    xref="paper",
                    yref="paper",
                    x=0.25,
                    y=-0.002,
                )
            ],
            xaxis=go.layout.XAxis(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=go.layout.YAxis(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    fig.show()

    if DISPLAY_RESULTS:
        DisplayResultsToStdOut(all_data, planet_types_needed, calculator)


def BuildEdgeTrace(x_edge, y_edge, line: go.scatter.Line = go.scatter.Line(width=0.5, color="#000")) -> go.Scatter:
    """
    Builds a Trace of Edge Lines, assuming the provided lists of coordinates are valid for edges ([X_start, X_end, empty, X2_start, X2_end])

    :param x_edge:(List[int]) list of X Coordinates for every edge
    :param y_edge:(List[int]) list of Y Coordinates for every edge

    :return plotly.graph_object.Scatter: A scatter graph of Lines.
    """

    return go.Scatter(
        x=x_edge,
        y=y_edge,
        line=line,
        hoverinfo="none",
        mode="lines",
    )


def BuildNodesTrace(
    x_cords: List[int],
    y_cords: List[int],
    node_text: List[str],
    custom_data: List[tuple],
    hover_template: str,
    weight: Optional[List(int)] = None,
    marker: Optional[go.scatter.Marker] = None,
) -> go.Scatter:
    """
    Builds the trace for Plotly nodes on a Scatter graph

    All lists are expected to be in the same order. So x, y, node_text, custom_data of index 0 all relate to the same node.

    :param x_cords(List[Int]): X Coordinates for each node.
    :param y_cords(List[Int]): Y Coordinates for each node.
    :param node_text(List[Str]): Text for each node, for the `%{text}` field of the hover_template.
    :param custom_data(List[Tuple]): Tuples of `%{customdata[tuple_index]}` for the hover_template.
    :param hover_template(Str): The template for the hover_text in plotly style.
    :param weight(Optional[List[Int]]): A list of Weights. Can be provided through Marker instead. If not provided, will default to all nodes being Green.
    :param marker(Optional[plotly.graph_objects.scatter.Marker]): A Marker object from plotly to define how the markers will look.
        Has a default marker if None is provided

    :return (plotly.graph_objects.Scatter) A Scatter Trace for applying to a plotly Figure.
    """
    if weight is None:
        weight = "Green"

    if marker is None:
        marker = go.scatter.Marker(
            showscale=True,
            colorscale="RdGy",
            reversescale=True,
            size=10,
            color=weight,
            colorbar=go.scatter.marker.ColorBar(
                thickness=15,
                title="Systems with fewest jumps to get to all raw resources",
                xanchor="left",
                titleside="right",
            ),
            line=go.scatter.marker.Line(width=2, color="black"),
        )

    top_results_trace = go.Scatter(
        x=x_cords,
        y=y_cords,
        customdata=custom_data,
        text=node_text,
        hovertemplate=hover_template,
        mode="markers",
        marker=marker,
    )

    return top_results_trace


def GenerateGraphValues(all_data: AllData, systemMap, calculator, graph_values):
    with alive_bar(all_data.TotalEdenSystems, title_length=47) as bar:
        for system in all_data.Systems:
            if system.Position.Universe == Universe.WORMHOLE:
                continue
            if len(system.Stargate_Ids) == 0:
                continue

            bar.title(
                f'Analyzing "{system.Constellation_Name}" in the "{system.GetConstellation().Region_Name}" Region'
            )
            bar()

            system_weight, weight_details = calculator.Run(system, method=WEIGHTING_METHOD)

            systemMap.add_node(system.Name)
            graph_values.node_names.append(f"{system.Name}#{system.Id}")
            graph_values.node_x.append(system.Position.X / X_POSITION_RELATIVE)
            graph_values.node_y.append(system.Position.Y / Y_POSITION_RELATIVE)
            if len(weight_details) == 0:
                weight_string = f"Not possible get all materials within {MAX_JUMPS}"
            else:
                weight_string = "<br>".join([detail.Html(simple=True) for detail in weight_details.values()])
            graph_values.node_custom_data.append(
                (
                    system_weight,
                    system.Constellation_Name,
                    system.Region_Name,
                    weight_string,
                )
            )

            graph_values.node_weight.append(system_weight)
            graph_values.node_text.append(f"{system.Name}")

            for destination in system.GetLinkedSystems():
                systemMap.add_edge(system.Name, destination.Name)
                graph_values.edge_x.append(system.Position.X / X_POSITION_RELATIVE)
                graph_values.edge_x.append(destination.Position.X / X_POSITION_RELATIVE)
                graph_values.edge_x.append(None)
                graph_values.edge_y.append(system.Position.Y / Y_POSITION_RELATIVE)
                graph_values.edge_y.append(destination.Position.Y / Y_POSITION_RELATIVE)
                graph_values.edge_y.append(None)

    if SAVE_AUDIT_LOGS:
        with open(f"logs.json", "w") as file:
            json.dump(calculator.AllAuditLogs, file)

    graph_values.save_top_details = calculator.TopDetails
    graph_values.save_top_weight = calculator.TopWeight
    for origin_system_id, weight_details in calculator.TopDetails.items():
        system = all_data.GetSystem(origin_system_id)
        graph_values.top_system_x.append(system.Position.X / X_POSITION_RELATIVE)
        graph_values.top_system_y.append(system.Position.Y / X_POSITION_RELATIVE)
        graph_values.top_system_text.append(f"{system.Name}#{system.Id}")
        graph_values.top_system_hover_extra.append(
            (
                system.Constellation_Name,
                system.Region_Name,
                "<br>".join([detail.Html() for detail in weight_details.values()]),
            )
        )


def GraphValuesFactory(calculator: WeightCalculator) -> GraphValues:
    """Produce a Graph Values object.
    If a pickle file exists and the PICKLE_GRAPH_DATA flag is set to true, then it will load the pickled values into the graph values.
    Loaded Graph values will cause cause the plotter to skip generating a new graph.

    :param calculator(WeightCalculator): The WeightCalculator being used. It will be pre-loaded with the Top Systems and Top Systems Details.
    """

    graph_values = GraphValues()
    if Path(PICKLE_FILE_PATH).is_file() and not PICKLE_GRAPH_DATA:
        print(f"Found {PICKLE_FILE_PATH} for this commodity - loading data")
        with open(PICKLE_FILE_PATH, "rb") as pickleFile:
            graph_values = load(pickleFile)
            calculator.TopWeight = graph_values.save_top_weight
            calculator.TopDetails = graph_values.save_top_details
    return graph_values


def DisplayResultsToStdOut(all_data, planet_types_needed, calculator):
    """
    Display the Top results to stdOut.
    """
    print(f"*** Looking for Planets to create: {COMMODITY_TO_TRACK} ***")
    print(f"> Needs:")
    print(f"    > {' | '.join(sorted([ptype.Name for ptype in planet_types_needed]))}")

    if PICKLE_GRAPH_DATA:
        print(f"=======Top Systems=======")
        print(f"     {', '.join([all_data.GetSystem(key).Name for key in calculator.TopDetails.keys()])}")

        for key, value in calculator.TopDetails.items():
            print(f">>>>> {all_data.GetSystem(key).Name}")
            for entry in value.values():
                print(entry)


if __name__ == "__main__":
    DisplayMap()
