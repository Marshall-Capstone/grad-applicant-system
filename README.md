# Graduate Applicant System

Graduate Applicant System is a Python-based project for ingesting, storing, querying, and exposing graduate applicant data through an MCP server backed by MySQL running in Docker.

At the current stage, the project provides:

- a MySQL database running in Docker
- an MCP HTTP server that exposes applicant-related tools
- startup scripts for backend and future UI workflows
- a smoke-test client used to verify MCP-to-MySQL communication
- a structured project layout prepared for future parsing, UI, and application logic work

---

## Current Goals

This repository is being structured to support future development in several areas:

- PDF parsing and applicant data extraction
- persistence of applicant/application data into MySQL
- MCP tool exposure for LLM interaction
- a future ImGui-based user interface
- cleaner separation of concerns across application layers

---

## Project Structure

```text
grad-applicant-system/
├─ db/
│  ├─ init/
│  └─ README.md
├─ scripts/
│  ├─ docker_utils.py
│  ├─ env_utils.py
│  ├─ run_backend.py
│  ├─ run_ui.py
│  ├─ venv_utils.py
│  └─ README.md
├─ src/
│  ├─ README.md
│  └─ grad_applicant_system/
│     ├─ __init__.py
│     ├─ application/
│     │  ├─ __init__.py
│     │  └─ README.md
│     ├─ domain/
│     │  ├─ __init__.py
│     │  └─ README.md
│     ├─ infrastructure/
│     │  ├─ __init__.py
│     │  ├─ parsing/
│     │  │  └─ __init__.py
│     │  ├─ persistence/
│     │  │  └─ __init__.py
│     │  └─ README.md
│     ├─ mcp/
│     │  ├─ __init__.py
│     │  ├─ server.py
│     │  └─ README.md
│     └─ presentation/
│        ├─ __init__.py
│        ├─ ui/
│        │  └─ __init__.py
│        └─ README.md
├─ tests/
│  └─ mcp_smoke_client.py
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
├─ requirements.txt
├─ start_all.py
└─ README.md
```

## Architecture Overview

The repository is organized by responsibility.

### Root-level folders

#### `db/`

Database setup artifacts such as schema and seed/init SQL.

#### `scripts/`

Developer-facing helper scripts for startup, environment setup, Docker bootstrapping, and local workflow support.

#### `src/`

The actual Python application code.

#### `tests/`

Integration and validation code, including early smoke-test utilities.

### Application folders inside `src/grad_applicant_system/`

#### `mcp/`

MCP server logic and tool exposure layer.

#### `infrastructure/`

Technical implementations such as persistence and parsing.

#### `application/`

Use-cases and orchestration logic.

#### `domain/`

Core concepts and business-facing models.

#### `presentation/`

Human-facing interface logic, including the future ImGui UI.

---

## Requirements

Before running the project, make sure you have:

- Python 3.12+ or another compatible Python version installed
- Docker Desktop installed and running
- Git installed
- PowerShell or another terminal

---

## Initial Setup

### 1. Clone the repository

```powershell
git clone <YOUR-REPO-URL>
cd grad-applicant-system
```

### 2. Create the virtual environment

```powershell
python -m venv .venv
```

If that stalls during pip bootstrapping on your machine, use:

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

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` with your local values.

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
```

### Important notes

- `.env` is for local development and should not be committed.
- `.env.example` should remain safe for GitHub and contain placeholder values only.

---

## Running the Project

### Start the backend

The main project entry point is:

```powershell
python start_all.py
```

This starts the backend workflow, which currently includes:

- ensuring the virtual environment is being used
- bringing up Docker services
- waiting for MySQL to become available
- starting the MCP server

When successful, the server should be available at:

```text
http://127.0.0.1:8000/mcp
```

---

## Smoke Test

A smoke-test client is included to verify that:

- the MCP server is reachable
- tools are exposed correctly
- the server can communicate with the MySQL container
- tool calls return expected data

Run it in a second terminal after the backend is up:

```powershell
python tests\mcp_smoke_client.py
```

Expected behavior includes output such as:

- discovered tool names
- successful `list_applicants` results
- structured content returned from the MCP server

---

## Database Notes

The `db/init/` folder contains initialization assets used by Docker/MySQL startup.

At this stage, those files exist to preserve working development behavior from earlier sandbox testing. Over time, the contents of `db/init/` may be refined to focus on:

- schema creation
- optional development seed data
- repeatable local bootstrap behavior

Even though future applicant records are expected to come from parsed PDF data, schema files will continue to belong here.

---

## UI Status

The project includes a placeholder UI startup path through `scripts/run_ui.py`.

A future ImGui-based UI will be developed under:

```text
src/grad_applicant_system/presentation/ui/
```

At the moment, UI infrastructure is scaffolded but not yet implemented as the main user workflow.

---

## Development Notes

### Imports and package layout

This repository uses a `src/` layout. The importable Python package lives under:

```text
src/grad_applicant_system/
```

Examples of future imports:

```python
from grad_applicant_system.mcp.server import serve
```

### Folder responsibility matters

Please place new code according to its role:

- developer helper/startup scripts -> `scripts/`
- MCP exposure logic -> `src/grad_applicant_system/mcp/`
- DB or parser implementation -> `src/grad_applicant_system/infrastructure/`
- use-cases/workflow logic -> `src/grad_applicant_system/application/`
- UI code -> `src/grad_applicant_system/presentation/`
- schema/init SQL -> `db/`

Folder-specific `README.md` files explain boundaries in more detail.

---

## Troubleshooting

### Docker is not starting

Make sure Docker Desktop is installed and running. The backend scripts attempt to detect Docker availability, but the Docker engine must still be reachable.

### `dotenv` or `mysql.connector` is not recognized

Make sure your virtual environment is activated and dependencies are installed into the active interpreter:

```powershell
python -m pip install -r requirements.txt
```

### VS Code still shows unresolved imports

Check that VS Code is using the project interpreter:

```text
<repo-root>\.venv\Scripts\python.exe
```

### Port conflict with MySQL

If another local project is already using port `3307` or `3306`, update:

- `MYSQL_PORT` in `.env`
- the matching port mapping in `docker-compose.yml`