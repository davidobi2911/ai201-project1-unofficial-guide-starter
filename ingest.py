"""Milestone 3 — Document ingestion and chunking.

Loads every .txt file in the documents/ folder and splits it into overlapping
character-based chunks for embedding (Milestone 4).

Chunking strategy (see planning.md):
  - Chunk size: 300 characters (target maximum)
  - Overlap:    50 characters
  These documents are mostly short, opinion-based reviews and tips (1-4 sentences
  each), so a 300-char window captures roughly one self-contained review/tip without
  merging unrelated opinions, while a 50-char overlap keeps a thought retrievable
  even when it straddles a chunk boundary.

Preprocessing before chunking:
  - URL-bearing lines (the "Primary URLs:" header blocks and inline "Source:/Profile:"
    citation lines) are dropped so no chunk is a bare URL fragment. The URLs are still
    recorded in README.md / planning.md for source attribution.
  - Chunk boundaries snap to the nearest whitespace, so no chunk starts or ends
    mid-word. Chunks are therefore <= 300 chars rather than exactly 300.

Run directly to see per-document and total chunk counts:
    python ingest.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


@dataclass
class Chunk:
    """One retrievable unit of text plus where it came from."""

    id: str           # stable unique id, e.g. "yelp_dining.txt::3"
    text: str         # the chunk content
    source_file: str  # filename, e.g. "yelp_dining.txt"
    source_label: str # human-readable source from the file's "Source:" header line
    chunk_index: int  # position of this chunk within its document


def load_documents(documents_dir: str = DOCUMENTS_DIR) -> list[tuple[str, str]]:
    """Return a list of (filename, text) for every .txt file in documents_dir."""
    docs: list[tuple[str, str]] = []
    for filename in sorted(os.listdir(documents_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(documents_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            docs.append((filename, text))
    return docs


def _source_label(text: str) -> str:
    """Pull a readable source name from the leading 'Source: ...' line, if present."""
    for line in text.lstrip().splitlines():
        if line.lower().startswith("source:") and "http" not in line.lower():
            return line.split(":", 1)[1].strip()
    return ""


def preprocess(text: str) -> str:
    """Strip URL-bearing lines before chunking and collapse blank-line runs.

    Removes header URL blocks (e.g. "- CLUE Tutoring: https://...") and inline citation
    lines ("Source: https://...", "Profile: https://...") so chunks are prose, not bare
    URL fragments. Non-URL header labels (plain "Source:", "Type:", etc.) are kept.
    """
    kept = [line for line in text.splitlines() if "http" not in line.lower()]
    out: list[str] = []
    for line in kept:
        # collapse consecutive blank lines left behind by removed URL lines
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return "\n".join(out).strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks, snapping boundaries to whitespace.

    A chunk is at most chunk_size characters and is trimmed back to the last whitespace
    so it never ends mid-word; the next chunk starts ~overlap characters earlier, also
    advanced to a word boundary so it never starts mid-word. Whitespace-only chunks are
    dropped.
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    text = text.strip()
    n = len(text)
    chunks: list[str] = []
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:  # not the final chunk: back off to the last whitespace in the window
            cut = max(text.rfind(" ", start + 1, end + 1),
                      text.rfind("\n", start + 1, end + 1))
            if cut > start:
                end = cut

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break

        # Step back by `overlap`, then snap forward to the next word boundary so the
        # next chunk doesn't begin mid-word. Always advance to avoid an infinite loop.
        nxt = max(end - overlap, start + 1)
        boundary = text.find(" ", nxt)
        if start < boundary < end:
            nxt = boundary + 1
        start = nxt
    return chunks


def chunk_documents(documents_dir: str = DOCUMENTS_DIR,
                    chunk_size: int = CHUNK_SIZE,
                    overlap: int = CHUNK_OVERLAP) -> list[Chunk]:
    """Load all documents and return a flat list of Chunk objects with metadata."""
    all_chunks: list[Chunk] = []
    for filename, text in load_documents(documents_dir):
        label = _source_label(text)
        cleaned = preprocess(text)
        for i, piece in enumerate(chunk_text(cleaned, chunk_size, overlap)):
            all_chunks.append(
                Chunk(
                    id=f"{filename}::{i}",
                    text=piece,
                    source_file=filename,
                    source_label=label,
                    chunk_index=i,
                )
            )
    return all_chunks


def main() -> None:
    docs = load_documents()
    chunks = chunk_documents()

    print(f"Loaded {len(docs)} documents from {DOCUMENTS_DIR}")
    print(f"Chunk size: {CHUNK_SIZE} chars, overlap: {CHUNK_OVERLAP} chars\n")

    per_file: dict[str, int] = {}
    for c in chunks:
        per_file[c.source_file] = per_file.get(c.source_file, 0) + 1

    width = max(len(name) for name in per_file)
    for filename, _ in docs:
        print(f"  {filename:<{width}}  {per_file.get(filename, 0):>3} chunks")

    print(f"\nTotal chunks across all documents: {len(chunks)}")

    # Show one example chunk so the output is easy to sanity-check.
    if chunks:
        ex = chunks[len(chunks) // 2]
        print(f"\nExample chunk [{ex.id}] from \"{ex.source_label}\":")
        print(f"  {ex.text!r}")


if __name__ == "__main__":
    main()
