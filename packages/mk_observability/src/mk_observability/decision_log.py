from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class DecisionLogRecord:
    component: str
    decision: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryDecisionLog:
    def __init__(self) -> None:
        self._records: list[DecisionLogRecord] = []

    def append(self, record: DecisionLogRecord) -> None:
        self._records.append(record)

    def tail(self, limit: int = 100) -> tuple[DecisionLogRecord, ...]:
        if limit <= 0:
            return ()
        return tuple(self._records[-limit:])
