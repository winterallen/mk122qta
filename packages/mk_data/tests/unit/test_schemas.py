from __future__ import annotations

from datetime import date
from decimal import Decimal

from mk_data.schemas import DailyBar
from pydantic import ValidationError


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


def test_daily_bar_parses_tushare_record() -> None:
    bar = DailyBar.model_validate(sample_record())

    assert bar.trade_date == date(2024, 1, 2)
    assert bar.volume == Decimal("1000")
    assert bar.to_record()["trade_date"] == "20240102"
    assert bar.to_record()["vol"] == "1000"


def test_daily_bar_rejects_empty_numeric_value() -> None:
    record = sample_record()
    record["close"] = ""

    try:
        DailyBar.model_validate(record)
    except ValidationError as exc:
        assert "numeric field cannot be empty" in str(exc)
    else:
        raise AssertionError("DailyBar should reject empty numeric fields")
