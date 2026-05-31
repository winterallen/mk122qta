from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_risk import RiskBudget, RiskGateState
from mk_signals import (
    FactorRaceState,
    generate_candidate_expressions,
    promote_factors,
    reports_to_seed_factors,
    run_validation_pipeline,
)
from mk_simulation import run_single_strategy_simulation
from mk_strategies import StrategyConfig


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


def p2_sample_bars() -> tuple[DailyBar, ...]:
    bars: list[DailyBar] = []
    profiles = {
        "000001.SZ": (Decimal("1.020"), Decimal("110")),
        "000002.SZ": (Decimal("1.006"), Decimal("35")),
        "000003.SZ": (Decimal("0.999"), Decimal("-5")),
        "000004.SZ": (Decimal("0.992"), Decimal("-30")),
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


def test_p2_factor_racing_produces_50_live_factors_and_keeps_strategy_sharpe() -> None:
    bars = p2_sample_bars()
    strategy_config = StrategyConfig(
        top_n=1,
        target_gross=Decimal("0.90"),
        max_symbol_weight=Decimal("0.90"),
    )
    risk_budget = RiskBudget(
        max_symbol_weight=Decimal("0.95"),
        max_order_notional=Decimal("2000000"),
        max_daily_turnover=Decimal("2.00"),
        min_cash_buffer=Decimal("0.00"),
    )
    baseline = run_single_strategy_simulation(
        bars,
        strategy_config=strategy_config,
        risk_budget=risk_budget,
    )
    reports = run_validation_pipeline(generate_candidate_expressions(limit=120), bars)
    race = promote_factors(reports)
    live_factors = reports_to_seed_factors(reports, limit=50)
    raced = run_single_strategy_simulation(
        bars,
        strategy_config=strategy_config,
        risk_budget=risk_budget,
        factors=live_factors,
    )

    assert len(live_factors) == 50
    assert race.live_count == 50
    assert {entry.state for entry in race.entries[:50]} == {FactorRaceState.LIVE}
    assert raced.sharpe >= baseline.sharpe
    assert {decision.state for decision in raced.risk_decisions} == {RiskGateState.PASS}
    assert raced.reconciliation.matched
