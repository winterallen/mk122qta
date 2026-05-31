from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from mk_data.ingestion import fetch_daily_to_raw
from mk_data.tushare_client import TushareDailyQuery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Tushare daily bars into raw CSV storage.")
    parser.add_argument("--ts-code", required=True, help="Tushare symbol, e.g. 000001.SZ")
    parser.add_argument("--start-date", required=True, help="Start date in YYYYMMDD")
    parser.add_argument("--end-date", required=True, help="End date in YYYYMMDD")
    parser.add_argument(
        "--output-root",
        default="data/raw/tushare/daily",
        help="Raw daily output root directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = fetch_daily_to_raw(
        TushareDailyQuery(
            ts_code=args.ts_code,
            start_date=args.start_date,
            end_date=args.end_date,
        ),
        output_root=Path(args.output_root),
    )
    print(f"wrote {result.written.rows} rows to {result.written.path}")
