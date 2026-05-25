"""CLI for the local document processor."""

from __future__ import annotations

import argparse

from .pipeline import process_document


def main() -> None:
    parser = argparse.ArgumentParser(description="AI document processor")
    parser.add_argument("document", help="Path to the source document")
    parser.add_argument("--output-dir", default="output", help="Directory for JSON output")
    args = parser.parse_args()

    result = process_document(args.document, args.output_dir)
    print(result)


if __name__ == "__main__":
    main()
