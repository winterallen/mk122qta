from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from mk_meta.circuit_breaker import StrategyCircuitBreaker
from mk_meta.scheduler import (
    AllocationDecision,
    BayesianParameterCandidate,
    MetaScheduler,
    SchedulerAudit,
    SchedulerConstraints,
    StrategyPerformance,
)

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True, slots=True)
class StrategyReturnSeries:
    strategy_id: str
    returns: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class MultiStrategySimulationReport:
    trade_date: str
    strategy_count: int
    active_strategy_count: int
    average_correlation: float
    portfolio_sharpe: float
    portfolio_returns: tuple[Decimal, ...]
    allocations: tuple[AllocationDecision, ...]
    audit: SchedulerAudit


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _pearson(left: Sequence[Decimal], right: Sequence[Decimal]) -> float:
    shared = min(len(left), len(right))
    if shared < 2:
        return 0.0
    left_values = [float(value) for value in left[:shared]]
    right_values = [float(value) for value in right[:shared]]
    left_mean = _mean(left_values)
    right_mean = _mean(right_values)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left_values, right_values, strict=True)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left_values)
        * sum((value - right_mean) ** 2 for value in right_values)
    )
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def annualized_sharpe(returns: Sequence[Decimal], *, periods_per_year: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    values = [float(value) for value in returns]
    volatility = _std(values)
    if volatility == 0.0:
        return 99.0 if _mean(values) > 0 else 0.0
    return _mean(values) / volatility * math.sqrt(periods_per_year)


def calculate_strategy_performance(series: StrategyReturnSeries) -> StrategyPerformance:
    values = [float(value) for value in series.returns]
    return StrategyPerformance(
        strategy_id=series.strategy_id,
        sharpe=annualized_sharpe(series.returns),
        volatility=max(_std(values), 0.0001),
        mean_return=_mean(values),
    )


def average_pairwise_correlation(series: tuple[StrategyReturnSeries, ...]) -> float:
    if len(series) < 2:
        return 0.0
    correlations: list[float] = []
    for left_index, left in enumerate(series):
        for right in series[left_index + 1 :]:
            correlations.append(abs(_pearson(left.returns, right.returns)))
    return _mean(correlations)


def _portfolio_returns(
    series: tuple[StrategyReturnSeries, ...],
    allocations: tuple[AllocationDecision, ...],
) -> tuple[Decimal, ...]:
    allocation_by_id = {
        allocation.strategy_id: allocation.target_weight for allocation in allocations
    }
    periods = min(len(item.returns) for item in series)
    returns: list[Decimal] = []
    for index in range(periods):
        daily_return = ZERO
        for item in series:
            daily_return += allocation_by_id.get(item.strategy_id, ZERO) * item.returns[index]
        returns.append(daily_return)
    return tuple(returns)


def run_multi_strategy_simulation(
    series: tuple[StrategyReturnSeries, ...],
    *,
    trade_date: str = "20240131",
    constraints: SchedulerConstraints | None = None,
    circuit_breaker: StrategyCircuitBreaker | None = None,
    bayesian_candidates: tuple[BayesianParameterCandidate, ...] = (),
) -> MultiStrategySimulationReport:
    if len(series) < 2:
        raise ValueError("multi strategy simulation requires at least two strategies")

    active_breaker = circuit_breaker or StrategyCircuitBreaker()
    circuit_decisions = tuple(
        active_breaker.evaluate(item.strategy_id, item.returns) for item in series
    )
    performances = tuple(calculate_strategy_performance(item) for item in series)
    scheduler = MetaScheduler(constraints)
    allocations = scheduler.allocate(
        performances,
        circuit_breakers=circuit_decisions,
        bayesian_candidates=bayesian_candidates,
    )
    portfolio_returns = _portfolio_returns(series, allocations)
    average_correlation = average_pairwise_correlation(series)
    portfolio_sharpe = annualized_sharpe(portfolio_returns)
    audit = SchedulerAudit(
        trade_date=trade_date,
        allocations=allocations,
        bayesian_clips=scheduler.bayesian_clips(allocations, bayesian_candidates),
        circuit_breakers=circuit_decisions,
        average_correlation=average_correlation,
        portfolio_sharpe=portfolio_sharpe,
    )
    return MultiStrategySimulationReport(
        trade_date=trade_date,
        strategy_count=len(series),
        active_strategy_count=sum(1 for allocation in allocations if allocation.active),
        average_correlation=average_correlation,
        portfolio_sharpe=portfolio_sharpe,
        portfolio_returns=portfolio_returns,
        allocations=allocations,
        audit=audit,
    )
