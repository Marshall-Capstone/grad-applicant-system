from __future__ import annotations

from typing import Any

from grad_applicant_system.infrastructure.parsing.pdf_document_parser import (
    PDFDocumentParser,
)
from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import (
    SimpleExtractionProcessor,
)


class PdfIngestionService:
    """
    Shared PDF ingestion workflow used by both the UI preview path and the
    server/MCP ingestion path.

    Responsibilities:
    - Extract raw text from a PDF.
    - Extract structured applicant fields from that text.
    - Optionally persist the structured result to the database.
    - Return one consistent result shape to callers.

    Notes:
    - `preview_*` methods never persist.
    - `ingest_*` methods attempt best-effort persistence.
    - Validation/guardrails for persistence can be tightened in the next branch.
    """

    def __init__(
        self,
        parser: PDFDocumentParser,
        extractor: SimpleExtractionProcessor,
    ) -> None:
        """
        Initialize the service with explicit parser/extractor dependencies.

        This keeps construction outside the caller and gives us a single place
        to own the PDF processing workflow.
        """
        self._parser = parser
        self._extractor = extractor

    def preview_pdf(self, file_path: str) -> dict[str, Any]:
        """
        Parse and extract a single PDF without attempting persistence.

        This is the safe path for the UI upload-preview flow.
        """
        return self._process_pdf(file_path=file_path, persist=False)

    def preview_pdfs(self, file_paths: list[str]) -> dict[str, dict[str, Any]]:
        """
        Parse and extract multiple PDFs without attempting persistence.

        Returns a mapping: file_path -> result dictionary.
        """
        results: dict[str, dict[str, Any]] = {}

        for file_path in file_paths:
            results[file_path] = self.preview_pdf(file_path)

        return results

    def ingest_pdf(self, file_path: str) -> dict[str, Any]:
        """
        Parse, extract, and best-effort persist a single PDF.
        """
        return self._process_pdf(file_path=file_path, persist=True)

    def ingest_pdfs(self, file_paths: list[str]) -> dict[str, dict[str, Any]]:
        """
        Parse, extract, and best-effort persist multiple PDFs.

        Returns a mapping: file_path -> result dictionary.
        """
        results: dict[str, dict[str, Any]] = {}

        for file_path in file_paths:
            results[file_path] = self.ingest_pdf(file_path)

        return results

    def _process_pdf(self, file_path: str, persist: bool) -> dict[str, Any]:
        """
        Shared internal workflow for single-file PDF processing.

        Result shape:
        - status
        - file
        - data
        - raw_text
        - raw_text_length
        - db

        `db` is either:
        - a persistence result dict
        - a skipped marker for preview mode
        - or an error dict if persistence failed
        """
        try:
            raw_text = self._parser.extract_text(file_path)
            data = self._extractor.extract(raw_text)

            if persist:
                try:
                    db_result = self._persist_extracted_data(data)
                except Exception as exc:
                    db_result = {"error": str(exc)}
            else:
                db_result = {"skipped": True, "reason": "preview_only"}

            return {
                "status": "success",
                "file": file_path,
                "data": data,
                "raw_text": raw_text,
                "raw_text_length": len(raw_text),
                "db": db_result,
            }

        except Exception as exc:
            return {
                "status": "error",
                "file": file_path,
                "message": str(exc),
                "data": {},
                "raw_text": "",
                "raw_text_length": 0,
                "db": None,
            }

    def _persist_extracted_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Best-effort persistence hook.

        This is intentionally small and isolated so the next branch can
        tighten validation and persistence rules in one place.
        """
        # Local import keeps preview-only callers from paying persistence
        # import/setup cost until persistence is actually requested.
        from grad_applicant_system.infrastructure.persistence import mysql_persistence

        return mysql_persistence.save_parsed_data(data)