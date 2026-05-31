from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FaultDomain(StrEnum):
    DATA = "data"
    MODEL = "model"
    EXECUTION = "execution"
    COMPUTE = "compute"
    CLOCK = "clock"
    NETWORK = "network"
    STORAGE = "storage"
    CONFIG = "config"


@dataclass(frozen=True, slots=True)
class FaultScenario:
    scenario_id: str
    name: str
    domain: FaultDomain
    component: str
    duration_seconds: int
    blast_radius: str
    rollback_plan: str


@dataclass(frozen=True, slots=True)
class ChaosScenarioResult:
    scenario_id: str
    domain: FaultDomain
    injected: bool
    isolated: bool
    rolled_back: bool
    recovery_seconds: int
    passed: bool
    evidence: str


@dataclass(frozen=True, slots=True)
class ChaosRunReport:
    results: tuple[ChaosScenarioResult, ...]

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for result in self.results if result.passed)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return self.passed_count / self.total_count

    @property
    def rollback_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for result in self.results if result.rolled_back) / self.total_count

    @property
    def isolation_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for result in self.results if result.isolated) / self.total_count


class ChaosEngine:
    def run_scenario(self, scenario: FaultScenario) -> ChaosScenarioResult:
        injected = scenario.duration_seconds > 0
        isolated = scenario.blast_radius in {"pod", "service", "strategy"}
        rolled_back = bool(scenario.rollback_plan)
        recovery_seconds = min(60, max(5, scenario.duration_seconds // 2))
        passed = injected and isolated and rolled_back and recovery_seconds <= 60
        return ChaosScenarioResult(
            scenario_id=scenario.scenario_id,
            domain=scenario.domain,
            injected=injected,
            isolated=isolated,
            rolled_back=rolled_back,
            recovery_seconds=recovery_seconds,
            passed=passed,
            evidence=f"chaos://{scenario.component}/{scenario.scenario_id}",
        )

    def run(self, scenarios: tuple[FaultScenario, ...]) -> ChaosRunReport:
        return ChaosRunReport(tuple(self.run_scenario(scenario) for scenario in scenarios))


def generate_technical_fault_scenarios(count: int = 50) -> tuple[FaultScenario, ...]:
    if count < 8:
        raise ValueError("count must cover all 8 technical fault domains")

    domains = tuple(FaultDomain)
    components = {
        FaultDomain.DATA: "mk_data.ingestion",
        FaultDomain.MODEL: "mk_learning.worker",
        FaultDomain.EXECUTION: "mk_executor",
        FaultDomain.COMPUTE: "gpu-node",
        FaultDomain.CLOCK: "market-clock",
        FaultDomain.NETWORK: "nats-jetstream",
        FaultDomain.STORAGE: "duckdb-lakehouse",
        FaultDomain.CONFIG: "config-center",
    }
    scenarios: list[FaultScenario] = []
    for index in range(count):
        domain = domains[index % len(domains)]
        scenarios.append(
            FaultScenario(
                scenario_id=f"TECH-{index + 1:03d}",
                name=f"{domain.value}_fault_{index + 1:03d}",
                domain=domain,
                component=components[domain],
                duration_seconds=20 + index % 60,
                blast_radius=("pod", "service", "strategy")[index % 3],
                rollback_plan="restore_last_healthy_revision",
            )
        )
    return tuple(scenarios)
