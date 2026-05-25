"""Local text extraction adapters."""

from __future__ import annotations

from pathlib import Path


def extract_text(path: str | Path) -> str:
    document_path = Path(path)
    raw_bytes = document_path.read_bytes()
    if document_path.suffix.lower() in {".txt", ".md", ".csv", ".json"}:
        return raw_bytes.decode("utf-8")

    # Local fallback to keep the pipeline runnable without external OCR services.
    return raw_bytes.decode("utf-8", errors="ignore")
