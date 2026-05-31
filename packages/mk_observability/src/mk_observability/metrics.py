from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MetricPoint:
    name: str
    value: Decimal
    labels: dict[str, str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryMetricRegistry:
    def __init__(self) -> None:
        self._points: defaultdict[str, list[MetricPoint]] = defaultdict(list)

    def record(self, point: MetricPoint) -> None:
        self._points[point.name].append(point)

    def latest(self, name: str) -> MetricPoint | None:
        points = self._points.get(name)
        if not points:
            return None
        return points[-1]
