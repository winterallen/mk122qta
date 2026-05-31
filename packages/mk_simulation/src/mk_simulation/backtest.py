from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mk_data.schemas import DailyBar


@dataclass(frozen=True, slots=True)
class OrderIntent:
    ts_code: str
    trade_date: str
    quantity: int
    side: str = "BUY"


@dataclass(frozen=True, slots=True)
class Fill:
    ts_code: str
    trade_date: str
    quantity: int
    price: Decimal
    side: str


@dataclass(frozen=True, slots=True)
class BacktestResult:
    ts_code: str
    start_date: str
    end_date: str
    start_close: Decimal
    end_close: Decimal
    total_return: Decimal
    fills: tuple[Fill, ...]


def run_close_to_close_backtest(bars: list[DailyBar], *, quantity: int = 100) -> BacktestResult:
    if len(bars) < 2:
        raise ValueError("backtest requires at least two daily bars")

    sorted_bars = sorted(bars, key=lambda bar: bar.trade_date)
    symbols = {bar.ts_code for bar in sorted_bars}
    if len(symbols) != 1:
        raise ValueError("backtest supports one symbol in P0")

    first = sorted_bars[0]
    last = sorted_bars[-1]
    fill = Fill(
        ts_code=first.ts_code,
        trade_date=first.trade_date_yyyymmdd,
        quantity=quantity,
        price=first.close,
        side="BUY",
    )
    total_return = (last.close - first.close) / first.close
    return BacktestResult(
        ts_code=first.ts_code,
        start_date=first.trade_date_yyyymmdd,
        end_date=last.trade_date_yyyymmdd,
        start_close=first.close,
        end_close=last.close,
        total_return=total_return,
        fills=(fill,),
    )
