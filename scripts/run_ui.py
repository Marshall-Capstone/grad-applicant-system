"""run_ui.py = runs the UI loop (for now a placeholder)"""

from __future__ import annotations

import sys
from pathlib import Path

from scripts.venv_utils import in_venv, reexec_into_venv


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    if not in_venv():
        reexec_into_venv(project_root)

    src_root = project_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from dotenv import load_dotenv

    load_dotenv(project_root / ".env")

    print("UI process started. Enter to exit UI.")
    input()


if __name__ == "__main__":
    main()