from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError


def _adapter(workspace: Path) -> RHWPAdapter:
    return RHWPAdapter(allowed_workspace=workspace)


def test_extract_text_from_txt(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("line one\nline two\n", encoding="utf-8")

    result = _adapter(tmp_path).extract_text(str(target))

    assert result.source_format == "txt"
    assert result.text == "line one\nline two"
    assert result.char_count == len("line one\nline two")
    assert result.truncated is False


def test_extract_text_from_md_truncates(tmp_path: Path) -> None:
    target = tmp_path / "big.md"
    target.write_text("a" * 100, encoding="utf-8")

    result = _adapter(tmp_path).extract_text(str(target), max_chars=10)

    assert result.source_format == "md"
    assert result.truncated is True
    assert len(result.text) == 10
    assert result.char_count == 100


def test_resolve_path_rejects_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("nope", encoding="utf-8")

    inside = tmp_path / "inside"
    inside.mkdir()
    adapter = RHWPAdapter(allowed_workspace=inside)

    with pytest.raises(RHWPAdapterError):
        _ = adapter.extract_text(str(outside))


def test_extract_text_unsupported_format_raises(tmp_path: Path) -> None:
    target = tmp_path / "image.png"
    target.write_bytes(b"\x89PNG\r\n")

    with pytest.raises(RHWPAdapterError):
        _ = _adapter(tmp_path).extract_text(str(target))


def test_extract_text_from_hwpx_via_bridge(
    sample_hwpx: Path,
    sample_hwpx_text: str,
) -> None:
    workspace = sample_hwpx.parent
    result = _adapter(workspace).extract_text(str(sample_hwpx))

    assert result.source_format == "hwpx"
    assert sample_hwpx_text in result.text
    assert result.char_count == len(result.text)
    assert (result.section_count or 0) >= 1
    assert (result.paragraph_count or 0) >= 1


def test_extract_structure_from_hwpx_via_bridge(
    sample_hwpx: Path,
    sample_hwpx_text: str,
) -> None:
    workspace = sample_hwpx.parent
    structure = _adapter(workspace).extract_structure(str(sample_hwpx))

    assert structure["source_format"] == "hwpx"
    paragraph_count = cast(int, structure["paragraph_count"])
    assert paragraph_count >= 1
    paragraphs = structure["paragraphs"]
    assert isinstance(paragraphs, list) and paragraphs
    assert any(sample_hwpx_text in str(cast(dict[str, object], p)["text"]) for p in paragraphs)


def test_extract_structure_from_markdown(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text(
        "# Title\n\nFirst paragraph.\n\n## Section\n\n| a | b |\n",
        encoding="utf-8",
    )

    structure = _adapter(tmp_path).extract_structure(str(target))

    assert structure["source_format"] == "md"
    assert int(cast(int, structure["section_count"])) >= 1
    assert int(cast(int, structure["table_count"])) >= 1


def test_extract_structure_reports_real_tables_from_hwpx_sample() -> None:
    sample = Path('/Users/moon/Desktop/master-of-hwp/samples/public-official/table-vpos-01.hwpx')
    structure = _adapter(sample.parent).extract_structure(str(sample))

    assert structure["source_format"] == "hwpx"
    assert int(cast(int, structure["table_count"])) >= 1
    tables = structure["tables"]
    assert isinstance(tables, list) and tables
    first_table = cast(dict[str, object], tables[0])
    assert int(cast(int, first_table["rowCount"])) >= 1
