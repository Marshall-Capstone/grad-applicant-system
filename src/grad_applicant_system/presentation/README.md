# presentation

## Purpose

This folder contains human-facing presentation logic for the Graduate Applicant System.

Its job is to provide interfaces through which a person interacts with the system.

For this project, that primarily means the future ImGui-based UI.

---

## Belongs here

- UI application entrypoints
- windows
- views
- view models or UI state helpers
- presentation-specific formatting
- human-facing interaction logic

Examples:
- `ui/app.py`
- `ui/main_window.py`
- `ui/applicant_list_view.py`

---

## Does not belong here

- MCP transport logic
- low-level database access
- PDF parsing implementation
- core domain models
- Docker or environment startup scripts

Those belong in:
- `mcp/`
- `infrastructure/`
- `domain/`
- `scripts/`

---

## Design rule

`presentation/` answers the question:

**How does a human user interact with the system?**

It should focus on user interaction and display, while calling into application logic for actual system behavior.