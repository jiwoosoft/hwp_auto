"""Integration tests for `HwpDocument.replace_paragraph`.

Verifies that the immutable edit method correctly dispatches on
`source_format` and preserves the rest of the document.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from master_of_hwp import HwpDocument

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def hwpx_sample(samples_dir: Path) -> Path:
    sample = samples_dir / "public-official" / "table-vpos-01.hwpx"
    if not sample.exists():
        pytest.skip("HWPX sample missing")
    return sample


def test_hwpx_replace_paragraph_returns_new_document(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    original_paragraphs = doc.section_paragraphs

    target_section = 0
    target_paragraph = next(i for i, text in enumerate(original_paragraphs[target_section]) if text)
    new_text = "교체된 문단 — integration test"

    edited = doc.replace_paragraph(target_section, target_paragraph, new_text)

    assert edited is not doc
    assert edited.raw_bytes != doc.raw_bytes
    assert edited.source_format == doc.source_format
    assert edited.path == doc.path

    edited_paragraphs = edited.section_paragraphs
    assert edited_paragraphs[target_section][target_paragraph] == new_text
    assert len(edited_paragraphs) == len(original_paragraphs)
    assert len(edited_paragraphs[target_section]) == len(original_paragraphs[target_section])


def test_hwpx_replace_paragraph_out_of_range_raises(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)

    with pytest.raises(IndexError):
        doc.replace_paragraph(999, 0, "never applied")
