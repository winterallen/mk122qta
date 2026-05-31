from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from mk_execution import ExecutionOrder
from mk_simulation import MatchRuleSet, ParameterizedMatchingEngine


class RuleChangeKind(StrEnum):
    TRADING_RULE = "trading_rule"
    MARKET_STRUCTURE = "market_structure"
    CHRONIC_DRIFT = "chronic_drift"
    NLP_NOISE = "nlp_noise"


@dataclass(frozen=True, slots=True)
class RuleChangeScenario:
    scenario_id: str
    kind: RuleChangeKind
    replay_date: str
    expected_settlement_lag: int


@dataclass(frozen=True, slots=True)
class RuleDrillResult:
    scenario_id: str
    kind: RuleChangeKind
    replay_date: str
    rule_version: str
    replayed: bool
    passed: bool
    evidence: str


@dataclass(frozen=True, slots=True)
class MarketRuleTimeline:
    rules: tuple[MatchRuleSet, ...]

    def rule_for(self, trade_date: str) -> MatchRuleSet:
        candidates = [rule for rule in self.rules if rule.effective_date <= trade_date]
        if not candidates:
            raise ValueError(f"no market rule available for {trade_date}")
        return sorted(candidates, key=lambda rule: rule.effective_date)[-1]


def build_market_rule_timeline() -> MarketRuleTimeline:
    return MarketRuleTimeline(
        rules=(
            MatchRuleSet(
                version="CN-A-2010",
                effective_date="20100101",
                limit_up_pct=Decimal("0.10"),
                limit_down_pct=Decimal("0.10"),
                settlement_lag_days=1,
                stamp_tax_rate=Decimal("0.0010"),
                commission_rate=Decimal("0.00030"),
            ),
            MatchRuleSet(
                version="CN-A-201508",
                effective_date="20150824",
                limit_up_pct=Decimal("0.10"),
                limit_down_pct=Decimal("0.10"),
                settlement_lag_days=1,
                stamp_tax_rate=Decimal("0.0010"),
                commission_rate=Decimal("0.00025"),
            ),
            MatchRuleSet(
                version="CN-A-202308",
                effective_date="20230828",
                limit_up_pct=Decimal("0.10"),
                limit_down_pct=Decimal("0.10"),
                settlement_lag_days=1,
                stamp_tax_rate=Decimal("0.00050"),
                commission_rate=Decimal("0.00020"),
            ),
            MatchRuleSet(
                version="CN-ETF-202401",
                effective_date="20240101",
                limit_up_pct=Decimal("0.20"),
                limit_down_pct=Decimal("0.20"),
                settlement_lag_days=0,
                stamp_tax_rate=Decimal("0.00000"),
                commission_rate=Decimal("0.00015"),
            ),
        )
    )


def generate_rule_change_scenarios() -> tuple[RuleChangeScenario, ...]:
    scenarios: list[RuleChangeScenario] = []
    dates = ("20100104", "20150825", "20230829", "20240103")
    for kind_index, kind in enumerate(RuleChangeKind):
        for offset in range(3):
            replay_date = dates[(kind_index + offset) % len(dates)]
            expected_lag = 0 if replay_date >= "20240101" else 1
            scenarios.append(
                RuleChangeScenario(
                    scenario_id=f"RULE-{len(scenarios) + 1:03d}",
                    kind=kind,
                    replay_date=replay_date,
                    expected_settlement_lag=expected_lag,
                )
            )
    return tuple(scenarios)


def run_rule_change_drills(
    scenarios: tuple[RuleChangeScenario, ...],
    *,
    timeline: MarketRuleTimeline | None = None,
) -> tuple[RuleDrillResult, ...]:
    active_timeline = timeline or build_market_rule_timeline()
    engine = ParameterizedMatchingEngine()
    results: list[RuleDrillResult] = []
    for scenario in scenarios:
        rule = active_timeline.rule_for(scenario.replay_date)
        order = ExecutionOrder(
            order_id=f"drill:{scenario.scenario_id}",
            strategy_id="rule_replay",
            ts_code="000001.SZ",
            trade_date=scenario.replay_date,
            side="SELL",
            quantity=100,
            reference_price=Decimal("10.00"),
        )
        fill = engine.match_order(
            order,
            previous_close=Decimal("10.00"),
            execution_price=Decimal("10.00"),
            rules=rule,
        )
        passed = fill.accepted and fill.settlement_lag_days == scenario.expected_settlement_lag
        results.append(
            RuleDrillResult(
                scenario_id=scenario.scenario_id,
                kind=scenario.kind,
                replay_date=scenario.replay_date,
                rule_version=rule.version,
                replayed=True,
                passed=passed,
                evidence=f"rules://{rule.version}/{scenario.scenario_id}",
            )
        )
    return tuple(results)
