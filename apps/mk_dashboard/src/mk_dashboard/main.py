from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from mk_autonomy import run_p7_meta_autonomy_validation
from mk_chaos import run_p5_chaos_validation
from mk_live import run_default_live_rollout


@dataclass(frozen=True, slots=True)
class DashboardPage:
    key: str
    title: str
    api_path: str


DASHBOARD_PAGES: tuple[DashboardPage, ...] = (
    DashboardPage("overview", "总览", "/api/overview"),
    DashboardPage("portfolio", "组合", "/api/portfolio"),
    DashboardPage("strategy", "策略", "/api/strategy"),
    DashboardPage("risk", "风控", "/api/risk"),
    DashboardPage("execution", "执行", "/api/execution"),
    DashboardPage("factors", "因子工厂", "/api/factors"),
    DashboardPage("meta", "元调度", "/api/meta-scheduler"),
    DashboardPage("decision_log", "决策日志", "/api/decision-log"),
    DashboardPage("drift", "漂移监控", "/api/drift-monitor"),
    DashboardPage("model_zoo", "模型动物园", "/api/model-zoo"),
    DashboardPage("chaos", "故障演练", "/api/chaos-center"),
    DashboardPage("live", "实盘灰度", "/api/live-rollout"),
    DashboardPage("autonomy", "元自治", "/api/autonomy"),
)


def _page_payload(page: DashboardPage) -> dict[str, str]:
    return {"key": page.key, "title": page.title, "api_path": page.api_path}


def dashboard_snapshot() -> dict[str, Any]:
    return {
        "status": "ready",
        "pages": [_page_payload(page) for page in DASHBOARD_PAGES],
        "portfolio": {
            "nav": "1000000.00",
            "cash": "100000.00",
            "gross_exposure": "0.90",
            "daily_return": "0.0120",
        },
        "strategy": {
            "strategy_id": "alpha_main",
            "seed_factors": 10,
            "trading_days": 10,
            "sharpe": 2.10,
        },
        "risk": {"gate_state": "PASS", "misfire_count": 0, "states_supported": 5},
        "execution": {"fills_today": 3, "reconcile_diff": "0.00"},
        "factors": factor_factory_snapshot(),
        "meta_scheduler": meta_scheduler_snapshot(),
        "decision_log": decision_log_snapshot(),
        "drift_monitor": drift_monitor_snapshot(),
        "model_zoo": model_zoo_snapshot(),
        "chaos_center": chaos_center_snapshot(),
        "live_rollout": live_rollout_snapshot(),
        "autonomy": autonomy_snapshot(),
    }


def factor_factory_snapshot() -> dict[str, Any]:
    return {
        "candidate_count": 1000,
        "live_count": 50,
        "validation_stages": [
            "basic",
            "single_factor",
            "stability",
            "correlation",
            "overfit",
            "cost",
        ],
        "ic_curve": [
            {"trade_date": "20240102", "ic": 0.08},
            {"trade_date": "20240103", "ic": 0.11},
            {"trade_date": "20240104", "ic": 0.10},
        ],
        "correlation_heatmap": [
            {"left": "momentum_close_3", "right": "rolling_slope_close_5", "corr": 0.72},
            {"left": "amount_trend_amount_3", "right": "volume_trend_volume_3", "corr": 0.64},
        ],
        "promotion_queue": [
            {"factor": "momentum_close_3", "state": "Live", "weight": "0.0300"},
            {"factor": "price_volume_close_5", "state": "Live", "weight": "0.0280"},
            {"factor": "quality_intraday_close_2", "state": "Shadow", "weight": "0.0000"},
        ],
    }


