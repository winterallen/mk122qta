"""Data ingestion package for MK122."""

from mk_data.ingestion import FetchDailyResult, fetch_daily_to_raw
from mk_data.lakehouse import DailySnapshot, query_daily_snapshot, write_daily_snapshot
from mk_data.lineage import LineageRecord, append_lineage_record
from mk_data.quality import DailyQualityReport, QualityIssue, validate_daily_bars
from mk_data.schemas import DailyBar, parse_daily_bars
from mk_data.tushare_client import TushareClient, TushareDailyQuery

__all__ = [
    "DailyBar",
    "DailyQualityReport",
    "DailySnapshot",
    "FetchDailyResult",
    "LineageRecord",
    "QualityIssue",
    "TushareClient",
    "TushareDailyQuery",
    "append_lineage_record",
    "fetch_daily_to_raw",
    "parse_daily_bars",
    "query_daily_snapshot",
    "validate_daily_bars",
    "write_daily_snapshot",
]
