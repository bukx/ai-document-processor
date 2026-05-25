"""Core document processing workflow."""

from __future__ import annotations

import json
from pathlib import Path

from .classifier import classify_text, extract_entities
from .extractor import extract_text


def process_document(path: str | Path, output_dir: str | Path) -> Path:
    source = Path(path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    text = extract_text(source)
    classification = classify_text(text)
    entities = extract_entities(text)

    payload = {
        "source_file": source.name,
        "classification": classification,
        "entities": entities,
        "text_preview": text[:500],
        "character_count": len(text),
    }

    result_file = output_path / f"{source.stem}.json"
    result_file.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return result_file
