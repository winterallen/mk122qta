from __future__ import annotations

from dataclasses import dataclass

from mk_chaos.engine import ChaosRunReport
from mk_chaos.rules import RuleDrillResult


@dataclass(frozen=True, slots=True)
class ResilienceScoreBreakdown:
    technical_pass_rate: float
    rule_pass_rate: float
    rollback_rate: float
    isolation_rate: float
    score: float
    threshold: float = 0.95

    @property
    def passed(self) -> bool:
        return self.score >= self.threshold


def calculate_resilience_score(
    technical_report: ChaosRunReport,
    rule_results: tuple[RuleDrillResult, ...],
    *,
    threshold: float = 0.95,
) -> ResilienceScoreBreakdown:
    if not rule_results:
        rule_pass_rate = 0.0
    else:
        rule_pass_rate = sum(1 for result in rule_results if result.passed) / len(rule_results)

    score = (
        0.45 * technical_report.pass_rate
        + 0.25 * rule_pass_rate
        + 0.20 * technical_report.rollback_rate
        + 0.10 * technical_report.isolation_rate
    )
    return ResilienceScoreBreakdown(
        technical_pass_rate=technical_report.pass_rate,
        rule_pass_rate=rule_pass_rate,
        rollback_rate=technical_report.rollback_rate,
        isolation_rate=technical_report.isolation_rate,
        score=round(score, 4),
        threshold=threshold,
    )
