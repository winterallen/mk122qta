from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Literal

Side = Literal["BUY", "SELL"]


class BrokerOrderStatus(StrEnum):
    ACCEPTED = "accepted"
    FILLED = "filled"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class BrokerOrderRequest:
    order_id: str
    account_id: str
    ts_code: str
    side: Side
    quantity: int
    limit_price: Decimal


@dataclass(frozen=True, slots=True)
class BrokerOrderAck:
    order_id: str
    broker_order_id: str
    status: BrokerOrderStatus
    message: str


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    account_id: str
    order_count: int
    unmatched_count: int
    cash_diff: Decimal

    @property
    def passed(self) -> bool:
        return self.unmatched_count == 0 and self.cash_diff == Decimal("0")


class PaperBrokerAdapter:
    def __init__(self) -> None:
        self._orders: dict[str, BrokerOrderRequest] = {}

    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderAck:
        if request.quantity <= 0:
            return BrokerOrderAck(
                order_id=request.order_id,
                broker_order_id="",
                status=BrokerOrderStatus.REJECTED,
                message="non_positive_quantity",
            )
        broker_order_id = f"paper:{request.account_id}:{request.order_id}"
        self._orders[request.order_id] = request
        return BrokerOrderAck(
            order_id=request.order_id,
            broker_order_id=broker_order_id,
            status=BrokerOrderStatus.FILLED,
            message="filled",
        )

    def query_order(self, order_id: str) -> BrokerOrderAck:
        request = self._orders[order_id]
        return BrokerOrderAck(
            order_id=order_id,
            broker_order_id=f"paper:{request.account_id}:{order_id}",
            status=BrokerOrderStatus.FILLED,
            message="filled",
        )

    def reconcile(self, account_id: str) -> ReconciliationResult:
        order_count = sum(1 for order in self._orders.values() if order.account_id == account_id)
        return ReconciliationResult(
            account_id=account_id,
            order_count=order_count,
            unmatched_count=0,
            cash_diff=Decimal("0"),
        )
