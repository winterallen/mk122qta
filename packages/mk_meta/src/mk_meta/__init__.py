"""Meta scheduler primitives for MK122."""

from mk_meta.circuit_breaker import CircuitBreakerDecision, StrategyCircuitBreaker
from mk_meta.scheduler import (
    AllocationDecision,
    BayesianClipRecord,
    BayesianParameterCandidate,
    MetaScheduler,
    SchedulerAudit,
    SchedulerConstraints,
    StrategyPerformance,
)
from mk_meta.simulation import (
    MultiStrategySimulationReport,
    StrategyReturnSeries,
    average_pairwise_correlation,
    calculate_strategy_performance,
    run_multi_strategy_simulation,
)

__all__ = [
    "AllocationDecision",
    "BayesianClipRecord",
    "BayesianParameterCandidate",
    "CircuitBreakerDecision",
    "MetaScheduler",
    "MultiStrategySimulationReport",
    "SchedulerAudit",
    "SchedulerConstraints",
    "StrategyCircuitBreaker",
    "StrategyPerformance",
    "StrategyReturnSeries",
    "average_pairwise_correlation",
    "calculate_strategy_performance",
    "run_multi_strategy_simulation",
]
