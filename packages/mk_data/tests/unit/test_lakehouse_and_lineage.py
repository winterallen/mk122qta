from __future__ import annotations

import json
from pathlib import Path

from mk_data.lakehouse import query_daily_snapshot, write_daily_snapshot
from mk_data.lineage import LineageRecord, append_lineage_record
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


def test_write_and_query_daily_snapshot(tmp_path: Path) -> None:
    bar = DailyBar.model_validate(sample_record())
    snapshot = write_daily_snapshot([bar], table_path=tmp_path / "daily_delta")

    rows = query_daily_snapshot(snapshot.table_path)

    assert snapshot.rows == 1
    assert rows == [("000001.SZ", "20240102", "9.30")]


def test_append_lineage_record_writes_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "lineage" / "events.jsonl"
    record = LineageRecord(
        operation="raw_to_delta",
        inputs=("data/raw/a.csv",),
        outputs=("data/lakehouse/daily",),
        row_count=1,
    )

    append_lineage_record(record, path)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["operation"] == "raw_to_delta"
    assert loaded["row_count"] == 1
