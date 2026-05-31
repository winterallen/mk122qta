from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_risk import RiskBudget, RiskGateState
from mk_signals import DEFAULT_SEED_FACTORS, score_bars
from mk_simulation import run_single_strategy_simulation
from mk_strategies import MultiFactorAlphaStrategyActor, StrategyConfig


def make_bar(symbol: str, trade_date: str, close: Decimal, volume: Decimal) -> DailyBar:
    amount = close * volume
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
            "amount": str(amount),
        }
    )


def p1_sample_bars() -> list[DailyBar]:
    bars: list[DailyBar] = []
    for index in range(10):
        trade_date = f"202401{index + 2:02d}"
        bars.append(
            make_bar(
                "000001.SZ",
                trade_date,
                Decimal("10.00") * (Decimal("1.02") ** index),
                Decimal("1000") + Decimal(index * 120),
            )
        )
        bars.append(
            make_bar(
                "000002.SZ",
                trade_date,
                Decimal("10.00") * (Decimal("0.995") ** index),
                Decimal("1000") - Decimal(index * 20),
            )
        )
        bars.append(
            make_bar(
                "000003.SZ",
                trade_date,
                Decimal("10.00") * (Decimal("1.001") ** index),
                Decimal("1000"),
            )
        )
    return bars


def test_p1_single_strategy_flow_completes_10_days_with_passed_risk_and_sharpe() -> None:
    bars = p1_sample_bars()
    scores = score_bars(bars)
    strategy_config = StrategyConfig(
        top_n=1,
        target_gross=Decimal("0.90"),
        max_symbol_weight=Decimal("0.90"),
    )
    targets = MultiFactorAlphaStrategyActor(strategy_config).generate_targets(scores)
    report = run_single_strategy_simulation(
        bars,
        strategy_config=strategy_config,
        risk_budget=RiskBudget(
            max_symbol_weight=Decimal("0.95"),
            max_order_notional=Decimal("2000000"),
            max_daily_turnover=Decimal("2.00"),
            min_cash_buffer=Decimal("0.00"),
        ),
    )

    assert len(DEFAULT_SEED_FACTORS) == 10
    assert targets[0].ts_code == "000001.SZ"
    assert report.trading_days == 10
    assert report.sharpe > 1
    assert {decision.state for decision in report.risk_decisions} == {RiskGateState.PASS}
    assert report.reconciliation.matched
    assert report.strategy_ledger.fills_seen > 0
