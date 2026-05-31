"""Factor scoring primitives for MK122."""

from mk_signals.expressions import (
    FactorExpression,
    FactorOperator,
    evaluate_expression,
    expression_to_seed_factor,
    generate_candidate_expressions,
    parse_factor_expression,
)
from mk_signals.factors import (
    DEFAULT_SEED_FACTORS,
    CompositeScore,
    FactorValue,
    SeedFactor,
    calculate_factor_values,
    score_bars,
)
from mk_signals.racing import (
    FactorRaceConfig,
    FactorRaceEntry,
    FactorRaceResult,
    FactorRaceState,
    ThompsonObservation,
    allocate_thompson_weights,
    merge_homogeneous_reports,
    promote_factors,
)
from mk_signals.validation import (
    FactorValidationConfig,
    FactorValidationReport,
    ValidationStage,
    ValidationStageResult,
    reports_to_seed_factors,
    run_validation_pipeline,
)

__all__ = [
    "DEFAULT_SEED_FACTORS",
    "CompositeScore",
    "FactorExpression",
    "FactorOperator",
    "FactorRaceConfig",
    "FactorRaceEntry",
    "FactorRaceResult",
    "FactorRaceState",
    "FactorValue",
    "FactorValidationConfig",
    "FactorValidationReport",
    "SeedFactor",
    "ThompsonObservation",
    "ValidationStage",
    "ValidationStageResult",
    "allocate_thompson_weights",
    "calculate_factor_values",
    "evaluate_expression",
    "expression_to_seed_factor",
    "generate_candidate_expressions",
    "merge_homogeneous_reports",
    "parse_factor_expression",
    "promote_factors",
    "reports_to_seed_factors",
    "run_validation_pipeline",
    "score_bars",
]
