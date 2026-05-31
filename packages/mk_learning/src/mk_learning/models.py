from __future__ import annotations

import math
from dataclasses import dataclass

from mk_learning.safety import GradientSafetyMonitor, GradientSafetyPolicy
from mk_learning.schemas import ModelPrediction, OnlineTrainingExample


@dataclass(frozen=True, slots=True)
class TrainingReport:
    model_id: str
    trade_date: str
    examples_seen: int
    updated_count: int
    discarded_count: int
    discard_rate: float
    daily_complete: bool


class OnlineLinearModel:
    def __init__(self, model_id: str, *, learning_rate: float = 0.05) -> None:
        self.model_id = model_id
        self.learning_rate = learning_rate
        self.weights: dict[str, float] = {}
        self.bias = 0.0

    def predict_value(self, features: dict[str, float]) -> float:
        return self.bias + sum(
            self.weights.get(key, 0.0) * value for key, value in features.items()
        )

    def predict(self, example: OnlineTrainingExample) -> ModelPrediction:
        value = self.predict_value(example.features)
        return ModelPrediction(self.model_id, example.trade_date, value, confidence=1.0)

    def partial_fit(
        self,
        examples: tuple[OnlineTrainingExample, ...],
        *,
        safety_monitor: GradientSafetyMonitor | None = None,
        policy: GradientSafetyPolicy | None = None,
    ) -> TrainingReport:
        monitor = safety_monitor or GradientSafetyMonitor()
        active_policy = policy or GradientSafetyPolicy()
        updated = 0
        for example in examples:
            prediction = self.predict_value(example.features)
            error = prediction - example.label
            gradient = {key: error * value for key, value in example.features.items()}
            decision = monitor.evaluate(gradient, error=error, policy=active_policy)
            if not decision.accepted:
                continue
            for key, value in gradient.items():
                self.weights[key] = self.weights.get(key, 0.0) - self.learning_rate * value
            self.bias -= self.learning_rate * error
            updated += 1
        return TrainingReport(
            model_id=self.model_id,
            trade_date=examples[-1].trade_date if examples else "19700101",
            examples_seen=len(examples),
            updated_count=updated,
            discarded_count=monitor.discarded_updates,
            discard_rate=monitor.discard_rate,
            daily_complete=updated > 0,
        )


class FTRLLinearModel:
    def __init__(
        self,
        model_id: str = "ftrl_baseline",
        *,
        alpha: float = 0.1,
        beta: float = 1.0,
        l1: float = 0.0,
        l2: float = 1.0,
    ) -> None:
        self.model_id = model_id
        self.alpha = alpha
        self.beta = beta
        self.l1 = l1
        self.l2 = l2
        self.z: dict[str, float] = {}
        self.n: dict[str, float] = {}
        self.bias = 0.0

    def _weight(self, key: str) -> float:
        z_value = self.z.get(key, 0.0)
        if abs(z_value) <= self.l1:
            return 0.0
        sign = 1.0 if z_value >= 0.0 else -1.0
        return -(z_value - sign * self.l1) / (
            (self.beta + math.sqrt(self.n.get(key, 0.0))) / self.alpha + self.l2
        )

    def predict_value(self, features: dict[str, float]) -> float:
        return self.bias + sum(self._weight(key) * value for key, value in features.items())

    def partial_fit(self, examples: tuple[OnlineTrainingExample, ...]) -> TrainingReport:
        updated = 0
        for example in examples:
            prediction = self.predict_value(example.features)
            error = prediction - example.label
            for key, value in example.features.items():
                gradient = error * value
                old_n = self.n.get(key, 0.0)
                sigma = (math.sqrt(old_n + gradient * gradient) - math.sqrt(old_n)) / self.alpha
                self.z[key] = self.z.get(key, 0.0) + gradient - sigma * self._weight(key)
                self.n[key] = old_n + gradient * gradient
            self.bias -= self.alpha * error
            updated += 1
        return TrainingReport(
            model_id=self.model_id,
            trade_date=examples[-1].trade_date if examples else "19700101",
            examples_seen=len(examples),
            updated_count=updated,
            discarded_count=0,
            discard_rate=0.0,
            daily_complete=updated > 0,
        )
