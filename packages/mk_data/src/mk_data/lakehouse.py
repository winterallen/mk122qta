from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import duckdb
import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from mk_data.raw_store import DAILY_CSV_FIELDS
from mk_data.schemas import DailyBar


@dataclass(frozen=True, slots=True)
class DailySnapshot:
    table_path: Path
    rows: int
    version: int


def write_daily_snapshot(
    bars: list[DailyBar],
    *,
    table_path: Path,
    mode: Literal["overwrite", "append", "ignore", "error"] = "overwrite",
) -> DailySnapshot:
    if not bars:
        raise ValueError("cannot write empty daily snapshot")

    table_path.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([bar.to_record() for bar in bars], columns=DAILY_CSV_FIELDS)
    table_data = pa.Table.from_pandas(frame, preserve_index=False)
    write_deltalake(str(table_path), table_data, mode=mode)
    table = DeltaTable(str(table_path))
    return DailySnapshot(table_path=table_path, rows=len(frame), version=table.version())


def query_daily_snapshot(
    table_path: Path,
    sql: str = "select ts_code, trade_date, close from daily_bars order by ts_code, trade_date",
) -> list[tuple[Any, ...]]:
    table = DeltaTable(str(table_path))
    frame = table.to_pandas()
    connection = duckdb.connect(":memory:")
    try:
        connection.register("daily_bars", frame)
        return list(connection.execute(sql).fetchall())
    finally:
        connection.close()
