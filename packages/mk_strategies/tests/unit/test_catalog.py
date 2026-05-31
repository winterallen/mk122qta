from __future__ import annotations

from decimal import Decimal

from mk_signals import CompositeScore
from mk_strategies import build_default_strategy_actors, run_strategy_catalog


def score(symbol: str, value: str) -> CompositeScore:
    return CompositeScore(
        ts_code=symbol,
        trade_date="20240131",
        score=Decimal(value),
        raw_factors={},
        normalized_factors={},
    )


def test_default_strategy_catalog_has_six_independent_actors() -> None:
    actors = build_default_strategy_actors()

    assert len(actors) == 6
    assert len({actor.spec.strategy_id for actor in actors}) == 6


def test_strategy_catalog_runs_all_actors() -> None:
    results = run_strategy_catalog(
        (
            score("000001.SZ", "1.0"),
            score("000002.SZ", "0.2"),
            score("000003.SZ", "-0.5"),
        )
    )

    assert len(results) == 6
    assert {result.strategy_id for result in results} == {
        "alpha_main",
        "style_rotation",
        "reversal_momentum",
        "event_driven",
        "etf_rotation",
        "cash_hedge",
    }
    assert results[-1].targets == ()
