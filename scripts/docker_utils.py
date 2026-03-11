from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path


def docker_ok() -> bool:
    docker = shutil.which("docker")
    if not docker:
        return False
    try:
        p = subprocess.run([docker, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return p.returncode == 0
    except Exception:
        return False


def find_docker_desktop_exe() -> Path | None:
    candidates: list[Path] = []
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.append(Path(pf) / "Docker" / "Docker" / "Docker Desktop.exe")
    lap = os.environ.get("LOCALAPPDATA")
    if lap:
        candidates.append(Path(lap) / "Programs" / "Docker" / "Docker" / "Docker Desktop.exe")
    for c in candidates:
        if c.exists():
            return c
    return None


def _start_docker_desktop(exe: Path) -> None:
    """Best-effort 'background' start for Docker Desktop."""
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200

        # These flags avoid tying Docker Desktop to your console window.
        subprocess.Popen(
            [str(exe)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        )
    else:
        subprocess.Popen([str(exe)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_docker_running(timeout_seconds: int = 300, poll_seconds: float = 0.5) -> None:
    """
    Ensure Docker engine is reachable. If not, start Docker Desktop and wait.

    Increase timeout_seconds on slower machines.
    """
    if docker_ok():
        return

    exe = find_docker_desktop_exe()
    if exe is None:
        raise RuntimeError(
            "Docker engine is not reachable, and Docker Desktop.exe was not found. "
            "Install Docker Desktop and ensure 'docker' is on PATH."
        )

    print("Docker engine not reachable. Starting Docker Desktop...")
    _start_docker_desktop(exe)

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
    """
    Prefer: docker compose
    Fallback: docker-compose

    Returns the command prefix as a list, e.g. ['docker', 'compose'] or ['docker-compose'].
    """
    docker = shutil.which("docker")
    if docker:
        p = subprocess.run([docker, "compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if p.returncode == 0:
            return [docker, "compose"]

    docker_compose = shutil.which("docker-compose")
    if docker_compose:
        return [docker_compose]

    raise RuntimeError("Neither 'docker compose' nor 'docker-compose' was found on PATH.")