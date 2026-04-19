"""Bootstrap the desktop UI process for the Grad Applicant System.

This script is a developer-facing entry point that ensures the local Python
environment is ready and then launches the presentation-layer application.

It lives in `scripts/` because it is an operational process launcher, while the
actual UI composition and runtime logic live in the application package under
`src/grad_applicant_system/presentation/ui/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Repository root used for locating .env, src/, and other project-level assets.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    # Make sibling `scripts/` imports available when this file is run directly.
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.venv_utils import in_venv, reexec_into_venv


def main() -> None:
    """Prepare the local UI environment and start the desktop application."""
    # Re-launch inside the project's virtual environment so the UI process uses
    # the expected dependencies on every developer machine.
    if not in_venv():
        reexec_into_venv(PROJECT_ROOT)

    src_root = PROJECT_ROOT / "src"
    if str(src_root) not in sys.path:
        # Allow direct imports from the src-based application package.
        sys.path.insert(0, str(src_root))

    from dotenv import load_dotenv

    # Load application configuration before constructing the UI object graph.
    load_dotenv(PROJECT_ROOT / ".env")

    from grad_applicant_system.presentation.ui.app import App

    # App is the presentation-layer composition root for the desktop UI.
    app = App()
    app.run()


if __name__ == "__main__":
    main()