def meta_scheduler_snapshot() -> dict[str, Any]:
    return {
        "strategy_count": 6,
        "active_strategy_count": 5,
        "average_correlation": 0.31,
        "portfolio_sharpe": 2.40,
        "allocations": [
            {"strategy_id": "alpha_main", "weight": "0.24", "active": True},
            {"strategy_id": "style_rotation", "weight": "0.21", "active": True},
            {"strategy_id": "reversal_momentum", "weight": "0.18", "active": True},
            {"strategy_id": "event_driven", "weight": "0.17", "active": True},
            {"strategy_id": "etf_rotation", "weight": "0.20", "active": True},
            {"strategy_id": "cash_hedge", "weight": "0.00", "active": False},
        ],
        "bayesian_clips": [
            {
                "strategy_id": "event_driven",
                "candidate_id": "event_decay_2",
                "reason": "shadow_candidate",
            }
        ],
        "circuit_breakers": [
            {"strategy_id": "cash_hedge", "tripped": True, "reason": "max_drawdown"}
        ],
    }


def decision_log_snapshot() -> dict[str, Any]:
    return {
        "records": [
            {
                "component": "mk_orchestrator",
                "decision": "allocate",
                "strategy_id": "alpha_main",
            },
            {
                "component": "mk_orchestrator",
                "decision": "bayesian_clip",
                "strategy_id": "event_driven",
            },
            {
                "component": "mk_risk",
                "decision": "strategy_breaker",
                "strategy_id": "cash_hedge",
            },
        ]
    }


def drift_monitor_snapshot() -> dict[str, Any]:
    return {
        "trade_date": "20240131",
        "accuracy": 1.0,
        "checks": [
            {"kind": "psi", "score": 0.04, "threshold": 0.10, "drifted": False},
            {"kind": "ks", "score": 0.12, "threshold": 0.25, "drifted": False},
            {"kind": "wasserstein", "score": 0.05, "threshold": 0.20, "drifted": False},
            {"kind": "residual", "score": 0.03, "threshold": 0.15, "drifted": False},
            {"kind": "importance", "score": 0.04, "threshold": 0.20, "drifted": False},
        ],
        "gradient_safety": {
            "discard_rate": 0.125,
            "alert": "ok",
            "guardrails": 6,
        },
    }


def model_zoo_snapshot() -> dict[str, Any]:
    return {
        "model_count": 7,
        "live_count": 6,
        "shadow_count": 0,
        "weights": [
            {"model_id": "main_online_linear", "status": "Live", "weight": "0.1565"},
            {"model_id": "ftrl_baseline", "status": "Live", "weight": "0.1412"},
            {"model_id": "online_lgbm_proxy", "status": "Live", "weight": "0.1469"},
            {"model_id": "river_proxy", "status": "Live", "weight": "0.1355"},
            {"model_id": "stacking_ensemble", "status": "Veteran", "weight": "0.1679"},
            {"model_id": "residual_guard", "status": "Live", "weight": "0.1317"},
            {"model_id": "offline_anchor", "status": "Live", "weight": "0.1203"},
        ],
        "market_state_stability": {
            "trend": 0.96,
            "range": 0.88,
            "high_vol": 0.76,
            "passed": True,
        },
    }


def chaos_center_snapshot() -> dict[str, Any]:
    report = run_p5_chaos_validation()
    return {
        "accepted": report.accepted,
        "technical_scenarios": report.technical_report.total_count,
        "technical_pass_rate": report.technical_report.pass_rate,
        "rule_scenarios": len(report.rule_results),
        "rule_pass_rate": report.resilience.rule_pass_rate,
        "resilience_score": report.resilience.score,
        "helm_release": report.helm_release.release_name,
        "k8s_ready": report.helm_release.ready,
        "service_discovery_ready": report.service_discovery_ready,
        "config_center_ready": report.config_center_ready,
        "manual_trigger": report.dashboard_manual_trigger,
        "history_replay_ready": report.history_replay_ready,
        "recent_results": [
            {
                "scenario_id": result.scenario_id,
                "domain": result.domain.value,
                "passed": result.passed,
                "recovery_seconds": result.recovery_seconds,
            }
            for result in report.technical_report.results[:5]
        ],
    }


