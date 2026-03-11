
---

## `scripts/README.md`

```md
# scripts

## Purpose

This folder contains developer-facing helper scripts used to start, manage, and support the local development environment.

These scripts are orchestration and convenience entrypoints. They help with:
- starting backend services
- starting the UI
- preparing environment variables
- working with Docker
- managing the virtual environment

They should remain thin and should call into code under `src/` rather than becoming the home of core application logic.

---

## Current contents

### `docker_utils.py`
Utility functions for:
- checking whether Docker is installed and reachable
- locating Docker Desktop
- starting Docker Desktop if needed
- detecting the proper Docker Compose command

This file supports local environment setup and startup orchestration.

### `env_utils.py`
Utility functions for:
- reading `.env`
- applying environment variables without overwriting already-set values
- building a child process environment
- setting `PYTHONPATH` for subprocesses

This is local runtime/bootstrap support, not domain logic.

### `run_backend.py`
Starts the backend development environment by:
1. ensuring the virtual environment is active
2. loading `.env`
3. bringing up Docker services
4. waiting for MySQL to become available
5. starting the MCP HTTP server

This is a launch/orchestration script.

### `run_ui.py`
Starts the UI process.

Right now this is a placeholder entrypoint for the future ImGui-based UI. Eventually it should launch the real UI loop while keeping UI implementation details in `src/`.

### `venv_utils.py`
Intended to provide virtual environment helper functions such as:
- detecting whether the current process is already inside `.venv`
- re-executing into the project virtual environment
- locating the venv Python executable

> Note: if this file currently contains placeholder or duplicated code, it should be corrected so it matches its intended role.

---

## What belongs here

Good candidates for `scripts/`:

- launch scripts
- developer utilities
- local setup helpers
- Docker bootstrapping helpers
- environment bootstrapping helpers
- testing or smoke-run helper scripts that are specifically for local development

---

## What does not belong here

The following should **not** live in `scripts/`:

- MCP tool implementations
- database query logic
- PDF parsing logic
- applicant/domain models
- business rules
- UI widgets or rendering code
- long-term reusable application services

Those belong in `src/`.

---

## Relationship to the project

These scripts act as entrypoints into the real application.

Typical flow:

- root `start_all.py`
  - calls scripts in `scripts/`
  - which prepare the environment and launch processes
  - which then invoke the real runtime code under `src/`

So the folder should remain focused on startup and developer workflow support.

---

## Design rule

A script in this folder may:
- read environment variables
- launch Docker
- spawn or invoke app processes
- call into `src/`

A script in this folder should **not** become the place where system behavior is implemented.

If a script starts gaining real application logic, that logic should be moved into `src/`, and the script should become a thin wrapper around it.