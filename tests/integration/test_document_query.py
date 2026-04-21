"""Integration tests for `HwpDocument` query / iteration / projection APIs.

Covers `plain_text`, `iter_paragraphs`, and `find_paragraphs` against
real HWP and HWPX samples.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from master_of_hwp import HwpDocument

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def hwp_sample(samples_dir: Path) -> Path:
    sample = samples_dir / "public-official" / "re-mixed-0tr.hwp"
    if not sample.exists():
        pytest.skip("HWP 5.0 sample missing")
    return sample


@pytest.fixture(scope="module")
def hwpx_sample(samples_dir: Path) -> Path:
    sample = samples_dir / "public-official" / "table-vpos-01.hwpx"
    if not sample.exists():
        pytest.skip("HWPX sample missing")
    return sample


# ---- plain_text -----------------------------------------------------


def test_hwp_document_plain_text_normalizes_carriage_return(hwp_sample: Path) -> None:
    doc = HwpDocument.open(hwp_sample)
    text = doc.plain_text
    assert isinstance(text, str)
    assert "\r" not in text, "HWP 5.0 \\r should be normalized to \\n"
    assert len(text) > 0


def test_hwpx_document_plain_text_returns_concatenated_string(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    text = doc.plain_text
    assert isinstance(text, str)
    assert len(text) > 0
    assert "보도자료" in text


def test_plain_text_uses_double_newline_section_separator(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    sections = doc.section_texts
    expected = "\n\n".join(sections)
    assert doc.plain_text == expected


# ---- iter_paragraphs ------------------------------------------------


def test_iter_paragraphs_yields_correct_total_count(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    paragraphs = doc.section_paragraphs
    expected_total = sum(len(s) for s in paragraphs)
    yielded = list(doc.iter_paragraphs())
    assert len(yielded) == expected_total


def test_iter_paragraphs_yields_in_document_order(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    indices = [(s, p) for s, p, _ in doc.iter_paragraphs()]
    assert indices == sorted(indices)


def test_iter_paragraphs_text_matches_section_paragraphs(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    paragraphs = doc.section_paragraphs
    for section_index, paragraph_index, text in doc.iter_paragraphs():
        assert paragraphs[section_index][paragraph_index] == text


# ---- find_paragraphs ------------------------------------------------


def test_find_paragraphs_substring_match(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    hits = doc.find_paragraphs("보도자료")
    assert len(hits) >= 1
    for _section_index, _paragraph_index, text in hits:
        assert "보도자료" in text


def test_find_paragraphs_returns_empty_for_no_match(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    assert doc.find_paragraphs("THIS_STRING_WILL_NEVER_EXIST_xyz123") == []


def test_find_paragraphs_case_insensitive(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    needle = next(text for _, _, text in doc.iter_paragraphs() if text)
    if not any(c.isalpha() for c in needle):
        pytest.skip("Sample paragraph has no case-bearing characters")
    case_sensitive_hits = doc.find_paragraphs(needle.upper())
    case_insensitive_hits = doc.find_paragraphs(needle.upper(), case_sensitive=False)
    assert len(case_insensitive_hits) >= len(case_sensitive_hits)


def test_find_paragraphs_regex_mode(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    hits = doc.find_paragraphs(r"^보도", regex=True)
    assert all(text.startswith("보도") for _, _, text in hits)


# ---- find + replace round-trip --------------------------------------


def test_find_then_replace_round_trip(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    hits = doc.find_paragraphs("보도자료")
    assert hits, "expected at least one '보도자료' paragraph in sample"
    section_index, paragraph_index, _ = hits[0]
    replacement = "REPLACED ONCE"
    edited = doc.replace_paragraph(section_index, paragraph_index, replacement)
    assert edited.section_paragraphs[section_index][paragraph_index] == replacement
    assert edited.find_paragraphs(replacement) == [(section_index, paragraph_index, replacement)]


# ---- summary() ------------------------------------------------------


def test_summary_returns_expected_keys(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    info = doc.summary()
    expected_keys = {
        "format",
        "filename",
        "byte_size",
        "sections_count",
        "paragraph_count",
        "non_empty_paragraph_count",
        "table_count",
        "first_paragraphs",
    }
    assert set(info.keys()) == expected_keys


def test_summary_does_not_leak_full_path(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    info = doc.summary()
    filename = info["filename"]
    assert filename == hwpx_sample.name
    assert isinstance(filename, str)
    assert "/" not in filename


def test_summary_previews_are_truncated(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    info = doc.summary(max_preview=20, preview_count=2)
    previews = info["first_paragraphs"]
    assert isinstance(previews, list)
    assert len(previews) <= 2
    for preview in previews:
        assert isinstance(preview, str)
        assert len(preview) <= 20


def test_summary_counts_match_section_data(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    info = doc.summary()
    assert info["sections_count"] == doc.sections_count
    assert info["paragraph_count"] == sum(len(s) for s in doc.section_paragraphs)
    assert info["table_count"] == sum(len(s) for s in doc.section_tables)
