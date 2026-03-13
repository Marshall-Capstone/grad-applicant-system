"""run_ui.py = runs the UI loop."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.venv_utils import in_venv, reexec_into_venv


def main() -> None:
    if not in_venv():
        reexec_into_venv(PROJECT_ROOT)

    src_root = PROJECT_ROOT / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))

    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    from grad_applicant_system.presentation.ui.app import App

    app = App()
    app.run()


if __name__ == "__main__":
    main()