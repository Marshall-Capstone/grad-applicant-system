# Graduate Applicant System

Graduate Applicant System is a Python desktop application for ingesting, storing, and querying graduate applicant data.

The project currently combines:

- a desktop UI built with ImGui + GLFW
- a MySQL database running in Docker
- an MCP HTTP server that exposes applicant query tools
- an Anthropic-backed assistant for database/tool querying
- a local fake assistant fallback for development when the real assistant is unavailable
- a centralized PDF ingestion workflow that parses applicant packets, extracts fields, and persists them to MySQL

---

## Current State

The project is no longer just a scaffold. The main workflow now works end to end:

1. A user uploads an applicant PDF from the UI.
2. The UI sends the file through the shared `PdfIngestionService`.
3. The system parses the PDF, extracts applicant fields, and persists the result to MySQL.
4. The extracted fields are shown back in the UI transcript as a preview.
5. The assistant can then answer database-backed questions about ingested applicants.

### Important architectural rule

**PDF upload from the UI is the authoritative ingestion path.**

The assistant is now **query-only**. It does **not** orchestrate PDF ingestion. Applicant documents are ingested and persisted first; the assistant then queries the existing data through the MCP/tool layer.

---

## Features

- Desktop UI with transcript, top menu, and message composer
- UI-driven applicant PDF upload and immediate persistence
- Page-aware PDF parsing and field extraction
- MySQL-backed applicant storage
- MCP server exposing applicant query tools
- Anthropic assistant integration for natural-language querying
- Fake assistant fallback for local/dev use without a real API-backed assistant
- Startup scripts for launching Docker, backend, and UI processes together
- Integration smoke tests for MCP connectivity and PDF ingestion

---

## Project Structure

```text
grad-applicant-system/
├── assets
│   └── ui
│       └── emblem.png
├── db
│   ├── init
│   │   ├── 001_schema_applicants.sql
│   │   └── 002_seed_applicants.sql
│   ├── __init__.py
│   └── README.md
├── scripts
│   ├── __init__.py
│   ├── docker_utils.py
│   ├── env_utils.py
│   ├── README.md
│   ├── run_backend.py
│   ├── run_ui.py
│   └── venv_utils.py
├── src
│   ├── grad_applicant_system
│   │   ├── application
│   │   │   ├── ports
│   │   │   │   ├── __init__.py
│   │   │   │   ├── applicant_assistant_service.py
│   │   │   │   ├── document_parser.py
│   │   │   │   └── extraction_processor.py
│   │   │   ├── __init__.py
│   │   │   └── README.md
│   │   ├── infrastructure
│   │   │   ├── assistant
│   │   │   │   ├── __init__.py
│   │   │   │   ├── anthropic_applicant_assistant_service.py
│   │   │   │   └── fake_applicant_assistant_service.py
│   │   │   ├── mcp
│   │   │   │   ├── __init__.py
│   │   │   │   └── mcp_tool_client.py
│   │   │   ├── parsing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pdf_document_parser.py
│   │   │   │   ├── pdf_ingestion_service.py
│   │   │   │   └── simple_extraction_processor.py
│   │   │   ├── persistence
│   │   │   │   ├── __init__.py
│   │   │   │   └── mysql_persistence.py
│   │   │   ├── __init__.py
│   │   │   └── README.md
│   │   ├── mcp
│   │   │   ├── __init__.py
│   │   │   ├── README.md
│   │   │   └── server.py
│   │   ├── presentation
│   │   │   ├── ui
│   │   │   │   ├── panes
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_pane.py
│   │   │   │   │   ├── message_composer_pane.py
│   │   │   │   │   ├── top_menu_pane.py
│   │   │   │   │   └── transcript_pane.py
│   │   │   │   ├── viewmodels
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── message_composer_viewmodel.py
│   │   │   │   ├── views
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_view.py
│   │   │   │   │   └── main_view.py
│   │   │   │   ├── widgets
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_widget.py
│   │   │   │   │   ├── button_widget.py
│   │   │   │   │   ├── separator_widget.py
│   │   │   │   │   ├── text_input_widget.py
│   │   │   │   │   └── text_widget.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── app.py
│   │   │   │   └── window.py
│   │   │   ├── __init__.py
│   │   │   └── README.md
│   │   └── __init__.py
│   └── README.md
├── tests
│   └── integration
│       ├── mcp_smoke_client.py
│       ├── parser_core_smoke.py
│       ├── pdf_ingestion_persist_smoke.py
│       └── pdf_ingestion_service_smoke.py
├── .env
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── imgui.ini
├── README.md
├── requirements.txt
└── start_all.py
```

