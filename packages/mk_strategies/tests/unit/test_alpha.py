from __future__ import annotations

from decimal import Decimal

from mk_signals import CompositeScore
from mk_strategies import MultiFactorAlphaStrategyActor, StrategyConfig


def score(symbol: str, value: str) -> CompositeScore:
    return CompositeScore(
        ts_code=symbol,
        trade_date="20240105",
        score=Decimal(value),
        raw_factors={},
        normalized_factors={},
    )


def test_alpha_strategy_selects_top_positive_scores() -> None:
    actor = MultiFactorAlphaStrategyActor(
        StrategyConfig(top_n=2, target_gross=Decimal("0.80"), max_symbol_weight=Decimal("0.45"))
    )

    targets = actor.generate_targets(
        (
            score("000001.SZ", "1.2"),
            score("000002.SZ", "-0.1"),
            score("000003.SZ", "0.8"),
        )
    )

    assert [target.ts_code for target in targets] == ["000001.SZ", "000003.SZ"]
    assert {target.target_weight for target in targets} == {Decimal("0.40")}
