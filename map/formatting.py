from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from buildMapData import *
from models.map import Constellation, Region, System

X_POSITION_RELATIVE = 1
Y_POSITION_RELATIVE = 1
Z_POSITION_RELATIVE = 1

USE_CACHE = True

DISPLAY_RESULTS = True


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
        self.node_weight = []
        self.node_text = []
        self.edge_x = []
        self.edge_y = []
        self.edge_z = []
        self.edge_marker = []


@dataclass
class EdgeText:
    x: int
    y: int
    z: int
    text: str


class iDisplayFormatting:
    color_map = {}

    @classmethod
    def node_naming(cls, system: System):
        raise NotImplementedError

    @classmethod
    def node_coloring(cls, system: System):
        raise NotImplementedError


class DefaultFormatting(iDisplayFormatting):
    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Name}#{system.Id}"

    @classmethod
    def node_coloring(cls, system: System):
        return "Green"


class RegionFormatting(iDisplayFormatting):
    color_map = {}

    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Region_Name}: {system.Name}"

    @classmethod
    def node_coloring(cls, system: System):

        return cls.color_map.get(system.Region_Name, system.Region_Id)


class WormholeClassFormatting(iDisplayFormatting):
    color_map = {
        "C1": "#f400ec",
        "C2": "#00ff00",
        "C3": "#0080ff",
        "C4": "#f28b03",
        "C5": "#71437e",
        "C6": "#50fab7",
        "Thera": "#ff0000",
        "C13": "#abf92c",
        "Drifter": "#d97fec",
    }

    region_class_map = {
        "A": "C1",
        "B": "C2",
        "C": "C3",
        "D": "C4",
        "E": "C5",
        "F": "C6",
        "G": "Thera",
        "H": "C13",
        "K": "Drifter",
    }

    anokis_map = {}

    @classmethod
    def node_naming(cls, system: System):
        wh_class = system.Region_Name[0]
        return f"{system.Name} ({cls.region_class_map[wh_class]})"

    @classmethod
    def node_coloring(cls, system: System):
        wh_class = system.Region_Name[0]

        return cls.color_map.get(cls.region_class_map[wh_class], "#000")


class WormholeStaticFormatting(iDisplayFormatting):
    color_map = {}
    anokis_map = {}

    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Name} ({cls.anokis_map[system.Name].statics})"

    @classmethod
    def node_coloring(cls, system: System):
        static = cls.anokis_map[system.Name].statics

        return cls.color_map.get(static, "#000")
