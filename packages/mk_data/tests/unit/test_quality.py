from __future__ import annotations

from datetime import date
from decimal import Decimal

from mk_data.quality import DailyQualityRules, validate_daily_bars
from mk_data.schemas import DailyBar


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


def make_bar(**overrides: str) -> DailyBar:
    record = sample_record()
    record.update(overrides)
    return DailyBar.model_validate(record)


def test_quality_gate_passes_valid_daily_bars() -> None:
    report = validate_daily_bars([make_bar()])

    assert report.passed
    assert report.rows_checked == 1


def test_quality_gate_reports_duplicate_keys() -> None:
    report = validate_daily_bars([make_bar(), make_bar()])

    assert not report.passed
    assert report.issues[0].code == "duplicate_key"


def test_quality_gate_reports_invalid_ohlc_range() -> None:
    report = validate_daily_bars([make_bar(high="9.20", close="9.30")])

    assert not report.passed
    assert report.issues[0].code == "invalid_high"


def test_quality_gate_reports_unexpected_symbol_and_extreme_change() -> None:
    report = validate_daily_bars(
        [make_bar(ts_code="000002.SZ", pct_chg="40")],
        rules=DailyQualityRules(
            expected_ts_code="000001.SZ",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            max_abs_pct_chg=Decimal("30"),
        ),
    )

    assert {issue.code for issue in report.issues} == {"unexpected_symbol", "extreme_pct_chg"}
