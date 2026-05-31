from __future__ import annotations

from mk_learning import DriftKind, KnownDriftScenario, detect_drift, evaluate_known_drift_accuracy


def scenario(index: int, *, drifted: bool) -> KnownDriftScenario:
    base = tuple(0.10 + item * 0.01 for item in range(20))
    if drifted:
        current = tuple(value + 0.40 + index * 0.001 for value in base)
        current_residuals = tuple(0.30 + item * 0.01 for item in range(10))
        current_importance = (0.10, 0.20, 0.70)
    else:
        current = tuple(value + 0.01 for value in base)
        current_residuals = tuple(0.02 + item * 0.001 for item in range(10))
        current_importance = (0.48, 0.31, 0.21)
    return KnownDriftScenario(
        name=f"scenario_{index}",
        expected_drifted=drifted,
        reference=base,
        current=current,
        reference_residuals=tuple(0.02 + item * 0.001 for item in range(10)),
        current_residuals=current_residuals,
        reference_importance=(0.50, 0.30, 0.20),
        current_importance=current_importance,
    )


def test_drift_report_contains_five_daily_checks() -> None:
    report = detect_drift(
        trade_date="20240131",
        reference=tuple(0.10 + item * 0.01 for item in range(20)),
        current=tuple(0.50 + item * 0.01 for item in range(20)),
        reference_residuals=(0.01, 0.02, 0.01),
        current_residuals=(0.30, 0.31, 0.29),
        reference_importance=(0.50, 0.30, 0.20),
        current_importance=(0.10, 0.20, 0.70),
    )

    assert {check.kind for check in report.checks} == set(DriftKind)
    assert report.drifted


def test_known_drift_accuracy_exceeds_95_percent() -> None:
    scenarios = tuple(scenario(index, drifted=index % 2 == 0) for index in range(20))

    accuracy = evaluate_known_drift_accuracy(scenarios)

    assert accuracy >= 0.95
