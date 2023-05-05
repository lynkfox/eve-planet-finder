from __future__ import annotations

# Types
# 11 - Temperate
# 12 - Ice
# 13 - Gas
# 2014 - Oceanic
# 2015 - Lava
# 2016 - Barren
# 2017 - Storm
# 2063 - Plasma

RAW_RESOURCE_TO_TYPE = {
    "2268": [2016, 13,12, 2014,11, 2017],
    "2305": [11],
    "2267": [2016, 13,2015, 2063, 2017],
    "2288": [2016, 2014, 11],
    "2287": [2014, 11],
    "2307": [2015],
    "2272": [12, 2015, 2063],
    "2309": [13, 2017],
    "2073": [2016, 12, 2014, 11],
    "2310": [13,12, 2017],
    "2270": [2016, 2063],
    "2306":[2015, 2063],
    "2286": [12, 2014],
    "2311": [13],
    "2308":[2015, 2063, 2017]
}

RawResources =[
    {"nameID":{"en":"Aqueous Liquids"}, "types": { "2268": {"isInput": False}}},
    {"nameID":{"en":"Autotrophs"}, "types": { "2305": {"isInput": False}}},
    {"nameID":{"en":"Base Metals"}, "types": { "2267": {"isInput": False}}},
    {"nameID":{"en":"Carbon Compounds"}, "types": { "2288": {"isInput": False}}},
    {"nameID":{"en":"Complex Organisms"}, "types": {"2287": {"isInput": False}}},
    {"nameID":{"en":"Felsic Magma"}, "types": { "2307": {"isInput": False}}},
    {"nameID":{"en":"Heavy Metals"}, "types": { "2272": {"isInput": False}}},
    {"nameID":{"en":"Micro-Organisms"}, "types": { "2073": {"isInput": False}}},
    {"nameID":{"en":"Ionic Solutions"}, "types": { "2309": {"isInput": False}}},
    {"nameID":{"en":"Noble Gas"}, "types": { "2310": {"isInput": False}}},
    {"nameID":{"en":"Noble Metals"}, "types": { "2270": {"isInput": False}}},
    {"nameID":{"en":"Non-CS Crystals"}, "types": { "2306": {"isInput": False}}},
    {"nameID":{"en":"Planktic Colonies"}, "types": { "2286": {"isInput": False}}},
    {"nameID":{"en":"Reactive Gas"}, "types": { "2311": {"isInput": False}}},
    {"nameID":{"en":"Suspended Plasma"}, "types": { "2308": {"isInput": False}}},
]

