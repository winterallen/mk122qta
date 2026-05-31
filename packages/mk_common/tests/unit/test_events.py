from __future__ import annotations

from mk_common import Event


def test_event_serializes_with_required_fields() -> None:
    event = Event(topic="data.ready", payload={"symbol": "000001.SZ"})

    data = event.to_dict()

    assert data["topic"] == "data.ready"
    assert data["payload"] == {"symbol": "000001.SZ"}
    assert data["event_id"]
    assert data["created_at"].endswith("+00:00")
