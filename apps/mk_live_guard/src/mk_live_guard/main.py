from __future__ import annotations

import json

from mk_live import run_default_live_rollout


def main() -> None:
    report = run_default_live_rollout()
    print(
        json.dumps(
            {
                "accepted": report.accepted,
                "stages": [stage.stage.value for stage in report.stages],
                "approval_count": len(report.approval_request.approvers),
                "kill_switch_armed": report.kill_switch.armed,
                "mobile_alert_ready": report.mobile_alert_ready,
            },
            ensure_ascii=False,
        )
    )
