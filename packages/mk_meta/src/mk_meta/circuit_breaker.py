from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True, slots=True)
class CircuitBreakerDecision:
    strategy_id: str
    tripped: bool
    reason: str
    max_drawdown: Decimal
    loss_streak: int


@dataclass(frozen=True, slots=True)
class StrategyCircuitBreaker:
    max_drawdown: Decimal = Decimal("0.05")
    max_loss_streak: int = 3

    def evaluate(self, strategy_id: str, returns: Sequence[Decimal]) -> CircuitBreakerDecision:
        equity = ONE
        peak = ONE
        worst_drawdown = ZERO
        loss_streak = 0
        worst_loss_streak = 0

        for daily_return in returns:
            equity *= ONE + daily_return
            peak = max(peak, equity)
            drawdown = ZERO if peak == ZERO else equity / peak - ONE
            worst_drawdown = min(worst_drawdown, drawdown)
            if daily_return < ZERO:
                loss_streak += 1
            else:
                loss_streak = 0
            worst_loss_streak = max(worst_loss_streak, loss_streak)

        if worst_drawdown <= -self.max_drawdown:
            return CircuitBreakerDecision(
                strategy_id=strategy_id,
                tripped=True,
                reason="max_drawdown",
                max_drawdown=worst_drawdown,
                loss_streak=worst_loss_streak,
            )
        if worst_loss_streak >= self.max_loss_streak:
            return CircuitBreakerDecision(
                strategy_id=strategy_id,
                tripped=True,
                reason="loss_streak",
                max_drawdown=worst_drawdown,
                loss_streak=worst_loss_streak,
            )
        return CircuitBreakerDecision(
            strategy_id=strategy_id,
            tripped=False,
            reason="within_limits",
            max_drawdown=worst_drawdown,
            loss_streak=worst_loss_streak,
        )
