from __future__ import annotations

import json
from decimal import Decimal

from mk_execution import build_rebalance_orders
from mk_strategies import TargetWeight


def main() -> None:
    targets = (
        TargetWeight(
            strategy_id="alpha_main",
            ts_code="000001.SZ",
            trade_date="20240103",
            target_weight=Decimal("0.30"),
            score=Decimal("1.20"),
        ),
    )
    orders = build_rebalance_orders(
        targets,
        current_positions={},
        prices={"000001.SZ": Decimal("10.00")},
        portfolio_value=Decimal("100000"),
    )
    print(
        json.dumps(
            [
                {
                    "order_id": order.order_id,
                    "side": order.side,
                    "quantity": order.quantity,
                    "reference_price": str(order.reference_price),
                }
                for order in orders
            ],
            ensure_ascii=False,
        )
    )
