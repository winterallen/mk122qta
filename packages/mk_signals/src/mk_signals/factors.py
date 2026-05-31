from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from mk_data.schemas import DailyBar

ZERO = Decimal("0")
ONE = Decimal("1")

FactorCalculator = Callable[[tuple[DailyBar, ...]], Decimal]


@dataclass(frozen=True, slots=True)
class SeedFactor:
    name: str
    weight: Decimal
    calculator: FactorCalculator


@dataclass(frozen=True, slots=True)
class FactorValue:
    ts_code: str
    trade_date: str
    factor_name: str
    value: Decimal


@dataclass(frozen=True, slots=True)
class CompositeScore:
    ts_code: str
    trade_date: str
    score: Decimal
    raw_factors: Mapping[str, Decimal]
    normalized_factors: Mapping[str, Decimal]


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return numerator / denominator


def _mean(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return sum(collected, ZERO) / Decimal(len(collected))


def _sorted_bars(bars: tuple[DailyBar, ...]) -> tuple[DailyBar, ...]:
    return tuple(sorted(bars, key=lambda bar: bar.trade_date))


def _daily_return(current: DailyBar, previous: DailyBar) -> Decimal:
    return _safe_ratio(current.close - previous.close, previous.close)


def _previous_bar(bars: tuple[DailyBar, ...], offset: int) -> DailyBar:
    if len(bars) > offset:
        return bars[-1 - offset]
    return bars[0]


def momentum_1d(bars: tuple[DailyBar, ...]) -> Decimal:
    ordered = _sorted_bars(bars)
    return _daily_return(ordered[-1], _previous_bar(ordered, 1))


def momentum_3d(bars: tuple[DailyBar, ...]) -> Decimal:
    ordered = _sorted_bars(bars)
    comparison = _previous_bar(ordered, 3)
    return _safe_ratio(ordered[-1].close - comparison.close, comparison.close)


def reversal_1d(bars: tuple[DailyBar, ...]) -> Decimal:
    return -momentum_1d(bars)


def low_volatility_3d(bars: tuple[DailyBar, ...]) -> Decimal:
    ordered = _sorted_bars(bars)
    returns = [
        abs(_daily_return(ordered[index], ordered[index - 1]))
        for index in range(max(1, len(ordered) - 3), len(ordered))
    ]
    return -_mean(returns)


def volume_momentum(bars: tuple[DailyBar, ...]) -> Decimal:
    ordered = _sorted_bars(bars)
    history = ordered[-4:-1]
    average_volume = _mean(bar.volume for bar in history)
    return _safe_ratio(ordered[-1].volume - average_volume, average_volume)


def amount_momentum(bars: tuple[DailyBar, ...]) -> Decimal:
    ordered = _sorted_bars(bars)
    history = ordered[-4:-1]
    average_amount = _mean(bar.amount for bar in history)
    return _safe_ratio(ordered[-1].amount - average_amount, average_amount)


def price_volume_trend(bars: tuple[DailyBar, ...]) -> Decimal:
    volume_boost = ONE + volume_momentum(bars)
    return momentum_1d(bars) * volume_boost


def close_to_high(bars: tuple[DailyBar, ...]) -> Decimal:
    latest = _sorted_bars(bars)[-1]
    return _safe_ratio(latest.close, latest.high)


def intraday_quality_proxy(bars: tuple[DailyBar, ...]) -> Decimal:
    latest = _sorted_bars(bars)[-1]
    day_range = latest.high - latest.low
    return _safe_ratio(latest.close - latest.low, day_range)


def value_reversion_proxy(bars: tuple[DailyBar, ...]) -> Decimal:
    latest = _sorted_bars(bars)[-1]
    return _safe_ratio(latest.pre_close - latest.close, latest.close)


DEFAULT_SEED_FACTORS: tuple[SeedFactor, ...] = (
    SeedFactor("momentum_1d", Decimal("1.00"), momentum_1d),
    SeedFactor("momentum_3d", Decimal("1.00"), momentum_3d),
    SeedFactor("reversal_1d", Decimal("0.35"), reversal_1d),
    SeedFactor("low_volatility_3d", Decimal("0.45"), low_volatility_3d),
    SeedFactor("volume_momentum", Decimal("0.75"), volume_momentum),
    SeedFactor("amount_momentum", Decimal("0.75"), amount_momentum),
    SeedFactor("price_volume_trend", Decimal("0.80"), price_volume_trend),
    SeedFactor("close_to_high", Decimal("0.45"), close_to_high),
    SeedFactor("quality_proxy", Decimal("0.45"), intraday_quality_proxy),
    SeedFactor("value_proxy", Decimal("0.25"), value_reversion_proxy),
)


def _group_by_symbol(bars: Iterable[DailyBar]) -> dict[str, tuple[DailyBar, ...]]:
    grouped: defaultdict[str, list[DailyBar]] = defaultdict(list)
    for bar in bars:
        grouped[bar.ts_code].append(bar)
    return {symbol: _sorted_bars(tuple(symbol_bars)) for symbol, symbol_bars in grouped.items()}


def calculate_factor_values(
    bars: Iterable[DailyBar],
    *,
    factors: tuple[SeedFactor, ...] = DEFAULT_SEED_FACTORS,
) -> tuple[FactorValue, ...]:
    values: list[FactorValue] = []
    for symbol, symbol_bars in _group_by_symbol(bars).items():
        latest = symbol_bars[-1]
        for factor in factors:
            values.append(
                FactorValue(
                    ts_code=symbol,
                    trade_date=latest.trade_date_yyyymmdd,
                    factor_name=factor.name,
                    value=factor.calculator(symbol_bars),
                )
            )
    return tuple(values)


def _normalize(
    raw_by_symbol: Mapping[str, Mapping[str, Decimal]],
    factors: tuple[SeedFactor, ...],
) -> dict[str, dict[str, Decimal]]:
    normalized: dict[str, dict[str, Decimal]] = {symbol: {} for symbol in raw_by_symbol}
    for factor in factors:
        values = {symbol: factors_map[factor.name] for symbol, factors_map in raw_by_symbol.items()}
        mean = _mean(values.values())
        average_deviation = _mean(abs(value - mean) for value in values.values())
        for symbol, value in values.items():
            normalized[symbol][factor.name] = (
                ZERO if average_deviation == ZERO else (value - mean) / average_deviation
            )
    return normalized


def score_bars(
    bars: Iterable[DailyBar],
    *,
    factors: tuple[SeedFactor, ...] = DEFAULT_SEED_FACTORS,
    factor_weights: Mapping[str, Decimal] | None = None,
) -> tuple[CompositeScore, ...]:
    grouped = _group_by_symbol(bars)
    if not grouped:
        return ()

    raw_by_symbol = {
        symbol: {factor.name: factor.calculator(symbol_bars) for factor in factors}
        for symbol, symbol_bars in grouped.items()
    }
    normalized_by_symbol = _normalize(raw_by_symbol, factors)
    weights = {factor.name: factor.weight for factor in factors}
    if factor_weights is not None:
        weights.update(factor_weights)
    weight_total = sum((abs(weights[factor.name]) for factor in factors), ZERO) or ONE

    scores = []
    for symbol, symbol_bars in grouped.items():
        normalized_factors = normalized_by_symbol[symbol]
        score = (
            sum(normalized_factors[factor.name] * weights[factor.name] for factor in factors)
            / weight_total
        )
        scores.append(
            CompositeScore(
                ts_code=symbol,
                trade_date=symbol_bars[-1].trade_date_yyyymmdd,
                score=score,
                raw_factors=raw_by_symbol[symbol],
                normalized_factors=normalized_factors,
            )
        )
    return tuple(sorted(scores, key=lambda item: (item.score, item.ts_code), reverse=True))
