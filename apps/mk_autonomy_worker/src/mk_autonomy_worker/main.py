from __future__ import annotations

import json

from mk_autonomy import run_p7_meta_autonomy_validation


def main() -> None:
    report = run_p7_meta_autonomy_validation()
    print(
        json.dumps(
            {
                "accepted": report.accepted,
                "nas_promoted_count": report.nas.promoted_count,
                "rl_weeks": len(report.recommendations),
                "rl_live_enabled": report.deployment.live_enabled,
                "split_algorithm": report.split_decision.algorithm,
                "decision_path_nodes": report.decision_path_tree.node_count,
            },
            ensure_ascii=False,
        )
    )
