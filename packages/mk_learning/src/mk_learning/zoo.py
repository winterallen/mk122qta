from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

ZERO = Decimal("0")
ONE = Decimal("1")


class ModelStatus(StrEnum):
    SHADOW = "Shadow"
    LIVE = "Live"
    VETERAN = "Veteran"
    REJECTED = "Rejected"


@dataclass(frozen=True, slots=True)
class ModelState:
    model_id: str
    family: str
    status: ModelStatus
    validation_score: float
    sharpe_by_state: dict[str, float]
    weight: Decimal = ZERO


@dataclass(frozen=True, slots=True)
class ModelZooReport:
    models: tuple[ModelState, ...]

    @property
    def live_count(self) -> int:
        return sum(
            1 for model in self.models if model.status in {ModelStatus.LIVE, ModelStatus.VETERAN}
        )


class ModelRegistry:
    def __init__(self, models: tuple[ModelState, ...]) -> None:
        self.models = models

    def promote_shadow_models(self, *, min_score: float = 0.55) -> ModelZooReport:
        promoted: list[ModelState] = []
        for model in self.models:
            status = model.status
            if model.status == ModelStatus.SHADOW and model.validation_score >= min_score:
                status = ModelStatus.LIVE
            elif model.status == ModelStatus.SHADOW:
                status = ModelStatus.REJECTED
            promoted.append(
                ModelState(
                    model.model_id,
                    model.family,
                    status,
                    model.validation_score,
                    model.sharpe_by_state,
                )
            )
        return ModelZooReport(models=_allocate_weights(tuple(promoted)))


def build_default_model_zoo() -> ModelRegistry:
    return ModelRegistry(
        (
            ModelState("main_online_linear", "online_linear", ModelStatus.LIVE, 0.82, _states(2.1)),
            ModelState("ftrl_baseline", "ftrl", ModelStatus.LIVE, 0.74, _states(1.9)),
            ModelState(
                "online_lgbm_proxy", "tree_boosting", ModelStatus.SHADOW, 0.77, _states(2.0)
            ),
            ModelState("river_proxy", "river_online", ModelStatus.SHADOW, 0.71, _states(1.8)),
            ModelState("stacking_ensemble", "stacking", ModelStatus.VETERAN, 0.88, _states(2.2)),
            ModelState("residual_guard", "residual", ModelStatus.LIVE, 0.69, _states(1.7)),
            ModelState("offline_anchor", "offline", ModelStatus.LIVE, 0.66, _states(1.6)),
        )
    )


def _states(base: float) -> dict[str, float]:
    return {"trend": base, "range": base * 0.88, "high_vol": base * 0.76}


def _allocate_weights(models: tuple[ModelState, ...]) -> tuple[ModelState, ...]:
    active = [model for model in models if model.status in {ModelStatus.LIVE, ModelStatus.VETERAN}]
    total = sum((Decimal(str(model.validation_score)) for model in active), ZERO)
    if total == ZERO:
        return models
    allocated = ZERO
    weighted: list[ModelState] = []
    active_ids = [model.model_id for model in active]
    for model in models:
        if model.model_id not in active_ids:
            weighted.append(model)
            continue
        if model.model_id == active_ids[-1]:
            weight = ONE - allocated
        else:
            weight = Decimal(str(model.validation_score)) / total
            allocated += weight
        weighted.append(
            ModelState(
                model.model_id,
                model.family,
                model.status,
                model.validation_score,
                model.sharpe_by_state,
                weight,
            )
        )
    return tuple(weighted)
