import logging
import re
from pathlib import Path

import fitz  # pymupdf

logger = logging.getLogger(__name__)


def extract_papers(intake_dir: str) -> list[dict]:
    """Extract text from all PDFs in intake_dir, preserving page numbers.

    Returns a list of dicts with keys: filename, pages, total_pages,
    extraction_success.
    """
    intake_path = Path(intake_dir)
    pdf_files = sorted(intake_path.glob("*.pdf"))

    if not pdf_files:
        return []

    papers = []
    for pdf_path in pdf_files:
        paper = _extract_single_paper(pdf_path)
        papers.append(paper)

    return papers


def _extract_single_paper(pdf_path: Path) -> dict:
    """Extract text from a single PDF file."""
    result = {
        "filename": pdf_path.name,
        "pages": [],
        "total_pages": 0,
        "extraction_success": False,
    }

    try:
        doc = fitz.open(str(pdf_path))
        result["total_pages"] = len(doc)

        for page_num in range(len(doc)):
            page = doc[page_num]
            raw_text = page.get_text()
            cleaned_text = _clean_text(raw_text)
            result["pages"].append({
                "page_num": page_num + 1,
                "text": cleaned_text,
            })

        doc.close()
        result["extraction_success"] = True
        logger.info(f"Extracted {result['total_pages']} pages from {pdf_path.name}")

    except Exception as e:
        logger.warning(f"Failed to extract {pdf_path.name}: {e}")

    return result


def _clean_text(text: str) -> str:
    """Strip excessive whitespace while preserving paragraph structure."""
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of spaces/tabs to a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse more than two consecutive newlines to two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
