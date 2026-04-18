from pathlib import Path
import json
import sys

# run from repo root with python tests\integration\parser_core_smoke.py

# tests/integration/parser_core_smoke.py
# parents[0] = tests/integration
# parents[1] = tests
# parents[2] = repo root
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "src"))

from grad_applicant_system.infrastructure.parsing.pdf_document_parser import PDFDocumentParser
from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import SimpleExtractionProcessor


def main() -> None:
    # Option 1: keep using absolute desktop PDF path
    pdf_path = Path(r"C:\Users\13045\Desktop\filled_test_application_packet_final.pdf")

    # Option 2: if we copy the sample PDF into the repo later, use something like:
    # pdf_path = repo_root / "tests" / "fixtures" / "filled_test_application_packet_final.pdf"

    parser = PDFDocumentParser()
    extractor = SimpleExtractionProcessor()

    text = parser.extract_text(str(pdf_path))
    data = extractor.extract(text)

    print("=" * 80)
    print("PDF PATH")
    print("=" * 80)
    print(pdf_path)

    print("\n" + "=" * 80)
    print("RAW TEXT LENGTH")
    print("=" * 80)
    print(len(text))

    print("\n" + "=" * 80)
    print("RAW TEXT PREVIEW")
    print("=" * 80)
    print(text[:2000])

    print("\n" + "=" * 80)
    print("EXTRACTED DATA")
    print("=" * 80)
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()