from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketStateSharpe:
    state: str
    baseline_sharpe: float
    online_sharpe: float

    @property
    def retention(self) -> float:
        if self.baseline_sharpe <= 0.0:
            return 1.0
        return self.online_sharpe / self.baseline_sharpe


@dataclass(frozen=True, slots=True)
class SharpeStabilityReport:
    states: tuple[MarketStateSharpe, ...]
    min_retention: float
    passed: bool


def validate_market_state_sharpe(
    states: tuple[MarketStateSharpe, ...],
    *,
    min_retention: float = 0.70,
) -> SharpeStabilityReport:
    observed_min = min((state.retention for state in states), default=0.0)
    return SharpeStabilityReport(
        states=states,
        min_retention=observed_min,
        passed=len(states) >= 3 and observed_min >= min_retention,
    )
