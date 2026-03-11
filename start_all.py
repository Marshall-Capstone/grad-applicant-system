"""
Docker Compose starts MySQL (capstone_sandbox-mysql-1 Running)
Backend waits until it can connect (MySQL is ready)
MCP backend starts and binds to http://127.0.0.1:8000/mcp
UI process runs separately and can exit independently
When UI exits, launcher stops the backend
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from scripts.venv_utils import in_venv, reexec_into_venv, venv_python
from scripts.docker_utils import ensure_docker_running, compose_cmd
from scripts.env_utils import child_env


def main() -> None:
    project_root = Path(__file__).resolve().parent

    if not in_venv():
        reexec_into_venv(project_root)

    py = venv_python(project_root)
    env = child_env(project_root)
    cwd = str(project_root)

    ensure_docker_running()
    print(f"Using compose command: {' '.join(compose_cmd())}")

    print("Starting backend in a separate process...")
    backend_proc = subprocess.Popen(
        [str(py), "-u", "-m", "scripts.run_backend"],
        cwd=cwd,
        env=env,
    )

    time.sleep(1.5)

    print("Starting UI in this process...")
    subprocess.run(
        [str(py), "-m", "scripts.run_ui"],
        cwd=cwd,
        env=env,
    )

    print("UI exited. Stopping backend...")
    backend_proc.terminate()


if __name__ == "__main__":
    main()