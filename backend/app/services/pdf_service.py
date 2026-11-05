"""
PDF service — text and image extraction from PDF files.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFService:
    @staticmethod
    def extract_text(file_path: str) -> list[str]:
        """
        Extract text per-page from a PDF.
        Falls back to OCR (pytesseract) for scanned pages.

        Returns a list of strings, one per page.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            pages: list[str] = []
            for page in doc:
                text = page.get_text()
                if not text.strip():
                    # Scanned page — try OCR
                    text = PDFService._ocr_page(page)
                pages.append(text)
            doc.close()
            return pages
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to extract text from %s: %s", file_path, exc)
            return []

    @staticmethod
    def _ocr_page(page) -> str:  # type: ignore[no-untyped-def]
        """OCR a single PyMuPDF page using Tesseract."""
        try:
            import pytesseract
            from PIL import Image
            import io

            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            return pytesseract.image_to_string(image)
        except Exception as exc:  # noqa: BLE001
            logger.warning("OCR failed for page: %s", exc)
            return ""

    @staticmethod
    def extract_page_count(file_path: str) -> Optional[int]:
        """Return number of pages in a PDF without full extraction."""
        try:
            import fitz

            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:  # noqa: BLE001
            return None
