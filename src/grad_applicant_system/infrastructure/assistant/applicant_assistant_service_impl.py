from grad_applicant_system.application.ports.applicant_assistant_service import ApplicantAssistantService


class ApplicantAssistantServiceImpl(ApplicantAssistantService):

    def __init__(self, parser, extractor):
        self.parser = parser
        self.extractor = extractor

    def parse_applicant_pdf(self, file_path: str) -> dict:
        text = self.parser.extract_text(file_path)
        data = self.extractor.extract_applicant_data(text)

        return {
            "file": file_path,
            "data": data,
            "raw_text_length": len(text)
        }
    
    def parse_applicant_pdfs(self, file_paths: list[str]) -> dict:
        """
        Parse multiple PDFs and return a mapping: file_path -> result dict.
        """
        results: dict = {}
        texts = {}
        # If parser supports batch extraction, use it for efficiency
        if hasattr(self.parser, "extract_texts"):
            try:
                texts = self.parser.extract_texts(file_paths)
            except Exception:
                texts = {p: self.parser.extract_text(p) for p in file_paths}
        else:
            texts = {p: self.parser.extract_text(p) for p in file_paths}

        for p, txt in texts.items():
            try:
                data = self.extractor.extract_applicant_data(txt)
                results[p] = {
                    "file": p,
                    "data": data,
                    "raw_text_length": len(txt or ""),
                }
            except Exception as exc:
                results[p] = {"file": p, "error": str(exc)}

        return results