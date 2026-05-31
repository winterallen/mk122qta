from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SplitDecision:
    order_id: str
    algorithm: str
    participation_rate: Decimal
    expected_slippage_bps: Decimal
    reason: str


class ContextualBanditSplitter:
    def select(
        self,
        *,
        order_id: str,
        volatility: Decimal,
        spread_bps: Decimal,
        urgency: Decimal,
    ) -> SplitDecision:
        if urgency >= Decimal("0.80") or volatility >= Decimal("0.04"):
            return SplitDecision(order_id, "POV", Decimal("0.12"), Decimal("5.0"), "urgent")
        if spread_bps <= Decimal("3.0"):
            return SplitDecision(order_id, "VWAP", Decimal("0.08"), Decimal("3.2"), "tight_spread")
        return SplitDecision(order_id, "TWAP", Decimal("0.05"), Decimal("2.8"), "default")
