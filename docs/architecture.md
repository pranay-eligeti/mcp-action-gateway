# Architecture

```text
LLM / MCP host
      |
      v
  MCP Server
      |
      v
 typed tool call
      |
      v
 Policy / allowlist
      |
      +------> approval gate
      |
      v
 Action Registry
   |          |
   |          +--> n8n webhook adapter (optional)
   |
   +--> local event/audit action
      |
      v
 Audit Log
```

## Design goals

- Make tool schemas explicit through typed Python functions.
- Keep dangerous or high-impact actions behind an allowlist and approval gate.
- Record action outcomes in an audit trail.
- Keep external integrations optional and disabled by default.
- Make the project testable in-memory without network calls.

The implementation is deliberately a portfolio project. It does not contain
production credentials, employer data, PHI, or private n8n endpoints.
