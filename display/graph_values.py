from dataclasses import dataclass, field
from typing import Any, Dict, List

import plotly.graph_objects as go

from calculate.search_map import WeightMethod


@dataclass
class GraphValues:
    """
    Struct for holding various graph data.
    """

    node_x_coords: List[Any] = field(kw_only=True, default_factory=list)
    node_y_coords: List[Any] = field(kw_only=True, default_factory=list)
    node_names: List[Any] = field(kw_only=True, default_factory=list)
    node_extra_data: List[Any] = field(kw_only=True, default_factory=list)
    node_weights: List[Any] = field(kw_only=True, default_factory=list)
    edge_x_coords: List[Any] = field(kw_only=True, default_factory=list)
    edge_y_coords: List[Any] = field(kw_only=True, default_factory=list)

    top_systems: List[Any] = field(kw_only=True, default_factory=list)
    top_system_x_coords: List[Any] = field(kw_only=True, default_factory=list)
    top_system_y_coords: List[Any] = field(kw_only=True, default_factory=list)
    top_system_text: List[Any] = field(kw_only=True, default_factory=list)
    top_system_extra_details: List[Any] = field(kw_only=True, default_factory=list)

    top_weight: List[Any] = field(kw_only=True, default_factory=list)
    top_values: Dict[Any] = field(kw_only=True, default_factory=dict)


@dataclass
class GraphStyle:
    NodeStyle: go.scatter.Marker = field(kw_only=True)
    TopNodeStyle: go.scatter.Marker = field(kw_only=True)
    EdgeStyle: go.scatter.Line = field(kw_only=True)

    NodeHoverTemplate: str = field(kw_only=True)
    TopNodeHoverTemplate: str = field(kw_only=True)


@dataclass
class GraphConstants:
    X_POSITION_RELATIVE: int = field(kw_only=True, default=1)
    Y_POSITION_RELATIVE: int = field(kw_only=True, default=1)
    MAX_JUMPS: int = field(kw_only=True, default=3)
    USE_CACHE: bool = field(kw_only=True, default=True)
    SAVE_AUDIT_LOGS: bool = field(kw_only=True, default=True)
    WEIGHTING_METHOD: WeightMethod = field(kw_only=True, default=WeightMethod.AVERAGE)
