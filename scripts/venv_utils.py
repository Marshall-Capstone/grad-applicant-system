from __future__ import annotations

import os
import sys
from pathlib import Path


def in_venv() -> bool:
    return getattr(sys, "base_prefix", sys.prefix) != sys.prefix


def venv_python(project_root: Path) -> Path:
    if os.name == "nt":
        return project_root / ".venv" / "Scripts" / "python.exe"
    return project_root / ".venv" / "bin" / "python"


def reexec_into_venv(project_root: Path) -> None:
    py = venv_python(project_root)
    if not py.exists():
        raise SystemExit(
            f"Virtual env python not found at: {py}\n"
            "Create venv first: python -m venv .venv\n"
            "Then install deps: .venv\\Scripts\\pip install -r requirements\\base.txt"
        )
    os.execv(str(py), [str(py), *sys.argv])