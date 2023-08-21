from datetime import datetime, timedelta
from typing import Dict, Optional

from dateutil.tz import tzutc
from pandas import DataFrame

from models.market.orders import MarketOrder, OrderHistoryEntry


def OrderHistoryEntry_Factory(
    existing_order: Optional[MarketOrder], new_order: Optional[MarketOrder], timestamp: Optional[int]
):
    """
    compares an existing order to a new order. Returns an OrderHistoryEntry. Timestamp is for historical orders being updated.

    returns None if there is no change
    """

    if timestamp is None:
        timestamp = datetime.timestamp(datetime.now(tz=tzutc()))

    ## If there is no existing order then its a new one, and we generate a New Order history entry
    if existing_order is None:
        return OrderHistoryEntry(new_order.order_id, timestamp, new_order=True, volume_change=new_order.volume_total)

    ## If there is no new order then either it was all sold/bought or it expired
    if new_order is None:
        existing_expiration = datetime.strptime(existing_order.issued) + timedelta(days=existing_order.duration)
        # given updates are every 30 mins or so, going to assume its expired if the expiration date + the duration has passed.
        expired = existing_expiration < datetime.now(tz=tzutc())

        # negative volume change if it was sold.
        amount_changed = -existing_order.remaining if not expired else 0
        return OrderHistoryEntry(existing_order.order_id, timestamp, expired=expired, volume_change=amount_changed)

    if existing_order.item() == new_order.item():
        return None

    differences = set(new_order.asdict().items()) - set(existing_order.asdict().items())

    volume_change = differences.get("remaining", None)
    price_change = differences.get("price", None)

    return OrderHistoryEntry(existing_order.order_id, timestamp, volume_change=volume_change, price_change=price_change)


def compare_snapshots(existing_orders: DataFrame, latest_orders: DataFrame, timestamp=None):

    order_updates = []
    new_orders = []

    for _, order in latest_orders.iterrows():
        if order.duration > 90:
            continue
        existing_order = existing_orders.get(order.order_id, None)
        if not existing_order:
            new_orders.append(order)
        update = OrderHistoryEntry_Factory(existing_order, order, timestamp)
        if update:
            order_updates.append(update)

        # remove order from existing orders as its already been checked
        if existing_order:
            existing_orders["checked"] = True

    # generate expiration or completion OrderHistoryEntries
    for order in existing_orders.loc[existing_orders["checked"] is True].iterrows():
        order_updates.append(OrderHistoryEntry_Factory(order, None, timestamp))

    new_orders_data = DataFrame(new_orders, columns=MarketOrder.__annotations__.values(), index="order_id")
    updates_data = DataFrame(order_updates, columns=OrderHistoryEntry.__annotations__.values(), index="order_id")

    return new_orders_data, updates_data
