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
    color_map = {
        "c6static": "#05fe29",
        "hs/ns": "#ff00ff",
        "c1/c5": "#0080ff",
        "c4static": "#ff8000",
        "c2/hs/ns": "#804080",
        "c5/ls/ns": "#bff951",
        "c4/hs/ns": "#43facc",
        "lsstatic": "#d27ffb",
        "c2/c5/ns": "#518904",
        "c1/c4": "#ff0000",
        "ls/ns": "#0000ff",
        "c4/ns": "#000080",
        "c4/ls/ns": "#0b9f83",
        "c2/c4/ns": "#f93d89",
        "c4/c5": "#91a18d",
        "c3/c5\n": "#8414ef",
        "c5static": "#7d2003",
        "c1/c2/hs": "#ff967b",
        "c3/hs": "#9fcff0",
        "c2/c3": "#6de608",
        "c1/hs/ls": "#025430",
        "c2/c4": "#1953b1",
        "c3/c6\n": "#6d63f8",
        "c1static": "#c2005e",
        "c1/c3": "#ffff00",
        "c5/c6/ns": "#afaa20",
        "c5/ls": "#44f470",
        "hs/ls/ns": "#b25e1c",
        "c2/hs/ls": "#d4d29f",
        "c1/c3/hs": "#54b34f",
        "c2/c3/hs": "#4da7ce",
        "c5/ns": "#13cbff",
        "c3/ls/ns": "#5a0a51",
        "c4/c6": "#01a927",
        "c4/ls": "#ce34e3",
        "c3static": "#570aa5",
        "c2/c4/ls": "#fbc838",
        "c2/ns": "#486a5d",
        "c2/ls": "#93feaf",
        "c3/hs/ns": "#bd639d",
        "c1/c3/ls": "#da02b0",
        "c5/c6\n": "#ffff80",
        "c2/c3/ns": "#2b3bf8",
        "c2/c5": "#fbacd6",
        "c4/c5/ns": "#fd4320",
        "c6/ns": "#0cd2b5",
        "c3/c4/ls": "#514e1b",
        "c3/ns": "#6874af",
        "hs/ls": "#fc68c7",
        "c3/ls": "#c61f18",
        "c3/c4/hs": "#9793d8",
        "nsstatic": "#36347c",
        "c3/c4/ns": "#06153f",
        "c4/c5/ls": "#997a59",
        "c3/c5/ns": "#80ffff",
        "c3/c4": "#9e16a7",
        "c4/hs": "#bf3c61",
        "c2static": "#9aca5a",
        "c1/ns": "#035e6f",
        "c6/ls/ns": "#bfe108",
        "c1/hs": "#07d35a",
        "c1/c2": "#e56f47",
        "hsstatic": "#061bba",
        "c1/c4/ns": "#017e00",
    }
    anokis_map = {}

    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Name} ({cls.anokis_map[system.Name].statics})"

    @classmethod
    def node_coloring(cls, system: System):
        static = cls.anokis_map[system.Name].statics

        return cls.color_map.get(static, "#000")
