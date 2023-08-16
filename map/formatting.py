from __future__ import annotations

from dataclasses import dataclass

import distinctipy
import networkx as nx
import plotly.graph_objects as go

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
    def marker(cls, weights: list, size: int = 10):
        return go.scatter.Marker(
            size=size,
            autocolorscale=False,
            color=weights,
            line=go.scatter.marker.Line(width=2, color="black"),
        )

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
        "Class: (c3) - Static ls/ns": (0.9857089871374185, 0.9955241587011132, 0.8530747827446243),
        "Class: (c2) - Static c4/hs/ns": (0.531516870774841, 0.6899402430638255, 0.41763575492859867),
        "Class: (c5) - Static c1": (0.976074100642694, 0.6646725253074323, 0.5207918800625223),
        "Class: (c4) - Static c3/c5/ns": (0.49205618764447806, 0.7122013060520427, 0.9681307644389184),
        "Class: (c5) - Static c3": (0.754044943400107, 0.9821265010787955, 0.4742774401356272),
        "Class: (c2) - Static c4/hs": (0.5552219204499699, 0.4894965573629999, 0.7007614452391042),
        "Class: (c5) - Static c5/ns": (0.7798610254671359, 0.4223446885562439, 0.42878974243023105),
        "Class: (c4) - Static c2/c5": (0.7818325844217144, 0.7820929056240077, 0.789383033875905),
        "Class: (sentinel) - Static c2": (0.41866458444850324, 0.994245961591074, 0.4879919584728313),
        "Class: (c6) - Static c2": (0.6028996151639636, 0.9886446044702114, 0.971723308315464),
        "Class: (c4) - Static c2/c3": (0.9864230298796756, 0.6852664535760411, 0.982769324398345),
        "Class: (c4) - Static c3/c4/ls": (0.4365163242764596, 0.4221743015876675, 0.9851177089610661),
        "Class: (c5) - Static c4": (0.981276489557631, 0.43474492693610983, 0.708414003106992),
        "Class: (c6) - Static c5/ns": (0.5145451419406021, 0.8253360072868754, 0.6604814251453169),
        "Class: (c4) - Static c1/c3": (0.9858822243560382, 0.8840706588882947, 0.5381804398613375),
        "Class: (c13) - Static c6/ns": (0.4207043347812574, 0.4577381518436087, 0.42155454274889265),
        "Class: (c2) - Static c4/ls/ns": (0.7415277366056655, 0.6223803906646587, 0.6302259211360879),
        "Class: (thera) - Static hs/ls/ns": (0.781567270689057, 0.7276595538088885, 0.41794318732976704),
        "Class: (c4) - Static c4/c5": (0.6752303090076158, 0.9791334340401551, 0.7167805532087053),
        "Class: (c4) - Static c4/c6": (0.9969608209272164, 0.4718651090422587, 0.4185280475553849),
        "Class: (c2) - Static c2/hs/ls": (0.46845935453515447, 0.6504688379958338, 0.6483834587967174),
        "Class: (c4) - Static c1/c2/hs": (0.6857862627245748, 0.8247043081928436, 0.9958908097671406),
        "Class: (vidette) - Static c2": (0.9918473625255263, 0.752031287347655, 0.7358151318820663),
        "Class: (c13) - Static c3/c5/ns": (0.5577120364953092, 0.8726151485890511, 0.41398665216351677),
        "Class: (c1) - Static ns": (0.4284969767006927, 0.8867521961367618, 0.9596800653798498),
        "Class: (c4) - Static c1/c4": (0.6524012113605853, 0.5873610834063075, 0.867984156693975),
        "Class: (c5) - Static c4/ns": (0.8175856541273463, 0.9892067648659194, 0.996446819913071),
        "Class: (c6) - Static c6/ns": (0.7714899468333315, 0.413656503306804, 0.6774086822529405),
        "Class: (c4) - Static c2/c4/ls": (0.9853851703517696, 0.8524288327817332, 0.9958950739443793),
        "Class: (c1) - Static ls": (0.8022622095584173, 0.8426426231903336, 0.5765493143811067),
        "Class: (c1) - Static ls/ns": (0.4336666627301018, 0.5615250180831124, 0.8449859166323936),
        "Class: (c5) - Static c6/ns": (0.8506765445176403, 0.6300528878859141, 0.8267863912709648),
        "Class: (c13) - Static c4/ns": (0.9923257317406419, 0.42867140430448375, 0.9744311406097448),
        "Class: (c4) - Static c1/c3/ls": (0.5974100592431099, 0.4228335869503058, 0.520632909108758),
        "Class: (c4) - Static c1/c3/hs": (0.6770087273107182, 0.5681112572949728, 0.4190304388868521),
        "Class: (c1) - Static hs/ns": (0.609668696759532, 0.7092420932856074, 0.765031640376897),
        "Class: (c4) - Static c2/c3/hs": (0.632422850467047, 0.4311026716758033, 0.9254417892878465),
        "Class: (c4) - Static c3/c5\n": (0.8531586786516722, 0.9943326430966231, 0.6884517742530736),
        "Class: (c1) - Static hs/ls": (0.8751067351433547, 0.5130804756055034, 0.587269405484597),
        "Class: (c13) - Static c2/c5/ns": (0.41538367868104376, 0.7444274967673697, 0.7884307455060957),
        "Class: (c2) - Static c1/hs/ls": (0.645537791216557, 0.7463510028215369, 0.551440414537241),
        "Class: (c3) - Static ls": (0.562788836229703, 0.8971805771940162, 0.8258637896858978),
        "Class: (c13) - Static c3/ns": (0.41533328878048786, 0.41830445555545087, 0.5997516850655168),
        "Class: (c2) - Static c6/ns": (0.5919087025518418, 0.955008439096889, 0.5578123295323504),
        "Class: (c2) - Static c6/ls/ns": (0.9896287229797893, 0.5983935966822725, 0.7351329169786008),
        "Class: (c13) - Static c5/ns": (0.9129215161974616, 0.9913374866236107, 0.41261477029394833),
        "Class: (c2) - Static c3/hs": (0.7985400636230641, 0.7029442805555707, 0.9730376775537254),
        "Class: (c2) - Static c2/ls": (0.49079062311004495, 0.9953114148709634, 0.7055964989974892),
        "Class: (c2) - Static c5/ns": (0.8913467872342462, 0.8880343765264612, 0.810313593069832),
        "Class: (c13) - Static c2/ns": (0.43232654670464105, 0.8178809629778255, 0.5086102749640197),
        "Class: (c5) - Static ls": (0.43629383208127287, 0.5552049903932627, 0.5317659444747674),
        "Class: (c2) - Static c2/hs/ns": (0.8636686641063175, 0.48780300486674943, 0.8088235287405552),
        "Class: (barbican) - Static c2": (0.7198983175321225, 0.9137205375994726, 0.8717425499886339),
        "Class: (c5) - Static c2": (0.9854235286784329, 0.5577375339640308, 0.9174854109728237),
        "Class: (c4) - Static c3/c4/hs": (0.5335162948276052, 0.527316304289613, 0.990768276068009),
        "Class: (c5) - Static c2/ls": (0.848840714507347, 0.5643779279927854, 0.4171089716185114),
        "Class: (c5) - Static c4/ls": (0.7995490145850018, 0.8633698327428555, 0.4126535236893907),
        "Class: (c13) - Static c3/c4/ns": (0.9050551027999454, 0.7745253087942944, 0.889939762731857),
        "Class: (c6) - Static c1": (0.6750297977027675, 0.8498179744597374, 0.676223759978512),
        "Class: (c3) - Static hs": (0.9359216462172779, 0.7750046809637443, 0.4186117746745779),
        "Class: (c6) - Static c3": (0.8687736597024507, 0.7053915955908341, 0.6830552398750422),
        "Class: (c4) - Static c2/c4": (0.5863818303247252, 0.6143832353136038, 0.547969362889519),
        "Class: (c4) - Static c4/c5/ls": (0.42484277909276713, 0.419940608597717, 0.7932786809960833),
        "Class: (c4) - Static c4/c5/ns": (0.6446272531821939, 0.6841375098522413, 0.9685135650257864),
        "Class: (c13) - Static c1/ns": (0.7107592458119995, 0.5083599056514309, 0.5664502558123),
        "Class: (c5) - Static c3/hs/ns": (0.7100442536072381, 0.4932768260318947, 0.7790343434840264),
        "Class: (c13) - Static c1/c4/ns": (0.986831263690241, 0.8671195986965027, 0.7022734348960624),
        "Class: (c1) - Static hs": (0.8471680397778442, 0.8761761228129954, 0.9761174875333007),
        "Class: (c4) - Static c5/c6/ns": (0.9490179431809117, 0.7689888832981835, 0.5852708379365493),
        "Class: (c6) - Static c6": (0.41432339435729354, 0.8617237192749989, 0.7703971673031016),
        "Class: (c3) - Static hs/ls": (0.4236302572598782, 0.9107547432289753, 0.6187221947186068),
        "Class: (c4) - Static c3/c4": (0.9932534592844123, 0.9792039117445696, 0.6381799495856825),
        "Class: (c2) - Static hs/ls": (0.4956940161134804, 0.9903444684584609, 0.8759263002403104),
        "Class: (c6) - Static c4": (0.5374079972022973, 0.7940271140913032, 0.8795150958819771),
        "Class: (c5) - Static c6": (0.6272268351096182, 0.9976122839883702, 0.42110197338949956),
        "Class: (c6) - Static c5": (0.6695570213608031, 0.8593763204644823, 0.5106469855160469),
        "Class: (c3) - Static ns": (0.630094274841723, 0.5784132765345196, 0.6920551885846385),
        "Class: (conflux) - Static c2": (0.873024965177236, 0.9410409726417119, 0.5528192066704775),
        "Class: (c2) - Static c5/ls/ns": (0.4183654402219402, 0.6027078876379038, 0.988421816801701),
        "Class: (c13) - Static c2/c3/ns": (0.7324424911834981, 0.7273680189049526, 0.676454041886333),
        "Class: (c4) - Static c3/c6\n": (0.853847688282554, 0.6252944497657195, 0.5463935264817837),
        "Class: (c4) - Static c1/c5": (0.5344419165948189, 0.5291373503386545, 0.4211405355649258),
        "Class: (c5) - Static c5/ls": (0.7516535582423162, 0.6010638979733687, 0.9664473766707034),
        "Class: (c13) - Static c2/c4/ns": (0.4165993421174211, 0.6925838195094903, 0.5237506241842176),
        "Class: (c2) - Static c3/ls/ns": (0.8718841004307007, 0.41257405253445995, 0.921434005463522),
        "Class: (c5) - Static c5": (0.7267702119136836, 0.6807698007098033, 0.8349091872635925),
        "Class: (c13) - Static c4/c5/ns": (0.4952794439662976, 0.6593716904929708, 0.8317223394339421),
        "Class: (c4) - Static c5/c6\n": (0.529837001265094, 0.47622346171555247, 0.8542499142180108),
        "Class: (c5) - Static c3/ls": (0.6908416227037977, 0.6635059393766622, 0.47790152888527715),
        "Class: (c2) - Static c3/hs/ns": (0.7827935317191143, 0.9004949147235092, 0.7189461091834839),
        "Class: (c2) - Static c1/hs": (0.41551535302290077, 0.5414664101263766, 0.6984841706804972),
        "Class: (c2) - Static c1/c2/hs": (0.8900933950032193, 0.6197131645447838, 0.9947586315833574),
        "Class: (c4) - Static c1/c2": (0.8997216561282793, 0.4214516396075859, 0.4577923825559667),
        "Class: (redoubt) - Static c2": (0.6446279947912195, 0.8058122831530198, 0.8025864339721883),
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
        "RedGiant": (0.9994202129467333, 0.5037269966838168, 0.5203155517901414),
        "BlackHole": (0.6142935734858075, 0.676891151555258, 0.49844051170588966),
        "Pulsar": (0.42805987814652285, 0.673540849674929, 0.9681946195925418),
        "CataclysmicVariable": (0.6858629475391169, 0.9342253810566741, 0.9923904970967451),
        "Wolf-RayetStar": (0.6763256574792263, 0.4631733780103952, 0.9661879926143114),
        "None": (1, 1, 1),
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
    def marker(cls, weights: list, size: int = 13):
        return go.scatter.Marker(
            size=size,
            symbol="diamond-dot",
            autocolorscale=False,
            color=weights,
            line=go.scatter.marker.Line(width=2, color="black"),
        )

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
