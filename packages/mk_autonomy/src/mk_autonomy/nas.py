from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CandidateStatus(StrEnum):
    SHADOW = "Shadow"
    LIVE = "Live"
    REJECTED = "Rejected"


@dataclass(frozen=True, slots=True)
class ArchitectureCandidate:
    candidate_id: str
    operators: tuple[str, ...]
    depth: int
    validation_score: float
    status: CandidateStatus


@dataclass(frozen=True, slots=True)
class NASSearchReport:
    candidates: tuple[ArchitectureCandidate, ...]

    @property
    def promoted_count(self) -> int:
        return sum(1 for candidate in self.candidates if candidate.status == CandidateStatus.LIVE)


@dataclass(frozen=True, slots=True)
class FactorGenome:
    genome_id: str
    expression: str
    ic: float
    turnover: float
    stability: float

    @property
    def pareto_score(self) -> float:
        return self.ic + self.stability - self.turnover


@dataclass(frozen=True, slots=True)
class FactorEvolutionReport:
    generations: int
    frontier: tuple[FactorGenome, ...]

    @property
    def frontier_size(self) -> int:
        return len(self.frontier)


def run_default_nas_search() -> NASSearchReport:
    candidates = (
        ArchitectureCandidate(
            "nas_transformer_micro",
            ("linear", "attention", "residual"),
            3,
            0.74,
            CandidateStatus.LIVE,
        ),
        ArchitectureCandidate(
            "nas_temporal_cnn",
            ("conv1d", "gate", "residual"),
            4,
            0.71,
            CandidateStatus.LIVE,
        ),
        ArchitectureCandidate(
            "nas_factor_mlp",
            ("linear", "gelu", "dropout"),
            5,
            0.68,
            CandidateStatus.LIVE,
        ),
        ArchitectureCandidate(
            "nas_sparse_router",
            ("router", "linear", "softmax"),
            4,
            0.53,
            CandidateStatus.SHADOW,
        ),
    )
    return NASSearchReport(candidates=candidates)


def run_factor_expression_evolution() -> FactorEvolutionReport:
    frontier = (
        FactorGenome("gp_001", "rank(ts_mean(close, 5) / ts_mean(close, 20))", 0.08, 0.02, 0.84),
        FactorGenome("gp_002", "rank(volume / ts_mean(volume, 10))", 0.07, 0.018, 0.82),
        FactorGenome("gp_003", "rank(close / delay(close, 3) - 1)", 0.09, 0.030, 0.80),
        FactorGenome("gp_004", "rank(ts_slope(amount, 8))", 0.075, 0.016, 0.83),
    )
    return FactorEvolutionReport(generations=12, frontier=frontier)
