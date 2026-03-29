"""run_backend.py = starts docker + waits for MySQL + starts MCP server (blocks)"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import shutil
from pathlib import Path

from scripts.docker_utils import compose_cmd, ensure_docker_running
from scripts.venv_utils import in_venv, reexec_into_venv


def compose_up(project_root: Path) -> None:
    ensure_docker_running()
    cmd = [*compose_cmd(), "up", "-d"]
    subprocess.run(cmd, cwd=project_root, check=True)


def wait_for_mysql(timeout_sec: int = 180) -> None:
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
        except Exception as e:
            if time.time() - start > timeout_sec:
                raise SystemExit(
                    f"MySQL did not become ready in {timeout_sec}s.\nLast error: {e}"
                )
            time.sleep(1)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    if not in_venv():
        reexec_into_venv(project_root)

    src_root = project_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from dotenv import load_dotenv
    from grad_applicant_system.mcp.server import serve

    # Ensure a .env exists for docker / app configuration. If the developer
    # hasn't created one, copy the example so `docker compose` and later
    # env lookups have sensible defaults.
    env_path = project_root / ".env"
    env_example = project_root / ".env.example"
    if not env_path.exists() and env_example.exists():
        shutil.copy(env_example, env_path)
        print("Created .env from .env.example. Review/update secrets as needed.")

    load_dotenv(env_path)

    print("Bringing up Docker services...")
    compose_up(project_root)

    print("Waiting for MySQL...")
    wait_for_mysql()

    print("Starting MCP HTTP server...")
    serve()


if __name__ == "__main__":
    main()