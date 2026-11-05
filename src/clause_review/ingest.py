"""Ingest: file -> text plus an offset-to-page map. Raises IngestError on unreadable files."""
import bisect
from dataclasses import dataclass
from pathlib import Path


class IngestError(Exception):
    pass


@dataclass
class Doc:
    name: str
    text: str
    page_starts: list  # char offset where each page begins (page 1 = index 0)

    def page_at(self, offset: int) -> int:
        return max(1, bisect.bisect_right(self.page_starts, offset))


def ingest(path) -> Doc:
    p = Path(path)
    try:
        if p.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            parts, starts, pos = [], [], 0
            for page in PdfReader(str(p)).pages:
                t = page.extract_text() or ""
                starts.append(pos)
                parts.append(t)
                pos += len(t) + 1
            text = "\n".join(parts)
        else:
            text, starts = p.read_text(encoding="utf-8", errors="replace"), [0]
    except Exception as e:  # corrupt PDF, permissions, etc.
        raise IngestError(f"{p.name}: {e}") from e
    if len(text.strip()) < 50:
        raise IngestError(f"{p.name}: no extractable text (scanned PDF? OCR is out of scope)")
    return Doc(p.name, text, starts or [0])
