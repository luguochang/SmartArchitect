"""
Document Parser Service
Handles parsing of PDF, Docx, and Markdown files for RAG system
"""

import logging
from pathlib import Path
from typing import List, Literal
import re

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of text from a document"""

    def __init__(self, content: str, chunk_id: str, metadata: dict):
        self.content = content
        self.chunk_id = chunk_id
        self.metadata = metadata


class DocumentParser:
    """Parser for various document formats"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_file(
        self, file_path: str, file_type: Literal["pdf", "markdown", "docx"]
    ) -> List[DocumentChunk]:
        """Parse a file and return chunks"""

        if file_type == "pdf":
            return self._parse_pdf(file_path)
        elif file_type == "markdown":
            return self._parse_markdown(file_path)
        elif file_type == "docx":
            return self._parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _parse_pdf(self, file_path: str) -> List[DocumentChunk]:
        """Parse PDF file"""

        if PdfReader is None:
            raise ImportError("PyPDF2 is not installed. Install with: pip install pypdf2")

        try:
            reader = PdfReader(file_path)
            full_text = ""

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

            filename = Path(file_path).name
            return self._chunk_text(full_text, filename, "pdf")

        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    def _parse_markdown(self, file_path: str) -> List[DocumentChunk]:
        """Parse Markdown file"""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            filename = Path(file_path).name
            return self._chunk_text(content, filename, "markdown")

        except Exception as e:
            logger.error(f"Failed to parse Markdown {file_path}: {e}")
            raise

    def _parse_docx(self, file_path: str) -> List[DocumentChunk]:
        """Parse Docx file"""

        if DocxDocument is None:
            raise ImportError(
                "python-docx is not installed. Install with: pip install python-docx"
            )

        try:
            doc = DocxDocument(file_path)
            full_text = "\n\n".join([para.text for para in doc.paragraphs if para.text])

            filename = Path(file_path).name
            return self._chunk_text(full_text, filename, "docx")

        except Exception as e:
            logger.error(f"Failed to parse Docx {file_path}: {e}")
            raise

    def _chunk_text(
        self, text: str, filename: str, file_type: str
    ) -> List[DocumentChunk]:
        """Split text into overlapping chunks"""

        # Clean text
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) == 0:
            logger.warning(f"Document {filename} is empty")
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size

            # Find the last complete sentence or word boundary
            if end < len(text):
                # Try to find last period, question mark, or exclamation point
                last_sentence = max(
                    text.rfind(".", start, end),
                    text.rfind("?", start, end),
                    text.rfind("!", start, end),
                )

                if last_sentence != -1 and last_sentence > start:
                    end = last_sentence + 1
                else:
                    # Fallback to last space
                    last_space = text.rfind(" ", start, end)
                    if last_space != -1 and last_space > start:
                        end = last_space

            chunk_content = text[start:end].strip()

            if chunk_content:
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_id=f"{filename}_chunk_{chunk_index}",
                    metadata={
                        "filename": filename,
                        "file_type": file_type,
                        "chunk_index": chunk_index,
                        "start_char": start,
                        "end_char": end,
                    },
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop if chunk_size is too small
            if start <= 0:
                start = end

        logger.info(f"Created {len(chunks)} chunks from {filename}")
        return chunks


# Helper function to create parser instance
def create_document_parser(chunk_size: int = 1000, chunk_overlap: int = 200):
    """Create a DocumentParser instance"""
    return DocumentParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
