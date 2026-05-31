from __future__ import annotations

from mk_learning import (
    GradientSafetyMonitor,
    GradientSafetyPolicy,
    KnownDriftScenario,
    MarketStateSharpe,
    OnlineLinearModel,
    OnlineTrainingExample,
    build_default_model_zoo,
    evaluate_known_drift_accuracy,
    validate_market_state_sharpe,
)


def make_examples() -> tuple[OnlineTrainingExample, ...]:
    return tuple(
        OnlineTrainingExample(
            trade_date=f"202401{index + 2:02d}",
            features={"momentum": 0.02 + index * 0.002, "quality": 0.30},
            label=0.01 + index * 0.0008,
            market_state=("trend", "range", "high_vol")[index % 3],
        )
        for index in range(12)
    )


def known_scenarios() -> tuple[KnownDriftScenario, ...]:
    base = tuple(0.10 + item * 0.01 for item in range(20))
    scenarios: list[KnownDriftScenario] = []
    for index in range(20):
        drifted = index % 2 == 0
        scenarios.append(
            KnownDriftScenario(
                name=f"known_{index}",
                expected_drifted=drifted,
                reference=base,
                current=tuple(value + (0.40 if drifted else 0.01) for value in base),
                reference_residuals=(0.01, 0.02, 0.01),
                current_residuals=(0.35, 0.34, 0.36) if drifted else (0.02, 0.01, 0.02),
                reference_importance=(0.50, 0.30, 0.20),
                current_importance=(0.10, 0.20, 0.70) if drifted else (0.49, 0.30, 0.21),
            )
        )
    return tuple(scenarios)


def test_p4_online_learning_flow_meets_acceptance_metrics() -> None:
    model = OnlineLinearModel("main_online_linear")
    monitor = GradientSafetyMonitor()
    training_report = model.partial_fit(
        make_examples()
        + (OnlineTrainingExample("20240131", {"momentum": 1000.0}, 1000.0, "high_vol"),),
        safety_monitor=monitor,
        policy=GradientSafetyPolicy(max_gradient_norm=5.0, max_abs_error=10.0),
    )
    drift_accuracy = evaluate_known_drift_accuracy(known_scenarios())
    zoo_report = build_default_model_zoo().promote_shadow_models()
    stability = validate_market_state_sharpe(
        (
            MarketStateSharpe("trend", 2.0, 1.90),
            MarketStateSharpe("range", 1.8, 1.45),
            MarketStateSharpe("high_vol", 1.5, 1.08),
        )
    )

    assert training_report.daily_complete
    assert training_report.updated_count >= 12
    assert training_report.discard_rate > 0.0
    assert drift_accuracy >= 0.95
    assert zoo_report.live_count == 7
    assert stability.passed
