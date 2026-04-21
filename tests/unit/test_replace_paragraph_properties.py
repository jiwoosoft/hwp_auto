"""Property-based tests for `HwpDocument.replace_paragraph` invariants.

Uses Hypothesis to assert structural properties that should hold for
any valid (section, paragraph, text) triple over the HWPX sample:

* **Idempotency**: replacing a paragraph with its current text produces
  a document whose paragraph enumeration is identical.
* **Locality**: replacing one paragraph leaves all other paragraphs
  unchanged.
* **Roundtrip**: re-parsing the edited bytes recovers the new text at
  the targeted index.
* **Sections preserved**: the section count never changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from master_of_hwp import HwpDocument

pytestmark = pytest.mark.property


@pytest.fixture(scope="module")
def hwpx_doc(samples_dir: Path) -> HwpDocument:
    sample = samples_dir / "public-official" / "table-vpos-01.hwpx"
    if not sample.exists():
        pytest.skip("HWPX sample missing")
    return HwpDocument.open(sample)


@pytest.fixture(scope="module")
def hwpx_paragraph_indices(hwpx_doc: HwpDocument) -> list[tuple[int, int]]:
    return [
        (s, p)
        for s, paragraphs in enumerate(hwpx_doc.section_paragraphs)
        for p in range(len(paragraphs))
    ]


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(index_choice=st.data())
def test_idempotent_replace_preserves_paragraph_structure(
    hwpx_doc: HwpDocument,
    hwpx_paragraph_indices: list[tuple[int, int]],
    index_choice: st.DataObject,
) -> None:
    section_index, paragraph_index = index_choice.draw(st.sampled_from(hwpx_paragraph_indices))
    original = hwpx_doc.section_paragraphs[section_index][paragraph_index]
    edited = hwpx_doc.replace_paragraph(section_index, paragraph_index, original)
    assert edited.section_paragraphs == hwpx_doc.section_paragraphs


@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    index_choice=st.data(),
    new_text=st.text(
        alphabet=st.characters(
            min_codepoint=0x20,
            max_codepoint=0xD7A3,
            blacklist_characters="\x00<>&",
        ),
        min_size=1,
        max_size=80,
    ),
)
def test_replace_only_affects_targeted_paragraph(
    hwpx_doc: HwpDocument,
    hwpx_paragraph_indices: list[tuple[int, int]],
    index_choice: st.DataObject,
    new_text: str,
) -> None:
    section_index, paragraph_index = index_choice.draw(st.sampled_from(hwpx_paragraph_indices))
    original_paragraphs = hwpx_doc.section_paragraphs

    edited = hwpx_doc.replace_paragraph(section_index, paragraph_index, new_text)
    edited_paragraphs = edited.section_paragraphs

    assert edited.sections_count == hwpx_doc.sections_count
    assert len(edited_paragraphs) == len(original_paragraphs)
    assert len(edited_paragraphs[section_index]) == len(original_paragraphs[section_index])
    assert edited_paragraphs[section_index][paragraph_index] == new_text

    for s, paragraphs in enumerate(edited_paragraphs):
        for p, text in enumerate(paragraphs):
            if (s, p) == (section_index, paragraph_index):
                continue
            assert text == original_paragraphs[s][p], f"paragraph ({s},{p}) changed unexpectedly"


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    new_text=st.text(
        alphabet=st.characters(
            min_codepoint=0x20,
            max_codepoint=0xD7A3,
            blacklist_characters="\x00<>&",
        ),
        min_size=1,
        max_size=40,
    ),
)
def test_replace_then_replace_back_recovers_text(
    hwpx_doc: HwpDocument,
    new_text: str,
) -> None:
    section_index, paragraph_index = 0, next(
        i for i, t in enumerate(hwpx_doc.section_paragraphs[0]) if t
    )
    original = hwpx_doc.section_paragraphs[section_index][paragraph_index]
    intermediate = hwpx_doc.replace_paragraph(section_index, paragraph_index, new_text)
    restored = intermediate.replace_paragraph(section_index, paragraph_index, original)
    assert restored.section_paragraphs[section_index][paragraph_index] == original
