from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

import networkx as nx
import plotly.graph_objects as go
from alive_progress import alive_bar

from buildMapData import *
from buildMapData import AllData
from calculate.search_map import iWeightFactor, iWeightResult, WeightCalculator
from display.graph_values import GraphConstants, GraphStyle, GraphValues
from models.common import Universe


@dataclass
class DisplayBuilder:
    Values: GraphValues = field(init=True)
    Styles: GraphStyle = field(init=True)
    AllUniverseData: AllData = field(init=True)
    Calculator: WeightCalculator = field(init=True)
    FullMap: bool = field(kw_only=True, default=True)
    GraphConstants = field(kw_only=True, default_factory=GraphConstants)

    def BuildEdgeTrace(self) -> go.Scatter:
        """
        Builds a Trace of Edge Lines, assuming the provided lists of coordinates are valid for edges ([X_start, X_end, empty, X2_start, X2_end])

        Values and Styles are defined in the class init
        """

        return go.Scatter(
            x=self.Values.edge_x,
            y=self.Values.edge_y,
            line=self.Styles.EdgeStyle,
            hoverinfo="none",
            mode="lines",
        )

    def BuildNodesTrace(self) -> go.Scatter:
        """
        Builds the trace for Plotly nodes on a Scatter graph

        All lists are expected to be in the same order. So x, y, node_text, custom_data of index 0 all relate to the same node.

        :return (plotly.graph_objects.Scatter) A Scatter Trace for applying to a plotly Figure.
        """

        if self.Styles.NodeStyle is None:
            self.Styles.NodeStyle = go.scatter.Marker(
                showscale=True,
                colorscale="RdGy",
                reversescale=True,
                size=10,
                color="Green",
                colorbar=go.scatter.marker.ColorBar(
                    thickness=15,
                    title="Systems with fewest jumps to get to all raw resources",
                    xanchor="left",
                    titleside="right",
                ),
                line=go.scatter.marker.Line(width=2, color="black"),
            )

        top_results_trace = go.Scatter(
            x=self.Values.node_x_coords,
            y=self.Values.node_y_coords,
            customdata=self.Values.node_extra_data,
            text=self.Values.node_names,
            hovertemplate=self.Styles.NodeHoverTemplate,
            mode="markers",
            marker=self.Styles.NodeStyle,
        )

        return top_results_trace

    def GenerateFullMap(self):

        with alive_bar(self.AllUniverseData.TotalEdenSystems, title_length=47) as bar:
            for system in self.AllUniverseData.Systems.values():
                if system.Position.Universe != Universe.EDEN or len(system.LinkedSystem_Ids) == 0:
                    continue

                bar.title(f'Analyzing "{system.Constellation_Name}" in the "{system.Region_Name}" Region')
                bar()

                system_weight, weight_details = self.Calculator.Run(system, method=self.GraphConstants.WEIGHTING_METHOD)

                self.Values.node_names.append(f"{system.Name}#{system.Id}")
                self.Values.node_x_coords.append(system.Position.X / self.GraphConstants.X_POSITION_RELATIVE)
                self.Values.node_y_coords.append(system.Position.Y / self.GraphConstants.Y_POSITION_RELATIVE)
                if len(weight_details) == 0:
                    weight_string = f"Not possible get all materials within {self.GraphConstants.MAX_JUMPS}"
                else:
                    weight_string = "<br>".join([detail.Html(simple=True) for detail in weight_details.values()])
                self.Values.node_extra_data.append(
                    (
                        system_weight,
                        system.Constellation_Name,
                        system.Region_Name,
                        weight_string,
                    )
                )

                self.Values.node_weights.append(system_weight)

                for destination in system.GetLinkedSystems():
                    self.Values.edge_x_coords.append(system.Position.X / self.GraphConstants.X_POSITION_RELATIVE)
                    self.Values.edge_x_coords.append(destination.Position.X / self.GraphConstants.X_POSITION_RELATIVE)
                    self.Values.edge_x_coords.append(None)
                    self.Values.edge_y_coords.append(system.Position.Y / self.GraphConstants.Y_POSITION_RELATIVE)
                    self.Values.edge_y_coords.append(destination.Position.Y / self.GraphConstants.Y_POSITION_RELATIVE)
                    self.Values.edge_y_coords.append(None)

        if self.GraphConstants.SAVE_AUDIT_LOGS:
            with open(f"logs.json", "w") as file:
                json.dump(self.Calculator.AllAuditLogs, file)

        for origin_system_id, weight_details in self.Calculator.TopDetails.items():
            system = self.AllUniverseData.GetSystem(origin_system_id)
            self.Values.top_system_x_coords.append(system.Position.X / self.GraphConstants.X_POSITION_RELATIVE)
            self.Values.top_system_y_coords.append(system.Position.Y / self.GraphConstants.X_POSITION_RELATIVE)
            self.Values.top_system_text.append(f"{system.Name}#{system.Id}")
            self.Values.top_system_extra_details.append(
                (
                    system.Constellation_Name,
                    system.Region_Name,
                    "<br>".join([detail.Html() for detail in weight_details.values()]),
                )
            )

        return systemMap
