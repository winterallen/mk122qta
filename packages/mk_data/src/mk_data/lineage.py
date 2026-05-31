from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from mk_common.clock import utc_now
from mk_common.ids import new_id


@dataclass(frozen=True, slots=True)
class LineageRecord:
    operation: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    row_count: int
    record_id: str = field(default_factory=lambda: new_id("lin"))
    created_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "operation": self.operation,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "row_count": self.row_count,
            "created_at": self.created_at,
        }


def append_lineage_record(record: LineageRecord, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True))
        file.write("\n")
