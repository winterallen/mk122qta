from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mk_common.clock import utc_now
from mk_common.ids import new_id


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic: str = Field(min_length=1)
    payload: dict[str, Any]
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    created_at: datetime = Field(default_factory=utc_now)
    schema_version: str = "v1"

    def to_event_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "schema_version": self.schema_version,
        }
