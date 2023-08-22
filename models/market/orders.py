from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from pandas import DataFrame
from pydantic.dataclasses import dataclass as pydanticDataclass


@pydanticDataclass(unsafe_hash=True)
class MarketOrder:
    """
    A Singular order at a given point in time. May already exist in storage. If the data pulled is newer
    than the order in storage, update the order in storage.
    """

    order_id: int = field(init=True, compare=True)
    type_id: int = field(init=True)
    issued: datetime = field(init=True, compare=True)
    is_buy_order: bool = field(init=True)
    volume_remaining: int = field(init=True, compare=True)
    volume_total: int = field(init=True, compare=True)
    min_volume: int = field(init=True, compare=True)
    price: float = field(init=True, compare=True)
    location_id: int = field(init=True, compare=True)
    range: str = field(init=True, compare=True)
    duration: int = field(init=True, compare=True)
    region: int = field(init=True)
    system_id: int = field(init=True)


@pydanticDataclass(unsafe_hash=True)
class OrderHistoryEntry:
    """
    A Record of changes to a given order. Every time an order is retrieved, if it is different from the known value
    then an OrderHistory Entry should be created to track what is different.
    """

    order_id: int = field(init=False, default=0)
    original_order: MarketOrder = field(init=True)
    date_changed: datetime = field(init=True)
    volume_change: Optional[int] = field(kw_only=True, default=0)
    expired: Optional[bool] = field(kw_only=True, default=None)
    new_order: Optional[bool] = field(kw_only=True, default=None)
    price_change: Optional[int] = field(kw_only=True, default=None)

    def __post_init__(self):
        self.order_id = self.original_order.order_id

    def as_dict(self):
        return {
            "order_id": self.order_id,
            "original_order": self.original_order,
            "date_changed": self.date_changed,
            "volume_change": self.volume_change,
            "expired": self.expired,
            "new_order": self.new_order,
            "price_change": self.price_change,
        }


@dataclass
class SystemItemHistory:
    """
    A collection of information for a single item in a single system.

    Used to create the heat map values on the map
    """

    type_id: int = field(init=True)
    system_id: int = field(init=True)
    item_history: DataFrame = field(init=False, default_factory=DataFrame)
    item_snapshots: DataFrame = field(init=False, default_factory=DataFrame)
    display_tick: int = field(init=False, default=6)  # hours

    def _number_of_snapshots_per_tick(self):
        snapshot_length = self.item_snapshots[0].snapshot_length  # in minutes
        self.snapshots_per_tick = (self.display_tick * 60) / snapshot_length

    def _create_tick(self, starting_idx=0, next_idx=1):

        snapshots_in_tick = self.item_snapshots[self.item_snapshots.isin(range(starting_idx, next_idx))]

        tick = SystemItemHistoryTick(
            self.type_id,
            self.system_id,
            snapshots_in_tick[0].snapshot_start,
            snapshots_in_tick[-1].snapshot_start + timedelta(minutes=snapshots_in_tick[-1].snapshot_length),
            self.display_tick,
        )
        tick.items_sold_through_sell_orders = snapshots_in_tick["items_sold_through_sell_orders"].sum()
        tick.items_sold_through_buy_orders = snapshots_in_tick["items_sold_through_buy_orders"].sum()
        tick.average_buy_price = snapshots_in_tick["average_buy_price"].mean()
        tick.average_sell_price = snapshots_in_tick["average_sell_price"].mean()
        tick.median_buy_price = snapshots_in_tick["median_buy_price"].median()
        tick.median_sell_price = snapshots_in_tick["median_sell_price"].median()
        tick.sell_orders_filled = snapshots_in_tick["sell_orders_filled"].sum()
        tick.buy_orders_filled = snapshots_in_tick["buy_orders_filled"].sum()
        tick.sell_orders_expired = snapshots_in_tick["sell_orders_expired"].sum()
        tick.buy_orders_expired = snapshots_in_tick["buy_orders_expired"].sum()

        return tick


@dataclass
class SystemItemHistorySnapshot:
    """
    A single small snapshot of time, in minutes - like 15 or 30 - and the changes that occurred over that time
    """

    type_id: int = field(init=True)
    system_id: int = field(init=True)
    snapshot_start: datetime = field(init=True)
    snapshot_length: int = field(init=False)  # minutes
    # below all represent item values over the snapshot_length starting at snapshot_start
    # so length of 15 starting at 00:00, this many items sold for this average price between 00:00 and 00:15
    average_sell_price: float = field(init=False)
    median_sell_price: float = field(init=False)
    average_buy_price: float = field(init=False)
    median_buy_price: float = field(init=False)
    items_sold_through_sell_orders: int = field(init=False)
    items_sold_through_buy_orders: int = field(init=False)
    sell_orders_filled: int = field(init=False)
    buy_orders_filled: int = field(init=False)
    sell_orders_expired: int = field(init=False)
    buy_orders_expired: int = field(init=False)


@dataclass
class SystemItemHistoryTick:
    """
    A Map display tick, that consists of collated data from several snapshots.
    """

    type_id: int = field(init=True)
    system_id: int = field(init=True)
    tick_start_time: datetime = field(init=True)
    tick_end_time: datetime = field(init=True)
    tick_length: int = field(init=True)
    average_sell_price: float = field(init=False)
    median_sell_price: float = field(init=False)
    average_buy_price: float = field(init=False)
    median_buy_price: float = field(init=False)
    sell_orders_filled: int = field(init=False)
    buy_orders_filled: int = field(init=False)
    items_sold_through_sell_orders: int = field(init=False)
    items_sold_through_buy_orders: int = field(init=False)
    sell_orders_expired: int = field(init=False)
    buy_orders_expired: int = field(init=False)