---

## Architecture Overview

The repository is organized by responsibility.

### `scripts/`

Developer-facing entry points and environment/bootstrap helpers.

- `start_all.py` orchestrates the local development session.
- `scripts/run_backend.py` starts Docker-backed services and the MCP server.
- `scripts/run_ui.py` launches the desktop UI process.
- helper modules handle Docker checks, environment shaping, and virtual environment re-execution.

### `src/grad_applicant_system/application/`

Application-facing ports and boundaries.

This layer defines the contracts that infrastructure implementations satisfy, such as:

- assistant service interface
- document parser interface
- extraction processor interface

### `src/grad_applicant_system/infrastructure/`

Technical implementations.

This is where the project's concrete behavior lives:

- Anthropic and fake assistant implementations
- MCP tool client
- PDF parsing and extraction logic
- centralized PDF ingestion service
- MySQL persistence

### `src/grad_applicant_system/mcp/`

MCP server/runtime layer.

This exposes query tools over HTTP so the assistant can query applicant data already stored in MySQL.

### `src/grad_applicant_system/presentation/`

Human-facing desktop UI.

This includes:

- the UI composition root (`presentation/ui/app.py`)
- window management
- panes, widgets, views, and view models

---

## Runtime Flow

### Local process model

When `start_all.py` runs:

1. the project re-execs into the local virtual environment if needed
2. Docker availability is checked
3. the backend process is started with `scripts.run_backend`
4. Docker Compose is brought up and MySQL is waited on
5. the MCP server starts
6. the UI process is launched with `scripts.run_ui`
7. when the UI exits, the launcher terminates the backend process

### UI ingestion flow

The UI upload path is the authoritative workflow for applicant imports:

1. user selects one or more PDF files
2. the view model calls `PdfIngestionService`
3. `PdfIngestionService` uses:
   - `PDFDocumentParser` for raw text extraction
   - `SimpleExtractionProcessor` for page-aware field extraction
   - MySQL persistence logic for saving the result
4. extracted fields are shown in the transcript
5. the ingested applicant is immediately available for later assistant/database queries

### Assistant flow

The assistant is query-only:

1. the user sends a chat message
2. the assistant uses MCP query tools as needed
3. the assistant returns a natural-language reply based on existing database content

The assistant does **not** perform PDF ingestion.

---

## Requirements

Before running the project locally, make sure you have:

- Python 3.x installed
- Docker Desktop installed
- Git installed
- a terminal such as PowerShell

For full assistant behavior, you will also need an Anthropic API key. Without one, the application can still run using the fake assistant fallback.

---

## Initial Setup

### 1. Clone the repository

```powershell
git clone <YOUR-REPO-URL>
cd grad-applicant-system
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

If `venv` stalls during pip bootstrapping, you can use:

```powershell
python -m venv .venv --without-pip
.\.venv\Scripts\python.exe -m ensurepip --upgrade
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Create your local `.env`

```powershell
Copy-Item .env.example .env
```

Then update `.env` with your local values.

---

## Environment Variables

The project expects a `.env` file at the repository root.

Example:

