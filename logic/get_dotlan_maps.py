import os
from io import BytesIO
from pickle import dump, load
from typing import Dict, Tuple

import requests
from bs4 import BeautifulSoup, ResultSet

from models.common import Position, Universe
from models.third_party.dotlan import *

REGION_X_OFFSET = 1000
REGION_Y_OFFSET = 1000
BASE_URL = "https://evemaps.dotlan.net/svg/"

REGION_NAMES = [
    "Aridia.svg",
    "Black_Rise.svg",
    "The_Bleak_Lands.svg",
    "Branch.svg",
    "Cache.svg",
    "Catch.svg",
    "The_Citadel.svg",
    "Cloud_Ring.svg",
    "Cobalt_Edge.svg",
    "Curse.svg",
    "Deklein.svg",
    "Delve.svg",
    "Derelik.svg",
    "Detorid.svg",
    "Devoid.svg",
    "Domain.svg",
    "Esoteria.svg",
    "Essence.svg",
    "Etherium_Reach.svg",
    "Everyshore.svg",
    "Fade.svg",
    "Feythabolis.svg",
    "The_Forge.svg",
    "Fountain.svg",
    "Geminate.svg",
    "Genesis.svg",
    "Great_Wildlands.svg",
    "Heimatar.svg",
    "Immensea.svg",
    "Impass.svg",
    "Insmother.svg",
    "Kador.svg",
    "The_Kalevala_Expanse.svg",
    "Khanid.svg",
    "Kor-Azor.svg",
    "Lonetrek.svg",
    "Malpais.svg",
    "Metropolis.svg",
    "Molden_Heath.svg",
    "Oasa.svg",
    "Omist.svg",
    "Outer_Passage.svg",
    "Outer_Ring.svg",
    "Paragon_Soul.svg",
    "Period_Basis.svg",
    "Perrigen_Falls.svg",
    "Placid.svg",
    "Providence.svg",
    "Pure_Blind.svg",
    "Querious.svg",
    "Scalding_Pass.svg",
    "Sinq_Laison.svg",
    "Solitude.svg",
    "The_Spire.svg",
    "Stain.svg",
    "Syndicate.svg",
    "Tash-Murkon.svg",
    "Tenal.svg",
    "Tenerifis.svg",
    "Tribute.svg",
    "Vale_of_the_Silent.svg",
    "Venal.svg",
    "Verge_Vendor.svg",
    "Wicked_Creek.svg",
    "Pochven.svg",
    "UUA-F4.svg",
    "J7HZ-F.svg",
    "A821-A.svg",
]


def get_map(name: str):
    map_url = f"{BASE_URL}{name}"
    response = requests.get(map_url)

    return BytesIO(response.content)


def get_region_map():
    return get_map("New_Eden.svg")


def build_region_central_coordinates():
    xml_root = BeautifulSoup(get_map("New_Eden.svg"), features="xml")

    return {
        region.name: region
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
    map_svg: BytesIO, all_data_client: "AllData", region_name: str, region_data: Dict[str, DotlanSystem]
) -> dict:
    """
    parse the xml representation of a dotlan map svg to pull out coordinate data for each system
    """
    xml_root = BeautifulSoup(map_svg, features="xml")
    region_name = region_name.replace(".svg", "")
    center_x, center_y = find_map_center(xml_root)
    region_x, region_y = determine_region_relative_position(region_name, region_data)

    region_offset = DotlanRegionOffset(center_x, center_y, region_x, region_y)

    systems = {
        system.sys_id: system
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

    x, y = offset_around_region(node, region_offset)

    if is_region_map or (region is None or region.text == expected_region):
        return DotlanSystem(
            sys_id=sys_id,
            name=region.text if is_region_map else all_data_client.GetSystem(sys_id).Name,
            Position=Position(X=x, Y=y, Z=0, Universe=Universe.EDEN),
            has_ice=ice is not None,
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


def get_all_dotlan_data(client: "AllData", build_data=True, progress_bar=None):
    """
    download all the svgs for each region from dotlan and extract system_ids, system x-y coords, and connection data

    if build_data=True will re-download and re-pickled
    """
    pickle_file_name = "data/pickled_dotlan_maps"

    data = {}
    pickled_file_exists = os.path.exists(pickle_file_name)
    region_data = None
    for region in REGION_NAMES:
        if progress_bar is not None:
            progress_bar.title(f"Loading {region} from Dotlan")

        if not build_data and pickled_file_exists and len(data) <= 0:
            with open(pickle_file_name, "rb") as pickleFile:
                data = load(pickleFile)

        if build_data or not pickled_file_exists:
            if region_data is None:
                region_data = build_region_central_coordinates()

            content = get_map(region)
            data[region] = parse_map(content, client, region, region_data)

        attach_dotlan_data(client, data[region])

        if progress_bar is not None:
            progress_bar()

    with open(pickle_file_name, "wb") as pickleFile:
        print(f"Pickling dotlan map data")
        dump(data, pickleFile)
