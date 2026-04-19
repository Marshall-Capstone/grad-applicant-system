from __future__ import annotations

"""Environment helpers for local startup scripts.

This module builds the environment dictionaries used by child processes started
from the repository's developer-facing scripts. It applies values from the
project's `.env` file and ensures the `src/` directory is available on
`PYTHONPATH` so package imports resolve correctly when launching subprocesses.
"""

import os
from pathlib import Path


def apply_dotenv(env: dict[str, str], dotenv_path: Path) -> dict[str, str]:
    """Merge simple KEY=VALUE entries from a .env file into an environment dict.

    Existing keys in `env` are preserved. This allows shell-defined variables to
    take precedence over defaults in the project's `.env` file.

    Args:
        env: The environment mapping to update.
        dotenv_path: Path to the `.env` file to read.

    Returns:
        The updated environment mapping.
    """
    if not dotenv_path.exists():
        # Missing .env is allowed so scripts can still run with shell-provided
        # environment variables or other external configuration.
        return env

    for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        # Ignore blank lines, comments, and malformed entries.
        if not line or line.startswith("#") or "=" not in line:
            continue

        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")

        # Preserve any value already supplied by the parent environment.
        env.setdefault(k, v)

    return env


def child_env(project_root: Path) -> dict[str, str]:
    """Build the environment used for child Python processes.

    This applies values from the project's `.env` file and prepends the
    repository's `src/` directory to `PYTHONPATH` so subprocesses can import the
    `grad_applicant_system` package without requiring installation into the
    active environment.

    Args:
        project_root: The repository root containing `.env` and `src/`.

    Returns:
        A child-process environment dictionary.
    """
    # Start from the current process environment so subprocesses inherit the
    # user's active shell configuration.
    env = os.environ.copy()
    env = apply_dotenv(env, project_root / ".env")

    src_root = str(project_root / "src")
    existing = env.get("PYTHONPATH", "")

    # Prepend src/ so local package imports resolve when launching scripts from
    # the repository root during development.
    env["PYTHONPATH"] = src_root if not existing else src_root + os.pathsep + existing
    return env