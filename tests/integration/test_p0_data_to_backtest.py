from __future__ import annotations

from pathlib import Path

from mk_data.lakehouse import query_daily_snapshot, write_daily_snapshot
from mk_data.lineage import LineageRecord, append_lineage_record
from mk_data.schemas import DailyBar
from mk_simulation import run_close_to_close_backtest


def make_bar(trade_date: str, close: str) -> DailyBar:
    return DailyBar.model_validate(
        {
            "ts_code": "000001.SZ",
            "trade_date": trade_date,
            "open": "10.00",
            "high": max("10.00", close),
            "low": min("10.00", close),
            "close": close,
            "pre_close": "10.00",
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": "1000",
            "amount": "10000",
        }
    )


def test_p0_data_to_backtest_flow(tmp_path: Path) -> None:
    bars = [make_bar("20240102", "10.00"), make_bar("20240103", "10.50")]
    snapshot = write_daily_snapshot(bars, table_path=tmp_path / "lakehouse" / "daily")
    rows = query_daily_snapshot(snapshot.table_path, "select count(*) from daily_bars")
    result = run_close_to_close_backtest(bars)

    append_lineage_record(
        LineageRecord(
            operation="p0_data_to_backtest",
            inputs=(str(snapshot.table_path),),
            outputs=("backtest:close_to_close",),
            row_count=snapshot.rows,
        ),
        tmp_path / "lineage" / "events.jsonl",
    )

    assert rows == [(2,)]
    assert result.total_return > 0
    assert (tmp_path / "lineage" / "events.jsonl").exists()
