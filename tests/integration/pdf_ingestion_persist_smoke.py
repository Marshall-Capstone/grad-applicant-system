from pathlib import Path
import json
import sys

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "src"))

from grad_applicant_system.infrastructure.parsing.pdf_document_parser import PDFDocumentParser
from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import SimpleExtractionProcessor
from grad_applicant_system.infrastructure.parsing.pdf_ingestion_service import PdfIngestionService


def main() -> None:
    pdf_path = r"C:\Users\13045\Desktop\filled_test_application_packet_final.pdf"

    parser = PDFDocumentParser()
    extractor = SimpleExtractionProcessor()
    service = PdfIngestionService(parser=parser, extractor=extractor)

    ingest_result = service.ingest_pdf(pdf_path)

    print("=" * 80)
    print("INGEST RESULT")
    print("=" * 80)
    print(json.dumps(ingest_result, indent=2, default=str))


if __name__ == "__main__":
    main()