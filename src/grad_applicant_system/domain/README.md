# domain

## Purpose

This folder contains the core concepts and business-facing models of the Graduate Applicant System.

Its job is to represent the meaning of the system independent of transport, UI, or storage details.

Examples may include:
- applicant entities
- document metadata
- evaluation concepts
- shared business rules
- value objects and domain-level abstractions

---

## Belongs here

- core models
- domain entities
- value objects
- domain rules
- business-relevant abstractions

---

## Does not belong here

- SQL queries
- PDF parser implementations
- MCP server code
- UI code
- Docker/dev scripts

Those belong in:
- `infrastructure/`
- `mcp/`
- `presentation/`
- `scripts/`

---

## Design rule

`domain/` answers the question:

**What is this system about at its core?**

This folder should remain as independent as possible from external technologies.