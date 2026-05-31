from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_data.schemas import DailyBar
from mk_signals import CompositeScore

from mk_strategies.alpha import TargetWeight

ZERO = Decimal("0")


class StrategyFamily(StrEnum):
    ALPHA = "alpha"
    STYLE = "style"
    REVERSAL = "reversal"
    EVENT = "event"
    ETF = "etf"
    HEDGE = "hedge"


@dataclass(frozen=True, slots=True)
class StrategySpec:
    strategy_id: str
    display_name: str
    family: StrategyFamily
    target_gross: Decimal = Decimal("0.20")


@dataclass(frozen=True, slots=True)
class StrategyRunResult:
    strategy_id: str
    trade_date: str
    targets: tuple[TargetWeight, ...]
    diagnostics: dict[str, str]


class IndependentStrategyActor:
    def __init__(self, spec: StrategySpec) -> None:
        self.spec = spec

    def generate_targets(
        self,
        scores: tuple[CompositeScore, ...],
        bars: tuple[DailyBar, ...] = (),
    ) -> StrategyRunResult:
        trade_date = scores[0].trade_date if scores else self._latest_trade_date(bars)
        selected = self._select_score(scores)
        if selected is None or self.spec.family == StrategyFamily.HEDGE:
            return StrategyRunResult(
                strategy_id=self.spec.strategy_id,
                trade_date=trade_date,
                targets=(),
                diagnostics={"mode": self.spec.family.value, "selected": "cash"},
            )
        return StrategyRunResult(
            strategy_id=self.spec.strategy_id,
            trade_date=trade_date,
            targets=(
                TargetWeight(
                    strategy_id=self.spec.strategy_id,
                    ts_code=selected.ts_code,
                    trade_date=trade_date,
                    target_weight=self.spec.target_gross,
                    score=selected.score,
                ),
            ),
            diagnostics={"mode": self.spec.family.value, "selected": selected.ts_code},
        )

    def _select_score(self, scores: tuple[CompositeScore, ...]) -> CompositeScore | None:
        if not scores:
            return None
        ranked = tuple(sorted(scores, key=lambda item: (item.score, item.ts_code), reverse=True))
        if self.spec.family in {StrategyFamily.ALPHA, StrategyFamily.STYLE, StrategyFamily.ETF}:
            return ranked[0]
        if self.spec.family == StrategyFamily.REVERSAL:
            return ranked[-1]
        if self.spec.family == StrategyFamily.EVENT:
            return ranked[min(1, len(ranked) - 1)]
        return None

    def _latest_trade_date(self, bars: tuple[DailyBar, ...]) -> str:
        if not bars:
            return "19700101"
        return max(bar.trade_date_yyyymmdd for bar in bars)


def build_default_strategy_actors() -> tuple[IndependentStrategyActor, ...]:
    specs = (
        StrategySpec("alpha_main", "Main Multi-Factor Alpha", StrategyFamily.ALPHA),
        StrategySpec("style_rotation", "Style Rotation", StrategyFamily.STYLE),
        StrategySpec("reversal_momentum", "Reversal / Momentum Branch", StrategyFamily.REVERSAL),
        StrategySpec("event_driven", "Event Driven", StrategyFamily.EVENT),
        StrategySpec("etf_rotation", "ETF Rotation", StrategyFamily.ETF),
        StrategySpec("cash_hedge", "Cash / Hedge", StrategyFamily.HEDGE, Decimal("0.10")),
    )
    return tuple(IndependentStrategyActor(spec) for spec in specs)


def run_strategy_catalog(
    scores: tuple[CompositeScore, ...],
    bars: tuple[DailyBar, ...] = (),
) -> tuple[StrategyRunResult, ...]:
    return tuple(actor.generate_targets(scores, bars) for actor in build_default_strategy_actors())
