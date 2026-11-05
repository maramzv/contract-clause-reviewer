"""Chunk: overlapping windows on paragraph boundaries, each carrying its absolute offset."""
from dataclasses import dataclass


@dataclass
class Chunk:
    start: int
    text: str


def chunk(text: str, size: int = 3000, overlap: int = 300):
    chunks, i, n = [], 0, len(text)
    while i < n:
        end = min(i + size, n)
        if end < n:  # prefer to break at a paragraph/sentence boundary
            cut = text.rfind("\n\n", i + size // 2, end)
            if cut == -1:
                cut = text.rfind(". ", i + size // 2, end)
            if cut != -1:
                end = cut + 1
        chunks.append(Chunk(i, text[i:end]))
        if end >= n:
            break
        i = max(end - overlap, i + 1)
    return chunks
