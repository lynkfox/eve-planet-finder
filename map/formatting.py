from __future__ import annotations

from dataclasses import dataclass
from typing import List

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
        self.connections: List[Connection] = []
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


@dataclass
class Connection:
    origin_x: float
    origin_y: float
    origin_z: float
    destination_x: float
    destination_y: float
    destination_z: float
    origin_sys: System
    destination_sys: System


class iDisplayFormatting:
    color_map = {}
    opacity = 1
    Name = "Default"

    @classmethod
    def marker(cls, weights: list, three_dimension: bool, size: int = 10):

        if three_dimension:
            return go.scatter3d.Marker(
                size=size,
                autocolorscale=False,
                color=weights,
                line=go.scatter3d.marker.Line(width=2, color="black"),
            )

        else:
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

    @classmethod
    def connection_grouping(cls, graphvalues):
        return None


class DefaultFormatting(iDisplayFormatting):
    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Name}#{system.Id}"

    @classmethod
    def node_coloring(cls, system: System):
        return "Green"


class RegionFormatting(iDisplayFormatting):
    Name = "Region"
    color_map = {
        "Derelik": (0.48367180992680553, 0.4228967402056644, 0.631376260468515),
        "The Forge": (0.44309497948771154, 0.9785364214921539, 0.4270652916504713),
        "Vale of the Silent": (0.999112829028171, 0.4215394747848921, 0.9904729984394264),
        "UUA-F4": (0.9526137142862056, 0.6987803465075032, 0.4242522621609294),
        "Detorid": (0.4135700031025266, 0.805119164788429, 0.9962124435731707),
        "Wicked Creek": (0.8106715320257543, 0.7110963305451602, 0.8826291822871289),
        "Cache": (0.8394393979078025, 0.971212543650325, 0.5749797401223352),
        "Scalding Pass": (0.5744431208923062, 0.6663835818625139, 0.43213878040257153),
        "Insmother": (0.8493720345378989, 0.4253821853758018, 0.5712652444780921),
        "Tribute": (0.6491297571861891, 0.42810477042346484, 0.9706010029618521),
        "Great Wildlands": (0.6693408034420097, 0.9784974886407952, 0.9488344419635937),
        "Curse": (0.41397055157357837, 0.6453234000047384, 0.7540219951139997),
        "Malpais": (0.5802266708488684, 0.8591832561935209, 0.6586198671093233),
        "Catch": (0.9966934305625766, 0.5757092565263122, 0.6771156152431717),
        "Venal": (0.9725577105185279, 0.8127695609824903, 0.6813436922941585),
        "Lonetrek": (0.5970441529202593, 0.6302936709160725, 0.9944801468251674),
        "J7HZ-F": (0.698562496291342, 0.5660686072986253, 0.6977239811379958),
        "The Spire": (0.4494021143271292, 0.97489114090635, 0.8110553089484329),
        "A821-A": (0.7506274963134374, 0.7841044032955112, 0.5101981642836175),
        "Tash-Murkon": (0.431493553484453, 0.4729040887309283, 0.8645675702163124),
        "Outer Passage": (0.5951060809090485, 0.45836775531083074, 0.41572249609190504),
        "Stain": (0.9966295080503849, 0.785639302293194, 0.9961506985828521),
        "Pure Blind": (0.8554642061255936, 0.49630702459439807, 0.8333653109429406),
        "Immensea": (0.662866726017054, 0.9366446150287642, 0.4215576385495741),
        "Etherium Reach": (0.8612780399793478, 0.9332526549803224, 0.8214290742211036),
        "Molden Heath": (0.4214754896265884, 0.8004656792501905, 0.48309658007274153),
        "Geminate": (0.7752785754225981, 0.6050009975415483, 0.4868245117678026),
        "Heimatar": (0.9702998740042404, 0.6061199460861807, 0.9992857169191575),
        "Impass": (0.9807017248383234, 0.9132586989555355, 0.4216132325279633),
        "Sinq Laison": (0.5843989791616034, 0.7485515626357253, 0.8350943827367436),
        "The Citadel": (0.9592992559218088, 0.5239257329348376, 0.458044944243143),
        "The Kalevala Expanse": (0.6721434133897867, 0.41333607792542526, 0.7581319986979818),
        "Deklein": (0.42170894907663337, 0.5300447309243096, 0.46739050735550036),
        "Devoid": (0.6961420293769736, 0.7989672847427323, 0.9986653577611337),
        "Everyshore": (0.8347244445280153, 0.668591180588647, 0.67643100044854),
        "The Bleak Lands": (0.6964001338114806, 0.9896659093849387, 0.737911679312917),
        "Esoteria": (0.4917605179542084, 0.9983484672682224, 0.624897707334829),
        "Oasa": (0.7715339066074992, 0.820606959996087, 0.7119215491995229),
        "Syndicate": (0.5638350433604276, 0.682266643003428, 0.6266529692680732),
        "Metropolis": (0.4147271147541653, 0.831771071883869, 0.8227453143763478),
        "Domain": (0.4120105860929768, 0.9808111075513355, 0.9949306694642741),
        "Solitude": (0.41756455003113574, 0.6221849011641428, 0.9655287849974448),
        "Tenal": (0.7913523434752807, 0.5709259780648748, 0.996385187709911),
        "Fade": (0.9979123551812061, 0.41494832835505735, 0.6556739052760551),
        "Providence": (0.8176138062089986, 0.41356410985497755, 0.991969669978996),
        "Placid": (0.585802110914635, 0.545912303827951, 0.5486288991034238),
        "Khanid": (0.9599450255113282, 0.705407688448263, 0.8015781292683862),
        "Querious": (0.55823214765146, 0.5708274298680278, 0.8041543578776205),
        "Cloud Ring": (0.9975169635050004, 0.9888827849343729, 0.7245497660453142),
        "Kador": (0.4150349425570906, 0.7896491827370581, 0.6544643691325477),
        "Cobalt Edge": (0.7736430585322213, 0.4305347792547112, 0.4134848921014199),
        "Aridia": (0.8686794262379874, 0.9090685992813234, 0.9996511172704999),
        "Branch": (0.5371724449775668, 0.8886912464736093, 0.953607203192308),
        "Feythabolis": (0.8228330836988166, 0.873358318739657, 0.41376115884264697),
        "Outer Ring": (0.4131183293226239, 0.6480979341461284, 0.5295639579472047),
        "Fountain": (0.5975057991828773, 0.8218245166988295, 0.4682121327620664),
        "Paragon Soul": (0.6773679516171555, 0.41399687142489333, 0.5493433060944453),
        "Delve": (0.9964222845199288, 0.6892298654226676, 0.597193342947248),
        "Tenerifis": (0.44952708881894443, 0.5655472691343425, 0.6369084039010298),
        "Omist": (0.6516889902850324, 0.8692219047471154, 0.8229412599759731),
        "Period Basis": (0.8707248135677751, 0.5506694392373365, 0.6026350092014127),
        "Essence": (0.6813715024677167, 0.643111608167827, 0.8600363248683316),
        "Kor-Azor": (0.9847778531571607, 0.8900188415031344, 0.8877722535461938),
        "Perrigen Falls": (0.8680577269274542, 0.9987541091873718, 0.41720933676063215),
        "Genesis": (0.6518489092009581, 0.9799857113127257, 0.5843808431442946),
        "Verge Vendor": (0.9992006981429616, 0.5151775541910333, 0.8238220710863791),
        "Black Rise": (0.8909484193651795, 0.7873515542656676, 0.5508922487618134),
        "Pochven": (0.44718224176731974, 0.7263963542188588, 0.8877678824649161),
        "A-R00001": (0.7808240640483303, 0.8307500415224941, 0.8717278277919476),
        "A-R00002": (0.7118071363323519, 0.5049649659759478, 0.8681356101996854),
        "A-R00003": (0.43671966195751905, 0.4122366307887418, 0.45932800783234096),
        "B-R00004": (0.6999518902552982, 0.7082134580424925, 0.6875692861208834),
        "B-R00005": (0.4248973573016437, 0.9004815491456243, 0.5967241734436551),
        "B-R00006": (0.4876804269744168, 0.49868861617058063, 0.9906874237462372),
        "B-R00007": (0.5571796939605541, 0.41493854319364604, 0.8443807374744318),
        "B-R00008": (0.9205687840354198, 0.41436186717021917, 0.43079239269533753),
        "C-R00009": (0.8587962822145222, 0.7908902049236864, 0.9952918578245465),
        "C-R00010": (0.8066985230237106, 0.4160944273005968, 0.728024564311568),
        "C-R00011": (0.9754702558496889, 0.9574823194444938, 0.5715108248607693),
        "C-R00012": (0.5565576391133702, 0.769513004056877, 0.9957280704169986),
        "C-R00013": (0.8896916936430629, 0.6163392052229184, 0.8716917002629863),
        "C-R00014": (0.7279008936741729, 0.8892713081724621, 0.5434813037226279),
        "C-R00015": (0.5847270454476954, 0.9625678756378653, 0.8299362616849023),
        "D-R00016": (0.6868412008880957, 0.6818225696386505, 0.5167353655299503),
        "D-R00017": (0.7296441248127702, 0.5258389419993668, 0.5671214540621584),
        "D-R00018": (0.6431169628082446, 0.5685388188446665, 0.42116718332764236),
        "D-R00019": (0.5423055922290999, 0.9187304003315693, 0.4994716652587623),
        "D-R00020": (0.9961612499596957, 0.8049017982647326, 0.4646001527832085),
        "D-R00021": (0.9179592264385316, 0.4858996506366809, 0.7084345300482546),
        "D-R00022": (0.8057565146203121, 0.5825119760635348, 0.7666739350518668),
        "D-R00023": (0.9008431639744334, 0.5030524200186134, 0.9730444538223334),
        "E-R00024": (0.6145455912343527, 0.4805003852758415, 0.6653686566083713),
        "E-R00025": (0.8269184190560956, 0.7065052126266933, 0.43223058778835),
        "E-R00026": (0.930665625354577, 0.6204958968567232, 0.5161627529808592),
        "E-R00027": (0.8938364395222003, 0.6939774779386653, 0.9855114263387628),
        "E-R00028": (0.614702209028402, 0.531640428372678, 0.9610289491992149),
        "E-R00029": (0.5338410573186094, 0.7830824497018944, 0.5706193737620928),
        "F-R00030": (0.8957074798155829, 0.8955565267285522, 0.6855956841684792),
        "G-R00031": (0.9431095057380954, 0.42142438251480646, 0.8503180469295424),
        "H-R00032": (0.4665307427909623, 0.74628760030459, 0.7614375303831892),
        "K-R00033": (0.7551363658575995, 0.6813526669169909, 0.9990168746202247),
        "ADR01": (0.9164248608120401, 0.8143295070251944, 0.8206500857323475),
        "ADR02": (0.5124121045962653, 0.7620608396471481, 0.415856416701373),
        "ADR03": (0.7039826708372839, 0.7546856316101695, 0.8656969501511911),
        "ADR04": (0.49520010374036844, 0.49105787847873555, 0.7554560883137199),
        "ADR05": (0.8300103047143625, 0.5050755918605613, 0.4871270906826873),
        "VR-01": (0.8489882821768713, 0.9924714085087198, 0.9271418934596984),
        "VR-02": (0.4333228465879262, 0.6887384204753956, 0.6421689007122676),
        "VR-03": (0.5163803632257226, 0.8898775916193946, 0.7765425096111288),
        "VR-04": (0.5227371299235167, 0.9862496317035543, 0.9376479366349941),
        "VR-05": (0.6921158808309297, 0.9034479442452703, 0.6839433872219896),
    }

    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Region_Name}: {system.Name}"

    @classmethod
    def node_coloring(cls, system: System):

        return cls._output_hex(cls.color_map.get(system.Region_Name, system.Region_Id))

    @classmethod
    def connection_grouping(cls, system: System):
        return system.GetRegion().Name


