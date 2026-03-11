# src

## Purpose

This folder contains the actual Python application code for the Graduate Applicant System.

Unlike `scripts/`, which contains developer-facing launch helpers, `src/` is where the runtime system itself lives.

This is the home of:
- backend application logic
- MCP server logic
- future database access layer
- future parsing/inference/integration code
- future UI implementation code

As the project matures, this folder should become the primary home of the system's reusable application code.

---

## Current contents

### `mcp_server_http.py`
This file currently defines and runs the MCP HTTP server.

Its responsibilities include:
- loading environment variables
- connecting to MySQL
- defining MCP tools
- exposing those tools over streamable HTTP

At the moment, it contains both:
- transport/server setup
- tool definitions
- direct database query logic

This is acceptable for an early sandbox, but later these concerns should be separated more cleanly.

### `mcp_smoke_client_http.py`
This is an early development/testing client used to verify that:
- the MCP server is reachable
- MCP tools are exposed correctly
- the server can communicate with MySQL
- tool results come back in the expected format

This file is primarily a smoke-test / development validation tool.

It may later be:
- removed
- moved to `scripts/`
- moved to `tests/`
- replaced by more formal integration tests

---

## What belongs here

Good candidates for `src/`:

- application runtime code
- MCP server code
- MCP tool definitions
- business/use-case logic
- database access code
- parsing modules
- document ingestion code
- UI implementation code
- reusable internal services

---

## What does not belong here

The following should generally **not** live in `src/`:

- ad hoc one-off launch helpers
- Docker startup wrappers
- virtual environment helpers
- shell-like orchestration scripts
- project management notes
- database seed SQL files

Those belong in:
- `scripts/`
- `db/`
- root documentation files

---

## Current architectural status

Right now `src/` is still in an early-stage sandbox form.

The current MCP server file combines several responsibilities:
- environment handling
- persistence access
- tool definitions
- HTTP transport

That is reasonable for proving the concept, but the long-term goal should be to move toward clearer boundaries.

A likely future structure is:

```text
src/
└─ grad_applicant_system/
   ├─ mcp/
   │  ├─ server.py
   │  └─ tools/
   ├─ infrastructure/
   │  ├─ persistence/
   │  └─ parsing/
   ├─ application/
   ├─ domain/
   └─ presentation/
      └─ ui/