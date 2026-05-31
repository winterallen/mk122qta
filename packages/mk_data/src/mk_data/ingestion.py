from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from mk_data.quality import DailyQualityReport, validate_daily_bars
from mk_data.raw_store import RawDailyWriteResult, write_daily_csv
from mk_data.schemas import DailyBar, parse_daily_bars
from mk_data.tushare_client import TushareClient, TushareDailyQuery

TUSHARE_DAILY_FIELDS = ",".join(
    [
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
)


@dataclass(frozen=True, slots=True)
class FetchDailyResult:
    bars: list[DailyBar]
    quality: DailyQualityReport
    written: RawDailyWriteResult


class DailyDataClient(Protocol):
    def daily(self, query: TushareDailyQuery, *, fields: str | None = None) -> Any: ...


def fetch_daily_to_raw(
    query: TushareDailyQuery,
    *,
    output_root: Path,
    client: DailyDataClient | None = None,
) -> FetchDailyResult:
    active_client = client or TushareClient()
    response = active_client.daily(query, fields=TUSHARE_DAILY_FIELDS)
    bars = parse_daily_bars(records_from_daily_response(response))
    quality = validate_daily_bars(bars)
    quality.raise_if_failed()
    written = write_daily_csv(bars, output_root)
    return FetchDailyResult(bars=bars, quality=quality, written=written)


def records_from_daily_response(response: Any) -> list[Mapping[str, Any]]:
    if hasattr(response, "to_dict"):
        records = response.to_dict("records")
        if isinstance(records, list):
            return [record for record in records if isinstance(record, Mapping)]

    if isinstance(response, Sequence) and not isinstance(response, str):
        return [record for record in response if isinstance(record, Mapping)]

    raise TypeError("daily response must be a pandas DataFrame or a sequence of mappings")
