from __future__ import annotations

from mk_common import Event


def main() -> None:
    event = Event(topic="app.started", payload={"app": "mk_signal_engine"})
    print(event.to_dict())
