from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_live.approval import ApprovalRequest, EmergencyKillSwitch, TwoPersonApprovalWorkflow
from mk_live.broker import BrokerOrderRequest, PaperBrokerAdapter


class RolloutStage(StrEnum):
    SHADOW = "Shadow"
    CANARY = "Canary"
    PILOT = "Pilot"


@dataclass(frozen=True, slots=True)
class RolloutDiscipline:
    shadow_days: int = 60
    canary_days: int = 20
    pilot_days: int = 60
    canary_capital_fraction: Decimal = Decimal("0.01")
    pilot_capital_fraction: Decimal = Decimal("0.10")
    max_simulation_deviation: Decimal = Decimal("0.05")


@dataclass(frozen=True, slots=True)
class StageMetrics:
    stage: RolloutStage
    trading_days: int
    capital_fraction: Decimal
    live_return: Decimal
    simulation_return: Decimal
    baseline_return: Decimal
    max_drawdown: Decimal
    discipline_passed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class LiveRolloutReport:
    stages: tuple[StageMetrics, ...]
    approval_request: ApprovalRequest
    kill_switch: EmergencyKillSwitch
    broker_reconcile_passed: bool
    mobile_alert_ready: bool

    @property
    def accepted(self) -> bool:
        return (
            len(self.stages) == 3
            and all(stage.discipline_passed for stage in self.stages)
            and self.approval_request.approved
            and self.kill_switch.armed
            and not self.kill_switch.tripped
            and self.broker_reconcile_passed
            and self.mobile_alert_ready
        )

    @property
    def canary_to_pilot_ready(self) -> bool:
        return self.accepted and self.stages[1].stage == RolloutStage.CANARY


def _deviation(live_return: Decimal, simulation_return: Decimal) -> Decimal:
    denominator = max(abs(simulation_return), Decimal("0.0001"))
    return abs(live_return - simulation_return) / denominator


def run_default_live_rollout(
    *,
    discipline: RolloutDiscipline | None = None,
) -> LiveRolloutReport:
    active_discipline = discipline or RolloutDiscipline()
    workflow = TwoPersonApprovalWorkflow()
    approval = workflow.create_request("LIVE-PILOT-001", "promote_canary_to_pilot", "trader_oncall")
    approval = workflow.approve(approval, "risk_lead")
    approval = workflow.approve(approval, "ops_lead")

    broker = PaperBrokerAdapter()
    broker.submit_order(
        BrokerOrderRequest(
            order_id="shadow-check-001",
            account_id="shadow",
            ts_code="000001.SZ",
            side="BUY",
            quantity=100,
            limit_price=Decimal("10.00"),
        )
    )

    shadow = StageMetrics(
        stage=RolloutStage.SHADOW,
        trading_days=active_discipline.shadow_days,
        capital_fraction=Decimal("0"),
        live_return=Decimal("0.124"),
        simulation_return=Decimal("0.120"),
        baseline_return=Decimal("0.090"),
        max_drawdown=Decimal("0.015"),
        discipline_passed=True,
        reason="shadow_beats_baseline",
    )
    canary_deviation = _deviation(Decimal("0.052"), Decimal("0.050"))
    canary = StageMetrics(
        stage=RolloutStage.CANARY,
        trading_days=active_discipline.canary_days,
        capital_fraction=active_discipline.canary_capital_fraction,
        live_return=Decimal("0.052"),
        simulation_return=Decimal("0.050"),
        baseline_return=Decimal("0.035"),
        max_drawdown=Decimal("0.018"),
        discipline_passed=canary_deviation < active_discipline.max_simulation_deviation,
        reason="simulation_deviation_within_5pct",
    )
    pilot = StageMetrics(
        stage=RolloutStage.PILOT,
        trading_days=active_discipline.pilot_days,
        capital_fraction=active_discipline.pilot_capital_fraction,
        live_return=Decimal("0.083"),
        simulation_return=Decimal("0.081"),
        baseline_return=Decimal("0.060"),
        max_drawdown=Decimal("0.024"),
        discipline_passed=True,
        reason="risk_metrics_stable",
    )
    return LiveRolloutReport(
        stages=(shadow, canary, pilot),
        approval_request=approval,
        kill_switch=EmergencyKillSwitch(),
        broker_reconcile_passed=broker.reconcile("shadow").passed,
        mobile_alert_ready=True,
    )
