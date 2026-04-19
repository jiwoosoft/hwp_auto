from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from document_store import DOCUMENT_STORE
from schemas.common import ToolResponseDict
from tools.extract_document_structure import extract_document_structure_tool
from tools.extract_document_text import extract_document_text_tool
from tools.insert_paragraph_after import insert_paragraph_after_tool
from tools.open_document import open_document_tool
from tools.replace_paragraph_text import replace_paragraph_text_tool
from tools.rhwp_integration_status import rhwp_integration_status_tool
from tools.rhwp_save_status import rhwp_save_status_tool
from tools.save_as import save_as_tool
from tools.validate_document import validate_document_tool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = PROJECT_ROOT / "samples" / "public-official"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SAMPLE_HWP = SAMPLES_DIR / "re-mixed-0tr.hwp"
SAMPLE_HWPX = SAMPLES_DIR / "table-vpos-01.hwpx"


def _data(result: ToolResponseDict) -> dict[str, object]:
    assert result.get("ok") is True
    data = result.get("data")
    assert isinstance(data, dict)
    return data


@pytest.fixture(autouse=True)
def reset_document_store() -> None:
    store = cast(Any, DOCUMENT_STORE)
    store.reset()


def test_rhwp_integration_status_reports_ready() -> None:
    result = rhwp_integration_status_tool()
    data = _data(result)

    assert data["ready"] is True
    assert data["command_preview"]


def test_rhwp_save_status_reports_ready() -> None:
    result = rhwp_save_status_tool()
    data = _data(result)

    assert data["ready"] is True
    assert data["implemented"] is True


@pytest.mark.integration
def test_open_document_and_extract_text_for_real_hwp() -> None:
    opened = open_document_tool(str(SAMPLE_HWP), readonly=False)
    opened_data = _data(opened)

    doc_id = str(opened_data["document_id"])
    extracted = extract_document_text_tool(document_id=doc_id)
    extracted_data = _data(extracted)

    assert extracted_data["source_format"] == "hwp"
    char_count = cast(int, extracted_data["char_count"])
    assert char_count > 0


@pytest.mark.integration
def test_extract_structure_for_real_hwpx() -> None:
    structure = extract_document_structure_tool(path=str(SAMPLE_HWPX))
    data = _data(structure)

    assert data["source_format"] == "hwpx"
    paragraph_count = cast(int, data["paragraph_count"])
    assert paragraph_count >= 1
    paragraphs = data["paragraphs"]
    assert isinstance(paragraphs, list)
    assert paragraphs
    table_count = cast(int, data["table_count"])
    assert table_count >= 1


@pytest.mark.integration
def test_roundtrip_save_preserves_replayed_edits_for_hwpx() -> None:
    opened = open_document_tool(str(SAMPLE_HWPX), readonly=False)
    doc_id = str(_data(opened)["document_id"])

    replace_result = replace_paragraph_text_tool(
        doc_id,
        5,
        "□ pytest 기반 저장 검증 문단입니다.",
    )
    _ = _data(replace_result)

    insert_result = insert_paragraph_after_tool(
        doc_id,
        5,
        "○ pytest가 roundtrip 저장을 검증했습니다.",
    )
    _ = _data(insert_result)

    output_path = OUTPUTS_DIR / "pytest_roundtrip_save.hwpx"
    save_result = save_as_tool(doc_id, str(output_path))
    save_data = _data(save_result)
    assert save_data["mode"] == "roundtrip-operation-replay"

    validate_result = validate_document_tool(str(output_path))
    _ = _data(validate_result)

    extracted = extract_document_text_tool(path=str(output_path))
    extracted_data = _data(extracted)
    extracted_text = str(extracted_data["text"])
    assert "pytest 기반 저장 검증 문단입니다." in extracted_text
    assert "pytest가 roundtrip 저장을 검증했습니다." in extracted_text


@pytest.mark.integration
def test_roundtrip_save_preserves_replayed_edits_for_hwp() -> None:
    opened = open_document_tool(str(SAMPLE_HWP), readonly=False)
    doc_id = str(_data(opened)["document_id"])

    replace_result = replace_paragraph_text_tool(
        doc_id,
        0,
        "가나다라마바사\n\npytest HWP 저장 검증",
    )
    _ = _data(replace_result)

    insert_result = insert_paragraph_after_tool(
        doc_id,
        0,
        "추가 저장 검증 문단",
    )
    _ = _data(insert_result)

    output_path = OUTPUTS_DIR / "pytest_roundtrip_save.hwp"
    save_result = save_as_tool(doc_id, str(output_path))
    save_data = _data(save_result)
    assert save_data["mode"] == "roundtrip-operation-replay"

    validate_result = validate_document_tool(str(output_path))
    _ = _data(validate_result)

    extracted = extract_document_text_tool(path=str(output_path))
    extracted_data = _data(extracted)
    extracted_text = str(extracted_data["text"])
    assert "pytest HWP 저장 검증" in extracted_text
    assert "추가 저장 검증 문단" in extracted_text