def live_rollout_snapshot() -> dict[str, Any]:
    report = run_default_live_rollout()
    return {
        "accepted": report.accepted,
        "canary_to_pilot_ready": report.canary_to_pilot_ready,
        "approval_count": len(report.approval_request.approvers),
        "kill_switch_armed": report.kill_switch.armed,
        "kill_switch_tripped": report.kill_switch.tripped,
        "broker_reconcile_passed": report.broker_reconcile_passed,
        "mobile_alert_ready": report.mobile_alert_ready,
        "stages": [
            {
                "stage": stage.stage.value,
                "trading_days": stage.trading_days,
                "capital_fraction": str(stage.capital_fraction),
                "discipline_passed": stage.discipline_passed,
                "reason": stage.reason,
            }
            for stage in report.stages
        ],
    }


def autonomy_snapshot() -> dict[str, Any]:
    report = run_p7_meta_autonomy_validation()
    return {
        "accepted": report.accepted,
        "nas_promoted_count": report.nas.promoted_count,
        "factor_frontier_size": report.factor_evolution.frontier_size,
        "rl_algorithm": report.training.algorithm,
        "rl_converged": report.training.converged,
        "rl_simulation_weeks": len(report.recommendations),
        "rl_live_enabled": report.deployment.live_enabled,
        "rule_veto_enabled": report.deployment.rule_veto_enabled,
        "violation_count": report.deployment.violation_count,
        "split_algorithm": report.split_decision.algorithm,
        "decision_path_nodes": report.decision_path_tree.node_count,
        "autonomous_days": report.autonomous_days,
        "resilience_score": report.resilience_score,
    }


