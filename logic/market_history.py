from dataclasses import fields
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from alive_progress import alive_bar
from dateutil.tz import tzutc
from pandas import concat, DataFrame, merge, Series

from models.market.orders import MarketOrder, OrderHistoryEntry


def OrderHistoryEntry_Factory(existing_order: Optional[Series], new_order: Optional[Series], timestamp: Optional[int]):
    """
    compares an existing order to a new order. Returns an OrderHistoryEntry. Timestamp is for historical orders being updated.

    returns None if there is no change
    """

    if timestamp is None:
        timestamp = datetime.timestamp(datetime.now(tz=tzutc()))

    ## If there is no existing order then its a new one, and we generate a New Order history entry
    if existing_order is None:
        return OrderHistoryEntry(
            create_dataclass(new_order, MarketOrder), timestamp, new_order=True, volume_change=new_order.volume_total
        )

    ## If there is no new order then either it was all sold/bought or it expired
    if new_order is None:
        existing_expiration = existing_order.issued + timedelta(days=existing_order.duration)
        existing_expiration = existing_expiration.tz_localize(tz=tzutc())
        # given updates are every 30 mins or so, going to assume its expired if the expiration date + the duration has passed.
        expired = existing_expiration < datetime.fromtimestamp(timestamp, tz=tzutc())

        # negative volume change if it was sold.
        amount_changed = -existing_order.volume_remaining if not expired else 0
        return OrderHistoryEntry(
            create_dataclass(existing_order, MarketOrder), timestamp, expired=expired, volume_change=amount_changed
        )

    if existing_order.item() == new_order.item():
        return None

    differences = set(new_order.asdict().items()) - set(existing_order.asdict().items())

    volume_change = differences.get("volume_remaining", None)
    price_change = differences.get("price", None)

    return OrderHistoryEntry(
        create_dataclass(existing_order, MarketOrder), timestamp, volume_change=volume_change, price_change=price_change
    )


def compare_snapshots(existing_orders: DataFrame, latest_orders: DataFrame, snapshot: int, timestamp=None):

    existing_orders.set_index("order_id")
    latest_orders.set_index("order_id")

    with alive_bar(len(latest_orders.index), title_length=47) as bar:
        bar.title(f"Compare {snapshot} from {datetime.fromtimestamp(timestamp, tz=tzutc())}")
        checked_orders = latest_orders.apply(
            process_new_snapshot_row, args=(existing_orders, timestamp), axis=1, progress_bar=bar
        )

    new_orders = get_all_new_orders(existing_orders, latest_orders)

    un_checked_orders = get_unchecked_orders(existing_orders, checked_orders)

    if len(un_checked_orders.index) > 0:
        with alive_bar(len(un_checked_orders.index), title_length=47) as bar2:
            bar.title(f"Process {snapshot-1} for expired or completed")
            done_history = un_checked_orders.apply(
                process_new_snapshot_row, args=(existing_orders, timestamp), axis=1, reverse=True, progress_bar=bar2
            )

        all_history = concat([checked_orders, done_history]).drop_duplicates()
        return all_history

    return new_orders, checked_orders


def get_unchecked_orders(existing_orders, checked_orders):
    """
    takes a dataframe of existing_orders and the ones that have already been checked for updates,
    merges and pulls out only those that exist in existing_orders for processing of completed/expired
    """
    checked_orders.columns = OrderHistoryEntry.__annotations__.keys()
    un_checked_orders = merge(checked_orders, existing_orders, on="order_id", indicator=True, how="right")
    un_checked_orders = un_checked_orders.loc[un_checked_orders["_merge"] == "right_only"]
    return un_checked_orders


def get_all_new_orders(existing_orders, latest_orders):
    """
    merges existing orders with latest orders, on a one sided merge, pulls out all that did not exist in existing_orders,
    cleans up the columns and returns a dataframe
    """
    order_difference = merge(latest_orders, existing_orders, on="order_id", indicator=True, how="left")
    orders_merged = order_difference.loc[order_difference["_merge"] == "left_only"]
    paired_to_just_left = orders_merged.dropna(axis=1, how="all")
    new_orders = paired_to_just_left.drop("_merge", axis=1)
    new_orders.columns = MarketOrder.__annotations__.keys()
    return new_orders


def process_new_snapshot_row(
    row: Series, existing: DataFrame, timestamp: float, reverse: bool = False, progress_bar=None
) -> OrderHistoryEntry:
    """
    pandas.df apply functionality. takes a single series and adds to it the update_log (an OrderHistoryEntry obj) and checked flags on a secondary dataframe.

    param:
    : row[pandas.Series] - a single row from a dataframe
    : existing[pandas.DataFrame] - a dataframe of already known orders
    : timestamp[float] - a unix epoch timestamp of when the row was recorded
    : reverse[boolean](Optional: Default=false) - flips the order of passing into OrderHistoryEntryFactory for discovering expired/sold out orders
    : progress_bar[alive_progress context bar] - an alive progress context bar for updating the progress bar.
    """
    if row["duration"] > 90:
        return None, None

    existing_order = existing.get(row["order_id"], None) if existing is not None else None
    row["new_order"] = existing_order is None
    if not reverse:
        update_item = OrderHistoryEntry_Factory(existing_order, row, timestamp)
    else:
        update_item = OrderHistoryEntry_Factory(row, None, timestamp)

    # Update the Alive-Progress bar
    if progress_bar:
        progress_bar()

    return Series(update_item.as_dict(), index=OrderHistoryEntry.__annotations__.keys())


def create_dataclass(data: Series, factory: Any) -> Any:
    return factory(**{f.name: data[f.name] for f in fields(factory)})
