from __future__ import annotations

import json

from mk_chaos import run_p5_chaos_validation


def main() -> None:
    report = run_p5_chaos_validation()
    print(
        json.dumps(
            {
                "accepted": report.accepted,
                "technical_scenarios": report.technical_report.total_count,
                "rule_scenarios": len(report.rule_results),
                "resilience_score": report.resilience.score,
                "helm_ready": report.helm_release.ready,
            },
            ensure_ascii=False,
        )
    )
