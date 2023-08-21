import codecs
import csv
import gzip
import json
import os
from io import BytesIO
from time import sleep
from typing import TextIO

import pandas
import requests
from dateutil.tz import tzutc

from logic.market_history import compare_snapshots
from models.market.orders import *


def load_fuzzworks_csv(file_name: str):
    """
    Loads a fuzzworks market history data into memory for parsing.
    """
    with open(file_name, "r") as file:
        reader = csv.reader(file, delimiter="\t")
        all_orders = [MarketOrder(*row) for row in reader]

    return all_orders


def parse_fuzzworks_csv(file_stream, cache=False, file_name=None):
    reader = csv.reader(codecs.iterdecode(file_stream, "utf-8"), delimiter="\t")

    if cache:
        with open(file_name, "w") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerows(reader)

    data = pandas.DataFrame(
        [MarketOrder(*row) for row in reader if len(row) > 0 and int(row[10]) < 100],
        columns=MarketOrder.__annotations__.keys(),
    )
    data.set_index("order_id")
    return data


def get_fuzzworks_zip(file_name: int):
    url = f"https://market.fuzzwork.co.uk/orderbooks/orderset-{file_name}.csv.gz"

    return gzip.open(BytesIO(requests.get(url).content))


def get_market_history(file_name):
    cached_file = f"./tmp/{file_name}.csv"
    if os.path.exists(cached_file):
        with open(cached_file, "rb") as f:
            return parse_fuzzworks_csv(f)

    fuzzworks_file = get_fuzzworks_zip(file_name)

    return parse_fuzzworks_csv(fuzzworks_file, cache=True, file_name=cached_file)


def get_historical_fuzzworks(starting=None):
    if not starting:
        latest = json.loads(requests.get("https://market.fuzzwork.co.uk/api/orderset").content)["orderset"]

    else:
        latest = starting

    thirty_days = int(latest) - 1440

    # sixty_days = thirty_days-1440

    # ninety_days = sixty_days-1440

    snapshot = thirty_days
    existing_history = None
    history_timestamp = None
    print(f"First snapshot to pull: {snapshot}")
    while snapshot < latest:
        print(f"Generating next snapshot dataframe {snapshot}")
        new_history = get_market_history(snapshot)

        if existing_history is not None:
            print(f"Comparing {snapshot}[new] to {snapshot-1}[previous]")
            history_timestamp = determine_fuzzworks_timestamp(snapshot, latest, history_timestamp)
            new_orders, updates = compare_snapshots(existing_history, new_history, history_timestamp)

            new_orders.to_sql()
            updates.to_sql()

        else:
            new_history.to_sql()

        existing_history = new_history.copy(deep=True)
        snapshot += 1


def determine_fuzzworks_timestamp(snapshot_number, latest_snapshot, previous_timestamp):

    if not previous_timestamp:
        now = datetime.now()
        rounded = now - (now - datetime.min) % timedelta(minutes=30)

        difference = (latest_snapshot - snapshot_number) * 30
        time_of_snapshot = rounded - timedelta(minutes=difference)
        time_of_snapshot.astimezone(tz=tzutc())
        return time_of_snapshot.timestamp()
    else:
        return previous_timestamp + 1800
