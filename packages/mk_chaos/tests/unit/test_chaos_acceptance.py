from __future__ import annotations

from decimal import Decimal

from mk_chaos import (
    generate_technical_fault_scenarios,
    run_p5_chaos_validation,
    run_rule_change_drills,
)
from mk_execution import ExecutionOrder
from mk_simulation import MatchRuleSet, ParameterizedMatchingEngine


def test_p5_chaos_validation_meets_acceptance_metrics() -> None:
    report = run_p5_chaos_validation()

    assert report.accepted
    assert report.technical_report.total_count == 50
    assert report.technical_report.pass_rate == 1.0
    assert len(report.rule_results) == 12
    assert report.resilience.score >= 0.95
    assert report.helm_release.ready


def test_technical_fault_generator_covers_eight_domains() -> None:
    scenarios = generate_technical_fault_scenarios(50)

    assert len({scenario.domain for scenario in scenarios}) == 8
    assert all(scenario.rollback_plan for scenario in scenarios)


def test_rule_drills_replay_market_timeline() -> None:
    results = run_rule_change_drills(())

    assert results == ()


def test_parameterized_matching_engine_applies_limit_fee_and_t_lag() -> None:
    engine = ParameterizedMatchingEngine()
    order = ExecutionOrder(
        order_id="order-1",
        strategy_id="alpha_main",
        ts_code="000001.SZ",
        trade_date="20240103",
        side="SELL",
        quantity=100,
        reference_price=Decimal("10.00"),
    )
    rules = MatchRuleSet(
        version="unit",
        effective_date="20240101",
        limit_up_pct=Decimal("0.10"),
        limit_down_pct=Decimal("0.10"),
        settlement_lag_days=1,
        stamp_tax_rate=Decimal("0.001"),
        commission_rate=Decimal("0.0002"),
    )

    accepted = engine.match_order(
        order,
        previous_close=Decimal("10.00"),
        execution_price=Decimal("10.50"),
        rules=rules,
    )
    rejected = engine.match_order(
        order,
        previous_close=Decimal("10.00"),
        execution_price=Decimal("11.50"),
        rules=rules,
    )

    assert accepted.accepted
    assert accepted.total_fee == Decimal("1.260000")
    assert accepted.settlement_lag_days == 1
    assert not rejected.accepted
    assert rejected.reason == "limit_up_blocked"
