from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ElasticLearningRateDecision:
    base_rate: float
    adjusted_rate: float
    reason: str


@dataclass(frozen=True, slots=True)
class DualTrackVote:
    online_score: float
    offline_score: float
    online_weight: float
    accepted_online: bool


def elastic_learning_rate(
    *,
    base_rate: float,
    drifted: bool,
    discard_rate: float,
) -> ElasticLearningRateDecision:
    if discard_rate > 0.20:
        return ElasticLearningRateDecision(base_rate, base_rate * 0.25, "high_discard_rate")
    if drifted:
        return ElasticLearningRateDecision(base_rate, base_rate * 0.50, "drift_cooldown")
    return ElasticLearningRateDecision(base_rate, base_rate, "stable")


def dual_track_vote(
    *,
    online_score: float,
    offline_score: float,
    min_relative_score: float = 0.70,
) -> DualTrackVote:
    if offline_score <= 0:
        return DualTrackVote(online_score, offline_score, 1.0, True)
    accepted = online_score >= offline_score * min_relative_score
    if accepted:
        online_weight = min(0.70, max(0.30, online_score / (online_score + offline_score)))
    else:
        online_weight = 0.0
    return DualTrackVote(online_score, offline_score, online_weight, accepted)
