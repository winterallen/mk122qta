from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from typing import Literal

from mk_data.schemas import DailyBar
from mk_strategies import TargetWeight

Side = Literal["BUY", "SELL"]
ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class ExecutionOrder:
    order_id: str
    strategy_id: str
    ts_code: str
    trade_date: str
    side: Side
    quantity: int
    reference_price: Decimal

    @property
    def notional(self) -> Decimal:
        return self.reference_price * Decimal(self.quantity)


@dataclass(frozen=True, slots=True)
class ExecutionFill:
    fill_id: str
    order_id: str
    strategy_id: str
    ts_code: str
    trade_date: str
    side: Side
    quantity: int
    price: Decimal

    @property
    def notional(self) -> Decimal:
        return self.price * Decimal(self.quantity)


def _floor_to_lot(quantity: int, lot_size: int) -> int:
    if lot_size <= 0:
        raise ValueError("lot_size must be positive")
    return (quantity // lot_size) * lot_size


def build_rebalance_orders(
    targets: tuple[TargetWeight, ...],
    *,
    current_positions: Mapping[str, int],
    prices: Mapping[str, Decimal],
    portfolio_value: Decimal,
    strategy_id: str = "alpha_main",
    trade_date: str | None = None,
    lot_size: int = 1,
) -> tuple[ExecutionOrder, ...]:
    if portfolio_value <= ZERO:
        raise ValueError("portfolio_value must be positive")
    resolved_trade_date = trade_date or (targets[0].trade_date if targets else None)
    if resolved_trade_date is None:
        raise ValueError("trade_date is required when targets are empty")

    target_by_symbol = {target.ts_code: target for target in targets}
    symbols = sorted(set(current_positions) | set(target_by_symbol))
    orders: list[ExecutionOrder] = []
    for symbol in symbols:
        price = prices[symbol]
        target = target_by_symbol.get(symbol)
        target_weight = target.target_weight if target else ZERO
        target_quantity = int(
            (portfolio_value * target_weight / price).to_integral_value(rounding=ROUND_FLOOR)
        )
        target_quantity = _floor_to_lot(target_quantity, lot_size)
        current_quantity = current_positions.get(symbol, 0)
        delta_quantity = target_quantity - current_quantity
        if delta_quantity == 0:
            continue

        side: Side = "BUY" if delta_quantity > 0 else "SELL"
        quantity = abs(delta_quantity)
        orders.append(
            ExecutionOrder(
                order_id=f"{strategy_id}:{resolved_trade_date}:{symbol}:{side}",
                strategy_id=strategy_id,
                ts_code=symbol,
                trade_date=resolved_trade_date,
                side=side,
                quantity=quantity,
                reference_price=price,
            )
        )
    return tuple(orders)


class SimulatedExecutor:
    def fill_at_close(
        self,
        orders: tuple[ExecutionOrder, ...],
        bars: tuple[DailyBar, ...],
    ) -> tuple[ExecutionFill, ...]:
        price_by_key = {(bar.ts_code, bar.trade_date_yyyymmdd): bar.close for bar in bars}
        fills: list[ExecutionFill] = []
        for order in orders:
            price = price_by_key[(order.ts_code, order.trade_date)]
            fills.append(
                ExecutionFill(
                    fill_id=f"fill:{order.order_id}",
                    order_id=order.order_id,
                    strategy_id=order.strategy_id,
                    ts_code=order.ts_code,
                    trade_date=order.trade_date,
                    side=order.side,
                    quantity=order.quantity,
                    price=price,
                )
            )
        return tuple(fills)
