"""Local and AWS-backed text extraction adapters."""

from __future__ import annotations

import os
from pathlib import Path

from .aws_helpers import client


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


def extract_text(path: str | Path) -> str:
    document_path = Path(path)
    return extract_text_from_bytes(document_path.read_bytes(), document_path.name)


def extract_text_from_bytes(raw_bytes: bytes, filename: str = "") -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return raw_bytes.decode("utf-8")

    # Local fallback to keep the pipeline runnable without external OCR services.
    return raw_bytes.decode("utf-8", errors="ignore")


def extract_text_from_s3(bucket_name: str, object_key: str) -> str:
    s3 = client("s3")
    document = s3.get_object(Bucket=bucket_name, Key=object_key)
    raw_bytes = document["Body"].read()

    if os.getenv("USE_TEXTRACT", "true").lower() != "true":
        return extract_text_from_bytes(raw_bytes, object_key)

    suffix = Path(object_key).suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return extract_text_from_bytes(raw_bytes, object_key)

    textract = client("textract")
    response = textract.detect_document_text(Document={"Bytes": raw_bytes})
    lines = [
        block["Text"]
        for block in response.get("Blocks", [])
        if block.get("BlockType") == "LINE" and block.get("Text")
    ]
    if lines:
        return "\n".join(lines)
    return extract_text_from_bytes(raw_bytes, object_key)
