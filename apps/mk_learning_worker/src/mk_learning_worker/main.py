from __future__ import annotations

import json

from mk_learning import (
    GradientSafetyMonitor,
    GradientSafetyPolicy,
    OnlineLinearModel,
    OnlineTrainingExample,
    build_default_model_zoo,
    detect_drift,
)


def _examples() -> tuple[OnlineTrainingExample, ...]:
    return tuple(
        OnlineTrainingExample(
            trade_date=f"202401{index + 2:02d}",
            features={"momentum": 0.02 + index * 0.001, "volatility": 0.10},
            label=0.01 + index * 0.0005,
            market_state="trend",
        )
        for index in range(8)
    )


def main() -> None:
    model = OnlineLinearModel("main_online_linear")
    monitor = GradientSafetyMonitor()
    report = model.partial_fit(
        _examples()
        + (
            OnlineTrainingExample(
                trade_date="20240131",
                features={"momentum": 1000.0},
                label=1000.0,
                market_state="high_vol",
            ),
        ),
        safety_monitor=monitor,
        policy=GradientSafetyPolicy(max_gradient_norm=5.0),
    )
    drift = detect_drift(
        trade_date="20240131",
        reference=(0.10, 0.11, 0.12, 0.13),
        current=(0.11, 0.12, 0.13, 0.14),
        reference_residuals=(0.01, 0.02, 0.01),
        current_residuals=(0.02, 0.01, 0.02),
        reference_importance=(0.50, 0.30, 0.20),
        current_importance=(0.48, 0.32, 0.20),
    )
    zoo = build_default_model_zoo().promote_shadow_models()
    print(
        json.dumps(
            {
                "model_id": report.model_id,
                "daily_complete": report.daily_complete,
                "discard_rate": report.discard_rate,
                "drifted": drift.drifted,
                "model_count": len(zoo.models),
                "live_count": zoo.live_count,
            },
            ensure_ascii=False,
        )
    )
