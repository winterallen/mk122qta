from __future__ import annotations

from decimal import Decimal

from mk_autonomy import (
    ContextualBanditSplitter,
    run_default_nas_search,
    run_factor_expression_evolution,
    run_p7_meta_autonomy_validation,
    simulate_rl_recommendation_period,
)


def test_p7_meta_autonomy_validation_meets_acceptance_metrics() -> None:
    report = run_p7_meta_autonomy_validation()

    assert report.accepted
    assert report.nas.promoted_count >= 3
    assert len(report.recommendations) == 12
    assert report.deployment.passed
    assert report.decision_path_tree.node_count >= 6


def test_nas_and_factor_evolution_create_live_candidates_and_frontier() -> None:
    nas = run_default_nas_search()
    evolution = run_factor_expression_evolution()

    assert nas.promoted_count == 3
    assert evolution.frontier_size >= 3
    assert all(genome.pareto_score > 0 for genome in evolution.frontier)


def test_rl_recommendation_period_is_suggestion_only_for_12_weeks() -> None:
    recommendations = simulate_rl_recommendation_period(12)

    assert all(item.suggestion_only for item in recommendations)
    assert any(item.beats_bayesian for item in recommendations)


def test_contextual_bandit_splitter_selects_urgent_pov() -> None:
    splitter = ContextualBanditSplitter()
    decision = splitter.select(
        order_id="order-1",
        volatility=Decimal("0.05"),
        spread_bps=Decimal("5.0"),
        urgency=Decimal("0.90"),
    )

    assert decision.algorithm == "POV"
    assert decision.reason == "urgent"
