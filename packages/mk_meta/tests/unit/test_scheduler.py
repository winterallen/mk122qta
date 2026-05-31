from __future__ import annotations

from decimal import Decimal

from mk_meta import (
    BayesianParameterCandidate,
    SchedulerConstraints,
    StrategyCircuitBreaker,
    StrategyReturnSeries,
    run_multi_strategy_simulation,
)


def test_single_strategy_circuit_breaker_does_not_stop_peers() -> None:
    good = StrategyReturnSeries("alpha_main", (Decimal("0.01"), Decimal("0.00")) * 6)
    bad = StrategyReturnSeries("cash_hedge", (Decimal("-0.03"),) * 12)

    report = run_multi_strategy_simulation(
        (good, bad),
        circuit_breaker=StrategyCircuitBreaker(max_drawdown=Decimal("0.05")),
    )

    breaker_by_id = {decision.strategy_id: decision for decision in report.audit.circuit_breakers}
    allocation_by_id = {allocation.strategy_id: allocation for allocation in report.allocations}

    assert breaker_by_id["cash_hedge"].tripped
    assert not breaker_by_id["alpha_main"].tripped
    assert allocation_by_id["alpha_main"].active
    assert not allocation_by_id["cash_hedge"].active


def test_meta_scheduler_records_bayesian_clip_audit() -> None:
    series = (
        StrategyReturnSeries("alpha_main", (Decimal("0.006"), Decimal("0.004")) * 6),
        StrategyReturnSeries("style_rotation", (Decimal("0.005"), Decimal("0.003")) * 6),
    )

    report = run_multi_strategy_simulation(
        series,
        constraints=SchedulerConstraints(max_strategy_weight=Decimal("0.60")),
        bayesian_candidates=(
            BayesianParameterCandidate("style_rotation", "style_window_8", 0.12, 0.30, shadow=True),
        ),
    )

    assert report.audit.bayesian_clips[0].strategy_id == "style_rotation"
    assert report.audit.bayesian_clips[0].reason == "shadow_candidate"
    assert report.active_strategy_count == 2
    assert report.portfolio_sharpe > 1.5
