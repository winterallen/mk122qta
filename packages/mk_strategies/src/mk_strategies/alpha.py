from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mk_signals import CompositeScore

ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    strategy_id: str = "alpha_main"
    top_n: int = 3
    target_gross: Decimal = Decimal("0.90")
    max_symbol_weight: Decimal = Decimal("0.35")
    min_score: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class TargetWeight:
    strategy_id: str
    ts_code: str
    trade_date: str
    target_weight: Decimal
    score: Decimal


class MultiFactorAlphaStrategyActor:
    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def generate_targets(self, scores: tuple[CompositeScore, ...]) -> tuple[TargetWeight, ...]:
        if self.config.top_n <= 0:
            raise ValueError("top_n must be positive")

        selected = tuple(
            sorted(
                (score for score in scores if score.score > self.config.min_score),
                key=lambda item: (item.score, item.ts_code),
                reverse=True,
            )[: self.config.top_n]
        )
        if not selected:
            return ()

        equal_weight = self.config.target_gross / Decimal(len(selected))
        target_weight = min(equal_weight, self.config.max_symbol_weight)
        return tuple(
            TargetWeight(
                strategy_id=self.config.strategy_id,
                ts_code=score.ts_code,
                trade_date=score.trade_date,
                target_weight=target_weight,
                score=score.score,
            )
            for score in selected
            if target_weight > ZERO
        )
