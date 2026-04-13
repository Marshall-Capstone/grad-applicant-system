import re
from typing import Optional


class SimpleExtractionProcessor:
    """Converts raw text to structured applicant data.

    Produces a dict containing keys that mirror the `applicants` table
    schema: `id`, `full_name`, `email`, `program`, `gpa`, `status`,
    `keywords_text`, `created_at` (where available). For backwards
    compatibility the key `name` is preserved as an alias for `full_name`.
    """

    def extract(self, text: Optional[str]) -> dict:
        if not text:
            return {
                "id": None,
                "full_name": None,
                "name": None,
                "email": None,
                "program": None,
                "gpa": None,
                "status": None,
                "keywords_text": None,
                "created_at": None,
            }

        # normalize to str
        text = str(text)

        full_name = self._full_name(text)
        gpa = self._gpa(text)

        return {
            "id": self._id(text),
            "full_name": full_name,
            # keep `name` for compatibility with older callers
            "name": full_name,
            "email": self._email(text),
            "program": self._program(text),
            "gpa": gpa,
            "status": self._status(text),
            "keywords_text": self._keywords_text(text),
            "created_at": self._created_at(text),
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

    def _status(self, text: str) -> Optional[str]:
        match = re.search(r"Status[:\s]*(\w+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _keywords_text(self, text: str) -> Optional[str]:
        match = re.search(r"Keywords?[:\s]*(.+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _created_at(self, text: str) -> Optional[str]:
        # Try to find an ISO-like date (YYYY-MM-DD) as a crude heuristic
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
        if match:
            return match.group(1)
        return None