"""Launch the full local development stack for the Grad Applicant System.

This top-level script coordinates the two-process local workflow used during
development:

- ensure the project is running inside the expected virtual environment
- prepare a child-process environment with `.env` values and `src/` on PYTHONPATH
- ensure Docker is available for MySQL
- start the backend/MCP server in a separate process
- run the desktop UI in the foreground
- stop the backend when the UI exits

This file lives at the repository root because it is a developer convenience
launcher rather than part of the application package itself.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from scripts.docker_utils import compose_cmd, ensure_docker_running
from scripts.env_utils import child_env
from scripts.venv_utils import in_venv, reexec_into_venv, venv_python


def main() -> None:
    """Start the backend process, run the UI, and stop the backend on exit."""
    project_root = Path(__file__).resolve().parent

    # Re-launch inside the project's virtual environment so both child processes
    # inherit a consistent interpreter and dependency set.
    if not in_venv():
        reexec_into_venv(project_root)

    py = venv_python(project_root)
    env = child_env(project_root)
    cwd = str(project_root)

    # Docker must be available before the backend attempts to bring up MySQL.
    ensure_docker_running()
    print(f"Using compose command: {' '.join(compose_cmd())}")

    print("Starting backend in a separate process...")
    backend_proc = subprocess.Popen(
        [str(py), "-u", "-m", "scripts.run_backend"],
        cwd=cwd,
        env=env,
    )

    # Give the backend a brief head start so it can begin Docker/MySQL startup
    # before the UI tries to interact with the system.
    time.sleep(5.0)

    # Run the UI in the foreground so closing the window ends the local session
    # naturally for the developer.
    print("Starting UI in this process...")
    subprocess.run(
        [str(py), "-m", "scripts.run_ui"],
        cwd=cwd,
        env=env,
    )

    # Once the UI exits, shut down the backend process to avoid leaving the
    # local development session half-running.
    print("UI exited. Stopping backend...")
    backend_proc.terminate()


if __name__ == "__main__":
    main()