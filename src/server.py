"""MCP server exposing safe, typed actions through a policy boundary."""

from __future__ import annotations

import os
import json

from mcp.server import MCPServer

from .actions import ActionRegistry, GatewayConfig
from .audit import AuditLog
from .policy import ActionPolicy

mcp = MCPServer("Pranay Action Gateway")

audit_log = AuditLog()
policy = ActionPolicy(
    allowed_actions=frozenset({"log_event", "notify_n8n"}),
    require_approval_for=frozenset({"notify_n8n"}),
)
registry = ActionRegistry(
    policy=policy,
    audit=audit_log,
    config=GatewayConfig(n8n_webhook_url=os.getenv("N8N_WEBHOOK_URL")),
)


@mcp.tool()
async def get_system_status() -> dict[str, str]:
    """Return gateway status and the current execution mode."""
    return await registry.get_system_status()


@mcp.tool()
async def run_action(action: str, message: str = "", approved: bool = False) -> dict[str, str]:
    """Run one allowlisted gateway action with policy and audit controls."""
    return await registry.run_action(action, {"message": message}, approved=approved)


@mcp.resource("gateway://policy")
def gateway_policy() -> str:
    """Expose the active gateway allowlist as read-only context."""
    return json.dumps(
        {
            "allowed_actions": sorted(policy.allowed_actions),
            "approval_required_for": sorted(policy.require_approval_for),
        },
        indent=2,
    )


@mcp.resource("gateway://audit")
def gateway_audit() -> str:
    """Expose the local audit trail as read-only context."""
    return json.dumps([event.__dict__ for event in audit_log.list()], indent=2)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
