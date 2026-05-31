from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_signals.validation import FactorValidationReport, _pearson

ZERO = Decimal("0")
ONE = Decimal("1")


class FactorRaceState(StrEnum):
    POOL = "Pool"
    SHADOW = "Shadow"
    LIVE = "Live"
    VETERAN = "Veteran"


@dataclass(frozen=True, slots=True)
class FactorRaceConfig:
    min_live_factors: int = 50
    shadow_size: int = 20
    veteran_score: float = 0.85
    homogeneous_correlation: float = 0.85


@dataclass(frozen=True, slots=True)
class FactorRaceEntry:
    factor_name: str
    state: FactorRaceState
    validation_score: float
    ic: float
    ir: float
    weight: Decimal = ZERO


@dataclass(frozen=True, slots=True)
class ThompsonObservation:
    factor_name: str
    successes: int
    failures: int


@dataclass(frozen=True, slots=True)
class FactorRaceResult:
    entries: tuple[FactorRaceEntry, ...]

    @property
    def live_count(self) -> int:
        return sum(1 for entry in self.entries if entry.state == FactorRaceState.LIVE)

    @property
    def veteran_count(self) -> int:
        return sum(1 for entry in self.entries if entry.state == FactorRaceState.VETERAN)


def promote_factors(
    reports: tuple[FactorValidationReport, ...],
    *,
    config: FactorRaceConfig | None = None,
) -> FactorRaceResult:
    active_config = config or FactorRaceConfig()
    ranked = sorted(
        (report for report in reports if report.passed),
        key=lambda report: (report.score, report.expression.name),
        reverse=True,
    )
    entries: list[FactorRaceEntry] = []
    for index, report in enumerate(ranked):
        if index < active_config.min_live_factors:
            state = FactorRaceState.LIVE
        elif report.score >= active_config.veteran_score:
            state = FactorRaceState.VETERAN
        elif index < active_config.min_live_factors + active_config.shadow_size:
            state = FactorRaceState.SHADOW
        else:
            state = FactorRaceState.POOL
        entries.append(
            FactorRaceEntry(
                factor_name=report.expression.name,
                state=state,
                validation_score=report.score,
                ic=report.ic,
                ir=report.ir,
            )
        )
    return FactorRaceResult(entries=tuple(entries))


def merge_homogeneous_reports(
    reports: tuple[FactorValidationReport, ...],
    *,
    threshold: float = 0.85,
) -> tuple[FactorValidationReport, ...]:
    kept: list[FactorValidationReport] = []
    for report in sorted(reports, key=lambda item: item.score, reverse=True):
        if not report.passed:
            continue
        is_duplicate = False
        for existing in kept:
            shared = min(len(report.value_vector), len(existing.value_vector))
            similarity = abs(_pearson(report.value_vector[:shared], existing.value_vector[:shared]))
            if similarity > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(report)
    return tuple(kept)


def allocate_thompson_weights(
    entries: tuple[FactorRaceEntry, ...],
    observations: tuple[ThompsonObservation, ...] = (),
    *,
    capital: Decimal = ONE,
) -> tuple[FactorRaceEntry, ...]:
    observation_by_name = {observation.factor_name: observation for observation in observations}
    active_entries = [
        entry for entry in entries if entry.state in {FactorRaceState.LIVE, FactorRaceState.VETERAN}
    ]
    if not active_entries:
        return entries

    scores: dict[str, Decimal] = {}
    for entry in active_entries:
        observation = observation_by_name.get(entry.factor_name)
        if observation is None:
            posterior_mean = Decimal("0.50")
        else:
            posterior_mean = Decimal(observation.successes + 1) / Decimal(
                observation.successes + observation.failures + 2
            )
        validation_boost = Decimal(str(max(entry.validation_score, 0.01)))
        scores[entry.factor_name] = posterior_mean * validation_boost

    total = sum(scores.values(), ZERO)
    if total == ZERO:
        equal_weight = capital / Decimal(len(active_entries))
        scores = {entry.factor_name: equal_weight for entry in active_entries}
        total = capital

    active_names = [entry.factor_name for entry in active_entries]
    allocated = ZERO
    weighted: list[FactorRaceEntry] = []
    for entry in entries:
        if entry.factor_name in scores:
            if entry.factor_name == active_names[-1]:
                weight = capital - allocated
            else:
                weight = (scores[entry.factor_name] / total) * capital
                allocated += weight
            weighted.append(
                FactorRaceEntry(
                    factor_name=entry.factor_name,
                    state=entry.state,
                    validation_score=entry.validation_score,
                    ic=entry.ic,
                    ir=entry.ir,
                    weight=weight,
                )
            )
        else:
            weighted.append(entry)
    return tuple(weighted)
