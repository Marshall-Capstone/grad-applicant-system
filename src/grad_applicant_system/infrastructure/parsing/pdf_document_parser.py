from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

GRADE_PATTERN = r"(?:A\+|A-|A|B\+|B-|B|C\+|C-|C|D\+|D-|D|F|P|NP|PASS|FAIL)"
DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b(\d{2}/\d{2}/\d{4})\b",
    r"\b(\d{2}-\d{2}-\d{4})\b",
]


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    page_count: int
    raw_text: str
    page_texts: List[str]
    extracted_fields: Dict[str, str]


def _extract_labeled_value(text: str, labels: List[str]) -> Optional[str]:
    for label in labels:
        pattern = rf"\b{label}\b\s*[:#-]?\s*([^\n\r]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip(" -:\t")
            if value:
                return value
    return None


def _parse_date_string(raw: str) -> Optional[str]:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _extract_all_courses_and_grades(text: str) -> List[tuple[str, str]]:
    pairs: List[tuple[str, str]] = []
    for line in text.splitlines():
        clean_line = re.sub(r"\s+", " ", line).strip()
        if not clean_line:
            continue

        colon_style = re.search(
            rf"\bcourse\b\s*[:#-]?\s*([A-Za-z0-9&/\.\-\s]+?)\s+\bgrade\b\s*[:#-]?\s*({GRADE_PATTERN})\b",
            clean_line,
            re.IGNORECASE,
        )
        if colon_style:
            course_name = colon_style.group(1).strip(" -")
            grade = colon_style.group(2).upper()
            pairs.append((course_name, grade))
            continue

        table_style = re.search(
            rf"\b([A-Z]{{2,4}}\s*\d{{2,4}}[A-Z]?)\b.*?\b({GRADE_PATTERN})\b",
            clean_line,
            re.IGNORECASE,
        )
        if table_style:
            course_name = table_style.group(1).replace("  ", " ").strip()
            grade = table_style.group(2).upper()
            pairs.append((course_name, grade))

        transcript_style = re.search(
            rf"\b([A-Z]{{2,6}}\s*-?\s*\d{{2,4}}[A-Z]?)\b\s*(?:[-:|]|\s)\s*([A-Za-z0-9&/().\-\s]{{2,80}}?)\s+(?:{GRADE_PATTERN})\b",
            clean_line,
            re.IGNORECASE,
        )
        if transcript_style:
            course_code = transcript_style.group(1).replace("  ", " ").strip()
            course_name = f"{course_code} {transcript_style.group(2).strip()}".strip()
            grade_match = re.search(rf"\b({GRADE_PATTERN})\b", clean_line, re.IGNORECASE)
            if grade_match:
                pairs.append((course_name, grade_match.group(1).upper()))
            continue

        pipe_style = re.search(
            rf"\b([A-Z]{{2,6}}\d{{2,4}}[A-Z]?)\b\s*[|,]\s*({GRADE_PATTERN})\b",
            clean_line,
            re.IGNORECASE,
        )
        if pipe_style:
            pairs.append((pipe_style.group(1).strip(), pipe_style.group(2).upper()))
            continue

        plain_row_style = re.search(
            rf"^([A-Za-z][A-Za-z0-9&/().\-\s]{{2,80}}?)\s+({GRADE_PATTERN})$",
            clean_line,
            re.IGNORECASE,
        )
        if plain_row_style:
            candidate_course = plain_row_style.group(1).strip(" -")
            if not re.search(r"\b(course\s+name|grade|section\s+\d+)\b", candidate_course, re.IGNORECASE):
                pairs.append((candidate_course, plain_row_style.group(2).upper()))

    unique: List[tuple[str, str]] = []
    seen = set()
    for course_name, grade in pairs:
        key = (course_name.lower(), grade)
        if key in seen:
            continue
        seen.add(key)
        unique.append((course_name, grade))
    return unique


def _split_degree_values(raw: str) -> List[str]:
    parts = [part.strip() for part in re.split(r"[,;|/]", raw) if part.strip()]
    if parts:
        return parts
    return [raw.strip()] if raw.strip() else []


