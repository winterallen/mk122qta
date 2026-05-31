from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_signals import (
    FactorRaceState,
    ThompsonObservation,
    allocate_thompson_weights,
    generate_candidate_expressions,
    merge_homogeneous_reports,
    promote_factors,
    run_validation_pipeline,
)


def make_bar(symbol: str, trade_date: str, close: Decimal, volume: Decimal) -> DailyBar:
    return DailyBar.model_validate(
        {
            "ts_code": symbol,
            "trade_date": trade_date,
            "open": str(close),
            "high": str(close * Decimal("1.01")),
            "low": str(close * Decimal("0.99")),
            "close": str(close),
            "pre_close": str(close),
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": str(volume),
            "amount": str(close * volume),
        }
    )


def sample_bars() -> tuple[DailyBar, ...]:
    bars: list[DailyBar] = []
    profiles = {
        "000001.SZ": (Decimal("1.020"), Decimal("90")),
        "000002.SZ": (Decimal("1.005"), Decimal("10")),
        "000003.SZ": (Decimal("0.997"), Decimal("-10")),
        "000004.SZ": (Decimal("0.990"), Decimal("-25")),
    }
    for index in range(20):
        trade_date = f"202401{index + 2:02d}"
        for symbol, (growth, volume_step) in profiles.items():
            bars.append(
                make_bar(
                    symbol,
                    trade_date,
                    Decimal("10.00") * (growth**index),
                    Decimal("1000") + volume_step * Decimal(index),
                )
            )
    return tuple(bars)


def test_validation_pipeline_runs_six_stages_and_promotes_live_factors() -> None:
    expressions = generate_candidate_expressions(limit=90)
    reports = run_validation_pipeline(expressions, sample_bars())
    race = promote_factors(reports)

    assert {stage.stage for stage in reports[0].stages} == {
        stage.stage for stage in reports[-1].stages
    }
    assert len(reports[0].stages) == 6
    assert sum(1 for report in reports if report.passed) >= 50
    assert race.live_count == 50


def test_homogeneous_merge_and_thompson_weights() -> None:
    reports = run_validation_pipeline(generate_candidate_expressions(limit=90), sample_bars())
    merged = merge_homogeneous_reports(reports, threshold=0.85)
    race = promote_factors(reports)
    weighted = allocate_thompson_weights(
        race.entries,
        (
            ThompsonObservation(race.entries[0].factor_name, successes=8, failures=2),
            ThompsonObservation(race.entries[1].factor_name, successes=4, failures=3),
        ),
    )
    live_weights = [
        entry.weight
        for entry in weighted
        if entry.state in {FactorRaceState.LIVE, FactorRaceState.VETERAN}
    ]

    assert len(merged) < sum(1 for report in reports if report.passed)
    assert sum(live_weights, Decimal("0")) == Decimal("1.000000000000000000000000000")
