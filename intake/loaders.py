import os
import hashlib
from typing import List, Dict, Any

import requests
import pypdf
import docx
from bs4 import BeautifulSoup


def get_file_hash(file_bytes: bytes) -> str:
    """Generate a SHA256 hash of file content for de-duplication / tracking."""
    return hashlib.sha256(file_bytes).hexdigest()


class Doc:
    """Lightweight native document container (no LangChain dependency)."""

    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Doc(len={len(self.page_content)}, metadata={self.metadata})"


class DocumentLoader:
    """Native multi-format loader: PDF (+OCR fallback), DOCX, TXT, and web pages."""

    @staticmethod
    def load_pdf(file_path: str) -> List[Doc]:
        """Extract text per page from a PDF, falling back to OCR for scanned pages."""
        docs = []
        filename = os.path.basename(file_path)
        reader = pypdf.PdfReader(file_path)

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            # Fallback 1: pdfplumber (handles some layouts pypdf misses)
            if not text.strip():
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        if page_idx < len(pdf.pages):
                            text = pdf.pages[page_idx].extract_text() or ""
                except Exception:
                    pass

            # Fallback 2: OCR via pytesseract for image-only / scanned pages
            if not text.strip():
                try:
                    import pytesseract
                    from PIL import Image
                    import fitz  # PyMuPDF

                    fitz_doc = fitz.open(file_path)
                    pix = fitz_doc[page_idx].get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text = pytesseract.image_to_string(img) or ""
                except Exception:
                    pass

            if text.strip():
                docs.append(Doc(
                    page_content=text,
                    metadata={
                        "source": file_path,
                        "filename": filename,
                        "file_type": "pdf",
                        "page": page_idx + 1,
                    },
                ))
        return docs

    @staticmethod
    def load_txt(file_path: str) -> List[Doc]:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return [Doc(
            page_content=content,
            metadata={"source": file_path, "filename": filename, "file_type": "txt", "page": 1},
        )]

    @staticmethod
    def load_docx(file_path: str) -> List[Doc]:
        document = docx.Document(file_path)
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        content = "\n\n".join(paragraphs)
        filename = os.path.basename(file_path)
        return [Doc(
            page_content=content,
            metadata={"source": file_path, "filename": filename, "file_type": "docx", "page": 1},
        )]

    @staticmethod
    def load_url(url: str) -> List[Doc]:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NimbusRAG/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = "\n".join(lines)

        return [Doc(
            page_content=cleaned,
            metadata={"source": url, "filename": url, "file_type": "url", "page": 1},
        )]

    @classmethod
    def load_file(cls, file_path: str) -> List[Doc]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.load_pdf(file_path)
        elif ext == ".txt" or ext == ".md":
            return cls.load_txt(file_path)
        elif ext in (".docx", ".doc"):
            return cls.load_docx(file_path)
        raise ValueError(f"Unsupported file format: {ext}")
