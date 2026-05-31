from __future__ import annotations

from decimal import Decimal

from mk_learning import (
    MarketStateSharpe,
    ModelStatus,
    build_default_model_zoo,
    validate_market_state_sharpe,
)


def test_model_zoo_promotes_shadow_models_and_allocates_weights() -> None:
    report = build_default_model_zoo().promote_shadow_models()
    live_weights = [
        model.weight
        for model in report.models
        if model.status in {ModelStatus.LIVE, ModelStatus.VETERAN}
    ]

    assert len(report.models) == 7
    assert report.live_count == 7
    assert sum(live_weights, Decimal("0")) == Decimal("1.000000000000000000000000000")


def test_market_state_sharpe_retention_passes_three_states() -> None:
    report = validate_market_state_sharpe(
        (
            MarketStateSharpe("trend", baseline_sharpe=2.0, online_sharpe=1.90),
            MarketStateSharpe("range", baseline_sharpe=1.7, online_sharpe=1.45),
            MarketStateSharpe("high_vol", baseline_sharpe=1.5, online_sharpe=1.08),
        )
    )

    assert report.passed
    assert report.min_retention >= 0.70
