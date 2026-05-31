from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, cast

from mk_common.config import load_env_value


class TushareProApi(Protocol):
    def daily(self, **kwargs: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class TushareDailyQuery:
    ts_code: str | None = None
    trade_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def to_params(self) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "ts_code": self.ts_code,
                "trade_date": self.trade_date,
                "start_date": self.start_date,
                "end_date": self.end_date,
            }.items()
            if value
        }


class TushareClient:
    def __init__(self, token: str | None = None, pro_api: TushareProApi | None = None) -> None:
        self._token = token
        self._pro_api = pro_api

    def daily(self, query: TushareDailyQuery, *, fields: str | None = None) -> Any:
        params = query.to_params()
        if fields:
            params["fields"] = fields
        return self._api().daily(**params)

    def _api(self) -> TushareProApi:
        if self._pro_api is not None:
            return self._pro_api

        token = self._token or load_env_value("TUSHARE_TOKEN", required=True)

        import tushare as ts

        self._pro_api = cast(TushareProApi, ts.pro_api(token))
        return self._pro_api
