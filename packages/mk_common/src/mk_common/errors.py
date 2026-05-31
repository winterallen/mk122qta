from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MK122Error(Exception):
    message: str
    code: str = "mk122.error"
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details or {},
        }


class ConfigurationError(MK122Error):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="mk122.configuration_error", details=details)


class DataQualityError(MK122Error):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="mk122.data_quality_error", details=details)
