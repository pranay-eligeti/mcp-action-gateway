# MCP Action Gateway

> A Python Model Context Protocol (MCP) gateway that turns typed tool calls into controlled operational actions through policy, approval, and audit boundaries.

[![Python CI](https://github.com/pranay-eligeti/mcp-action-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/pranay-eligeti/mcp-action-gateway/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python)
![MCP](https://img.shields.io/badge/MCP-2026%20SDK-purple)
![Tests](https://img.shields.io/badge/tests-pytest-orange)

## Why this project

I have worked with MCP-based automation where an LLM moves beyond chat and invokes operational workflows.

This repository turns that concept into a public, sanitized implementation: an MCP server exposes typed actions, an allowlist decides what can run, approval gates protect sensitive actions, and an audit log records outcomes.

It contains no employer credentials, PHI, private workflow definitions, or private endpoints.

## Architecture

```text
LLM / MCP host
      |
      v
MCP Server (typed tools)
      |
      v
Policy / allowlist
      |
      +--> approval gate for sensitive action
      |
      v
Action Registry
   |          |
   |          +--> optional n8n webhook
   |
   +--> local event action
      |
      v
Audit Log
```

## Exposed MCP primitives

### Tools

`get_system_status`  
Returns a small operational status object.

`run_action(action, message, approved)`  
Runs an allowlisted action. `notify_n8n` requires explicit approval; when no webhook is configured it remains a dry run.

### Resources

`gateway://policy`  
Read-only view of the active allowlist and approval requirements.

`gateway://audit`  
Read-only view of the local audit trail.

## Quick start

Requires Python 3.10+; CI runs on Python 3.12. The project pins `mcp>=2,<3` and uses `MCPServer` and the in-memory `Client` API.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
pytest -q
```

Run the server over Streamable HTTP:

```bash
python -m src.server
```

For development, the MCP SDK also provides an Inspector workflow.

## Engineering decisions

**Typed contracts**  
Python type hints define tool input/output contracts instead of hand-written protocol parsing.

**Policy boundary**  
The server does not execute arbitrary tool names. Every action must be allowlisted, and sensitive actions can require explicit approval.

**Auditability**  
Successes, dry runs, and failures are recorded as structured audit events.

**Safe defaults**  
The optional n8n adapter does nothing unless `N8N_WEBHOOK_URL` is configured; the public test suite never performs network calls.

**In-memory testing**  
The official MCP SDK supports testing a server through an in-memory `Client(mcp)` connection, so tests avoid a running port or subprocess.

## Try a controlled action

From the repository root, this credential-free example invokes the real MCP protocol in memory:

```python
import asyncio
from mcp import Client
from src.server import mcp

async def main():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "run_action", {"action": "log_event", "message": "portfolio demo"}
        )
        print(result.structured_content)

asyncio.run(main())
```

The result contains `{"status": "ok", "action": "log_event"}`. The test suite verifies tool discovery, event execution/auditing, rejection of unapproved n8n actions, and rejection of unknown actions.

## Integration boundaries

`N8N_WEBHOOK_URL` is read from the process environment when the server is imported. An approved `notify_n8n` call posts JSON with a 10-second timeout; without a URL it records a dry run. The `approved` flag is supplied by the MCP caller: a deployed host must establish human authorization before setting it. This flag is an action-policy check, not user authentication.

The audit trail is in memory. Durable storage, retries, and idempotency are extension points rather than implemented guarantees.

## Extending the gateway

A natural next step is a typed connector layer for additional actions such as ticket creation, CRM updates, or workflow triggers. Each connector should remain behind the same policy, approval, timeout, retry, idempotency, and audit boundary.

## Security / privacy

Never commit:

- API keys or tokens
- n8n webhook URLs from private systems
- healthcare records or PHI
- employer-only workflow definitions
- session files or private channel identifiers

This repository intentionally demonstrates the architecture without publishing private operational systems.

## Author

**Pranay Eligeti**  
[LinkedIn](https://www.linkedin.com/in/pranay-eligeti) · [GitHub](https://github.com/pranay-eligeti)
