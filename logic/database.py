import json
from typing import Dict

import MySQLdb

from models.market.orders import MarketOrder


def SqlClientFactory(config_file="env_config.json"):
    with open(config_file, "r") as file:
        settings = json.load(file)

    client_settings = settings["sql"]

    return MySQLdb.connect(
        host=client_settings["host"],
        user=client_settings["user"],
        passwd=client_settings["password"],
        db=client_settings["database"],
    )


def BatchInsertOrders(db_client, snapshot: Dict[str, MarketOrder]):

    cursor = db_client.cursor()

    query = ""
