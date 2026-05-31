from __future__ import annotations

import json
from decimal import Decimal

from mk_risk import RiskSnapshot, evaluate_risk_gate


def main() -> None:
    decision = evaluate_risk_gate(
        RiskSnapshot(
            gross_exposure=Decimal("0.90"),
            max_symbol_weight=Decimal("0.30"),
            order_notional=Decimal("100000"),
            daily_turnover=Decimal("0.10"),
            cash_buffer=Decimal("0.10"),
        )
    )
    print(
        json.dumps(
            {
                "state": decision.state.value,
                "approved_weight_scale": str(decision.approved_weight_scale),
                "reasons": decision.reasons,
            },
            ensure_ascii=False,
        )
    )
