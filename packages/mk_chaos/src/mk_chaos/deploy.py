from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppDeploymentSpec:
    app_name: str
    image: str
    replicas: int
    health_path: str = "/api/health"

    @property
    def ready(self) -> bool:
        return self.replicas >= 1 and self.image.startswith("mk122/")


@dataclass(frozen=True, slots=True)
class HelmReleasePlan:
    release_name: str
    namespace: str
    apps: tuple[AppDeploymentSpec, ...]
    prometheus_enabled: bool
    grafana_dashboard_count: int

    @property
    def ready(self) -> bool:
        return (
            bool(self.apps)
            and all(app.ready for app in self.apps)
            and self.prometheus_enabled
            and self.grafana_dashboard_count >= 1
        )


@dataclass(frozen=True, slots=True)
class ServiceDiscoveryPlan:
    backend: str
    registered_services: tuple[str, ...]
    health_check_interval_seconds: int

    @property
    def ready(self) -> bool:
        return (
            self.backend in {"consul", "etcd"}
            and len(self.registered_services) >= 8
            and self.health_check_interval_seconds <= 15
        )


@dataclass(frozen=True, slots=True)
class ConfigCenterPlan:
    backend: str
    dynamic_keys: tuple[str, ...]
    audit_enabled: bool
    rollback_enabled: bool

    @property
    def ready(self) -> bool:
        return (
            self.backend in {"consul", "etcd"}
            and len(self.dynamic_keys) >= 4
            and self.audit_enabled
            and self.rollback_enabled
        )


def build_default_helm_release() -> HelmReleasePlan:
    apps = (
        AppDeploymentSpec("mk-dashboard", "mk122/mk-dashboard:0.1.0", 2),
        AppDeploymentSpec("mk-signal-engine", "mk122/mk-signal-engine:0.1.0", 1),
        AppDeploymentSpec("mk-strategy-runner", "mk122/mk-strategy-runner:0.1.0", 1),
        AppDeploymentSpec("mk-risk-gate", "mk122/mk-risk-gate:0.1.0", 2),
        AppDeploymentSpec("mk-executor", "mk122/mk-executor:0.1.0", 1),
        AppDeploymentSpec("mk-orchestrator", "mk122/mk-orchestrator:0.1.0", 1),
        AppDeploymentSpec("mk-learning-worker", "mk122/mk-learning-worker:0.1.0", 1),
        AppDeploymentSpec("mk-chaos-runner", "mk122/mk-chaos-runner:0.1.0", 1),
    )
    return HelmReleasePlan(
        release_name="mk122",
        namespace="trading",
        apps=apps,
        prometheus_enabled=True,
        grafana_dashboard_count=5,
    )


def build_default_service_discovery_plan() -> ServiceDiscoveryPlan:
    return ServiceDiscoveryPlan(
        backend="consul",
        registered_services=tuple(app.app_name for app in build_default_helm_release().apps),
        health_check_interval_seconds=10,
    )


def build_default_config_center_plan() -> ConfigCenterPlan:
    return ConfigCenterPlan(
        backend="consul",
        dynamic_keys=(
            "risk.max_gross",
            "execution.commission_rate",
            "chaos.enabled",
            "learning.online_update_enabled",
            "live.kill_switch",
        ),
        audit_enabled=True,
        rollback_enabled=True,
    )
