import pytest
from mcp import Client

from src.server import mcp, policy, audit_log


@pytest.mark.asyncio
async def test_tools_are_exposed():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert {"get_system_status", "run_action"}.issubset(names)


@pytest.mark.asyncio
async def test_log_action_executes_and_audits():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "run_action",
            {"action": "log_event", "message": "portfolio test"},
        )
        assert result.structured_content["status"] == "ok"
        assert audit_log.list()[-1].action == "log_event"


@pytest.mark.asyncio
async def test_n8n_action_requires_approval():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "run_action",
            {"action": "notify_n8n", "message": "not approved"},
        )
        assert result.is_error is True


@pytest.mark.asyncio
async def test_policy_blocks_unknown_action_directly():
    with pytest.raises(PermissionError):
        policy.authorize("delete_everything")
