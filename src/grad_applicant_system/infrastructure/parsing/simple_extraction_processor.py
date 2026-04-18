from __future__ import annotations

import re
from typing import Optional


class SimpleExtractionProcessor:
    """
    Convert raw PDF text into structured applicant/application data.

    This extractor expects page-marked text of the form:

        === PAGE 1 ===
        ...
        === PAGE 2 ===
        ...

    It uses page-aware regex heuristics to recover fields relevant to:
    - applicant creation
    - program/advisor association
    - application metadata
    """

    def extract(self, text: Optional[str]) -> dict:
        """
        Extract structured applicant-related data from raw PDF text.

        Returns a dictionary aligned with the persistence layer. If no text is
        provided, all expected keys are present with `None` values so callers
        can rely on a stable shape.
        """
        empty_result = {
            "applicant_name": None,
            "full_name": None,
            "name": None,
            "undergraduate_gpa": None,
            "degree_earned": None,
            "program_major": None,
            "advisor_name": None,
            "term_applying_for": None,
            "admission_decision": None,
            "email": None,
            "muid": None,
        }

        if not text:
            return empty_result

        # Normalize to string in case a caller passes another text-like type.
        text = str(text)

        # Recover page-local blocks from the page-marked raw text.
        pages = self._split_pages(text)
        full_text = "\n\n".join(pages.values())

        applicant_name = self._extract_name(pages, full_text)

        return {
            "applicant_name": applicant_name,
            "full_name": applicant_name,
            "name": applicant_name,
            "undergraduate_gpa": self._extract_gpa(pages, full_text),
            "degree_earned": self._extract_degree(pages, full_text),
            "program_major": self._extract_program(pages, full_text),
            "advisor_name": self._extract_advisor(pages, full_text),
            "term_applying_for": self._extract_term(pages, full_text),
            "admission_decision": self._extract_admission_decision(pages, full_text),
            "email": self._extract_email(pages, full_text),
            "muid": self._extract_muid(pages, full_text),
        }

    def process_extracted_text(self, text: Optional[str]) -> dict:
        """
        Compatibility adapter for callers expecting a
        `process_extracted_text(...)` method.
        """
        return self.extract(text)

    def extract_applicant_data(self, text: Optional[str]) -> dict:
        """
        Legacy compatibility adapter for callers still using the older
        `extract_applicant_data(...)` method name.
        """
        return self.extract(text)

    def _split_pages(self, text: str) -> dict[int, str]:
        """
        Split page-marked text into a page-number -> page-content mapping.

        If no page markers are present, the full text is treated as page 1.
        """
        pattern = re.compile(r"=== PAGE (\d+) ===\n")
        matches = list(pattern.finditer(text))

        if not matches:
            return {1: text}

        pages: dict[int, str] = {}

        for index, match in enumerate(matches):
            page_num = int(match.group(1))
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            pages[page_num] = text[start:end].strip()

        return pages

    def _clean(self, value: Optional[str]) -> Optional[str]:
        """
        Clean a captured regex value before returning it.

        This removes redundant whitespace and trims common punctuation from the
        edges of a captured field.
        """
        if value is None:
            return None

        value = re.sub(r"\s+", " ", value).strip(" \n\t:-")
        return value or None

    def _search(
        self,
        blocks: list[str],
        patterns: list[str],
        flags: int = re.IGNORECASE | re.DOTALL,
    ) -> Optional[str]:
        """
        Search a list of text blocks with one or more regex patterns.

        The first successful capture group match is cleaned and returned.
        This helper makes it easy for field-specific extraction methods to
        express:
        - preferred pages first
        - broad fallback later
        """
        for block in blocks:
            if not block:
                continue

            for pattern in patterns:
                match = re.search(pattern, block, flags)
                if match:
                    return self._clean(match.group(1))

        return None

    def _extract_name(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the applicant's name.

        Strategy:
        - Prefer page 1, where the form's populated value cluster often appears.
        - Fall back to transcript / application detail pages if needed.
        """
        page_one = pages.get(1, "")

        value = self._search(
            [page_one],
            [
                r"\b([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+)\s+(?:Fall|Spring|Summer)\s+\d{4}\b",
                r"\bApplicant\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+)\b",
            ],
        )

        # Guard against obvious label-like false positives.
        if value and value not in {"Other Suffix", "Last Name Preferred First Name"}:
            return value

        # Stronger fallback from transcript / education history pages.
        return self._search(
            [pages.get(6, ""), pages.get(5, ""), full_text],
            [
                r"\bApplicant\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+)\b",
                r"\bEDU-\d+\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)+)\b",
            ],
        )

    def _extract_email(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the applicant's email address.

        We collect all email-like strings, then filter out known office /
        institutional Marshall addresses so the result is more likely to be
        the applicant's personal or application email.
        """
        emails = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            full_text,
        )

        for email in emails:
            lowered = email.lower()

            if "marshall.edu" in lowered:
                continue
            if "services@" in lowered or "graduateadmissions@" in lowered:
                continue

            return email

        return None

    def _extract_muid(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the applicant's MUID.

        The form typically exposes a 9-digit identifier. We search page 1,
        then the checklist page, then the full document as a fallback.
        """
        return self._search(
            [pages.get(1, ""), pages.get(3, ""), full_text],
            [r"\b([0-9]{9})\b"],
        )

    def _extract_program(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the applicant's intended program or major.

        Preference order:
        - application summary page
        - checklist page
        - page 1 form cluster
        - full document fallback
        """
        return self._search(
            [pages.get(4, ""), pages.get(3, ""), pages.get(1, ""), full_text],
            [
                r"Program\s+([A-Za-z][^\n]{0,80}\([A-Za-z]{2}\))",
                r"Major\s+([A-Za-z][^\n]{0,80}\([A-Za-z]{2}\))",
                r"Major:\s*([A-Za-z][^\n]{0,80}\([A-Za-z]{2}\))",
            ],
        )

    def _extract_term(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the term the applicant is applying for.

        Handles common formats such as:
        - 'Summer 2025'
        - 'Term applying for: Summer 2025'
        - checklist style: semester and year appearing separately
        """
        value = self._search(
            [pages.get(4, ""), pages.get(3, ""), pages.get(1, ""), full_text],
            [
                r"Term\s+((?:Fall|Spring|Summer)\s+\d{4})",
                r"Term applying for:\s*((?:Fall|Spring|Summer)\s+\d{4})",
                r"ENROLLING SEMESTER:.*?(Fall|Spring|Summer)\b.*?YEAR:\s*(\d{4})",
                r"\b((?:Fall|Spring|Summer)\s+\d{4})\b",
            ],
        )

        # `_search(...)` only returns group(1), so if the two-group checklist
        # pattern matched, we need to reconstruct the "Season Year" result.
        if value and value in {"Fall", "Spring", "Summer"}:
            year_match = re.search(
                r"ENROLLING SEMESTER:.*?"
                + re.escape(value)
                + r".*?YEAR:\s*(\d{4})",
                pages.get(3, "") + "\n" + full_text,
                re.IGNORECASE | re.DOTALL,
            )
            if year_match:
                return f"{value} {year_match.group(1)}"

        return value

    def _extract_advisor(
        self,
        pages: dict[int, str],
        full_text: str,
    ) -> Optional[str]:
        """
        Extract the advisor assigned to the applicant.

        We prefer page 1 because advisor assignment usually appears there.
        The first pattern looks for a realistic 'Dr. ...' name. The second
        pattern is a broader fallback around the labeled advisor field.
        """
        page_one = pages.get(1, "")

        value = self._search(
            [page_one, full_text],
            [
                r"\b(Dr\.\s+[A-Z][A-Za-z.-]+(?:-[A-Z][A-Za-z.-]+)?\s+[A-Z][A-Za-z'-]+)\b",
                r"Advisor Assigned to Applicant:\s*([A-Za-z.\-'\s]+?)(?:\(|Authorized Signature|Date:)",
            ],
        )

        # Ignore obvious blank underline captures.
        if value and "_" not in value:
            return value

        return None

    def _extract_degree(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the degree earned by the applicant.

        This favors transcript / education-history pages, where degree data is
        usually more reliable than on checklist or cover pages.
        """
        return self._search(
            [pages.get(6, ""), pages.get(3, ""), full_text],
            [
                r"Degree Earned\s+([^\n]+)",
                r"Degree Earned[:\s]+([^\n]+)",
                r"Degree 1 Official\s+([^\n]+)",
            ],
        )

    def _extract_gpa(self, pages: dict[int, str], full_text: str) -> Optional[str]:
        """
        Extract the applicant's undergraduate GPA.

        Preference order:
        1. Transcript totals page with the OVERALL GPA row.
        2. Checklist-style GPA fields if transcript totals are unavailable.
        """
        value = self._search(
            [pages.get(8, ""), full_text],
            [r"OVERALL\s+\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+([0-4]\.\d{2})"],
        )
        if value:
            return value

        return self._search(
            [pages.get(3, ""), full_text],
            [r"GPA[:\s]*([0-4](?:\.\d{1,2})?)"],
        )

    def _extract_admission_decision(
        self,
        pages: dict[int, str],
        full_text: str,
    ) -> Optional[str]:
        """
        Infer the admission decision from page 1.

        Important:
        - This form always contains boilerplate option labels for both
          'Conditional Admission' and 'Denial of Admission'.
        - We therefore avoid interpreting those labels alone as a real
          decision.
        - For now, we only emit 'Conditional' when there are supporting
          signals in the filled value cluster.
        """
        page_one = pages.get(1, "")

        if re.search(r"Conditional Admission", page_one, re.IGNORECASE):
            if re.search(r"Degree not related to CS", page_one, re.IGNORECASE) and re.search(
                r"Dr\.\s+[A-Z]",
                page_one,
                re.IGNORECASE,
            ):
                return "Conditional"

        return None