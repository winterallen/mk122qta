from __future__ import annotations

from decimal import Decimal

import pytest
from mk_live import (
    BrokerOrderRequest,
    BrokerOrderStatus,
    PaperBrokerAdapter,
    TwoPersonApprovalWorkflow,
    run_default_live_rollout,
)


def test_default_live_rollout_meets_shadow_canary_pilot_discipline() -> None:
    report = run_default_live_rollout()

    assert report.accepted
    assert report.canary_to_pilot_ready
    assert [stage.trading_days for stage in report.stages] == [60, 20, 60]
    assert [stage.capital_fraction for stage in report.stages] == [
        Decimal("0"),
        Decimal("0.01"),
        Decimal("0.10"),
    ]
    assert report.mobile_alert_ready


def test_two_person_approval_blocks_requester_self_approval() -> None:
    workflow = TwoPersonApprovalWorkflow()
    request = workflow.create_request("REQ-1", "promote", "requester")

    with pytest.raises(ValueError, match="requester cannot approve"):
        workflow.approve(request, "requester")


def test_paper_broker_adapter_handles_order_query_and_reconcile() -> None:
    adapter = PaperBrokerAdapter()
    ack = adapter.submit_order(
        BrokerOrderRequest(
            order_id="order-1",
            account_id="canary",
            ts_code="000001.SZ",
            side="BUY",
            quantity=100,
            limit_price=Decimal("10.00"),
        )
    )

    assert ack.status == BrokerOrderStatus.FILLED
    assert adapter.query_order("order-1").broker_order_id
    assert adapter.reconcile("canary").passed
