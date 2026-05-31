from __future__ import annotations

from mk_learning import (
    FTRLLinearModel,
    GradientSafetyMonitor,
    GradientSafetyPolicy,
    OnlineLinearModel,
    OnlineTrainingExample,
    dual_track_vote,
    elastic_learning_rate,
)


def examples() -> tuple[OnlineTrainingExample, ...]:
    return tuple(
        OnlineTrainingExample(
            trade_date=f"202401{index + 2:02d}",
            features={"momentum": 0.02 + index * 0.001, "volatility": 0.10},
            label=0.01 + index * 0.0005,
            market_state="trend",
        )
        for index in range(6)
    )


def test_online_linear_model_completes_daily_incremental_update() -> None:
    model = OnlineLinearModel("main_online_linear")
    monitor = GradientSafetyMonitor()

    report = model.partial_fit(examples(), safety_monitor=monitor)

    assert report.daily_complete
    assert report.updated_count == 6
    assert model.predict_value({"momentum": 0.03, "volatility": 0.10}) != 0.0


def test_ftrl_baseline_updates_daily() -> None:
    model = FTRLLinearModel()

    report = model.partial_fit(examples())

    assert report.daily_complete
    assert report.updated_count == 6


def test_gradient_safety_discards_abnormal_update_and_tracks_rate() -> None:
    model = OnlineLinearModel("main_online_linear")
    monitor = GradientSafetyMonitor()
    abnormal = OnlineTrainingExample(
        trade_date="20240109",
        features={"momentum": 1000.0},
        label=1000.0,
    )

    report = model.partial_fit(
        examples() + (abnormal,),
        safety_monitor=monitor,
        policy=GradientSafetyPolicy(max_gradient_norm=5.0, max_abs_error=10.0),
    )

    assert report.discarded_count >= 1
    assert report.discard_rate > 0.0
    assert GradientSafetyPolicy().guardrail_count == 6


def test_elastic_learning_rate_and_dual_track_vote() -> None:
    learning_rate = elastic_learning_rate(base_rate=0.10, drifted=True, discard_rate=0.05)
    vote = dual_track_vote(online_score=0.80, offline_score=1.00)

    assert learning_rate.adjusted_rate == 0.05
    assert learning_rate.reason == "drift_cooldown"
    assert vote.accepted_online
    assert vote.online_weight > 0.0
