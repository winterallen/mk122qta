from __future__ import annotations

from decimal import Decimal

from mk_risk import RiskBudget, RiskGateState, RiskSnapshot, evaluate_risk_gate


def snapshot(
    *,
    gross_exposure: Decimal = Decimal("0.80"),
    max_symbol_weight: Decimal = Decimal("0.30"),
    order_notional: Decimal = Decimal("100000"),
    daily_turnover: Decimal = Decimal("0.10"),
    cash_buffer: Decimal = Decimal("0.10"),
    data_quality_errors: int = 0,
    kill_switch: bool = False,
) -> RiskSnapshot:
    return RiskSnapshot(
        gross_exposure=gross_exposure,
        max_symbol_weight=max_symbol_weight,
        order_notional=order_notional,
        daily_turnover=daily_turnover,
        cash_buffer=cash_buffer,
        data_quality_errors=data_quality_errors,
        kill_switch=kill_switch,
    )


def test_risk_gate_pass_state() -> None:
    decision = evaluate_risk_gate(snapshot())
    assert decision.state == RiskGateState.PASS


def test_risk_gate_block_state() -> None:
    decision = evaluate_risk_gate(snapshot(gross_exposure=Decimal("1.20")))
    assert decision.state == RiskGateState.BLOCK


def test_risk_gate_reduce_state() -> None:
    decision = evaluate_risk_gate(
        snapshot(max_symbol_weight=Decimal("0.60")),
        RiskBudget(max_symbol_weight=Decimal("0.30")),
    )
    assert decision.state == RiskGateState.REDUCE
    assert decision.approved_weight_scale == Decimal("0.5")


def test_risk_gate_freeze_state() -> None:
    decision = evaluate_risk_gate(snapshot(data_quality_errors=1))
    assert decision.state == RiskGateState.FREEZE


def test_risk_gate_halt_state() -> None:
    decision = evaluate_risk_gate(snapshot(kill_switch=True))
    assert decision.state == RiskGateState.HALT
