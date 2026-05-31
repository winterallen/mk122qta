from __future__ import annotations

from pathlib import Path

from mk_data.ingestion import TUSHARE_DAILY_FIELDS, fetch_daily_to_raw
from mk_data.tushare_client import TushareDailyQuery


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


class FakeTushareClient:
    def __init__(self) -> None:
        self.calls: list[tuple[TushareDailyQuery, str | None]] = []

    def daily(self, query: TushareDailyQuery, *, fields: str | None = None) -> list[dict[str, str]]:
        self.calls.append((query, fields))
        return [sample_record()]


def test_fetch_daily_to_raw_writes_csv(tmp_path: Path) -> None:
    client = FakeTushareClient()

    result = fetch_daily_to_raw(
        TushareDailyQuery(ts_code="000001.SZ", start_date="20240102", end_date="20240102"),
        output_root=tmp_path,
        client=client,
    )

    assert result.quality.passed
    assert result.written.rows == 1
    assert result.written.path.read_text(encoding="utf-8").splitlines() == [
        "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount",
        "000001.SZ,20240102,9.10,9.40,9.00,9.30,9.00,0.30,3.33,1000,9300",
    ]
    assert client.calls[0][1] == TUSHARE_DAILY_FIELDS
