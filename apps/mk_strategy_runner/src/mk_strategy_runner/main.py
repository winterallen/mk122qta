from __future__ import annotations

import json
from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_signals import score_bars
from mk_strategies import MultiFactorAlphaStrategyActor


def _sample_bar(symbol: str, trade_date: str, close: str) -> DailyBar:
    return DailyBar.model_validate(
        {
            "ts_code": symbol,
            "trade_date": trade_date,
            "open": close,
            "high": str(Decimal(close) * Decimal("1.01")),
            "low": str(Decimal(close) * Decimal("0.99")),
            "close": close,
            "pre_close": close,
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": "1000",
            "amount": "10000",
        }
    )


def main() -> None:
    bars = (
        _sample_bar("000001.SZ", "20240102", "10.00"),
        _sample_bar("000002.SZ", "20240102", "9.00"),
        _sample_bar("000001.SZ", "20240103", "10.30"),
        _sample_bar("000002.SZ", "20240103", "8.90"),
    )
    targets = MultiFactorAlphaStrategyActor().generate_targets(score_bars(bars))
    print(
        json.dumps(
            [
                {
                    "strategy_id": target.strategy_id,
                    "ts_code": target.ts_code,
                    "trade_date": target.trade_date,
                    "target_weight": str(target.target_weight),
                    "score": str(target.score),
                }
                for target in targets
            ],
            ensure_ascii=False,
        )
    )
