from __future__ import annotations

from mk_common.ids import new_id
from mk_common.schemas import EventEnvelope


def test_new_id_adds_normalized_prefix() -> None:
    value = new_id("Task_Run")

    assert value.startswith("task-run_")


def test_event_envelope_serializes_schema_version() -> None:
    envelope = EventEnvelope(topic="data.ready", payload={"rows": 10})

    data = envelope.to_event_dict()

    assert data["event_id"].startswith("evt_")
    assert data["topic"] == "data.ready"
    assert data["schema_version"] == "v1"
