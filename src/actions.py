"""Safe action adapters used by the MCP gateway."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .audit import AuditLog
from .policy import ActionPolicy


@dataclass(frozen=True)
class GatewayConfig:
    n8n_webhook_url: str | None = None


class ActionRegistry:
    def __init__(self, policy: ActionPolicy, audit: AuditLog, config: GatewayConfig) -> None:
        self.policy = policy
        self.audit = audit
        self.config = config

    async def get_system_status(self) -> dict[str, str]:
        return {
            "gateway": "online",
            "mode": "portfolio-demo",
            "execution": "allowlisted-actions-only",
        }

    async def run_action(self, action: str, payload: dict[str, str], approved: bool = False) -> dict[str, str]:
        try:
            self.policy.authorize(action, approved=approved)
            if action == "notify_n8n":
                return await self._notify_n8n(payload)
            if action == "log_event":
                message = payload.get("message", "")
                self.audit.record(action, "success", message)
                return {"status": "ok", "action": action}
            raise ValueError(f"Unknown registered action: {action}")
        except Exception as exc:
            self.audit.record(action, "error", str(exc))
            raise

    async def _notify_n8n(self, payload: dict[str, str]) -> dict[str, str]:
        if not self.config.n8n_webhook_url:
            self.audit.record("notify_n8n", "dry_run", "No webhook configured")
            return {"status": "dry_run", "action": "notify_n8n"}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.config.n8n_webhook_url, json=payload)
            response.raise_for_status()
        self.audit.record("notify_n8n", "success", "Webhook delivered")
        return {"status": "sent", "action": "notify_n8n"}
