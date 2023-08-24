import re
from time import sleep

import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from logic.common import try_parse
from models.third_party.dotlan import DotlanAdditionalSystemData, DotlanAgent, DotlanStation


def parse_extra_dotlan_data(system_name: str, system_id: int):
    """
    primary function to scrape extra Dotlan data from the dotlan/system/name page for a given system.

    try to call it sparingly. Data should be cached.
    """
    scrape = _scrape_page(system_name, "")
    stations = _get_subpage_data(system_name, "", "Services", image_indicator="tlogo", _page=scrape)
    system_data = _get_subpage_data(
        system_name, "", "Belts/Icebelts", unique_element_tag="td", _page=scrape, drop_header=False
    )

    SystemData = DotlanAdditionalSystemDataFactory(system_data)

    SystemData.Stations = DotlanStationFactory(stations, system_id)
    SystemData.Agents = DotlanAgentFactory(system_name, system_id)

    return SystemData


def DotlanAgentFactory(system_name: str, sys_id: int):
    """
    parses a list of data from dotlan/system/name/agents page and returns a list of DotlanAgents
    """
    agents = _get_subpage_data(system_name, "agents", "Division / Type / Research")
    parsed_agents = []
    current_station = "In Space"
    for agent in agents:
        if len(agent) == 1:
            # set station_name for next several rows
            current_station = agent[0]
            continue

        notes = agent[2]
        parsed_agents.append(
            DotlanAgent(
                Name=agent[0],
                Corporation=agent[1],
                Station=current_station,
                System_Id=try_parse(int, sys_id),
                Level=agent[3],
                Notes=notes if notes != "-" else None,
            )
        )

    return parsed_agents


def DotlanStationFactory(stations: list, system_id: int):
    """
    parses the table of Stations from dotlan/system/name page and returns a list of DotlanStation objects
    """
    parsed_stations = []
    for station in stations:

        parsed_stations.append(DotlanStation(*station, System_Id=try_parse(int, system_id)))

    return parsed_stations


def DotlanAdditionalSystemDataFactory(system_data: list):
    """
    Takes captured system data from the dotlan system/name page and returns a DotlanAdditionalSystemData obj
    """

    mapping = {"Planets": None, "Moons": None, "Belts/Icebelts": None, "Security Class": None, "Local Pirates": None}
    skip_col = False
    for row in system_data:
        for idx, col in enumerate(row):
            if skip_col:
                skip_col = False
                continue
            if col in mapping.keys():
                mapping[col] = row[idx + 1]
                skip_col = True

    return DotlanAdditionalSystemData(*[value for value in mapping.values()])


def _get_subpage_data(
    system_name: str,
    sub_page: str,
    unique_elment_value: str,
    unique_element_tag: str = "th",
    image_indicator: str = None,
    _page=None,
    drop_header: bool = True,
):
    """
    Scrapes a system/subpage off dotlan for tables, finds the correct table, and parses the rows into a list.
    """
    _page = _scrape_page(system_name, sub_page) if _page is None else _page

    _table = _find_correct_dotlan_table(_page, unique_elment_value, unique_element_tag)
    if _table is None:
        return []
    _data = _parse_table_into_list(_table, image_indicator)
    _rows = [datum for datum in _data if len(datum) > 0]

    return _rows[1:] if drop_header else _rows


def _scrape_page(system_name: str, subpage: str, backoff: int = 5, count: int = 1):
    """
    Get dotlan system/name/subpage data
    """
    base_url = f"https://evemaps.dotlan.net/system/{system_name}/"
    document = requests.get(f"{base_url}{subpage}")
    if document.status_code == 200:
        return BeautifulSoup(document.content, features="html.parser")
    else:
        if count > 4:
            raise Exception(f"Cannot scrape {system_name}/{subpage}")
        sleep(backoff)
        _scrape_page(system_name, subpage, backoff=backoff * 2, count=count + 1)


def _find_correct_dotlan_table(page: BeautifulSoup, unique_text: str, element_tag):
    """
    checks all elements of a given tag [element_tag] for text that would indicate its part of the table that is needed.
    Returns said table.
    """
    page_tables = page.findAll("table", **{"class": "tablelist"})
    for table in page_tables:
        table_elements = table.findAll(element_tag)
        for header in table_elements:
            if header.text == unique_text:
                return table


def _parse_table_into_list(table: ResultSet, image_indicator: str):
    """
    converts an html table into a set of rows of text for each cell, or potentially image link.
    """
    rows = table.findAll("tr")
    table_data = []
    for row in rows:
        cols = row.findAll(re.compile(r"(td|th)"))
        parsed_cols = [_parse_row_element(ele, image_indicator) for ele in cols]
        table_data.append(parsed_cols)
    return table_data


def _parse_row_element(element: Tag, image_indicator: str):
    """
    gets the text or the img src link out of an table element
    """
    if image_indicator is None or image_indicator.strip() == "":
        return element.text.strip()

    if image_indicator in str(element.attrs.values()):
        for child in element.findAll("img"):
            return child.attrs["src"]

    return element.text.strip()
