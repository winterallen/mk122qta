from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GradientSafetyPolicy:
    max_gradient_norm: float = 5.0
    max_abs_feature: float = 100.0
    max_abs_error: float = 10.0
    min_direction_cosine: float = -0.95
    cooldown_updates: int = 1
    max_prediction_jump: float = 5.0

    @property
    def guardrail_count(self) -> int:
        return 6


@dataclass(frozen=True, slots=True)
class GradientSafetyResult:
    accepted: bool
    reason: str
    gradient_norm: float


class GradientSafetyMonitor:
    def __init__(self) -> None:
        self.total_updates = 0
        self.discarded_updates = 0
        self._cooldown_left = 0
        self._last_gradient: dict[str, float] | None = None

    @property
    def discard_rate(self) -> float:
        if self.total_updates == 0:
            return 0.0
        return self.discarded_updates / self.total_updates

    def evaluate(
        self,
        gradient: dict[str, float],
        *,
        error: float,
        policy: GradientSafetyPolicy,
    ) -> GradientSafetyResult:
        self.total_updates += 1
        norm = math.sqrt(sum(value * value for value in gradient.values()))
        reason = self._reject_reason(gradient, error, norm, policy)
        if reason is not None:
            self.discarded_updates += 1
            self._cooldown_left = policy.cooldown_updates
            return GradientSafetyResult(False, reason, norm)
        if self._cooldown_left > 0:
            self.discarded_updates += 1
            self._cooldown_left -= 1
            return GradientSafetyResult(False, "cooldown", norm)

        self._last_gradient = dict(gradient)
        return GradientSafetyResult(True, "accepted", norm)

    def _reject_reason(
        self,
        gradient: dict[str, float],
        error: float,
        norm: float,
        policy: GradientSafetyPolicy,
    ) -> str | None:
        if any(abs(value) > policy.max_abs_feature for value in gradient.values()):
            return "feature_or_gradient_outlier"
        if abs(error) > policy.max_abs_error:
            return "loss_outlier"
        if norm > policy.max_gradient_norm:
            return "norm_clipped"
        if self._last_gradient is not None:
            cosine = _cosine(self._last_gradient, gradient)
            if cosine < policy.min_direction_cosine:
                return "opposite_direction"
        return None


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    numerator = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
    left_norm = math.sqrt(sum(left.get(key, 0.0) ** 2 for key in keys))
    right_norm = math.sqrt(sum(right.get(key, 0.0) ** 2 for key in keys))
    if left_norm == 0.0 or right_norm == 0.0:
        return 1.0
    return numerator / (left_norm * right_norm)
