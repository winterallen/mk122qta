from __future__ import annotations

import json
from decimal import Decimal

from mk_meta import (
    BayesianParameterCandidate,
    SchedulerConstraints,
    StrategyReturnSeries,
    run_multi_strategy_simulation,
)


def _series(strategy_id: str, mean: Decimal, pattern: tuple[int, ...]) -> StrategyReturnSeries:
    returns = tuple(mean + Decimal(item) * Decimal("0.001") for item in pattern)
    return StrategyReturnSeries(strategy_id=strategy_id, returns=returns)


def main() -> None:
    pattern = (1, 1, -1, -1, 1, -1, 1, -1) * 3
    series = (
        _series("alpha_main", Decimal("0.0080"), pattern),
        _series("style_rotation", Decimal("0.0065"), tuple(reversed(pattern))),
        _series("reversal_momentum", Decimal("0.0060"), (1, -1, 1, -1, 1, -1, 1, -1) * 3),
        _series("event_driven", Decimal("0.0055"), (1, 1, 1, -1, -1, -1, 1, -1) * 3),
        _series("etf_rotation", Decimal("0.0050"), (1, -1, -1, 1, 1, -1, -1, 1) * 3),
        StrategyReturnSeries("cash_hedge", returns=(Decimal("-0.03"),) * 24),
    )
    report = run_multi_strategy_simulation(
        series,
        constraints=SchedulerConstraints(max_strategy_weight=Decimal("0.35")),
        bayesian_candidates=(
            BayesianParameterCandidate("alpha_main", "alpha_depth_3", 0.25, 0.10, shadow=False),
            BayesianParameterCandidate("event_driven", "event_decay_2", 0.10, 0.20, shadow=True),
        ),
    )
    print(
        json.dumps(
            {
                "strategy_count": report.strategy_count,
                "active_strategy_count": report.active_strategy_count,
                "average_correlation": report.average_correlation,
                "portfolio_sharpe": report.portfolio_sharpe,
                "bayesian_clips": [
                    {
                        "strategy_id": clip.strategy_id,
                        "candidate_id": clip.candidate_id,
                        "reason": clip.reason,
                    }
                    for clip in report.audit.bayesian_clips
                ],
            },
            ensure_ascii=False,
        )
    )
