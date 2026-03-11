# application

## Purpose

This folder contains the application's use-cases and orchestration logic.

Its job is to describe what the system does at the workflow level.

Examples of use-cases include:
- list applicants
- get applicant by email
- ingest an uploaded PDF
- parse an applicant document and save it
- prepare applicant data for downstream evaluation

---

## Belongs here

- use-case functions/classes
- application services
- workflow orchestration
- DTOs related to application flows
- coordination between domain logic and infrastructure

Examples:
- `list_applicants.py`
- `get_applicant_by_email.py`
- `ingest_application.py`

---

## Does not belong here

- low-level SQL code
- PDF extraction implementation details
- MCP transport/server code
- UI widgets or rendering logic
- raw developer startup scripts

Those belong in:
- `infrastructure/`
- `mcp/`
- `presentation/`
- `scripts/`

---

## Design rule

`application/` answers the question:

**What is the system trying to do?**

It should coordinate work, not contain every technical detail of how that work is performed.