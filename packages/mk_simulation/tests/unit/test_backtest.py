from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_simulation import run_close_to_close_backtest


def sample_record() -> dict[str, str]:
    return {
        "ts_code": "000001.SZ",
        "trade_date": "20240102",
        "open": "9.10",
        "high": "9.40",
        "low": "9.00",
        "close": "9.30",
        "pre_close": "9.00",
        "change": "0.30",
        "pct_chg": "3.33",
        "vol": "1000",
        "amount": "9300",
    }


def make_bar(trade_date: str, close: str) -> DailyBar:
    record = sample_record()
    record["trade_date"] = trade_date
    record["close"] = close
    record["high"] = max(record["open"], close)
    record["low"] = min(record["open"], close)
    return DailyBar.model_validate(record)


def test_run_close_to_close_backtest_returns_reproducible_result() -> None:
    result = run_close_to_close_backtest(
        [
            make_bar("20240102", "10.00"),
            make_bar("20240103", "11.00"),
        ]
    )

    assert result.ts_code == "000001.SZ"
    assert result.total_return == Decimal("0.10")
    assert result.fills[0].price == Decimal("10.00")
