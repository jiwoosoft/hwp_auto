"""Unit tests for the minimal HWPX ZIP reader."""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from master_of_hwp.adapters.hwpx_reader import HwpxFormatError, count_sections


@pytest.mark.unit
def test_empty_bytes_raise_value_error() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        count_sections(b"")


@pytest.mark.unit
def test_non_zip_raises_hwpx_format_error() -> None:
    with pytest.raises(HwpxFormatError, match="ZIP"):
        count_sections(b"NOT-A-ZIP-FILE" * 100)


@pytest.mark.unit
def test_manifest_fallback_counts_section_refs() -> None:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "Contents/content.hpf",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/">'
                "<opf:manifest>"
                '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
                '<opf:item id="section1" href="Contents/section1.xml" media-type="application/xml"/>'
                "</opf:manifest>"
                "<opf:spine>"
                '<opf:itemref idref="section0" linear="yes"/>'
                '<opf:itemref idref="section1" linear="yes"/>'
                "</opf:spine>"
                "</opf:package>"
            ),
        )

    assert count_sections(buffer.getvalue()) == 2


@pytest.mark.unit
def test_real_sample_returns_positive_section_count(samples_dir: Path) -> None:
    sample = samples_dir / "public-official" / "table-vpos-01.hwpx"
    if not sample.exists():
        pytest.skip("sample missing")

    section_count = count_sections(sample.read_bytes())

    assert section_count >= 1
