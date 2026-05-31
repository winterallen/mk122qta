from __future__ import annotations

from decimal import Decimal

from mk_data.schemas import DailyBar
from mk_execution import SimulatedExecutor, build_rebalance_orders
from mk_strategies import TargetWeight


def make_bar() -> DailyBar:
    return DailyBar.model_validate(
        {
            "ts_code": "000001.SZ",
            "trade_date": "20240105",
            "open": "10.00",
            "high": "10.20",
            "low": "9.90",
            "close": "10.00",
            "pre_close": "10.00",
            "change": "0.00",
            "pct_chg": "0.00",
            "vol": "1000",
            "amount": "10000",
        }
    )


def test_build_rebalance_orders_and_fill_at_close() -> None:
    targets = (
        TargetWeight(
            strategy_id="alpha_main",
            ts_code="000001.SZ",
            trade_date="20240105",
            target_weight=Decimal("0.50"),
            score=Decimal("1.0"),
        ),
    )

    orders = build_rebalance_orders(
        targets,
        current_positions={},
        prices={"000001.SZ": Decimal("10.00")},
        portfolio_value=Decimal("10000"),
    )
    fills = SimulatedExecutor().fill_at_close(orders, (make_bar(),))

    assert orders[0].quantity == 500
    assert fills[0].price == Decimal("10.00")
    assert fills[0].notional == Decimal("5000.00")