class SecurityFormatting(iDisplayFormatting):
    Name = "Security"
    color_map = {
        "HighSec": distinctipy.get_hex("forestgreen"),
        "LowSec": distinctipy.get_hex("darkorange"),
        "Nullsec": distinctipy.get_hex("firebrick"),
    }

    @classmethod
    def node_naming(cls, system: System):
        return f"{system.Name}: {system.Security_Status}"

    @classmethod
    def node_coloring(cls, system: System):
        if system.Security_Status >= 0.5:
            return "forestgreen"
        if system.Security_Status > 0:
            return "darkorange"
        if system.Security_Status <= 0:
            return "firebrick"


class WormholeClassFormatting(iDisplayFormatting):
    Name = "WH Class"
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
    Name = "WH Statics"
    color_map = {
        "Class: (c3) - Static ls/ns": (0.9857089871374185, 0.9955241587011132, 0.8530747827446243),
        "Class: (c2) - Static c4/hs/ns": (0.531516870774841, 0.6899402430638255, 0.41763575492859867),
        "Class: (c5) - Static c1": (0.976074100642694, 0.6646725253074323, 0.5207918800625223),
        "Class: (c4) - Static c3/c5/ns": (0.49205618764447806, 0.7122013060520427, 0.9681307644389184),
        "Class: (c5) - Static c3": (0.754044943400107, 0.9821265010787955, 0.4742774401356272),
        "Class: (c2) - Static c4/hs": (0.5552219204499699, 0.4894965573629999, 0.7007614452391042),
        "Class: (c5) - Static c5/ns": (0.7798610254671359, 0.4223446885562439, 0.42878974243023105),
        "Class: (c4) - Static c2/c5": (0.7818325844217144, 0.7820929056240077, 0.789383033875905),
        "Class: (drifter) - Static c2": (0.41866458444850324, 0.994245961591074, 0.4879919584728313),
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
        "Class: (drifter) - Static c2": (0.9918473625255263, 0.752031287347655, 0.7358151318820663),
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
        "Class: (drifter) - Static c2": (0.7198983175321225, 0.9137205375994726, 0.8717425499886339),
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
        "Class: (drifter) - Static c2": (0.873024965177236, 0.9410409726417119, 0.5528192066704775),
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
        "Class: (drifter) - Static c2": (0.6446279947912195, 0.8058122831530198, 0.8025864339721883),
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
    Name = "WH Weather"
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
    def marker(cls, weights: list, three_dimension: bool, size: int = 13):
        if three_dimension:
            return go.scatter3d.Marker(
                size=size - 3,
                symbol="diamond",
                autocolorscale=False,
                color=weights,
                line=go.scatter3d.marker.Line(width=2, color="black"),
            )
        else:

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