def _html() -> str:
    nav = "".join(
        f"<button data-page='{page.key}'>{page.title}</button>" for page in DASHBOARD_PAGES
    )
    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MK122 控制台</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif;
      color: #18212f;
      background: #f6f8fb;
    }}
    .layout {{ min-height: 100vh; display: flex; }}
    aside {{
      width: 224px;
      flex: 0 0 224px;
      background: #ffffff;
      border-right: 1px solid #d7dde8;
      padding: 20px 14px;
    }}
    .brand {{ padding: 0 10px 18px; border-bottom: 1px solid #e3e8f1; }}
    .brand h1 {{ margin: 0; font-size: 24px; line-height: 1.2; }}
    .brand p {{ margin: 8px 0 0; color: #5b677a; font-size: 13px; }}
    nav {{ display: grid; gap: 6px; margin-top: 16px; }}
    button {{
      border: 1px solid #b9c4d6;
      background: #ffffff;
      padding: 10px 12px;
      border-radius: 6px;
      color: #253246;
      cursor: pointer;
      font-size: 14px;
      text-align: left;
      width: 100%;
    }}
    button.active {{
      border-color: #3178c6;
      background: #eaf2fb;
      color: #174f8a;
    }}
    .content {{ flex: 1; min-width: 0; }}
    header {{ padding: 18px 24px; background: #ffffff; border-bottom: 1px solid #d7dde8; }}
    header h2 {{ margin: 0; font-size: 22px; }}
    header p {{ margin: 6px 0 0; color: #5b677a; }}
    main {{ padding: 20px 24px; display: grid; gap: 16px; }}
    section {{
      background: #ffffff;
      border: 1px solid #d7dde8;
      border-radius: 8px;
      padding: 16px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .metric {{ border-left: 3px solid #3178c6; padding-left: 12px; min-height: 52px; }}
    .label {{ color: #5b677a; font-size: 12px; }}
    .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
    .panel-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }}
    .panel-header h3 {{ margin: 0; font-size: 18px; }}
    .panel-header p {{ margin: 6px 0 0; color: #5b677a; }}
    .view-content {{ display: grid; gap: 14px; }}
    .subsection {{ display: grid; gap: 10px; }}
    .subsection h4 {{ margin: 0; font-size: 15px; color: #253246; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
    }}
    .info-card {{
      border: 1px solid #e3e8f1;
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
    }}
    .card-label {{ color: #5b677a; font-size: 12px; }}
    .card-value {{ margin-top: 6px; font-size: 18px; font-weight: 700; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid #e3e8f1; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; background: #ffffff; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e8edf5; text-align: left; }}
    th {{ color: #5b677a; background: #f7f9fc; font-weight: 600; }}
    tr:last-child td {{ border-bottom: 0; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      font-weight: 600;
    }}
    .badge-ok {{ color: #17633a; background: #e9f7ef; }}
    .badge-warn {{ color: #8a4d00; background: #fff4df; }}
    .badge-off {{ color: #5b677a; background: #edf1f6; }}
    .list {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip {{
      border: 1px solid #d7dde8;
      border-radius: 999px;
      padding: 4px 8px;
      background: #ffffff;
    }}
    details {{ margin-top: 16px; border-top: 1px solid #e3e8f1; padding-top: 12px; }}
    summary {{ cursor: pointer; color: #3178c6; font-weight: 600; }}
    .raw-payload {{
      white-space: pre-wrap;
      word-break: break-word;
      margin-top: 10px;
      color: #253246;
    }}
    .empty {{ color: #5b677a; }}
    @media (max-width: 760px) {{
      .layout {{ display: block; }}
      aside {{ width: 100%; border-right: 0; border-bottom: 1px solid #d7dde8; }}
      nav {{ grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); }}
      button {{ text-align: center; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <div class="brand">
        <h1>MK122</h1>
        <p>自治量化交易系统</p>
      </div>
      <nav aria-label="主菜单">{nav}</nav>
    </aside>
    <div class="content">
      <header>
        <h2>总览控制台</h2>
        <p>策略、风控、执行、学习、演练、实盘与自治状态</p>
      </header>
      <main>
        <section class="grid">
          <div class="metric"><div class="label">净值</div><div id="nav" class="value">-</div></div>
          <div class="metric">
            <div class="label">夏普</div><div id="sharpe" class="value">-</div>
          </div>
          <div class="metric">
            <div class="label">风控闸门</div><div id="risk" class="value">-</div>
          </div>
          <div class="metric">
            <div class="label">对账差异</div><div id="reconcile" class="value">-</div>
          </div>
        </section>
        <section class="panel">
          <div class="panel-header">
            <div>
              <h3 id="view-title">总览</h3>
              <p id="view-desc">系统关键状态</p>
            </div>
          </div>
          <div id="view-content" class="view-content"></div>
          <details>
            <summary>原始数据</summary>
            <pre id="raw-payload" class="raw-payload"></pre>
          </details>
        </section>
      </main>
    </div>
  </div>
  <script>
    const pages = {json.dumps({page.key: page.api_path for page in DASHBOARD_PAGES})};
    const pageTitles = {
        json.dumps(
            {page.key: page.title for page in DASHBOARD_PAGES},
            ensure_ascii=False,
        )
    };
    const rootByPage = {{
      overview: "overview",
      portfolio: "portfolio",
      strategy: "strategy",
      risk: "risk",
      execution: "execution",
      factors: "factors",
      meta: "meta_scheduler",
      decision_log: "decision_log",
      drift: "drift_monitor",
      model_zoo: "model_zoo",
      chaos: "chaos_center",
      live: "live_rollout",
      autonomy: "autonomy",
    }};
    const labels = {{
      accepted: "验收状态",
      active: "启用",
      active_strategy_count: "启用策略数",
      alert: "告警状态",
      allocation: "分配",
      allocations: "资金分配",
      approval_count: "审批人数",
      average_correlation: "平均相关性",
      autonomy: "元自治",
      autonomous_days: "自治天数",
      bayesian_clips: "贝叶斯裁剪",
      broker_reconcile_passed: "券商对账",
      canary_to_pilot_ready: "Canary 到 Pilot",
      candidate_count: "候选数量",
      cash: "现金",
      chaos_center: "故障演练",
      checks: "检测项",
      circuit_breakers: "熔断状态",
      component: "组件",
      config_center_ready: "配置中心",
      correlation_heatmap: "相关性热力",
      daily_return: "日收益",
      decision: "决策",
      decision_log: "决策日志",
      decision_path_nodes: "决策路径节点",
      discipline_passed: "纪律通过",
      drift_monitor: "漂移监控",
      drifted: "发生漂移",
      execution: "执行",
      factor: "因子",
      factor_frontier_size: "因子前沿数量",
      factors: "因子工厂",
      fills_today: "今日成交",
      gate_state: "闸门状态",
      gradient_safety: "梯度安全",
      gross_exposure: "总敞口",
      guardrails: "防线数量",
      helm_release: "Helm Release",
      history_replay_ready: "历史回放",
      ic: "IC",
      ic_curve: "IC 曲线",
      k8s_ready: "K8s 就绪",
      kind: "类型",
      kill_switch_armed: "熔断开关就绪",
      kill_switch_tripped: "熔断触发",
      live_count: "Live 数量",
      live_rollout: "实盘灰度",
      manual_trigger: "手动触发",
      market_state_stability: "市场状态稳定性",
      meta_scheduler: "元调度",
      misfire_count: "误触发次数",
      mobile_alert_ready: "移动告警",
      model_count: "模型数量",
      model_id: "模型 ID",
      model_zoo: "模型动物园",
      nas_promoted_count: "NAS 晋级数",
      nav: "净值",
      pages: "页面",
      passed: "通过",
      portfolio: "组合",
      portfolio_sharpe: "组合夏普",
      promotion_queue: "晋级队列",
      recent_results: "最近演练",
      reconcile_diff: "对账差异",
      recovery_seconds: "恢复秒数",
      resilience_score: "韧性评分",
      risk: "风控",
      rl_algorithm: "RL 算法",
      rl_converged: "RL 收敛",
      rl_live_enabled: "RL 上线",
      rl_simulation_weeks: "RL 仿真周数",
      rule_pass_rate: "规则通过率",
      rule_scenarios: "规则场景",
      rule_veto_enabled: "规则一票否决",
      service_discovery_ready: "服务发现",
      shadow_count: "Shadow 数量",
      sharpe: "夏普",
      split_algorithm: "拆单算法",
      stage: "阶段",
      stages: "灰度阶段",
      state: "状态",
      status: "状态",
      strategy: "策略",
      strategy_count: "策略数量",
      strategy_id: "策略 ID",
      technical_pass_rate: "技术通过率",
      technical_scenarios: "技术故障场景",
      threshold: "阈值",
      trade_date: "交易日",
      trading_days: "交易日数",
      validation_stages: "验证阶段",
      violation_count: "违例次数",
      weight: "权重",
      weights: "模型权重",
    }};
    const valueLabels = {{
      true: "是",
      false: "否",
      ready: "就绪",
      ok: "正常",
      PASS: "通过",
      Live: "在线",
      Veteran: "老兵",
      Shadow: "影子",
      accepted: "已接受",
      allocated: "已分配",
      max_drawdown: "最大回撤",
      shadow_candidate: "影子候选",
      strategy_breaker: "策略熔断",
      bayesian_clip: "贝叶斯裁剪",
      allocate: "分配",
    }};
    const setActive = (key) => {{
      document.querySelectorAll("nav button").forEach((button) => {{
        button.classList.toggle("active", button.dataset.page === key);
      }});
    }};
    const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({{
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }}[char]));
    const formatLabel = (key) => labels[key] || key.replaceAll("_", " ");
    const displayText = (value) => {{
      if (value === null || value === undefined) return "-";
      if (typeof value === "boolean") return value ? "是" : "否";
      return valueLabels[String(value)] || String(value);
    }};
    const renderValue = (value) => {{
      if (typeof value === "boolean") {{
        return "<span class='badge " +
          (value ? "badge-ok" : "badge-off") +
          "'>" + displayText(value) + "</span>";
      }}
      const text = displayText(value);
      if (["通过", "正常", "就绪", "是", "在线", "老兵", "已接受", "已分配"].includes(text)) {{
        return "<span class='badge badge-ok'>" + escapeHtml(text) + "</span>";
      }}
      if (["否", "影子", "最大回撤", "影子候选"].includes(text)) {{
        return "<span class='badge badge-warn'>" + escapeHtml(text) + "</span>";
      }}
      return escapeHtml(text);
    }};
    const isPrimitive = (value) => value === null || typeof value !== "object";
    const renderCards = (entries) => {{
      if (!entries.length) return "";
      return "<div class='cards'>" + entries.map(([key, value]) =>
        "<div class='info-card'><div class='card-label'>" + escapeHtml(formatLabel(key)) +
        "</div><div class='card-value'>" + renderValue(value) + "</div></div>"
      ).join("") + "</div>";
    }};
    const renderTable = (rows) => {{
      if (!rows.length) return "<div class='empty'>暂无数据</div>";
      const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
      const head = columns.map((column) =>
        "<th>" + escapeHtml(formatLabel(column)) + "</th>"
      ).join("");
      const body = rows.map((row) => "<tr>" + columns.map((column) =>
        "<td>" + renderValue(row[column]) + "</td>"
      ).join("") + "</tr>").join("");
      return "<div class='table-wrap'><table><thead><tr>" +
        head + "</tr></thead><tbody>" +
        body + "</tbody></table></div>";
    }};
    const renderArray = (items) => {{
      if (!items.length) return "<div class='empty'>暂无数据</div>";
      if (items.every((item) => isPrimitive(item))) {{
        return "<div class='list'>" +
          items.map((item) => "<span class='chip'>" + renderValue(item) + "</span>").join("") +
          "</div>";
      }}
      if (items.every((item) => item && typeof item === "object" && !Array.isArray(item))) {{
        return renderTable(items);
      }}
      return items.map((item, index) => renderSection("item_" + (index + 1), item)).join("");
    }};
    const renderSection = (key, value) => {{
      if (Array.isArray(value)) {{
        return "<div class='subsection'><h4>" +
          escapeHtml(formatLabel(key)) +
          "</h4>" + renderArray(value) + "</div>";
      }}
      if (value && typeof value === "object") {{
        const entries = Object.entries(value);
        const primitiveEntries = entries.filter(([, item]) => isPrimitive(item));
        const nestedEntries = entries.filter(([, item]) => !isPrimitive(item));
        return "<div class='subsection'><h4>" + escapeHtml(formatLabel(key)) + "</h4>" +
          renderCards(primitiveEntries) +
          nestedEntries.map(([nestedKey, nestedValue]) =>
            renderSection(nestedKey, nestedValue)
          ).join("") +
          "</div>";
      }}
      return "<div class='subsection'><h4>" +
        escapeHtml(formatLabel(key)) +
        "</h4>" + renderCards([[key, value]]) + "</div>";
    }};
    const renderOverview = (data) => {{
      document.getElementById("nav").textContent = data.portfolio.nav;
      document.getElementById("sharpe").textContent = data.strategy.sharpe;
      document.getElementById("risk").textContent = data.risk.gate_state;
      document.getElementById("reconcile").textContent = data.execution.reconcile_diff;
    }};
    const renderView = (key, data) => {{
      const title = pageTitles[key] || "总览";
      const rootKey = rootByPage[key];
      const rootData = rootKey === "overview" ? data : data[rootKey];
      document.getElementById("view-title").textContent = title;
      document.getElementById("view-desc").textContent =
        key === "overview" ? "系统关键状态" : "业务指标与运行状态";
      document.getElementById("view-content").innerHTML = rootKey === "overview"
        ? Object.entries(data).map(([sectionKey, sectionValue]) =>
          renderSection(sectionKey, sectionValue)
        ).join("")
        : renderSection(rootKey, rootData);
      document.getElementById("raw-payload").textContent = JSON.stringify(data, null, 2);
    }};
    const render = (data) => {{
      renderOverview(data);
      renderView("overview", data);
      setActive("overview");
    }};
    document.querySelectorAll("nav button").forEach((button) => {{
      button.addEventListener("click", async () => {{
        const key = button.dataset.page;
        const response = await fetch(pages[key]);
        const data = await response.json();
        renderView(key, data);
        setActive(key);
      }});
    }});
    fetch("/api/overview").then((response) => response.json()).then(render);
    const source = new EventSource("/api/stream");
    source.addEventListener("dashboard", (event) => renderOverview(JSON.parse(event.data)));
  </script>
</body>
</html>
"""


async def _event_stream() -> AsyncIterator[str]:
    yield f"event: dashboard\ndata: {json.dumps(dashboard_snapshot())}\n\n"
    await asyncio.sleep(0)


def create_app() -> FastAPI:
    dashboard_app = FastAPI(title="MK122 控制台", version="0.1.0")

    @dashboard_app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _html()

    @dashboard_app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @dashboard_app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(status_code=204)

    @dashboard_app.get("/api/pages")
    async def pages() -> dict[str, list[dict[str, str]]]:
        return {"pages": [_page_payload(page) for page in DASHBOARD_PAGES]}

    @dashboard_app.get("/api/overview")
    async def overview() -> dict[str, Any]:
        return dashboard_snapshot()

    @dashboard_app.get("/api/portfolio")
    async def portfolio() -> dict[str, Any]:
        return {"portfolio": dashboard_snapshot()["portfolio"]}

    @dashboard_app.get("/api/strategy")
    async def strategy() -> dict[str, Any]:
        return {"strategy": dashboard_snapshot()["strategy"]}

    @dashboard_app.get("/api/risk")
    async def risk() -> dict[str, Any]:
        return {"risk": dashboard_snapshot()["risk"]}

    @dashboard_app.get("/api/execution")
    async def execution() -> dict[str, Any]:
        return {"execution": dashboard_snapshot()["execution"]}

    @dashboard_app.get("/api/factors")
    async def factors() -> dict[str, Any]:
        return {"factors": factor_factory_snapshot()}

    @dashboard_app.get("/api/meta-scheduler")
    async def meta_scheduler() -> dict[str, Any]:
        return {"meta_scheduler": meta_scheduler_snapshot()}

    @dashboard_app.get("/api/decision-log")
    async def decision_log() -> dict[str, Any]:
        return {"decision_log": decision_log_snapshot()}

    @dashboard_app.get("/api/drift-monitor")
    async def drift_monitor() -> dict[str, Any]:
        return {"drift_monitor": drift_monitor_snapshot()}

    @dashboard_app.get("/api/model-zoo")
    async def model_zoo() -> dict[str, Any]:
        return {"model_zoo": model_zoo_snapshot()}

    @dashboard_app.get("/api/chaos-center")
    async def chaos_center() -> dict[str, Any]:
        return {"chaos_center": chaos_center_snapshot()}

    @dashboard_app.get("/api/live-rollout")
    async def live_rollout() -> dict[str, Any]:
        return {"live_rollout": live_rollout_snapshot()}

    @dashboard_app.get("/api/autonomy")
    async def autonomy() -> dict[str, Any]:
        return {"autonomy": autonomy_snapshot()}

    @dashboard_app.get("/api/stream")
    async def stream() -> StreamingResponse:
        return StreamingResponse(_event_stream(), media_type="text/event-stream")

    return dashboard_app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("mk_dashboard.main:app", host="127.0.0.1", port=8010, reload=False)
