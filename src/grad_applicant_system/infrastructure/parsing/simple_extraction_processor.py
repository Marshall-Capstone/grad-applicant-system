import re
from typing import Optional


class SimpleExtractionProcessor:
    """Converts raw text to structured applicant data.
    """

    def extract(self, text: Optional[str]) -> dict:
        if not text:
            return {"name": None, "email": None, "gpa": None}

        # normalize to str
        text = str(text)

        return {
            "name": self._name(text),
            "email": self._email(text),
            "gpa": self._gpa(text),
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
        match = re.search(r"GPA[:\s]*([0-4]\.\d+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def _name(self, text: str) -> Optional[str]:
        for line in text.split("\n"):
            if line and line.strip():
                return line.strip()
        return None