import os
from io import BytesIO
from pickle import dump, load
from time import sleep
from typing import Dict, Tuple

import requests
from bs4 import BeautifulSoup, ResultSet

from logic.common import ProgressBar
from logic.parse_dotlan_system_data import *
from models.common import Position, Universe
from models.third_party.dotlan import *

REGION_X_OFFSET = 1000
REGION_Y_OFFSET = 1000
BASE_URL = "https://evemaps.dotlan.net/svg/"

REGION_NAMES = [
    "Aridia",
    "Black_Rise",
    "The_Bleak_Lands",
    "Branch",
    "Cache",
    "Catch",
    "The_Citadel",
    "Cloud_Ring",
    "Cobalt_Edge",
    "Curse",
    "Deklein",
    "Delve",
    "Derelik",
    "Detorid",
    "Devoid",
    "Domain",
    "Esoteria",
    "Essence",
    "Etherium_Reach",
    "Everyshore",
    "Fade",
    "Feythabolis",
    "The_Forge",
    "Fountain",
    "Geminate",
    "Genesis",
    "Great_Wildlands",
    "Heimatar",
    "Immensea",
    "Impass",
    "Insmother",
    "Kador",
    "The_Kalevala_Expanse",
    "Khanid",
    "Kor-Azor",
    "Lonetrek",
    "Malpais",
    "Metropolis",
    "Molden_Heath",
    "Oasa",
    "Omist",
    "Outer_Passage",
    "Outer_Ring",
    "Paragon_Soul",
    "Period_Basis",
    "Perrigen_Falls",
    "Placid",
    "Providence",
    "Pure_Blind",
    "Querious",
    "Scalding_Pass",
    "Sinq_Laison",
    "Solitude",
    "The_Spire",
    "Stain",
    "Syndicate",
    "Tash-Murkon",
    "Tenal",
    "Tenerifis",
    "Tribute",
    "Vale_of_the_Silent",
    "Venal",
    "Verge_Vendor",
    "Wicked_Creek",
    "Pochven",
    "UUA-F4",
    "J7HZ-F",
    "A821-A",
]


def get_map(name: str, backoff: int = 5, count=1):
    map_url = f"{BASE_URL}{name}.svg"
    response = requests.get(map_url)
    if response.status_code == 200:
        return BytesIO(response.content)

    else:
        if count > 5:
            raise Exception(f"Cannot get {name} map")
        sleep(backoff)
        get_map(name, backoff=backoff * 2, count=count + 1)


def get_region_map():
    return get_map("New_Eden")


def build_region_central_coordinates():
    xml_root = BeautifulSoup(get_map("New_Eden"), features="xml")

    return {
        region.Name: region
        for region in [parse_system(None, xml_root, node, "", is_region_map=True) for node in xml_root.findAll("use")]
        if region is not None
    }


def determine_region_relative_position(region_name, region_data):
    dotlan_region_sys = region_data.get(region_name.replace("_", " "), None)
    if dotlan_region_sys is not None:
        position = dotlan_region_sys.Position
        return (position.X * REGION_X_OFFSET, position.Y * REGION_Y_OFFSET)


def find_map_center(xml_root: BeautifulSoup):
    all_coordinates = xml_root.findAll("use")

    max_x = 0
    max_y = 0
    for coord in all_coordinates:
        x = float(coord.get("x"))
        y = float(coord.get("y"))
        max_x = x if x > max_x else max_x
        max_y = y if y > max_y else max_y

    return (max_x / 2, max_y / 2)


def parse_map(
    map_svg: BytesIO,
    all_data_client: "AllData",
    region_name: str,
    region_data: Dict[str, DotlanSystem],
    force_active_dotlan_scrape: bool,
) -> dict:
    """
    parse the xml representation of a dotlan map svg to pull out coordinate data for each system
    """
    xml_root = BeautifulSoup(map_svg, features="xml")
    center_x, center_y = find_map_center(xml_root)
    region_x, region_y = determine_region_relative_position(region_name, region_data)

    region_offset = DotlanRegionOffset(center_x, center_y, region_x, region_y)

    systems = {
        system.System_Id: system
        for system in [
            parse_system(all_data_client, xml_root, node, region_name, region_offset=region_offset)
            for node in xml_root.findAll("use")
        ]
        if system is not None
    }
    connections = {
        connection.origin.sys_id: connection
        for connection in [parse_connections(node, region_offset=region_offset) for node in xml_root.findAll("line")]
    }

    return {"systems": systems, "connections": connections}


def load_dotlan_extra_data(region_name, force_active_dotlan_scrape, systems, progress_bar: ProgressBar):
    cache = {}
    region_extra_pickle = f"data/pickled_{region_name}_dotlan_extra"
    base_update_string = f"D-Scrape[{region_name}]"
    pickle_exists = os.path.exists(region_extra_pickle)
    if not force_active_dotlan_scrape:
        if pickle_exists:
            progress_bar.Update(f"{base_update_string}: Load Pickle")
            with open(region_extra_pickle, "rb") as pickleFile:
                cache = load(pickleFile)

    for system in systems.values():
        progress_bar.Update(f"{base_update_string}: {system.Name}")
        if system.System_Id not in cache.keys():
            cache[system.System_Id] = parse_extra_dotlan_data(system.Name, system.System_Id)

        system.More = cache[system.System_Id]

    if not pickle_exists or force_active_dotlan_scrape:
        progress_bar.Update(f"{base_update_string}: Pickling")
        with open(region_extra_pickle, "wb") as pickleFile:
            dump(cache, pickleFile)


