"""Bootstrap the backend development process for the Grad Applicant System.

This script is a developer-facing entry point that ensures the local runtime
environment is ready before starting the MCP server. It is responsible for:

- re-executing into the project's virtual environment if needed
- ensuring Docker is running
- bringing up the project's Docker Compose services
- waiting for MySQL to accept connections
- starting the MCP HTTP server in the foreground

This file lives in `scripts/` because it is an operational launcher, not part
of the core application package itself.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from scripts.docker_utils import compose_cmd, ensure_docker_running
from scripts.venv_utils import in_venv, reexec_into_venv


def compose_up(project_root: Path) -> None:
    """Start the project's Docker Compose services in detached mode.

    This ensures the required local infrastructure, such as MySQL, is running
    before the backend server starts.

    Args:
        project_root: Repository root containing the docker-compose file.

    Raises:
        subprocess.CalledProcessError: If Docker Compose fails.
    """
    # Make sure the Docker engine is actually available before invoking Compose.
    ensure_docker_running()

    cmd = [*compose_cmd(), "up", "-d"]
    subprocess.run(cmd, cwd=project_root, check=True)


def wait_for_mysql(timeout_sec: int = 180) -> None:
    """Poll the configured MySQL instance until it becomes reachable.

    This is used after `docker compose up` because the container may be running
    before MySQL is ready to accept connections.

    Args:
        timeout_sec: Maximum number of seconds to wait for MySQL readiness.

    Raises:
        SystemExit: If required environment variables are missing or MySQL does
            not become available before the timeout expires.
    """
    import mysql.connector

    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MYSQL_PORT", "3307"))
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    required = ["MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Missing env vars in .env: {missing}")

    start = time.time()
    while True:
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connection_timeout=3,
            )
            conn.close()
            print("MySQL is ready.")
            return
        except Exception as exc:
            if time.time() - start > timeout_sec:
                raise SystemExit(
                    f"MySQL did not become ready in {timeout_sec}s.\nLast error: {exc}"
                )

            # Retry until the database accepts connections or the timeout expires.
            time.sleep(1)


def main() -> None:
    """Prepare the local backend environment and start the MCP server."""
    project_root = Path(__file__).resolve().parents[1]

    # Re-launch inside the project's virtual environment so imports and
    # dependencies are resolved consistently across developer machines.
    if not in_venv():
        reexec_into_venv(project_root)

    src_root = project_root / "src"
    if str(src_root) not in sys.path:
        # Allow direct package imports when this script is run from the repo root.
        sys.path.insert(0, str(src_root))

    from dotenv import load_dotenv
    from grad_applicant_system.mcp.server import serve

    # Ensure a .env exists for Docker and application configuration. If a
    # developer has not created one yet, seed it from the example file so local
    # startup has a usable baseline configuration.
    env_path = project_root / ".env"
    env_example = project_root / ".env.example"
    if not env_path.exists() and env_example.exists():
        shutil.copy(env_example, env_path)
        print("Created .env from .env.example. Review/update secrets as needed.")

    # Load environment variables before any Docker/MySQL/MCP startup logic.
    load_dotenv(env_path)

    print("Bringing up Docker services...")
    compose_up(project_root)

    print("Waiting for MySQL...")
    wait_for_mysql()

    # The backend runs in the foreground because this script is the dedicated
    # backend process entry point. Process orchestration happens elsewhere.
    print("Starting MCP HTTP server...")
    serve()


if __name__ == "__main__":
    main()