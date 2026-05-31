from __future__ import annotations

from fastapi.testclient import TestClient
from mk_autonomy import run_p7_meta_autonomy_validation
from mk_chaos import run_p5_chaos_validation
from mk_dashboard import create_app
from mk_live import run_default_live_rollout


def test_p5_p6_p7_acceptance_reports_are_all_green() -> None:
    p5 = run_p5_chaos_validation()
    p6 = run_default_live_rollout()
    p7 = run_p7_meta_autonomy_validation()

    assert p5.accepted
    assert p5.technical_report.total_count >= 50
    assert len(p5.rule_results) >= 12
    assert p5.resilience.score >= 0.95
    assert p6.accepted
    assert p6.canary_to_pilot_ready
    assert p7.accepted
    assert p7.deployment.violation_count == 0


def test_dashboard_exposes_p5_p6_p7_pages_and_apis() -> None:
    client = TestClient(create_app())

    pages = client.get("/api/pages").json()["pages"]
    chaos = client.get("/api/chaos-center").json()["chaos_center"]
    live = client.get("/api/live-rollout").json()["live_rollout"]
    autonomy = client.get("/api/autonomy").json()["autonomy"]

    assert len(pages) == 13
    assert pages[-3]["key"] == "chaos"
    assert chaos["technical_scenarios"] >= 50
    assert chaos["rule_scenarios"] >= 12
    assert chaos["resilience_score"] >= 0.95
    assert live["canary_to_pilot_ready"]
    assert len(live["stages"]) == 3
    assert autonomy["nas_promoted_count"] >= 3
    assert autonomy["rl_simulation_weeks"] >= 12
    assert autonomy["violation_count"] == 0
