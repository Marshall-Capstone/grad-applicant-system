from __future__ import annotations

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


class FakeApplicantAssistantService(ApplicantAssistantService):
    """Temporary development implementation for the conversational assistant."""

    def send_message(self, user_message: str, available_files: list[str] | None = None) -> AssistantReply:
        text = user_message.strip()

        if not text:
            return AssistantReply(
                user_message="",
                assistant_message="Please enter a message.",
            )

        lowered = text.lower()

        if "list" in lowered and "applicant" in lowered:
            reply = (
                "Fake assistant response: later this will ask the LLM to use "
                "the MCP tools to list applicants."
            )
        elif "email" in lowered:
            reply = (
                "Fake assistant response: later this will ask the LLM to use "
                "the MCP tools to look up an applicant by email."
            )
        else:
            reply = (
                "Fake assistant response: the UI-to-assistant boundary is now "
                "conversation-oriented. Real Anthropic + MCP integration will "
                "be added next."
            )

        return AssistantReply(
            user_message=text,
            assistant_message=reply,
        )

    def parse_applicant_pdf(self, file_path: str) -> dict:
        # Try to perform a real local parse if parser/extractor available,
        # otherwise return a simple placeholder.
        try:
            from grad_applicant_system.infrastructure.parsing.pdf_document_parser import (
                PDFDocumentParser,
            )
            from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import (
                SimpleExtractionProcessor,
            )

            parser = PDFDocumentParser()
            extractor = SimpleExtractionProcessor()

            text = parser.extract_text(file_path) or ""
            data = extractor.extract(text)

            return {"file": file_path, "data": data, "raw_text_length": len(text)}
        except Exception:
            return {"file": file_path, "data": {}, "raw_text_length": 0}

    def parse_applicant_pdfs(self, file_paths: list[str]) -> dict:
        results = {}
        try:
            from grad_applicant_system.infrastructure.parsing.pdf_document_parser import (
                PDFDocumentParser,
            )
            from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import (
                SimpleExtractionProcessor,
            )

            parser = PDFDocumentParser()
            extractor = SimpleExtractionProcessor()

            if hasattr(parser, "extract_texts"):
                texts = parser.extract_texts(file_paths)
            else:
                texts = {p: parser.extract_text(p) for p in file_paths}

            for p, txt in texts.items():
                data = extractor.extract(txt)
                results[p] = {"file": p, "data": data, "raw_text_length": len(txt or "")}

        except Exception:
            for p in file_paths:
                results[p] = {"file": p, "data": {}, "raw_text_length": 0}

        return results