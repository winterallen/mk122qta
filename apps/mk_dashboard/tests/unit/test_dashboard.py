from __future__ import annotations

from fastapi.testclient import TestClient
from mk_dashboard import DASHBOARD_PAGES, create_app


def test_dashboard_has_factor_factory_page_and_health_route() -> None:
    client = TestClient(create_app())

    response = client.get("/api/pages")
    health = client.get("/api/health")
    favicon = client.get("/favicon.ico")

    assert health.json() == {"status": "ok"}
    assert favicon.status_code == 204
    assert response.status_code == 200
    assert len(response.json()["pages"]) == 13
    assert len(DASHBOARD_PAGES) == 13
    assert response.json()["pages"][-8]["key"] == "factors"
    assert response.json()["pages"][0]["title"] == "总览"
    assert response.json()["pages"][-1]["title"] == "元自治"


def test_dashboard_sse_stream_returns_event() -> None:
    client = TestClient(create_app())

    response = client.get("/api/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: dashboard" in response.text
    assert '"status": "ready"' in response.text


def test_dashboard_index_renders_structured_chinese_view() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert 'lang="zh-CN"' in response.text
    assert 'aria-label="主菜单"' in response.text
    assert 'id="view-content"' in response.text
    assert 'id="raw-payload"' in response.text
    assert "原始数据" in response.text
    assert 'id="payload"' not in response.text


def test_dashboard_factor_factory_api() -> None:
    client = TestClient(create_app())

    response = client.get("/api/factors")
    payload = response.json()["factors"]

    assert response.status_code == 200
    assert payload["live_count"] == 50
    assert len(payload["validation_stages"]) == 6
    assert payload["ic_curve"]
    assert payload["correlation_heatmap"]
    assert payload["promotion_queue"]


def test_dashboard_meta_scheduler_and_decision_log_api() -> None:
    client = TestClient(create_app())

    meta = client.get("/api/meta-scheduler").json()["meta_scheduler"]
    log = client.get("/api/decision-log").json()["decision_log"]

    assert meta["strategy_count"] == 6
    assert meta["active_strategy_count"] == 5
    assert meta["bayesian_clips"]
    assert meta["circuit_breakers"]
    assert len(log["records"]) >= 3


def test_dashboard_drift_monitor_and_model_zoo_api() -> None:
    client = TestClient(create_app())

    drift = client.get("/api/drift-monitor").json()["drift_monitor"]
    zoo = client.get("/api/model-zoo").json()["model_zoo"]

    assert drift["accuracy"] >= 0.95
    assert len(drift["checks"]) == 5
    assert drift["gradient_safety"]["guardrails"] == 6
    assert zoo["model_count"] == 7
    assert zoo["live_count"] >= 6
    assert zoo["market_state_stability"]["passed"]


def test_dashboard_chaos_live_and_autonomy_api() -> None:
    client = TestClient(create_app())

    chaos = client.get("/api/chaos-center").json()["chaos_center"]
    live = client.get("/api/live-rollout").json()["live_rollout"]
    autonomy = client.get("/api/autonomy").json()["autonomy"]

    assert chaos["accepted"]
    assert chaos["technical_scenarios"] >= 50
    assert chaos["rule_scenarios"] >= 12
    assert chaos["resilience_score"] >= 0.95
    assert live["accepted"]
    assert live["canary_to_pilot_ready"]
    assert autonomy["accepted"]
    assert autonomy["nas_promoted_count"] >= 3
    assert autonomy["rl_simulation_weeks"] == 12
