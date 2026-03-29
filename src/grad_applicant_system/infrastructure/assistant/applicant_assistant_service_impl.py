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