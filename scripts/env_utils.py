from __future__ import annotations

import os
from pathlib import Path


def apply_dotenv(env: dict[str, str], dotenv_path: Path) -> dict[str, str]:
    if not dotenv_path.exists():
        return env

    for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        env.setdefault(k, v)
    return env


def child_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env = apply_dotenv(env, project_root / ".env")

    src_root = str(project_root / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src_root if not existing else src_root + os.pathsep + existing
    return env