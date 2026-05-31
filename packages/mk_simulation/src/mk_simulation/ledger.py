from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mk_execution import ExecutionFill

ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class Position:
    ts_code: str
    quantity: int
    average_cost: Decimal


@dataclass(frozen=True, slots=True)
class LedgerSnapshot:
    trade_date: str
    cash: Decimal
    market_value: Decimal
    total_equity: Decimal
    daily_return: Decimal
    positions: tuple[Position, ...]


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    cash_diff: Decimal
    position_diff: Decimal
    nav_diff: Decimal

    @property
    def matched(self) -> bool:
        return self.cash_diff == ZERO and self.position_diff == ZERO and self.nav_diff == ZERO


class PortfolioLedger:
    def __init__(self, initial_cash: Decimal) -> None:
        if initial_cash <= ZERO:
            raise ValueError("initial_cash must be positive")
        self.cash = initial_cash
        self._positions: dict[str, Position] = {}
        self.fills: list[ExecutionFill] = []
        self.snapshots: list[LedgerSnapshot] = []

    @property
    def positions(self) -> tuple[Position, ...]:
        return tuple(sorted(self._positions.values(), key=lambda position: position.ts_code))

    def position_quantities(self) -> dict[str, int]:
        return {symbol: position.quantity for symbol, position in self._positions.items()}

    def apply_fill(self, fill: ExecutionFill) -> None:
        if fill.quantity <= 0:
            raise ValueError("fill quantity must be positive")

        current = self._positions.get(fill.ts_code)
        if fill.side == "BUY":
            old_quantity = current.quantity if current else 0
            old_cost = current.average_cost if current else ZERO
            new_quantity = old_quantity + fill.quantity
            average_cost = ((old_cost * Decimal(old_quantity)) + fill.notional) / Decimal(
                new_quantity
            )
            self.cash -= fill.notional
            self._positions[fill.ts_code] = Position(fill.ts_code, new_quantity, average_cost)
        else:
            if current is None or current.quantity < fill.quantity:
                raise ValueError("cannot sell more than current position")
            new_quantity = current.quantity - fill.quantity
            self.cash += fill.notional
            if new_quantity == 0:
                del self._positions[fill.ts_code]
            else:
                self._positions[fill.ts_code] = Position(
                    fill.ts_code,
                    new_quantity,
                    current.average_cost,
                )
        self.fills.append(fill)

    def market_value(self, prices: dict[str, Decimal]) -> Decimal:
        total = ZERO
        for position in self._positions.values():
            total += prices[position.ts_code] * Decimal(position.quantity)
        return total

    def total_equity(self, prices: dict[str, Decimal]) -> Decimal:
        return self.cash + self.market_value(prices)

    def mark_to_market(self, trade_date: str, prices: dict[str, Decimal]) -> LedgerSnapshot:
        market_value = self.market_value(prices)
        total_equity = self.cash + market_value
        previous_equity = self.snapshots[-1].total_equity if self.snapshots else total_equity
        daily_return = (
            ZERO if previous_equity == ZERO else (total_equity - previous_equity) / previous_equity
        )
        snapshot = LedgerSnapshot(
            trade_date=trade_date,
            cash=self.cash,
            market_value=market_value,
            total_equity=total_equity,
            daily_return=daily_return,
            positions=self.positions,
        )
        self.snapshots.append(snapshot)
        return snapshot

    def reconcile(
        self,
        snapshot: LedgerSnapshot,
        prices: dict[str, Decimal],
    ) -> ReconciliationReport:
        recomputed_nav = self.cash + self.market_value(prices)
        return ReconciliationReport(
            cash_diff=self.cash - snapshot.cash,
            position_diff=ZERO,
            nav_diff=recomputed_nav - snapshot.total_equity,
        )


@dataclass(slots=True)
class StrategyLedger:
    strategy_id: str
    targets_seen: int = 0
    orders_seen: int = 0
    fills_seen: int = 0

    def record_targets(self, count: int) -> None:
        self.targets_seen += count

    def record_orders(self, count: int) -> None:
        self.orders_seen += count

    def record_fills(self, count: int) -> None:
        self.fills_seen += count
