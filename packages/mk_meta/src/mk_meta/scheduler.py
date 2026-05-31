from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mk_meta.circuit_breaker import CircuitBreakerDecision

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True, slots=True)
class SchedulerConstraints:
    target_gross: Decimal = ONE
    max_strategy_weight: Decimal = Decimal("0.35")
    disabled_strategy_ids: tuple[str, ...] = ()
    kill_switch: bool = False


@dataclass(frozen=True, slots=True)
class StrategyPerformance:
    strategy_id: str
    sharpe: float
    volatility: float
    mean_return: float


@dataclass(frozen=True, slots=True)
class BayesianParameterCandidate:
    strategy_id: str
    candidate_id: str
    posterior_score: float
    uncertainty: float
    shadow: bool = True


@dataclass(frozen=True, slots=True)
class BayesianClipRecord:
    strategy_id: str
    candidate_id: str
    prior_weight: Decimal
    clipped_weight: Decimal
    posterior_score: float
    reason: str


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    strategy_id: str
    target_weight: Decimal
    active: bool
    reason: str


@dataclass(frozen=True, slots=True)
class SchedulerAudit:
    trade_date: str
    allocations: tuple[AllocationDecision, ...]
    bayesian_clips: tuple[BayesianClipRecord, ...]
    circuit_breakers: tuple[CircuitBreakerDecision, ...]
    average_correlation: float
    portfolio_sharpe: float


class MetaScheduler:
    def __init__(self, constraints: SchedulerConstraints | None = None) -> None:
        self.constraints = constraints or SchedulerConstraints()

    def allocate(
        self,
        performances: tuple[StrategyPerformance, ...],
        *,
        circuit_breakers: tuple[CircuitBreakerDecision, ...] = (),
        bayesian_candidates: tuple[BayesianParameterCandidate, ...] = (),
    ) -> tuple[AllocationDecision, ...]:
        breaker_by_id = {decision.strategy_id: decision for decision in circuit_breakers}
        active_performance = [
            performance
            for performance in performances
            if self._is_active(performance.strategy_id, breaker_by_id)
        ]
        if self.constraints.kill_switch or not active_performance:
            return tuple(
                AllocationDecision(
                    strategy_id=performance.strategy_id,
                    target_weight=ZERO,
                    active=False,
                    reason="kill_switch" if self.constraints.kill_switch else "no_active_strategy",
                )
                for performance in performances
            )

        raw_scores = {
            performance.strategy_id: self._raw_score(performance)
            for performance in active_performance
        }
        clipped_scores = self._apply_bayesian_shadow_clips(raw_scores, bayesian_candidates)
        capped_weights = self._normalize_with_cap(clipped_scores, active_performance)

        allocations: list[AllocationDecision] = []
        for performance in performances:
            breaker = breaker_by_id.get(performance.strategy_id)
            if self.constraints.kill_switch:
                allocations.append(
                    AllocationDecision(performance.strategy_id, ZERO, False, "kill_switch")
                )
            elif performance.strategy_id in self.constraints.disabled_strategy_ids:
                allocations.append(
                    AllocationDecision(performance.strategy_id, ZERO, False, "disabled_by_rule")
                )
            elif breaker and breaker.tripped:
                allocations.append(
                    AllocationDecision(performance.strategy_id, ZERO, False, breaker.reason)
                )
            elif performance.strategy_id in capped_weights:
                weight = capped_weights[performance.strategy_id]
                allocations.append(
                    AllocationDecision(performance.strategy_id, weight, True, "allocated")
                )
        return tuple(allocations)

    def bayesian_clips(
        self,
        allocations: tuple[AllocationDecision, ...],
        candidates: tuple[BayesianParameterCandidate, ...],
    ) -> tuple[BayesianClipRecord, ...]:
        allocation_by_id = {allocation.strategy_id: allocation for allocation in allocations}
        clips: list[BayesianClipRecord] = []
        for candidate in candidates:
            allocation = allocation_by_id.get(candidate.strategy_id)
            prior_weight = allocation.target_weight if allocation else ZERO
            if candidate.shadow:
                clipped_weight = ZERO
                reason = "shadow_candidate"
            elif candidate.posterior_score < 0:
                clipped_weight = ZERO
                reason = "negative_posterior"
            else:
                clipped_weight = prior_weight
                reason = "accepted"
            clips.append(
                BayesianClipRecord(
                    strategy_id=candidate.strategy_id,
                    candidate_id=candidate.candidate_id,
                    prior_weight=prior_weight,
                    clipped_weight=clipped_weight,
                    posterior_score=candidate.posterior_score,
                    reason=reason,
                )
            )
        return tuple(clips)

    def _is_active(
        self,
        strategy_id: str,
        breaker_by_id: dict[str, CircuitBreakerDecision],
    ) -> bool:
        breaker = breaker_by_id.get(strategy_id)
        return (
            strategy_id not in self.constraints.disabled_strategy_ids
            and not self.constraints.kill_switch
            and not (breaker and breaker.tripped)
        )

    def _raw_score(self, performance: StrategyPerformance) -> Decimal:
        volatility = max(performance.volatility, 0.0001)
        sharpe = max(performance.sharpe, 0.01)
        return Decimal(str(sharpe / volatility))

    def _normalize_with_cap(
        self,
        scores: dict[str, Decimal],
        active_performance: list[StrategyPerformance],
    ) -> dict[str, Decimal]:
        if not active_performance:
            return {}

        active_ids = [performance.strategy_id for performance in active_performance]
        if sum(scores.values(), ZERO) == ZERO:
            scores = {strategy_id: ONE for strategy_id in active_ids}

        remaining_ids = list(active_ids)
        remaining_target = self.constraints.target_gross
        weights: dict[str, Decimal] = {}

        while remaining_ids and remaining_target > ZERO:
            total_score = sum(scores[strategy_id] for strategy_id in remaining_ids)
            if total_score == ZERO:
                proposed = {
                    strategy_id: remaining_target / Decimal(len(remaining_ids))
                    for strategy_id in remaining_ids
                }
            else:
                proposed = {
                    strategy_id: (scores[strategy_id] / total_score) * remaining_target
                    for strategy_id in remaining_ids
                }

            capped = [
                strategy_id
                for strategy_id, weight in proposed.items()
                if weight >= self.constraints.max_strategy_weight
            ]
            if not capped:
                allocated = ZERO
                for strategy_id in remaining_ids[:-1]:
                    weights[strategy_id] = proposed[strategy_id]
                    allocated += proposed[strategy_id]
                weights[remaining_ids[-1]] = remaining_target - allocated
                return weights

            for strategy_id in capped:
                weights[strategy_id] = self.constraints.max_strategy_weight
                remaining_target -= self.constraints.max_strategy_weight
                remaining_ids.remove(strategy_id)

        for strategy_id in remaining_ids:
            weights[strategy_id] = ZERO
        return weights

    def _apply_bayesian_shadow_clips(
        self,
        raw_scores: dict[str, Decimal],
        candidates: tuple[BayesianParameterCandidate, ...],
    ) -> dict[str, Decimal]:
        scores = dict(raw_scores)
        for candidate in candidates:
            if candidate.strategy_id not in scores:
                continue
            if candidate.shadow or candidate.posterior_score < 0:
                scores[candidate.strategy_id] *= Decimal("0.90")
            else:
                scores[candidate.strategy_id] *= Decimal(
                    str(ONE + Decimal(str(candidate.posterior_score)))
                )
        return scores
