# infrastructure

## Purpose

This folder contains concrete technical implementations used by the application.

Its job is to connect the system to external or technical resources such as:
- databases
- document files
- PDF parsers
- external services
- future LLM or integration clients

---

## Belongs here

- MySQL connection code
- repository implementations
- SQL execution helpers
- PDF parsing code
- text extraction code
- file ingestion helpers
- integration adapters

Examples:
- `persistence/mysql_connection.py`
- `persistence/applicant_repository.py`
- `parsing/pdf_parser.py`

---

## Does not belong here

- MCP server transport
- UI rendering code
- core business workflow definitions
- high-level use-case orchestration
- developer startup scripts

Those belong in:
- `mcp/`
- `presentation/`
- `application/`
- `scripts/`

---

## Design rule

`infrastructure/` answers the question:

**How does the system technically connect to resources?**

It should support the application layer, not control the whole system flow.