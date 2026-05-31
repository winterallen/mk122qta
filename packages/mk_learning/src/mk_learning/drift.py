from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class DriftKind(StrEnum):
    PSI = "psi"
    KS = "ks"
    WASSERSTEIN = "wasserstein"
    RESIDUAL = "residual"
    IMPORTANCE = "importance"


@dataclass(frozen=True, slots=True)
class DriftCheckResult:
    kind: DriftKind
    score: float
    threshold: float
    drifted: bool


@dataclass(frozen=True, slots=True)
class DriftReport:
    trade_date: str
    checks: tuple[DriftCheckResult, ...]

    @property
    def drifted(self) -> bool:
        return any(check.drifted for check in self.checks)


@dataclass(frozen=True, slots=True)
class KnownDriftScenario:
    name: str
    expected_drifted: bool
    reference: tuple[float, ...]
    current: tuple[float, ...]
    reference_residuals: tuple[float, ...]
    current_residuals: tuple[float, ...]
    reference_importance: tuple[float, ...]
    current_importance: tuple[float, ...]


def detect_drift(
    *,
    trade_date: str,
    reference: tuple[float, ...],
    current: tuple[float, ...],
    reference_residuals: tuple[float, ...] = (),
    current_residuals: tuple[float, ...] = (),
    reference_importance: tuple[float, ...] = (),
    current_importance: tuple[float, ...] = (),
) -> DriftReport:
    checks = (
        _check(DriftKind.PSI, _psi(reference, current), 0.25),
        _check(DriftKind.KS, _ks(reference, current), 0.25),
        _check(DriftKind.WASSERSTEIN, _wasserstein(reference, current), 0.20),
        _check(
            DriftKind.RESIDUAL,
            abs(_mean(current_residuals) - _mean(reference_residuals)),
            0.15,
        ),
        _check(
            DriftKind.IMPORTANCE,
            _wasserstein(reference_importance, current_importance),
            0.20,
        ),
    )
    return DriftReport(trade_date=trade_date, checks=checks)


def evaluate_known_drift_accuracy(scenarios: tuple[KnownDriftScenario, ...]) -> float:
    if not scenarios:
        return 0.0
    correct = 0
    for scenario in scenarios:
        report = detect_drift(
            trade_date="20240131",
            reference=scenario.reference,
            current=scenario.current,
            reference_residuals=scenario.reference_residuals,
            current_residuals=scenario.current_residuals,
            reference_importance=scenario.reference_importance,
            current_importance=scenario.current_importance,
        )
        if report.drifted == scenario.expected_drifted:
            correct += 1
    return correct / len(scenarios)


def _check(kind: DriftKind, score: float, threshold: float) -> DriftCheckResult:
    return DriftCheckResult(kind=kind, score=score, threshold=threshold, drifted=score >= threshold)


def _mean(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _psi(reference: tuple[float, ...], current: tuple[float, ...], bins: int = 10) -> float:
    if not reference or not current:
        return 0.0
    low = min(min(reference), min(current))
    high = max(max(reference), max(current))
    if high == low:
        return 0.0
    width = (high - low) / bins
    total = 0.0
    for index in range(bins):
        lower = low + width * index
        upper = low + width * (index + 1)
        ref_ratio = _bucket_ratio(reference, lower, upper, index == bins - 1)
        cur_ratio = _bucket_ratio(current, lower, upper, index == bins - 1)
        total += (cur_ratio - ref_ratio) * math.log(cur_ratio / ref_ratio)
    return total


def _bucket_ratio(
    values: tuple[float, ...], lower: float, upper: float, include_upper: bool
) -> float:
    count = 0
    for value in values:
        in_closed_bucket = include_upper and lower <= value <= upper
        in_half_open_bucket = not include_upper and lower <= value < upper
        if in_closed_bucket or in_half_open_bucket:
            count += 1
    return max(count / len(values), 0.0001)


def _ks(reference: tuple[float, ...], current: tuple[float, ...]) -> float:
    if not reference or not current:
        return 0.0
    points = sorted(set(reference) | set(current))
    return max(abs(_cdf(reference, point) - _cdf(current, point)) for point in points)


def _cdf(values: tuple[float, ...], point: float) -> float:
    return sum(1 for value in values if value <= point) / len(values)


def _wasserstein(reference: tuple[float, ...], current: tuple[float, ...]) -> float:
    if not reference or not current:
        return 0.0
    shared = min(len(reference), len(current))
    left = sorted(reference)[:shared]
    right = sorted(current)[:shared]
    return sum(abs(a - b) for a, b in zip(left, right, strict=True)) / shared