def parse_connections(node: ResultSet, region_offset: DotlanRegionOffset) -> DotlanConnection:
    system_id = node.get("id")

    origin_x, origin_y = offset_around_region(node, region_offset, "x1", "y1")
    dest_x, dest_y = offset_around_region(node, region_offset, "x2", "y2")

    return DotlanConnection(
        connection_type=node.get("class"),
        origin=DotlanConnectionEndpoint(
            sys_id=int(system_id[11:19]), Position=Position(X=origin_x, Y=origin_y, Z=0, Universe=Universe.EDEN)
        ),
        destination=DotlanConnectionEndpoint(
            sys_id=int(system_id[2:10]), Position=Position(X=dest_x, Y=dest_y, Z=0, Universe=Universe.EDEN)
        ),
    )


def parse_system(
    all_data_client: "AllData",
    root_node: ResultSet,
    node: ResultSet,
    expected_region,
    is_region_map: bool = False,
    region_offset: DotlanRegionOffset = None,
):
    """
    pull out system data if the system is in the expected region (to prevent duplications)
    """

    sys_id = node.get("id")[3:]

    data_node = root_node.find(f"symbol", id=f"def{sys_id}")

    if is_region_map:
        region = data_node.find("text", **{"class": "ss"})
    else:
        region = data_node.find("text", **{"class": "er"})

    ice = data_node.find("text", id=f"ice{sys_id}")
    refining = data_node.find("polygon", **{"class": "v1"})
    cloning = data_node.find("polygon", **{"class": "v2"})
    industry = data_node.find("polygon", **{"class": "v3"})
    research = data_node.find("polygon", **{"class": "v4"})
    alliance = data_node.find("text", **{"class": "st"})
    link = data_node.find("a").get("xlink:href", "")

    x, y = offset_around_region(node, region_offset)

    if is_region_map or (region is None or region.text == expected_region):
        return DotlanSystem(
            System_Id=sys_id,
            Name=region.text if is_region_map else all_data_client.GetSystem(sys_id).Name,
            Position=Position(X=x, Y=y, Z=0, Universe=Universe.EDEN),
            faction=alliance.text if alliance is not None else "",
            has_ice=ice is not None,
            has_refinery=refining is not None,
            has_cloning=cloning is not None,
            has_industry=industry is not None,
            has_research=research is not None,
            dotlan_link=link,
        )

    return None


def offset_around_region(node, region_offset: DotlanRegionOffset, x_name: str = "x", y_name: str = "y"):
    original_x = float(node.get(x_name))
    original_y = float(node.get(y_name))

    if region_offset is not None:
        relative_x = region_offset.center_x - original_x
        relative_y = region_offset.center_y - original_y

        return region_offset.offset_x - (relative_x * (REGION_X_OFFSET / 10)), region_offset.offset_y - (
            relative_y * (REGION_Y_OFFSET / 10)
        )
    else:
        return original_x, original_y


def attach_dotlan_data(client: "AllData", region_data: dict):

    regions: Dict[int, DotlanSystem] = region_data["systems"]
    for sys_id, dotlan_system in regions.items():
        system = client.GetSystem(sys_id)
        system.Dotlan = dotlan_system

    connections: Dict[int, DotlanConnection] = region_data["connections"]
    for sys_id, connection in connections.items():
        system = client.GetSystem(sys_id)
        destination_id = connection.destination.sys_id

        origin_stargate = next(
            (
                stargate
                for stargate in system.GetStargates(cache=True)
                if stargate.DestinationSystem_Id == destination_id
            ),
            None,
        )
        origin_stargate.DotlanOrigin = connection.origin
        origin_stargate.DotlanDestination = connection.destination

        destination_system = system = client.GetSystem(destination_id)
        destination_stargate = next(
            (stargate for stargate in destination_system.GetStargates() if stargate.DestinationSystem_Id == sys_id),
            None,
        )
        destination_stargate.DotlanOrigin = connection.destination
        destination_stargate.DotlanDestination = connection.origin


def get_all_dotlan_data(
    client: "AllData", build_data=True, progress_bar: ProgressBar = None, force_dotlan_scrape: bool = False
):
    """
    download all the svgs for each region from dotlan and extract system_ids, system x-y coords, and connection data

    if build_data=True will re-download and re-pickled
    """
    progress_bar = ProgressBar(None) if progress_bar is None else progress_bar
    pickle_file_name = "data/pickled_dotlan_maps"

    data = {}
    pickled_file_exists = os.path.exists(pickle_file_name)
    region_data = None
    for region in REGION_NAMES:
        base_update_string = f"Dotlan[{region}]"
        progress_bar.Update(base_update_string)

        if not build_data and pickled_file_exists and len(data) <= 0:
            progress_bar.Update(f"{base_update_string}: Load Pickle")
            with open(pickle_file_name, "rb") as pickleFile:
                data = load(pickleFile)

        if build_data or not pickled_file_exists:
            if region_data is None:
                progress_bar.Update(f"{base_update_string}: Region Offset")
                region_data = build_region_central_coordinates()

            if data.get(region, None) is None:
                progress_bar.Update(f"{base_update_string}: Refresh data")
                content = get_map(region)
                data[region] = parse_map(content, client, region, region_data, force_dotlan_scrape)
                sleep(15)

            load_dotlan_extra_data(region, force_dotlan_scrape, data[region]["systems"], progress_bar)

        attach_dotlan_data(client, data[region])

        progress_bar.Advance()

    with open(pickle_file_name, "wb") as pickleFile:
        print(f"Pickling dotlan map data")
        dump(data, pickleFile)
