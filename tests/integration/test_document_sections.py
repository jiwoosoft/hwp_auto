"""Integration scaffold for `HwpDocument.sections_count`.

This test intentionally targets an API that does NOT yet exist on
`HwpDocument`. It locks in the expected contract so that the eventual
integration (once both `hwp5_reader` and `hwpx_reader` spikes land) has
an executable spec to satisfy.

Current state:
    * `hwp5_reader.count_sections` — implemented (spike #001)
    * `hwpx_reader.count_sections` — pending (spike #002)
    * `HwpDocument.sections_count` — pending (integration task #003)

Status: integration task #003 is now complete — `sections_count` is
wired on `HwpDocument` and dispatches on `source_format`.
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


def test_hwp_document_exposes_sections_count(hwp_sample: Path) -> None:
    doc = HwpDocument.open(hwp_sample)
    count = doc.sections_count
    assert isinstance(count, int)
    assert count >= 1


def test_hwpx_document_exposes_sections_count(hwpx_sample: Path) -> None:
    doc = HwpDocument.open(hwpx_sample)
    count = doc.sections_count
    assert isinstance(count, int)
    assert count >= 1
