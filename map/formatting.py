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
        "Class: (c5) - Static c2static": "#00ff00",
        "Class: (c2) - Static c2/hs/ls": "#d101fd",
        "Class: (c13) - Static c2/ns": "#ff8000",
        "Class: (c5) - Static c3/hs/ns": "#1396d5",
        "Class: (c5) - Static c4/ls": "#0000ff",
        "Class: (redoubt) - Static c2static": "#80ff80",
        "Class: (c4) - Static c2/c4": "#874668",
        "Class: (c5) - Static c1static": "#f985ca",
        "Class: (barbican) - Static c2static": "#ff0000",
        "Class: (c13) - Static c2/c3/ns": "#ffff00",
        "Class: (c3) - Static hs/ls": "#1b7e04",
        "Class: (c3) - Static hsstatic": "#00ffff",
        "Class: (c2) - Static c1/c2/hs": "#000080",
        "Class: (c2) - Static c6/ns": "#8bd206",
        "Class: (c4) - Static c1/c3/ls": "#89cbf8",
        "Class: (c13) - Static c4/ns": "#683ae4",
        "Class: (c5) - Static c6/ns": "#eac86d",
        "Class: (conflux) - Static c2static": "#03e087",
        "Class: (c5) - Static c6static": "#800000",
        "Class: (c1) - Static ls/ns": "#fd4168",
        "Class: (c13) - Static c1/c4/ns": "#6ba373",
        "Class: (c5) - Static c5/ls": "#22627f",
        "Class: (c4) - Static c5/c6\n": "#8f7c11",
        "Class: (c2) - Static c5/ls/ns": "#9d7df7",
        "Class: (c1) - Static nsstatic": "#0150fd",
        "Class: (c5) - Static c3/ls": "#b9035d",
        "Class: (c5) - Static c5/ns": "#c03fc0",
        "Class: (c3) - Static nsstatic": "#06bb35",
        "Class: (c4) - Static c4/c5/ls": "#3f1d42",
        "Class: (c2) - Static c4/hs": "#bf8080",
        "Class: (c6) - Static c2static": "#63099c",
        "Class: (c4) - Static c1/c3": "#32fc46",
        "Class: (c13) - Static c3/c4/ns": "#46e8ca",
        "Class: (c13) - Static c3/c5/ns": "#ba3519",
        "Class: (c5) - Static c4static": "#fe07aa",
        "Class: (c5) - Static lsstatic": "#c5fbbb",
        "Class: (c2) - Static c1/hs/ls": "#f3c8cc",
        "Class: (c4) - Static c4/c5": "#e7be01",
        "Class: (c5) - Static c2/ls": "#5b7ab3",
        "Class: (c2) - Static c4/hs/ns": "#8000ff",
        "Class: (c6) - Static c5/ns": "#1534b6",
        "Class: (c13) - Static c4/c5/ns": "#bcfd2c",
        "Class: (c5) - Static c3static": "#3e4202",
        "Class: (c13) - Static c3/ns": "#05513b",
        "Class: (c4) - Static c3/c4/ls": "#a5c250",
        "Class: (c4) - Static c4/c6": "#51aa0b",
        "Class: (c2) - Static c5/ns": "#1aa188",
        "Class: (c6) - Static c3static": "#aab6a1",
        "Class: (c13) - Static c6/ns": "#ff4bfe",
        "Class: (c5) - Static c5static": "#ffff80",
        "Class: (c4) - Static c3/c5\n": "#556835",
        "Class: (c6) - Static c4static": "#26c6fb",
        "Class: (c6) - Static c1static": "#d06142",
        "Class: (c4) - Static c1/c3/hs": "#fb8d58",
        "Class: (c2) - Static c2/ls": "#50fe05",
        "Class: (c4) - Static c3/c6\n": "#62b6b7",
        "Class: (c2) - Static c3/hs/ns": "#4d7afa",
        "Class: (c4) - Static c2/c5": "#3003cd",
        "Class: (c6) - Static c6static": "#80ffff",
        "Class: (c1) - Static hs/ns": "#b101b2",
        "Class: (vidette) - Static c2static": "#fe3e15",
        "Class: (c4) - Static c2/c3/hs": "#c5affb",
        "Class: (c4) - Static c3/c4/hs": "#4dd986",
        "Class: (c4) - Static c1/c5": "#ff0858",
        "Class: (c1) - Static lsstatic": "#780156",
        "Class: (c2) - Static c4/ls/ns": "#c3fb74",
        "Class: (c4) - Static c4/c5/ns": "#03febf",
        "Class: (c13) - Static c1/ns": "#6ee53f",
        "Class: (c4) - Static c1/c2": "#020243",
        "Class: (c2) - Static c3/ls/ns": "#018558",
        "Class: (c2) - Static c1/hs": "#0468b7",
        "Class: (c4) - Static c3/c5/ns": "#ea5d9f",
        "Class: (c13) - Static c2/c4/ns": "#6041a3",
        "Class: (c6) - Static c6/ns": "#02346d",
        "Class: (c3) - Static lsstatic": "#25d301",
        "Class: (c4) - Static c1/c2/hs": "#773022",
        "Class: (c4) - Static c1/c4": "#b2a811",
        "Class: (c6) - Static c5static": "#9861a6",
        "Class: (c2) - Static c2/hs/ns": "#91dfb8",
        "Class: (c4) - Static c5/c6/ns": "#d52489",
        "Class: (c1) - Static hs/ls": "#8d7b54",
        "Class: (c4) - Static c2/c3": "#ad2bfe",
        "Class: (thera) - Static hs/ls/ns": "#f0e83c",
        "Class: (sentinel) - Static c2static": "#0acabc",
        "Class: (c4) - Static c3/c4": "#012f12",
        "Class: (c5) - Static c4/ns": "#459e43",
        "Class: (c2) - Static c3/hs": "#420609",
        "Class: (c3) - Static ls/ns": "#942c98",
        "Class: (c2) - Static hs/ls": "#c85cfb",
        "Class: (c4) - Static c2/c4/ls": "#606e79",
        "Class: (c13) - Static c2/c5/ns": "#b50119",
        "Class: (c1) - Static hsstatic": "#c5f6ff",
        "Class: (c13) - Static c5/ns": "#dfa697",
        "Class: (c2) - Static c6/ls/ns": "#b586be",
    }
    anokis_map = {}

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

    @classmethod
    def node_naming(cls, system: System):
        wh_class = system.Region_Name[0]
        class_name = cls.region_class_map[wh_class]
        return f"{system.Name} ({class_name}) - {cls.anokis_map[system.Name].statics}"

    @classmethod
    def node_coloring(cls, system: System):
        wh_class = system.Region_Name[0]
        class_name = cls.region_class_map[wh_class]
        static = cls.anokis_map[system.Name].statics

        key = f"Class: ({class_name.lower()}) - Static {static}"

        return cls.color_map.get(key, "#000")
