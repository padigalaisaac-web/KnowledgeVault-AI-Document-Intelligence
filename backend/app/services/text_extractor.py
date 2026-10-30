"""Text extraction service supporting PDF, TXT, and Markdown with page tracking."""
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger("knowledgevault.extractor")


def normalize_whitespace(text: str) -> str:
    """Normalize excessive whitespace while preserving intentional paragraph breaks."""
    if not text:
        return ""
    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace sequences of 3+ newlines with double newline (paragraph boundary)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Replace non-newline whitespace runs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Strip leading and trailing whitespace on lines
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


class ExtractedPage:
    def __init__(self, page_number: int, text: str, is_empty: bool = False, is_scanned_suspicion: bool = False):
        self.page_number = page_number
        self.text = text
        self.is_empty = is_empty
        self.is_scanned_suspicion = is_scanned_suspicion


class TextExtractor:
    """Extracts text page-by-page from PDF, TXT, and Markdown files."""

    @classmethod
    def extract(cls, file_path: str, file_type: str) -> Tuple[List[ExtractedPage], Dict[str, Any]]:
        """Extract text content and metadata from the given file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return cls._extract_pdf(path)
        elif ext in [".txt", ".md", ".markdown"]:
            return cls._extract_plaintext(path, ext)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Allowed: .pdf, .txt, .md")

    @classmethod
    def _extract_pdf(cls, path: Path) -> Tuple[List[ExtractedPage], Dict[str, Any]]:
        """Extract PDF pages using PyMuPDF (fitz) or pypdf fallback."""
        pages: List[ExtractedPage] = []
        meta: Dict[str, Any] = {"extractor": "pypdf", "page_count": 0, "warnings": []}

        # Try PyMuPDF first
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            meta["extractor"] = "PyMuPDF"
            meta["page_count"] = len(doc)

            for i in range(len(doc)):
                page = doc[i]
                raw_text = page.get_text("text") or ""
                cleaned = normalize_whitespace(raw_text)
                is_empty = len(cleaned) == 0
                is_scanned = (not is_empty) and (len(cleaned) < 30)

                if is_scanned:
                    meta["warnings"].append(
                        f"Page {i+1} has very little text ({len(cleaned)} chars); it may be an image or scanned page."
                    )

                pages.append(ExtractedPage(
                    page_number=i + 1,
                    text=cleaned,
                    is_empty=is_empty,
                    is_scanned_suspicion=is_scanned
                ))
            doc.close()
            return pages, meta
        except (ImportError, Exception) as pymupdf_err:
            logger.info("PyMuPDF unavailable or threw error (%s), using pypdf fallback", pymupdf_err)

        # Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            meta["extractor"] = "pypdf"
            meta["page_count"] = len(reader.pages)

            for i, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                cleaned = normalize_whitespace(raw_text)
                is_empty = len(cleaned) == 0
                is_scanned = (not is_empty) and (len(cleaned) < 30)

                if is_scanned:
                    meta["warnings"].append(
                        f"Page {i+1} has very little text ({len(cleaned)} chars); it may be an image or scanned page."
                    )

                pages.append(ExtractedPage(
                    page_number=i + 1,
                    text=cleaned,
                    is_empty=is_empty,
                    is_scanned_suspicion=is_scanned
                ))
            return pages, meta
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF {path.name}: {str(e)}")

    @classmethod
    def _extract_plaintext(cls, path: Path, ext: str) -> Tuple[List[ExtractedPage], Dict[str, Any]]:
        """Extract plain text or markdown files."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file {path.name}: {str(e)}")

        cleaned = normalize_whitespace(content)
        pages = [ExtractedPage(page_number=1, text=cleaned, is_empty=len(cleaned) == 0)]
        meta = {
            "extractor": "plaintext" if ext == ".txt" else "markdown",
            "page_count": 1,
            "char_count": len(cleaned),
            "warnings": []
        }
        return pages, meta
