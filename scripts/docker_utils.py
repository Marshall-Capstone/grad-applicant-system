from __future__ import annotations

"""Utilities for detecting and starting Docker during local development.

This module supports developer-facing startup scripts by checking whether the
Docker CLI and engine are available, locating Docker Desktop on Windows, and
choosing the correct Docker Compose command variant for the host machine.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path


def docker_ok() -> bool:
    """Return True if the Docker CLI is installed and the engine is reachable."""
    docker = shutil.which("docker")
    if not docker:
        # Docker is not on PATH, so nothing else in this module can work.
        return False

    try:
        # `docker info` is a simple way to verify both the CLI and daemon.
        p = subprocess.run(
            [docker, "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return p.returncode == 0
    except Exception:
        # Treat any unexpected process/OS failure as "Docker not available."
        return False


def find_docker_desktop_exe() -> Path | None:
    """Return the Docker Desktop executable path on Windows, if found."""
    candidates: list[Path] = []

    # Check the standard system-wide installation path first.
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.append(Path(pf) / "Docker" / "Docker" / "Docker Desktop.exe")

    # Some installations live under the current user's LOCALAPPDATA directory.
    lap = os.environ.get("LOCALAPPDATA")
    if lap:
        candidates.append(
            Path(lap) / "Programs" / "Docker" / "Docker" / "Docker Desktop.exe"
        )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def _start_docker_desktop(exe: Path) -> None:
    """Start Docker Desktop in a detached process.

    On Windows, detached creation flags are used so Docker Desktop is not tied
    to the current console window. On other platforms, a normal background
    process launch is used.
    """
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200

        # Launch Docker Desktop independently of the current terminal session.
        subprocess.Popen(
            [str(exe)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        )
    else:
        subprocess.Popen(
            [str(exe)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def ensure_docker_running(
    timeout_seconds: int = 300,
    poll_seconds: float = 0.5,
) -> None:
    """Ensure the Docker engine is reachable before continuing.

    If Docker is already running, this function returns immediately. Otherwise,
    it attempts to locate and start Docker Desktop, then polls until the Docker
    engine becomes reachable or the timeout expires.

    Args:
        timeout_seconds: Maximum time to wait for Docker to become available.
        poll_seconds: Delay between readiness checks.

    Raises:
        RuntimeError: If Docker is unavailable, Docker Desktop cannot be found,
            or the engine does not become reachable before the timeout.
    """
    if docker_ok():
        # Fast path for machines where Docker is already running.
        return

    exe = find_docker_desktop_exe()
    if exe is None:
        raise RuntimeError(
            "Docker engine is not reachable, and Docker Desktop.exe was not found. "
            "Install Docker Desktop and ensure 'docker' is on PATH."
        )

    print("Docker engine not reachable. Starting Docker Desktop...")
    _start_docker_desktop(exe)

    # Poll until Docker responds or until we hit the timeout.
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if docker_ok():
            print("Docker is up.")
            return
        time.sleep(poll_seconds)

    raise RuntimeError(
        f"Docker Desktop started, but the Docker engine still isn't reachable after {timeout_seconds}s. "
        "Open Docker Desktop and confirm the engine is running."
    )


def compose_cmd() -> list[str]:
    """Return the available Docker Compose command prefix.

    Prefers the modern `docker compose` form and falls back to the legacy
    `docker-compose` executable when necessary.

    Returns:
        A command prefix such as ['docker', 'compose'] or ['docker-compose'].

    Raises:
        RuntimeError: If neither Compose variant is available on PATH.
    """
    docker = shutil.which("docker")
    if docker:
        # Prefer the plugin-based Compose command when supported.
        p = subprocess.run(
            [docker, "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if p.returncode == 0:
            return [docker, "compose"]

    docker_compose = shutil.which("docker-compose")
    if docker_compose:
        # Fall back to the standalone legacy executable.
        return [docker_compose]

    raise RuntimeError(
        "Neither 'docker compose' nor 'docker-compose' was found on PATH."
    )