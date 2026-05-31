from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_data.schemas import DailyBar

from mk_signals.expressions import FactorExpression, evaluate_expression, expression_to_seed_factor
from mk_signals.factors import SeedFactor

ZERO = Decimal("0")


class ValidationStage(StrEnum):
    BASIC = "basic"
    SINGLE_FACTOR = "single_factor"
    STABILITY = "stability"
    CORRELATION = "correlation"
    OVERFIT = "overfit"
    COST = "cost"


@dataclass(frozen=True, slots=True)
class ValidationStageResult:
    stage: ValidationStage
    passed: bool
    metric: float
    threshold: float


@dataclass(frozen=True, slots=True)
class FactorValidationReport:
    expression: FactorExpression
    stages: tuple[ValidationStageResult, ...]
    ic: float
    ir: float
    max_abs_correlation: float
    turnover_proxy: float
    observations: int
    value_vector: tuple[float, ...]

    @property
    def passed(self) -> bool:
        return all(stage.passed for stage in self.stages)

    @property
    def score(self) -> float:
        stability_bonus = min(abs(self.ir), 5.0) / 10.0
        return abs(self.ic) + stability_bonus


@dataclass(frozen=True, slots=True)
class FactorValidationConfig:
    min_observations: int = 12
    min_abs_ic: float = 0.001
    min_abs_ir: float = 0.0
    max_abs_correlation: float = 1.0
    max_turnover_proxy: float = 5.0


def _pearson(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return 0.0
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right, strict=True))
    left_var = sum((x - left_mean) ** 2 for x in left)
    right_var = sum((y - right_mean) ** 2 for y in right)
    denominator = math.sqrt(left_var * right_var)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _bars_by_symbol(bars: tuple[DailyBar, ...]) -> dict[str, tuple[DailyBar, ...]]:
    grouped: defaultdict[str, list[DailyBar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.ts_code].append(bar)
    return {
        symbol: tuple(sorted(symbol_bars, key=lambda item: item.trade_date))
        for symbol, symbol_bars in grouped.items()
    }


def _safe_forward_return(current: DailyBar, next_bar: DailyBar) -> float:
    if current.close == ZERO:
        return 0.0
    return float((next_bar.close - current.close) / current.close)


def _evaluate_series(
    expression: FactorExpression,
    bars: tuple[DailyBar, ...],
) -> tuple[tuple[str, float, float], ...]:
    rows: list[tuple[str, float, float]] = []
    for symbol_bars in _bars_by_symbol(bars).values():
        for index in range(len(symbol_bars) - 1):
            history = symbol_bars[: index + 1]
            value = float(evaluate_expression(expression, history))
            forward_return = _safe_forward_return(symbol_bars[index], symbol_bars[index + 1])
            rows.append((symbol_bars[index].trade_date_yyyymmdd, value, forward_return))
    return tuple(rows)


def _daily_ic(rows: tuple[tuple[str, float, float], ...]) -> tuple[float, ...]:
    grouped: defaultdict[str, list[tuple[float, float]]] = defaultdict(list)
    for trade_date, value, forward_return in rows:
        grouped[trade_date].append((value, forward_return))

    correlations: list[float] = []
    for pairs in grouped.values():
        if len(pairs) < 2:
            continue
        values = tuple(pair[0] for pair in pairs)
        returns = tuple(pair[1] for pair in pairs)
        correlations.append(_pearson(values, returns))
    return tuple(correlations)


def _mean(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: tuple[float, ...]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _stage(
    stage: ValidationStage,
    passed: bool,
    metric: float,
    threshold: float,
) -> ValidationStageResult:
    return ValidationStageResult(stage=stage, passed=passed, metric=metric, threshold=threshold)


def run_validation_pipeline(
    expressions: tuple[FactorExpression, ...],
    bars: tuple[DailyBar, ...],
    *,
    config: FactorValidationConfig | None = None,
) -> tuple[FactorValidationReport, ...]:
    active_config = config or FactorValidationConfig()
    reports: list[FactorValidationReport] = []
    vectors: dict[str, tuple[float, ...]] = {}

    for expression in expressions:
        rows = _evaluate_series(expression, bars)
        value_vector = tuple(row[1] for row in rows)
        daily_ic = _daily_ic(rows)
        ic = _mean(daily_ic)
        ic_std = _std(daily_ic)
        ir = 0.0 if ic_std == 0.0 else ic / ic_std
        turnover_proxy = _std(value_vector)

        max_abs_correlation = 0.0
        for previous_vector in vectors.values():
            shared = min(len(previous_vector), len(value_vector))
            max_abs_correlation = max(
                max_abs_correlation,
                abs(_pearson(previous_vector[:shared], value_vector[:shared])),
            )
        vectors[expression.name] = value_vector

        stages = (
            _stage(
                ValidationStage.BASIC,
                len(value_vector) >= active_config.min_observations and len(set(value_vector)) > 1,
                float(len(value_vector)),
                float(active_config.min_observations),
            ),
            _stage(
                ValidationStage.SINGLE_FACTOR,
                abs(ic) >= active_config.min_abs_ic,
                abs(ic),
                active_config.min_abs_ic,
            ),
            _stage(
                ValidationStage.STABILITY,
                abs(ir) >= active_config.min_abs_ir and len(daily_ic) >= 2,
                abs(ir),
                active_config.min_abs_ir,
            ),
            _stage(
                ValidationStage.CORRELATION,
                max_abs_correlation <= active_config.max_abs_correlation,
                max_abs_correlation,
                active_config.max_abs_correlation,
            ),
            _stage(
                ValidationStage.OVERFIT,
                len(value_vector) >= active_config.min_observations,
                float(len(value_vector)),
                float(active_config.min_observations),
            ),
            _stage(
                ValidationStage.COST,
                turnover_proxy <= active_config.max_turnover_proxy,
                turnover_proxy,
                active_config.max_turnover_proxy,
            ),
        )
        reports.append(
            FactorValidationReport(
                expression=expression,
                stages=stages,
                ic=ic,
                ir=ir,
                max_abs_correlation=max_abs_correlation,
                turnover_proxy=turnover_proxy,
                observations=len(value_vector),
                value_vector=value_vector,
            )
        )
    return tuple(reports)


def reports_to_seed_factors(
    reports: tuple[FactorValidationReport, ...],
    *,
    limit: int = 50,
) -> tuple[SeedFactor, ...]:
    selected = sorted(
        (report for report in reports if report.passed),
        key=lambda report: (report.score, report.expression.name),
        reverse=True,
    )[:limit]
    return tuple(
        expression_to_seed_factor(
            report.expression,
            weight=Decimal("1") if report.ic >= 0 else Decimal("-1"),
        )
        for report in selected
    )
