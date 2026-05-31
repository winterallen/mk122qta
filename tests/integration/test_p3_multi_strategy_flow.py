from __future__ import annotations

from decimal import Decimal

from mk_meta import (
    BayesianParameterCandidate,
    SchedulerConstraints,
    StrategyCircuitBreaker,
    StrategyReturnSeries,
    run_multi_strategy_simulation,
)


def make_series(strategy_id: str, mean: str, pattern: tuple[int, ...]) -> StrategyReturnSeries:
    returns = tuple(Decimal(mean) + Decimal(item) * Decimal("0.001") for item in pattern)
    return StrategyReturnSeries(strategy_id=strategy_id, returns=returns)


def test_p3_multi_strategy_flow_meets_correlation_sharpe_and_isolation_acceptance() -> None:
    series = (
        make_series("alpha_main", "0.0080", (1, 1, 1, 1, -1, -1, -1, -1) * 3),
        make_series("style_rotation", "0.0068", (1, 1, -1, -1, 1, 1, -1, -1) * 3),
        make_series("reversal_momentum", "0.0062", (1, -1, 1, -1, 1, -1, 1, -1) * 3),
        make_series("event_driven", "0.0058", (1, 1, -1, -1, -1, -1, 1, 1) * 3),
        make_series("etf_rotation", "0.0052", (1, -1, -1, 1, 1, -1, -1, 1) * 3),
        StrategyReturnSeries("cash_hedge", returns=(Decimal("-0.03"),) * 24),
    )

    report = run_multi_strategy_simulation(
        series,
        constraints=SchedulerConstraints(max_strategy_weight=Decimal("0.35")),
        circuit_breaker=StrategyCircuitBreaker(max_drawdown=Decimal("0.05")),
        bayesian_candidates=(
            BayesianParameterCandidate("alpha_main", "alpha_depth_3", 0.24, 0.10, shadow=False),
            BayesianParameterCandidate("event_driven", "event_decay_2", 0.10, 0.20, shadow=True),
        ),
    )

    allocation_by_id = {allocation.strategy_id: allocation for allocation in report.allocations}
    breaker_by_id = {decision.strategy_id: decision for decision in report.audit.circuit_breakers}

    assert report.strategy_count == 6
    assert report.active_strategy_count == 5
    assert report.average_correlation < 0.5
    assert report.portfolio_sharpe > 1.5
    assert breaker_by_id["cash_hedge"].tripped
    assert not allocation_by_id["cash_hedge"].active
    assert all(
        allocation_by_id[strategy_id].active
        for strategy_id in allocation_by_id
        if strategy_id != "cash_hedge"
    )
    assert report.audit.bayesian_clips[1].reason == "shadow_candidate"
