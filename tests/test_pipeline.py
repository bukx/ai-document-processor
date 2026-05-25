from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_document_processor.classifier import classify_text, extract_entities  # noqa: E402
from ai_document_processor.pipeline import process_document  # noqa: E402


class PipelineTests(unittest.TestCase):
    def test_classifier_detects_invoice(self) -> None:
        label = classify_text("Invoice INV-12\nVendor: Acme\nTotal Due: $99.00")
        self.assertEqual(label, "invoice")

    def test_extract_entities_finds_email_and_amount(self) -> None:
        entities = extract_entities("Contact buyer@example.com before 2026-06-01 for $42.50")
        self.assertIn("buyer@example.com", entities["emails"])
        self.assertIn("$42.50", entities["currency_amounts"])
        self.assertIn("2026-06-01", entities["dates"])

    def test_pipeline_writes_result_file(self) -> None:
        tmpdir = pathlib.Path(tempfile.mkdtemp())
        source = tmpdir / "resume.txt"
        source.write_text("Skills: Python, Terraform, Kubernetes\nExperience: 5 years")

        output_file = process_document(source, tmpdir / "output")
        payload = json.loads(output_file.read_text())

        self.assertEqual(payload["classification"], "resume")
        self.assertEqual(payload["source_file"], "resume.txt")


if __name__ == "__main__":
    unittest.main()
