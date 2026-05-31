from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_signals import DEFAULT_SEED_FACTORS, calculate_factor_values, score_bars


def make_bar(symbol: str, trade_date: str, close: str, volume: str) -> DailyBar:
    amount = Decimal(close) * Decimal(volume)
    return DailyBar.model_validate(
        {
            "ts_code": symbol,
            "trade_date": trade_date,
            "open": close,
            "high": str(Decimal(close) * Decimal("1.01")),
            "low": str(Decimal(close) * Decimal("0.99")),
            "close": close,
            "pre_close": close,
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": volume,
            "amount": str(amount),
        }
    )


def test_seed_factor_catalog_has_ten_factors() -> None:
    assert len(DEFAULT_SEED_FACTORS) == 10
    assert {factor.name for factor in DEFAULT_SEED_FACTORS} >= {
        "momentum_1d",
        "momentum_3d",
        "quality_proxy",
        "value_proxy",
    }


def test_score_bars_ranks_momentum_and_liquidity_leader_first() -> None:
    bars = (
        make_bar("000001.SZ", "20240102", "10.00", "1000"),
        make_bar("000001.SZ", "20240103", "10.40", "1300"),
        make_bar("000001.SZ", "20240104", "10.90", "1600"),
        make_bar("000001.SZ", "20240105", "11.50", "2200"),
        make_bar("000002.SZ", "20240102", "10.00", "1000"),
        make_bar("000002.SZ", "20240103", "9.90", "900"),
        make_bar("000002.SZ", "20240104", "9.70", "850"),
        make_bar("000002.SZ", "20240105", "9.40", "800"),
        make_bar("000003.SZ", "20240102", "10.00", "1000"),
        make_bar("000003.SZ", "20240103", "10.00", "1000"),
        make_bar("000003.SZ", "20240104", "10.00", "1000"),
        make_bar("000003.SZ", "20240105", "10.00", "1000"),
    )

    factor_values = calculate_factor_values(bars)
    scores = score_bars(bars)

    assert len(factor_values) == 30
    assert scores[0].ts_code == "000001.SZ"
    assert scores[0].score > scores[-1].score
