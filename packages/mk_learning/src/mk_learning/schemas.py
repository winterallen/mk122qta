from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OnlineTrainingExample:
    trade_date: str
    features: dict[str, float]
    label: float
    market_state: str = "unknown"


@dataclass(frozen=True, slots=True)
class ModelPrediction:
    model_id: str
    trade_date: str
    value: float
    confidence: float
