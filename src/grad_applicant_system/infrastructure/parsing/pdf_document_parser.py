from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ParsedDocument:
    """
    Convenience container for a parsed PDF document.

    This is kept for compatibility with any callers that may want a single
    object containing:
    - the source filename
    - page count
    - raw extracted text
    - per-page text
    - extracted structured fields
    """
    filename: str
    page_count: int
    raw_text: str
    page_texts: List[str]
    extracted_fields: Dict[str, Any]


class PDFDocumentParser:
    """
    Extract raw text from PDF files for downstream field extraction.

    Design goals:
    - Keep the parser responsible only for text extraction.
    - Prefer `pypdf` first, then fall back to `pdfplumber` if needed.
    - Preserve page boundaries using explicit page markers so downstream
      extraction logic can remain page-aware.
    - Avoid import-time crashes if one backend is missing.
    """

    def __init__(self) -> None:
        """
        Detect optional PDF backends at runtime.

        We do this lazily and defensively so the module can still import even
        if one extraction library is unavailable on a machine.
        """
        self._has_pypdf = False
        self._has_pdfplumber = False

        try:
            from pypdf import PdfReader  # type: ignore

            _ = PdfReader
            self._has_pypdf = True
        except Exception:
            self._has_pypdf = False

        try:
            import pdfplumber  # type: ignore

            _ = pdfplumber
            self._has_pdfplumber = True
        except Exception:
            self._has_pdfplumber = False

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a PDF and return it as one page-marked string.

        Strategy:
        1. Validate the file path.
        2. Try `pypdf` first.
        3. If that result is empty or too small to be useful, fall back to
           `pdfplumber`.
        4. Return a single text blob with explicit '=== PAGE N ===' markers.

        Returning page markers is important because the extractor uses them
        to reconstruct page-local context for more accurate regex matching.
        """
        if not file_path:
            return ""

        path = Path(file_path)
        if not path.exists():
            return ""

        # First attempt: pypdf
        if self._has_pypdf:
            try:
                text = self._extract_with_pypdf(str(path))
                if text and len(text.strip()) >= 50:
                    return text
            except Exception:
                pass

        # Fallback: pdfplumber
        if self._has_pdfplumber:
            try:
                return self._extract_with_pdfplumber(str(path))
            except Exception:
                pass

        return ""

    def extract_pages(self, file_path: str) -> list[str]:
        """
        Extract and return normalized text for each page of a PDF.

        This is primarily a debugging / inspection helper. It is useful when
        you want to see page-local content without manually re-splitting the
        page-marked text returned by `extract_text(...)`.
        """
        if not file_path:
            return []

        path = Path(file_path)
        if not path.exists():
            return []

        pages: list[str] = []

        # Prefer pypdf first.
        if self._has_pypdf:
            try:
                pages = self._extract_pages_with_pypdf(str(path))
            except Exception:
                pages = []

        # Fall back if the first result is empty or too weak.
        if (
            (not pages or sum(len(p.strip()) for p in pages) < 100)
            and self._has_pdfplumber
        ):
            try:
                pages = self._extract_pages_with_pdfplumber(str(path))
            except Exception:
                pass

        # Normalize page text so downstream regexes are more stable.
        return [
            self._normalize_page_text(page_text)
            for page_text in pages
            if page_text and page_text.strip()
        ]

    def extract_texts(self, file_paths: list[str]) -> dict[str, str]:
        """
        Extract text from multiple PDFs.

        Returns:
            A mapping of file_path -> extracted_text.

        Failures are tolerated per-file and represented as an empty string.
        That keeps batch workflows simple and resilient.
        """
        results: dict[str, str] = {}

        for file_path in file_paths:
            try:
                results[file_path] = self.extract_text(file_path)
            except Exception:
                results[file_path] = ""

        return results

    def extract_fields(self, text: Optional[str]) -> Dict[str, Any]:
        """
        Compatibility wrapper that delegates structured extraction to the
        dedicated extraction processor.

        The parser should not own regex field extraction, but this method is
        kept so older callers do not break during the refactor.
        """
        if not text:
            return {}

        # Local import avoids circular import concerns and keeps module
        # responsibilities separate.
        from .simple_extraction_processor import SimpleExtractionProcessor

        extractor = SimpleExtractionProcessor()
        return extractor.extract(text)

    def coerce_types(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Light compatibility helper for callers that expect a coercion step.

        At the moment, the primary useful coercion here is GPA -> float.
        Everything else is returned as-is.
        """
        coerced: Dict[str, Any] = dict(fields)

        if "undergraduate_gpa" in coerced and coerced["undergraduate_gpa"] is not None:
            try:
                coerced["undergraduate_gpa"] = float(coerced["undergraduate_gpa"])
            except (TypeError, ValueError):
                # Leave the original value alone if coercion fails.
                pass

        return coerced

    def parse_document(self, file_path: str) -> ParsedDocument:
        """
        Convenience method that returns both raw extracted text and structured
        extracted fields in one object.

        This is not the main runtime path for the current app, but it is handy
        for dev scripts and any callers that want one all-in-one parse result.
        """
        raw_text = self.extract_text(file_path)
        page_texts = self.extract_pages(file_path)
        extracted_fields = self.extract_fields(raw_text)

        return ParsedDocument(
            filename=Path(file_path).name,
            page_count=len(page_texts),
            raw_text=raw_text,
            page_texts=page_texts,
            extracted_fields=extracted_fields,
        )

    def _extract_with_pypdf(self, file_path: str) -> str:
        """
        Extract PDF text with `pypdf` and include explicit page markers.

        Page markers are required by the downstream extraction processor so it
        can reconstruct page-level sections from the flattened text stream.
        """
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(file_path)
        text_parts: list[str] = []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            if page_text.strip():
                text_parts.append(
                    f"=== PAGE {page_number} ===\n{self._normalize_page_text(page_text)}"
                )

        return "\n\n".join(text_parts).strip()

    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """
        Extract PDF text with `pdfplumber` and include explicit page markers.

        This serves as a fallback when `pypdf` cannot recover enough usable
        text from the document.
        """
        import pdfplumber  # type: ignore

        text_parts: list[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""

                if page_text.strip():
                    text_parts.append(
                        f"=== PAGE {page_number} ===\n{self._normalize_page_text(page_text)}"
                    )

        return "\n\n".join(text_parts).strip()

    def _extract_pages_with_pypdf(self, file_path: str) -> list[str]:
        """
        Extract raw page text with `pypdf` as a list of per-page strings.
        """
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(file_path)
        page_texts: list[str] = []

        for page in reader.pages:
            try:
                page_texts.append(page.extract_text() or "")
            except Exception:
                page_texts.append("")

        return page_texts

    def _extract_pages_with_pdfplumber(self, file_path: str) -> list[str]:
        """
        Extract raw page text with `pdfplumber` as a list of per-page strings.
        """
        import pdfplumber  # type: ignore

        page_texts: list[str] = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_texts.append(page.extract_text() or "")
                except Exception:
                    page_texts.append("")

        return page_texts

    def _normalize_page_text(self, text: str) -> str:
        """
        Normalize page text while preserving meaningful line structure.

        We intentionally do only light cleanup:
        - normalize line endings
        - collapse repeated spaces/tabs
        - reduce excessive blank lines

        This keeps enough layout signal intact for page-aware regex searches.
        """
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
