from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from mk_data.schemas import DailyBar

DAILY_CSV_FIELDS = [
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount",
]


@dataclass(frozen=True, slots=True)
class RawDailyWriteResult:
    path: Path
    rows: int


def write_daily_csv(bars: list[DailyBar], output_root: Path) -> RawDailyWriteResult:
    if not bars:
        raise ValueError("cannot write empty daily dataset")

    sorted_bars = sorted(bars, key=lambda bar: (bar.ts_code, bar.trade_date))
    ts_codes = sorted({bar.ts_code for bar in sorted_bars})
    start_date = min(bar.trade_date_yyyymmdd for bar in sorted_bars)
    end_date = max(bar.trade_date_yyyymmdd for bar in sorted_bars)
    symbol_part = ts_codes[0] if len(ts_codes) == 1 else "multi"

    target_dir = output_root / f"ts_code={symbol_part}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"daily_{start_date}_{end_date}.csv"

    with target_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=DAILY_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(bar.to_record() for bar in sorted_bars)

    return RawDailyWriteResult(path=target_path, rows=len(sorted_bars))
