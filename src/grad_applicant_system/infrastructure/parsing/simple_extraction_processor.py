import re
from typing import Optional


class SimpleExtractionProcessor:
    """Converts raw text to structured applicant / application data.

    Produces a dict with keys aligned to the updated schema:
    - `applicant_name`, `undergraduate_gpa`, `degree_earned`
    - `program_major`
    - `advisor_name`
    - `term_applying_for`, `admission_decision`

    Backwards-compatible keys are preserved where sensible (`full_name`, `name`).
    """

    def extract(self, text: Optional[str]) -> dict:
        if not text:
            return {
                "applicant_name": None,
                "full_name": None,
                "name": None,
                "undergraduate_gpa": None,
                "degree_earned": None,
                "program_major": None,
                "advisor_name": None,
                "term_applying_for": None,
                "admission_decision": None,
            }

        # normalize to str
        text = str(text)

        full_name = self._full_name(text)

        return {
            # Applicant
            "applicant_name": full_name,
            "full_name": full_name,
            "name": full_name,
            "undergraduate_gpa": self._gpa(text),
            "degree_earned": self._degree(text),

            # Program / advisor / application
            "program_major": self._program(text),
            "advisor_name": self._advisor(text),
            "term_applying_for": self._term(text),
            "admission_decision": self._status(text),
        }

    # Backwards-compatible adapters
    def process_extracted_text(self, text: Optional[str]) -> dict:
        """Adapter for the `ExtractionProcessor` port expected method name.

        Keeps existing behavior but provides the port-compatible name so
        callers don't need to be changed when this class is used directly.
        """
        return self.extract(text)

    def extract_applicant_data(self, text: Optional[str]) -> dict:
        """Legacy adapter used by some callers.

        Maintains compatibility with older code that calls
        `extract_applicant_data` instead of `extract`.
        """
        return self.extract(text)

    def _email(self, text: str) -> Optional[str]:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    def _gpa(self, text: str) -> Optional[str]:
        # Match common GPA formats like 3.7, 3.70 or 4.00
        match = re.search(r"GPA[:\s]*([0-4](?:\.\d{1,2})?)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def _degree(self, text: str) -> Optional[str]:
        match = re.search(r"Degree[:\s]*(.+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _name(self, text: str) -> Optional[str]:
        # Deprecated alias retained for compatibility. Prefer `_full_name`.
        return self._full_name(text)

    def _id(self, text: str) -> Optional[str]:
        match = re.search(r"(?:Applicant ID|Student ID|ID)[:\s]*([A-Za-z0-9-]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def _full_name(self, text: str) -> Optional[str]:
        # Look for explicit labels first
        match = re.search(r"(?:Full Name|Name)[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Fallback: first non-empty line
        for line in text.split("\n"):
            if line and line.strip():
                return line.strip()
        return None

    def _program(self, text: str) -> Optional[str]:
        match = re.search(r"(?:Program|Intended Program|Major)[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _advisor(self, text: str) -> Optional[str]:
        match = re.search(r"Advisor[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _term(self, text: str) -> Optional[str]:
        match = re.search(r"Term[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _status(self, text: str) -> Optional[str]:
        match = re.search(r"Status[:\s]*(\w+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None