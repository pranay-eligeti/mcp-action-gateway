"""In-memory audit log for local demonstrations and tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuditEvent:
    action: str
    status: str
    details: str
    timestamp: str


class AuditLog:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(self, action: str, status: str, details: str) -> None:
        self._events.append(
            AuditEvent(
                action=action,
                status=status,
                details=details,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def list(self) -> list[AuditEvent]:
        return list(self._events)
