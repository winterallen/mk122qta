from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mk_execution import ExecutionOrder


@dataclass(frozen=True, slots=True)
class MatchRuleSet:
    version: str
    effective_date: str
    limit_up_pct: Decimal
    limit_down_pct: Decimal
    settlement_lag_days: int
    stamp_tax_rate: Decimal
    commission_rate: Decimal
    lot_size: int = 100


@dataclass(frozen=True, slots=True)
class ParameterizedFillReport:
    order_id: str
    accepted: bool
    execution_price: Decimal
    commission: Decimal
    stamp_tax: Decimal
    settlement_lag_days: int
    reason: str

    @property
    def total_fee(self) -> Decimal:
        return self.commission + self.stamp_tax


class ParameterizedMatchingEngine:
    def match_order(
        self,
        order: ExecutionOrder,
        *,
        previous_close: Decimal,
        execution_price: Decimal,
        rules: MatchRuleSet,
    ) -> ParameterizedFillReport:
        if order.quantity <= 0:
            return self._reject(order, execution_price, rules, "non_positive_quantity")
        if order.quantity % rules.lot_size != 0:
            return self._reject(order, execution_price, rules, "invalid_lot_size")
        if execution_price > previous_close * (Decimal("1") + rules.limit_up_pct):
            return self._reject(order, execution_price, rules, "limit_up_blocked")
        if execution_price < previous_close * (Decimal("1") - rules.limit_down_pct):
            return self._reject(order, execution_price, rules, "limit_down_blocked")

        notional = execution_price * Decimal(order.quantity)
        commission = notional * rules.commission_rate
        stamp_tax = notional * rules.stamp_tax_rate if order.side == "SELL" else Decimal("0")
        return ParameterizedFillReport(
            order_id=order.order_id,
            accepted=True,
            execution_price=execution_price,
            commission=commission,
            stamp_tax=stamp_tax,
            settlement_lag_days=rules.settlement_lag_days,
            reason="accepted",
        )

    def _reject(
        self,
        order: ExecutionOrder,
        execution_price: Decimal,
        rules: MatchRuleSet,
        reason: str,
    ) -> ParameterizedFillReport:
        return ParameterizedFillReport(
            order_id=order.order_id,
            accepted=False,
            execution_price=execution_price,
            commission=Decimal("0"),
            stamp_tax=Decimal("0"),
            settlement_lag_days=rules.settlement_lag_days,
            reason=reason,
        )
