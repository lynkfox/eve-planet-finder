from __future__ import annotations

from dataclasses import dataclass

import distinctipy
import networkx as nx

from buildMapData import *
from models.map import Constellation, Region, System

X_POSITION_RELATIVE = 1
Y_POSITION_RELATIVE = 1
Z_POSITION_RELATIVE = 1

USE_CACHE = True

DISPLAY_RESULTS = True


def generate_distinct_colorings(keys: list, existing: dict = None, pastel_factor: bool = False) -> dict:

    ignore = list(existing.values()) if existing is not None else None

    if pastel_factor:
        colors = distinctipy.get_colors(len(keys), ignore, pastel_factor=0.7)
    else:
        colors = distinctipy.get_colors(len(keys), ignore)

    return dict(zip(keys, [c for c in colors]))


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

    @classmethod
    def _output_hex(cls, color):
        if isinstance(color, tuple):
            return distinctipy.get_hex(color)
        else:
            return color


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

        return cls._output_hex(cls.color_map.get(system.Region_Name, system.Region_Id))


class WormholeClassFormatting(iDisplayFormatting):
    color_map = {
        "C1": (0.01410150138348698, 0.9938560702764367, 0.15529185179496618),
        "C2": (1.0, 0.0, 1.0),
        "C3": (0.0, 0.5, 1.0),
        "C4": (1.0, 0.5, 0.0),
        "C5": (0.5, 0.25, 0.5),
        "C6": (0.7173603662305557, 0.9976305514667957, 0.02990937732375487),
        "C13": (0.336123635844083, 0.9869328337546734, 0.7861524279720865),
        "Thera": (0.8052675059247655, 0.4985193389577768, 0.9744253651630016),
        "Drifter": (1.0, 0.0, 0.0),
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

        return cls._output_hex(cls.color_map.get(cls.region_class_map[wh_class], "#000"))


class WormholeStaticFormatting(iDisplayFormatting):
    color_map = {
        "Class: (c5) - Static c2": "#00ff00",
        "Class: (c2) - Static c2/hs/ls": "#d101fd",
        "Class: (c13) - Static c2/ns": "#ff8000",
        "Class: (c5) - Static c3/hs/ns": "#1396d5",
        "Class: (c5) - Static c4/ls": "#0000ff",
        "Class: (drifter) - Static c2": "#80ff80",
        "Class: (c4) - Static c2/c4": "#874668",
        "Class: (c5) - Static c1": "#f985ca",
        "Class: (drifter) - Static c2": "#ff0000",
        "Class: (c13) - Static c2/c3/ns": "#ffff00",
        "Class: (c3) - Static hs/ls": "#1b7e04",
        "Class: (c3) - Static hs": "#00ffff",
        "Class: (c2) - Static c1/c2/hs": "#000080",
        "Class: (c2) - Static c6/ns": "#8bd206",
        "Class: (c4) - Static c1/c3/ls": "#89cbf8",
        "Class: (c13) - Static c4/ns": "#683ae4",
        "Class: (c5) - Static c6/ns": "#eac86d",
        "Class: (drifter) - Static c2": "#03e087",
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
        "Class: (c6) - Static c2": "#63099c",
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
        "Class: (c6) - Static c1": "#d06142",
        "Class: (c4) - Static c1/c3/hs": "#fb8d58",
        "Class: (c2) - Static c2/ls": "#50fe05",
        "Class: (c4) - Static c3/c6\n": "#62b6b7",
        "Class: (c2) - Static c3/hs/ns": "#4d7afa",
        "Class: (c4) - Static c2/c5": "#3003cd",
        "Class: (c6) - Static c6static": "#80ffff",
        "Class: (c1) - Static hs/ns": "#b101b2",
        "Class: (drifter) - Static c2": "#fe3e15",
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
        "Class: (drifter) - Static c2": "#0acabc",
        "Class: (c4) - Static c3/c4": "#012f12",
        "Class: (c5) - Static c4/ns": "#459e43",
        "Class: (c2) - Static c3/hs": "#420609",
        "Class: (c3) - Static ls/ns": "#942c98",
        "Class: (c2) - Static hs/ls": "#c85cfb",
        "Class: (c4) - Static c2/c4/ls": "#606e79",
        "Class: (c13) - Static c2/c5/ns": "#b50119",
        "Class: (c1) - Static hs": "#c5f6ff",
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

        return cls._output_hex(cls.color_map.get(key, "#000"))


class WormholeWeatherFormatting(iDisplayFormatting):
    color_map = {
        "Magnetar": (0.9910620813933451, 0.9515538007257447, 0.6644358723871735),
        "RedGiant": (0.6142935734858075, 0.676891151555258, 0.49844051170588966),
        "BlackHole": (0.9994202129467333, 0.5037269966838168, 0.5203155517901414),
        "Pulsar": (0.42805987814652285, 0.673540849674929, 0.9681946195925418),
        "CataclysmicVariable": (0.6858629475391169, 0.9342253810566741, 0.9923904970967451),
        "Wolf-RayetStar": (0.6363977243366369, 0.9858504160200827, 0.5307043219279302),
        "None": (0.4284663657025158, 0.422568615684784, 0.8003065474614218),
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
        return f"{system.Name} ({cls.region_class_map[wh_class]}) {cls.anokis_map[system.Name].weather}"

    @classmethod
    def node_coloring(cls, system: System):
        weather = cls.anokis_map[system.Name].weather

        if weather is None:
            weather = "None"

        return cls._output_hex(cls.color_map.get(weather, "#FFF"))
