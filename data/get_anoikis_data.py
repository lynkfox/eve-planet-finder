from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


def get_anokis_system_page():
    # anokis_system_page = requests.get("http://anoik.is/systems")
    with open("data/anokis_system_page.html") as file:
        return BeautifulSoup(file, "html.parser")


def get_bracket_group(html_tree):

    return html_tree.find_all("section", attrs={"class": "bracketgroup"})


def get_system_from_bracket(bracket_tree):
    return bracket_tree.find_all("div", attrs={"class": "system"})


def get_systems(html_tree):
    brackets = get_bracket_group(html_tree)
    return [get_system_from_bracket(entry) for entry in brackets]


@dataclass
class AnokisSystem:
    name: str
    wh_class: str
    statics: str
    weather: str


def AnokisFactory(system_tree):
    name = system_tree.find("a", attrs={"class": "system-link"}).text
    wh_class = system_tree.find("span", attrs={"class": "wormholeclass"}).text
    statics = system_tree.find("span", attrs={"class": "statics"}).text.replace(" ", "").replace("statics", "")
    weather_node = system_tree.find("span", attrs={"class": "effect"})
    weather = None if weather_node is None else weather_node.text

    return AnokisSystem(name, wh_class, statics, weather)


def GetAnokisData():
    html_data = get_anokis_system_page()
    systems = get_system_from_bracket(html_data)
    return [AnokisFactory(system) for system in systems]
