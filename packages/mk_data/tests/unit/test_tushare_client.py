from __future__ import annotations

from typing import Any

from mk_data import TushareClient, TushareDailyQuery


class FakeTushareApi:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def daily(self, **kwargs: str) -> list[dict[str, str]]:
        self.calls.append(kwargs)
        return [{"ts_code": kwargs["ts_code"]}]


def test_daily_query_omits_empty_params() -> None:
    query = TushareDailyQuery(ts_code="000001.SZ", start_date="20240101")

    assert query.to_params() == {
        "ts_code": "000001.SZ",
        "start_date": "20240101",
    }


def test_client_delegates_daily_query_without_real_network() -> None:
    api = FakeTushareApi()
    client = TushareClient(pro_api=api)

    result: Any = client.daily(TushareDailyQuery(ts_code="000001.SZ"))

    assert result == [{"ts_code": "000001.SZ"}]
    assert api.calls == [{"ts_code": "000001.SZ"}]
