from __future__ import annotations

from pathlib import Path
from typing import Optional


class PDFDocumentParser:
    """Responsible ONLY for extracting raw text from PDFs.

    The constructor checks for optional backends but does not raise if
    they're missing; that prevents import-time errors.
    """

    def __init__(self) -> None:
        self._has_pypdf = False
        self._has_pdfplumber = False

        try:
            # only check availability; don't keep module-level references
            import pypdf  # type: ignore

            # ensure PdfReader exists
            from pypdf import PdfReader  # type: ignore

            _ = PdfReader
            self._has_pypdf = True
        except Exception:
            self._has_pypdf = False

        try:
            import pdfplumber  # type: ignore

            self._has_pdfplumber = True
        except Exception:
            self._has_pdfplumber = False

    def extract_text(self, file_path: str) -> str:
        """Return text extracted from `file_path`.

        If no backends are available or the file cannot be read, an empty
        string is returned rather than raising at import time.
        """
        if not file_path:
            return ""

        path = Path(file_path)
        if not path.exists():
            return ""

        text = ""

        if self._has_pypdf:
            try:
                text = self._extract_with_pypdf(str(path))
            except Exception:
                text = ""

        # fallback to pdfplumber if pypdf produced nothing useful
        if (not text or len(text.strip()) < 50) and self._has_pdfplumber:
            try:
                text = self._extract_with_pdfplumber(str(path))
            except Exception:
                # leave text as-is (possibly empty)
                pass

        return text or ""

    def _extract_with_pypdf(self, file_path: str) -> str:
        """Extract using pypdf backend.
        """
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(file_path)
        text = ""

        for page in getattr(reader, "pages", []):
            try:
                text += page.extract_text() or ""
            except Exception:
                # ignore page-level extraction errors
                continue

        return text

    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract using pdfplumber backend.
        """
        import pdfplumber  # type: ignore

        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    text += page.extract_text() or ""
                except Exception:
                    continue

        return text