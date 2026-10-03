"""Adapter and policy tests with HTTP fully mocked."""

import httpx
import pytest

from src.actions import ActionRegistry, GatewayConfig
from src.audit import AuditLog
from src.policy import ActionPolicy


def registry(url=None):
    return ActionRegistry(
        ActionPolicy(frozenset({"log_event", "notify_n8n"}), frozenset({"notify_n8n"})),
        AuditLog(),
        GatewayConfig(url),
    )


@pytest.mark.asyncio
async def test_approved_dry_run_and_policy_failure_audited():
    actions = registry()
    assert (await actions.run_action("notify_n8n", {}, approved=True))["status"] == "dry_run"
    assert actions.audit.list()[-1].status == "dry_run"
    with pytest.raises(PermissionError):
        await actions.run_action("unknown", {})
    assert actions.audit.list()[-1].status == "error"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 503])
async def test_webhook_dispatch_and_sanitized_failure(monkeypatch, status):
    url = "https://example.invalid/webhook/dummy-private-token"
    actions = registry(url)
    real_client = httpx.AsyncClient
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(status, text="dummy private response")

    def client(**kwargs):
        assert kwargs["timeout"] == 10
        return real_client(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client)
    if status == 200:
        assert (await actions.run_action("notify_n8n", {"message": "safe"}, True))[
            "status"
        ] == "sent"
    else:
        with pytest.raises(RuntimeError, match="n8n webhook delivery failed") as error:
            await actions.run_action("notify_n8n", {"message": "safe"}, True)
        assert error.value.__suppress_context__
        assert url not in str(error.value)
    assert len(seen) == 1
    assert seen[0].method == "POST" and seen[0].content == b'{"message":"safe"}'
    assert "dummy-private-token" not in actions.audit.list()[-1].details


@pytest.mark.asyncio
async def test_unapproved_webhook_never_constructs_client(monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError("Policy must reject before HTTP")

    monkeypatch.setattr(httpx, "AsyncClient", forbidden)
    with pytest.raises(PermissionError):
        await registry("https://example.invalid").run_action("notify_n8n", {})
