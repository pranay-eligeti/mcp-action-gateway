"""Simple allowlist policy for gateway actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionPolicy:
    allowed_actions: frozenset[str]
    require_approval_for: frozenset[str]

    def authorize(self, action: str, approved: bool = False) -> None:
        if action not in self.allowed_actions:
            raise PermissionError(f"Action not allowed: {action}")
        if action in self.require_approval_for and not approved:
            raise PermissionError(f"Explicit approval required: {action}")
