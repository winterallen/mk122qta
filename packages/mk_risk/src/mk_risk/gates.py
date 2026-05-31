from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

ZERO = Decimal("0")
ONE = Decimal("1")


class RiskGateState(StrEnum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    REDUCE = "REDUCE"
    FREEZE = "FREEZE"
    HALT = "HALT"


@dataclass(frozen=True, slots=True)
class RiskBudget:
    max_gross_exposure: Decimal = Decimal("1.00")
    max_symbol_weight: Decimal = Decimal("0.35")
    max_order_notional: Decimal = Decimal("1000000")
    max_daily_turnover: Decimal = Decimal("0.95")
    min_cash_buffer: Decimal = Decimal("0.02")
    max_daily_loss: Decimal = Decimal("0.08")


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    gross_exposure: Decimal
    max_symbol_weight: Decimal
    order_notional: Decimal
    daily_turnover: Decimal
    cash_buffer: Decimal
    daily_drawdown: Decimal = ZERO
    data_quality_errors: int = 0
    reconcile_break: Decimal = ZERO
    manual_freeze: bool = False
    kill_switch: bool = False


@dataclass(frozen=True, slots=True)
class RiskDecision:
    state: RiskGateState
    approved_weight_scale: Decimal
    reasons: tuple[str, ...]

    @property
    def is_tradable(self) -> bool:
        return self.state in {RiskGateState.PASS, RiskGateState.REDUCE}


def _scale_or_zero(limit: Decimal, observed: Decimal) -> Decimal:
    if observed <= ZERO:
        return ONE
    return max(ZERO, min(ONE, limit / observed))


def evaluate_risk_gate(snapshot: RiskSnapshot, budget: RiskBudget | None = None) -> RiskDecision:
    active_budget = budget or RiskBudget()

    if snapshot.kill_switch or snapshot.daily_drawdown <= -active_budget.max_daily_loss:
        return RiskDecision(
            state=RiskGateState.HALT,
            approved_weight_scale=ZERO,
            reasons=("hard_stop_or_kill_switch",),
        )

    if (
        snapshot.manual_freeze
        or snapshot.data_quality_errors > 0
        or snapshot.reconcile_break != ZERO
    ):
        return RiskDecision(
            state=RiskGateState.FREEZE,
            approved_weight_scale=ZERO,
            reasons=("data_or_reconcile_freeze",),
        )

    block_reasons: list[str] = []
    if snapshot.gross_exposure > active_budget.max_gross_exposure:
        block_reasons.append("gross_exposure_exceeded")
    if snapshot.order_notional > active_budget.max_order_notional:
        block_reasons.append("order_notional_exceeded")
    if snapshot.cash_buffer < active_budget.min_cash_buffer:
        block_reasons.append("cash_buffer_breached")
    if block_reasons:
        return RiskDecision(
            state=RiskGateState.BLOCK,
            approved_weight_scale=ZERO,
            reasons=tuple(block_reasons),
        )

    reduce_scales: list[Decimal] = []
    reduce_reasons: list[str] = []
    if snapshot.max_symbol_weight > active_budget.max_symbol_weight:
        reduce_scales.append(
            _scale_or_zero(active_budget.max_symbol_weight, snapshot.max_symbol_weight)
        )
        reduce_reasons.append("symbol_weight_exceeded")
    if snapshot.daily_turnover > active_budget.max_daily_turnover:
        reduce_scales.append(
            _scale_or_zero(active_budget.max_daily_turnover, snapshot.daily_turnover)
        )
        reduce_reasons.append("turnover_exceeded")
    if reduce_scales:
        return RiskDecision(
            state=RiskGateState.REDUCE,
            approved_weight_scale=min(reduce_scales),
            reasons=tuple(reduce_reasons),
        )

    return RiskDecision(
        state=RiskGateState.PASS,
        approved_weight_scale=ONE,
        reasons=("within_budget",),
    )
