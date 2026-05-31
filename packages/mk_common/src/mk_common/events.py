from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from mk_common.clock import utc_now


@dataclass(frozen=True, slots=True)
class Event:
    topic: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }
