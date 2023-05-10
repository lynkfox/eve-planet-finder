import json
from itertools import chain
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

import networkx as nx
import plotly.graph_objects as go
from alive_progress import alive_bar

from buildMapData import *
from calculate.planetary_industry import PlanetaryIndustryResult, PlanetaryIndustryWeightFactor
from calculate.search_map import WeightCalculator
from models.common import Universe, WeightMethod

if TYPE_CHECKING:
    from models.map.commodity import Commodity
    from models.map.galaxy import Constellation, Region
    from models.map.planet import Planet, PlanetType
    from models.map.system import Stargate, System


def GenerateFullSystemMapForPIWeights():
    all_data = AllData(skip_build=True)

    commodity_obj = next(
        commodity for commodity in all_data.Commodities.values() if commodity.Name == COMMODITY_TO_TRACK
    )
    raw_resources = commodity_obj.RawResources

    raw_resource_ids = [commodity for commodity in raw_resources.values()]
    production_chain = commodity_obj.ProductionChainIngredients
    min_planet_types_needed_in_a_jump_chain = set(
        chain(*[commodity.PlanetTypes for commodity in raw_resources.values()])
    )

    possible_pi = None
    for system in all_data.Systems.values():
        possible_pi = system.SingleSystemCommodities
        break

    calculator = WeightCalculator(
        WeightFactors=PlanetaryIndustryWeightFactor(
            PlanetTypesDesired=min_planet_types_needed_in_a_jump_chain,
            ProductionChainCommodities=production_chain,
            JumpWeight=50,
            TypeDensityWeight=50,
            TypeDiversityWeight=25,
            SecurityWeight=50,
            SecurityPreference=SecurityStatus.HIGH_SEC,
        ),
        WeightResults=PlanetaryIndustryResult,
        MaxJumps=MAX_JUMPS,
        MustFindTargets=min_planet_types_needed_in_a_jump_chain,
    )

    graph_values = GraphValuesFactory(calculator)

    if len(graph_values.node_names) == 0:  # basically, if there has not yet been any data loaded into the graph values
        GenerateGraphValues(all_data, calculator, graph_values)

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


if __name__ == "__main__":
    GenerateFullSystemMapForPIWeights()