```env
# MySQL container / connection settings
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_DATABASE=grad_applicant_system
MYSQL_USER=grad_app_user
MYSQL_PASSWORD=change_me
MYSQL_ROOT_PASSWORD=change_root_me

# MCP server settings
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_SERVER_URL=http://127.0.0.1:8000/mcp

# Assistant settings
USE_REAL_ASSISTANT=true
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_API_KEY=your_api_key_here
```

### Notes

- `.env` is for local development and should not be committed.
- `.env.example` should contain placeholder values only.
- if `USE_REAL_ASSISTANT=false`, the application will use the fake assistant fallback.

---

## Running the Project

### Recommended: run the full local stack

```powershell
python start_all.py
```

This will:

- ensure the project is running from the virtual environment
- ensure Docker is running
- start backend services
- wait for MySQL
- start the MCP server
- launch the desktop UI

### Run the backend only

```powershell
python -m scripts.run_backend
```

### Run the UI only

```powershell
python -m scripts.run_ui
```

---

## Smoke Tests

The repository includes integration smoke tests under `tests/integration/`.

### MCP smoke test

Run this after the backend is up:

```powershell
python tests\integration\mcp_smoke_client.py
```

This verifies that:

- the MCP server is reachable
- tools are listed correctly
- applicant query tools can be called successfully

### PDF ingestion smoke tests

These help validate parsing, extraction, and persistence behavior:

```powershell
python tests\integration\parser_core_smoke.py
python tests\integration\pdf_ingestion_service_smoke.py
python tests\integration\pdf_ingestion_persist_smoke.py
```

---

## Database Notes

The `db/init/` folder contains the SQL used to initialize the local MySQL container.

- `001_schema_applicants.sql` defines the schema
- `002_seed_applicants.sql` provides development seed data

Because Docker uses an initialized data volume, schema/seed updates may require resetting volumes during development.

A common refresh flow is:

```powershell
docker compose down -v
docker compose up -d
```

If your local machine uses a different Compose command form, the project scripts will attempt to use either `docker compose` or `docker-compose` automatically.

---

## Development Notes

### `src/` layout

This repository uses a `src/` layout. The importable package lives under:

```text
src/grad_applicant_system/
```

### Code placement guidelines

Place new code according to its role:

- developer/process launch helpers -> `scripts/`
- application interfaces/ports -> `src/grad_applicant_system/application/`
- concrete technical implementations -> `src/grad_applicant_system/infrastructure/`
- MCP server/tool exposure -> `src/grad_applicant_system/mcp/`
- desktop UI code -> `src/grad_applicant_system/presentation/`
- SQL/bootstrap assets -> `db/`

### Current architectural direction

The current project shape is intentionally pragmatic:

- assistant responsibilities are limited to chat and querying
- PDF ingestion is handled by the UI workflow and shared ingestion service
- MCP tools are kept focused on querying stored applicant data

---

## Troubleshooting

### Docker is not starting

Make sure Docker Desktop is installed and the Docker engine is reachable.

### MySQL does not become ready

Check:

- your `.env` values
- whether Docker containers are healthy
- whether another local service is already using the configured MySQL port

### Assistant is not using the real model

Check:

- `USE_REAL_ASSISTANT=true`
- `ANTHROPIC_API_KEY` is set
- `MCP_SERVER_URL` matches the running backend

If those are not configured, the application may fall back to the fake assistant.

### Python imports are unresolved

Make sure:

- the virtual environment is activated
- dependencies are installed
- your editor is using the project's `.venv` interpreter

### Need to rebuild the database from seed

You may need to remove the Docker volume and recreate containers:

```powershell
docker compose down -v
docker compose up -d
```

---

## Additional Project Docs

The repository also includes:

- `ARCHITECTURE.md`
- `CONTRIBUTING.md`
- folder-level `README.md` files inside `db/`, `scripts/`, `application/`, `infrastructure/`, `mcp/`, and `presentation/`

These provide more focused notes about boundaries and local development responsibilities.
