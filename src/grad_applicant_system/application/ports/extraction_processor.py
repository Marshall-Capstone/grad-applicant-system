from abc import ABC, abstractmethod


class ExtractionProcessor(ABC):
    @abstractmethod
    def process_extracted_text(self, text: str) -> dict:
        pass