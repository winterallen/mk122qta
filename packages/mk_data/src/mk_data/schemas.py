from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DailyBar(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    ts_code: str = Field(min_length=6)
    trade_date: date
    open: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    low: Decimal = Field(ge=0)
    close: Decimal = Field(ge=0)
    pre_close: Decimal = Field(ge=0)
    change: Decimal
    pct_chg: Decimal
    volume: Decimal = Field(alias="vol", ge=0)
    amount: Decimal = Field(ge=0)

    @field_validator("trade_date", mode="before")
    @classmethod
    def parse_trade_date(cls, value: Any) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return datetime.strptime(value, "%Y%m%d").date()
        raise TypeError("trade_date must be a date or YYYYMMDD string")

    @field_validator(
        "open",
        "high",
        "low",
        "close",
        "pre_close",
        "change",
        "pct_chg",
        "volume",
        "amount",
        mode="before",
    )
    @classmethod
    def parse_decimal(cls, value: Any) -> Decimal:
        if value is None:
            raise ValueError("numeric field cannot be empty")

        text = str(value).strip()
        if not text or text.lower() in {"nan", "nat", "none"}:
            raise ValueError("numeric field cannot be empty")

        try:
            return Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"invalid decimal value: {value}") from exc

    @property
    def trade_date_yyyymmdd(self) -> str:
        return self.trade_date.strftime("%Y%m%d")

    def to_record(self) -> dict[str, str]:
        return {
            "ts_code": self.ts_code,
            "trade_date": self.trade_date_yyyymmdd,
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "pre_close": str(self.pre_close),
            "change": str(self.change),
            "pct_chg": str(self.pct_chg),
            "vol": str(self.volume),
            "amount": str(self.amount),
        }


def parse_daily_bars(records: Iterable[Mapping[str, Any]]) -> list[DailyBar]:
    return [DailyBar.model_validate(record) for record in records]
