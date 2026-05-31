from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_data.schemas import DailyBar

from mk_signals.factors import SeedFactor

ZERO = Decimal("0")
ONE = Decimal("1")


class FactorOperator(StrEnum):
    MOMENTUM = "momentum"
    REVERSAL = "reversal"
    ROLLING_MEAN = "rolling_mean"
    ROLLING_SLOPE = "rolling_slope"
    VOLATILITY = "volatility"
    VOLUME_TREND = "volume_trend"
    AMOUNT_TREND = "amount_trend"
    RANGE_POSITION = "range_position"
    CLOSE_TO_HIGH = "close_to_high"
    LIQUIDITY_SHOCK = "liquidity_shock"
    PRICE_VOLUME = "price_volume"
    QUALITY_INTRADAY = "quality_intraday"


@dataclass(frozen=True, slots=True)
class FactorExpression:
    name: str
    operator: FactorOperator
    field: str
    window: int
    depth: int = 1

    @property
    def dsl(self) -> str:
        return f"{self.operator.value}({self.field},{self.window})"


def parse_factor_expression(text: str) -> FactorExpression:
    operator_text, separator, tail = text.strip().partition("(")
    if separator != "(" or not tail.endswith(")"):
        raise ValueError("factor expression must look like operator(field,window)")

    args = [item.strip() for item in tail[:-1].split(",")]
    if len(args) != 2:
        raise ValueError("factor expression requires field and window")

    operator = FactorOperator(operator_text)
    field = args[0]
    window = int(args[1])
    if window <= 0:
        raise ValueError("window must be positive")

    return FactorExpression(
        name=f"{operator.value}_{field}_{window}",
        operator=operator,
        field=field,
        window=window,
    )


def generate_candidate_expressions(
    *,
    windows: tuple[int, ...] = (1, 2, 3, 5, 8),
    fields: tuple[str, ...] = ("close", "high", "low", "volume", "amount"),
    max_depth: int = 4,
    limit: int = 1000,
) -> tuple[FactorExpression, ...]:
    expressions: list[FactorExpression] = []
    for operator in FactorOperator:
        for field in fields:
            for window in windows:
                if len(expressions) >= limit:
                    return tuple(expressions)
                expression = FactorExpression(
                    name=f"{operator.value}_{field}_{window}",
                    operator=operator,
                    field=field,
                    window=window,
                    depth=min(max_depth, 2 if operator == FactorOperator.PRICE_VOLUME else 1),
                )
                expressions.append(expression)
    return tuple(expressions)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return numerator / denominator


def _mean(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return sum(collected, ZERO) / Decimal(len(collected))


def _field_value(bar: DailyBar, field: str) -> Decimal:
    if field == "volume":
        return bar.volume
    value = getattr(bar, field)
    if not isinstance(value, Decimal):
        raise TypeError(f"unsupported factor field: {field}")
    return value


def _ordered(bars: tuple[DailyBar, ...]) -> tuple[DailyBar, ...]:
    return tuple(sorted(bars, key=lambda bar: bar.trade_date))


def _window_values(bars: tuple[DailyBar, ...], field: str, window: int) -> tuple[Decimal, ...]:
    ordered = _ordered(bars)
    return tuple(_field_value(bar, field) for bar in ordered[-window:])


def evaluate_expression(expression: FactorExpression, bars: tuple[DailyBar, ...]) -> Decimal:
    if not bars:
        return ZERO

    ordered = _ordered(bars)
    latest = ordered[-1]
    values = _window_values(ordered, expression.field, max(1, expression.window))
    current_value = _field_value(latest, expression.field)
    reference = values[0]

    if expression.operator == FactorOperator.MOMENTUM:
        return _safe_ratio(current_value - reference, reference)
    if expression.operator == FactorOperator.REVERSAL:
        return -_safe_ratio(current_value - reference, reference)
    if expression.operator == FactorOperator.ROLLING_MEAN:
        return _safe_ratio(_mean(values) - current_value, current_value)
    if expression.operator == FactorOperator.ROLLING_SLOPE:
        return _safe_ratio(values[-1] - values[0], Decimal(max(1, len(values) - 1)) * values[0])
    if expression.operator == FactorOperator.VOLATILITY:
        returns = [
            abs(_safe_ratio(values[index] - values[index - 1], values[index - 1]))
            for index in range(1, len(values))
        ]
        return -_mean(returns)
    if expression.operator == FactorOperator.VOLUME_TREND:
        previous = tuple(bar.volume for bar in ordered[-expression.window - 1 : -1])
        return _safe_ratio(latest.volume - _mean(previous), _mean(previous))
    if expression.operator == FactorOperator.AMOUNT_TREND:
        previous = tuple(bar.amount for bar in ordered[-expression.window - 1 : -1])
        return _safe_ratio(latest.amount - _mean(previous), _mean(previous))
    if expression.operator == FactorOperator.RANGE_POSITION:
        return _safe_ratio(latest.close - latest.low, latest.high - latest.low)
    if expression.operator == FactorOperator.CLOSE_TO_HIGH:
        return _safe_ratio(latest.close, latest.high)
    if expression.operator == FactorOperator.LIQUIDITY_SHOCK:
        previous = tuple(bar.amount for bar in ordered[-expression.window - 1 : -1])
        return _safe_ratio(latest.amount - _mean(previous), _mean(previous))
    if expression.operator == FactorOperator.PRICE_VOLUME:
        price = _safe_ratio(
            latest.close - ordered[-min(len(ordered), expression.window)].close, latest.close
        )
        volume = evaluate_expression(
            FactorExpression(
                "volume_trend", FactorOperator.VOLUME_TREND, "volume", expression.window
            ),
            ordered,
        )
        return price * (ONE + volume)
    if expression.operator == FactorOperator.QUALITY_INTRADAY:
        return _safe_ratio(latest.close - latest.low, latest.high - latest.low)

    raise ValueError(f"unsupported factor operator: {expression.operator}")


def expression_to_seed_factor(
    expression: FactorExpression,
    *,
    weight: Decimal = ONE,
) -> SeedFactor:
    return SeedFactor(
        name=expression.name,
        weight=weight,
        calculator=lambda bars: evaluate_expression(expression, bars),
    )
