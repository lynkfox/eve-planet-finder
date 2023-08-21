from dataclasses import dataclass
from pickle import dump, load

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

    def __getstate__(self):
        return (self.name, self.wh_class, self.statics, self.weather)

    def __setstate__(self, state):
        self.name, self.wh_class, self.statics, self.weather = state


def AnokisFactory(system_tree):
    name = system_tree.find("a", attrs={"class": "system-link"}).text
    wh_class = system_tree.find("span", attrs={"class": "wormholeclass"}).text
    statics = (
        system_tree.find("span", attrs={"class": "statics"})
        .text.replace(" ", "")
        .replace("statics", "")
        .replace("static", "")
    )
    weather_node = system_tree.find("span", attrs={"class": "effect"})
    weather = None if weather_node is None else weather_node.text.replace(" ", "").replace("\n", "")

    return AnokisSystem(name, wh_class, statics, weather)


def GetAnokisData(pickle_data: bool):
    pickle_file_path = "data/pickled_anokis_systems"
    if not pickle_data:
        try:
            with open(pickle_file_path, "rb") as pickleFile:
                return load(pickleFile)
        except:
            print("Pickled Anokis System data not found - retrieving data")
            pickle_data = True
            pass

    html_data = get_anokis_system_page()
    systems = get_system_from_bracket(html_data)
    anokis_data = [AnokisFactory(system) for system in systems]

    if pickle_data:
        with open(pickle_file_path, "wb") as pickleFile:
            print(f"Pickling Anokis Systems data")
            dump(anokis_data, pickleFile)

    return anokis_data
