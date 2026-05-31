from __future__ import annotations

from decimal import Decimal

from mk_execution import ExecutionFill
from mk_simulation import PortfolioLedger


def fill(side: str, quantity: int, price: str) -> ExecutionFill:
    return ExecutionFill(
        fill_id=f"fill-{side}",
        order_id=f"order-{side}",
        strategy_id="alpha_main",
        ts_code="000001.SZ",
        trade_date="20240105",
        side=side,  # type: ignore[arg-type]
        quantity=quantity,
        price=Decimal(price),
    )


def test_portfolio_ledger_tracks_cash_position_nav_and_reconcile() -> None:
    ledger = PortfolioLedger(Decimal("10000"))

    ledger.apply_fill(fill("BUY", 100, "10.00"))
    snapshot = ledger.mark_to_market("20240105", {"000001.SZ": Decimal("11.00")})
    reconciliation = ledger.reconcile(snapshot, {"000001.SZ": Decimal("11.00")})

    assert ledger.cash == Decimal("9000.00")
    assert snapshot.market_value == Decimal("1100.00")
    assert snapshot.total_equity == Decimal("10100.00")
    assert reconciliation.matched