def _extract_degree_lines(text: str) -> List[str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    start = -1
    for index, line in enumerate(lines):
        if re.search(r"\bdegrees?\s+completed\b|\beducation\b|\bdegree\s+earned\b", line, re.IGNORECASE):
            start = index
            break

    if start < 0:
        return []

    results: List[str] = []
    for line in lines[start + 1 : start + 8]:
        if not line:
            if results:
                break
            continue
        if re.search(r"\b(classes?|courses?|grades?|gpa|date\s+of\s+birth|applicant|student\s+name)\b", line, re.IGNORECASE):
            break
        if re.search(r"\b(BS|BA|BSc|MS|MA|MSc|MBA|PhD|Doctorate|Associate)\b", line, re.IGNORECASE):
            results.append(line.strip("-• "))

    return results


def _extract_gpa_value(text: str) -> Optional[str]:
    gpa_patterns = [
        r"\bgpa\b\s*[:=\-]?\s*([0-4](?:\.\d{1,3})?)",
        r"\bcumulative\s+gpa\b\s*[:=\-]?\s*([0-4](?:\.\d{1,3})?)",
        r"\bgrade\s+point\s+average\b\s*[:=\-]?\s*([0-4](?:\.\d{1,3})?)",
        r"\b([0-4](?:\.\d{1,3})?)\s*/\s*4(?:\.0+)?\b",
    ]
    for pattern in gpa_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    for line in text.splitlines():
        clean_line = re.sub(r"\s+", " ", line).strip()
        if "gpa" not in clean_line.lower():
            continue
        match = re.search(r"([0-4](?:\.\d{1,3})?)", clean_line)
        if match:
            return match.group(1)
    return None


def _extract_name_fallback(text: str) -> Optional[str]:
    patterns = [
        r"\bapplicant\b\s*[:#-]?\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})",
        r"\bstudent\b\s*[:#-]?\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})",
        r"\bname\b\s*[:#-]?\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){1,3})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


class PDFDocumentParser:
    """Responsible ONLY for extracting raw text from PDFs.

    The constructor checks for optional backends but does not raise if
    they're missing; that prevents import-time errors.
    """

    def __init__(self) -> None:
        self._has_pypdf = False
        self._has_pdfplumber = False

        try:
            import pypdf  # type: ignore
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

        page_texts = self._extract_page_texts(file_path)
        return "\n".join(page_texts).strip()

    def _extract_page_texts(self, file_path: str) -> List[str]:
        path = Path(file_path)
        if not path.exists():
            return []

        page_texts: List[str] = []
        if self._has_pypdf:
            try:
                page_texts = self._extract_with_pypdf(str(path))
            except Exception:
                page_texts = []

        if (
            not page_texts
            or len("\n".join(page_texts).strip()) < 50
        ) and self._has_pdfplumber:
            try:
                page_texts = self._extract_with_pdfplumber(str(path))
            except Exception:
                pass

        return [page or "" for page in page_texts]

    def _extract_with_pypdf(self, file_path: str) -> List[str]:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(file_path)
        texts: List[str] = []
        for page in getattr(reader, "pages", []):
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
        return texts

    def _extract_with_pdfplumber(self, file_path: str) -> List[str]:
        import pdfplumber  # type: ignore

        texts: List[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    texts.append(page.extract_text() or "")
                except Exception:
                    texts.append("")
        return texts

    def extract_texts(self, file_paths: list[str]) -> dict[str, str]:
        """
        Convenience helper to extract text from multiple PDF file paths.

        Returns a mapping of file_path -> extracted_text (empty string on failure).
        """
        results: dict[str, str] = {}
        for p in file_paths:
            try:
                results[p] = self.extract_text(p) or ""
            except Exception:
                results[p] = ""
        return results

    def extract_fields(self, text: Optional[str]) -> Dict[str, str]:
        """Extract common fields from PDF text using regex heuristics."""
        if not text:
            return {}

        fields: Dict[str, str] = {}

        for line in (line.strip() for line in text.splitlines()):
            if line:
                fields["title"] = line[:255]
                break

        doc_type = None
        lowered = text.lower()
        if "invoice" in lowered:
            doc_type = "invoice"
        elif "receipt" in lowered:
            doc_type = "receipt"
        elif "report" in lowered:
            doc_type = "report"
        elif "graduate application" in lowered:
            doc_type = "graduate"
        elif "undergraduate application" in lowered:
            doc_type = "undergraduate"
        elif "transfer application" in lowered:
            doc_type = "transfer"
        elif "international application" in lowered:
            doc_type = "international"
        elif "application" in lowered:
            doc_type = "student_application"
        if doc_type:
            fields["doc_type"] = doc_type

        student_name = _extract_labeled_value(text, ["student\\s+name", "applicant\\s+name", "name"])
        if not student_name:
            student_name = _extract_name_fallback(text)
        if student_name:
            fields["student_name"] = student_name
            if "title" not in fields or len(fields["title"]) < 3:
                fields["title"] = f"{student_name} Application"[:255]

        email_raw = _extract_labeled_value(text, ["email", "email\\s+address", "e-mail"])
        if not email_raw:
            email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b", text)
            if email_match:
                email_raw = email_match.group(1)
        if email_raw:
            fields["email"] = email_raw.strip()

        phone_raw = _extract_labeled_value(text, ["phone", "phone\\s+number", "telephone", "contact\\s+phone"])
        if not phone_raw:
            phone_match = re.search(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b", text)
            if phone_match:
                phone_raw = phone_match.group(0)
        if phone_raw:
            fields["phone_num"] = phone_raw.strip()

        address_raw = _extract_labeled_value(text, ["address", "home\\s+address", "mailing\\s+address", "street\\s+address"])
        if address_raw:
            fields["address"] = address_raw.strip()[:255]

        dob_raw = _extract_labeled_value(text, ["date\\s+of\\s+birth", "dob", "birth\\s+date"])
        if dob_raw:
            date_match = None
            for pattern in DATE_PATTERNS:
                found = re.search(pattern, dob_raw)
                if found:
                    date_match = found.group(1)
                    break
            if date_match:
                parsed_dob = _parse_date_string(date_match)
                fields["date_of_birth"] = parsed_dob or date_match

        application_date_raw = _extract_labeled_value(text, ["application\\s+date", "submission\\s+date", "date\\s+submitted"])
        if application_date_raw:
            for pattern in DATE_PATTERNS:
                date_match = re.search(pattern, application_date_raw)
                if date_match:
                    fields["doc_date"] = _parse_date_string(date_match.group(1)) or date_match.group(1)
                    break

        gpa_raw = _extract_labeled_value(text, ["gpa", "cumulative\\s+gpa", "grade\\s+point\\s+average"])
        gpa_value = None
        if gpa_raw:
            numeric_match = re.search(r"([0-4](?:\.\d{1,3})?)", gpa_raw)
            if numeric_match:
                gpa_value = numeric_match.group(1)
        if not gpa_value:
            gpa_value = _extract_gpa_value(text)
        if gpa_value:
            fields["gpa"] = gpa_value

        degrees_raw = _extract_labeled_value(text, ["degrees?\\s+completed", "degree\\s+earned", "degrees?"])
        if degrees_raw:
            degrees = _split_degree_values(degrees_raw)
            if degrees:
                fields["degrees_completed"] = "; ".join(degrees)
        else:
            degree_lines = _extract_degree_lines(text)
            if degree_lines:
                fields["degrees_completed"] = "; ".join(degree_lines)

        course_pairs = _extract_all_courses_and_grades(text)
        if course_pairs:
            fields["classes_taken"] = "; ".join(course for course, _ in course_pairs)
            fields["grades"] = "; ".join(grade for _, grade in course_pairs)
            fields["recorded_grades"] = "; ".join(f"{course}:{grade}" for course, grade in course_pairs)

        match = re.search(r"\b(?:invoice|doc|document|receipt)\s*(?:#|no\.?|number)\s*[:#-]?\s*([A-Z0-9-]+)", text, re.IGNORECASE)
        if match:
            fields["document_number"] = match.group(1)

        total_match = re.search(r"\btotal\s*(?:amount)?\s*[:$]?\s*([0-9,]+\.?[0-9]{0,2})", text, re.IGNORECASE)
        if total_match:
            fields["total_amount"] = total_match.group(1).replace(",", "")

        if "doc_date" not in fields:
            dob_value = str(fields.get("date_of_birth", "")) if fields.get("date_of_birth") else ""
            for pattern in DATE_PATTERNS:
                date_match = re.search(pattern, text)
                if date_match:
                    candidate_date = _parse_date_string(date_match.group(1)) or date_match.group(1)
                    if dob_value and candidate_date == dob_value:
                        continue
                    fields["doc_date"] = candidate_date
                    break

        vendor_match = re.search(r"\bfrom\s*[:]?\s*(.+)", text, re.IGNORECASE)
        if vendor_match:
            fields["vendor"] = vendor_match.group(1).strip()[:255]

        return fields

    def coerce_types(self, fields: Dict[str, str]) -> Dict[str, object]:
        """Coerce certain fields to native types for downstream use."""
        coerced: Dict[str, object] = dict(fields)
        if "total_amount" in coerced:
            try:
                coerced["total_amount"] = float(coerced["total_amount"])
            except (TypeError, ValueError):
                coerced["total_amount"] = None

        if "gpa" in coerced:
            try:
                coerced["gpa"] = float(coerced["gpa"])
            except (TypeError, ValueError):
                coerced["gpa"] = None

        if "doc_date" in coerced:
            raw = str(coerced["doc_date"])
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
                try:
                    coerced["doc_date"] = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue

        if "date_of_birth" in coerced:
            raw_dob = str(coerced["date_of_birth"])
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"):
                try:
                    coerced["date_of_birth"] = datetime.strptime(raw_dob, fmt)
                    break
                except ValueError:
                    continue

        return coerced

    def parse_document(self, file_path: str) -> ParsedDocument:
        page_texts = self._extract_page_texts(file_path)
        raw_text = "\n".join(page_texts).strip()
        extracted_fields = self.extract_fields(raw_text)

        return ParsedDocument(
            filename=Path(file_path).name,
            page_count=len(page_texts),
            raw_text=raw_text,
            page_texts=page_texts,
            extracted_fields=extracted_fields,
        )
