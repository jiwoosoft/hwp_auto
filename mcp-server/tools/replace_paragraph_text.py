from __future__ import annotations

import re

from adapters.rhwp_adapter import RHWPAdapter, RHWPAdapterError
from document_store import (
    DOCUMENT_STORE,
    DocumentStoreError,
    OperationRecord,
    ParagraphRecord,
)
from schemas.common import ToolResponseDict, build_tool_response


def replace_paragraph_text_tool(
    document_id: str,
    paragraph_index: int,
    new_text: str,
) -> ToolResponseDict:
    resolved_document_id = document_id.strip()
    if not resolved_document_id:
        return build_tool_response(
            ok=False,
            error_code="MISSING_DOCUMENT_ID",
            message="document_id is required.",
            suggestion="Call open_document first and reuse its document_id.",
        )

    try:
        record = DOCUMENT_STORE.get(resolved_document_id)
    except DocumentStoreError as exc:
        return build_tool_response(
            ok=False,
            error_code="UNKNOWN_DOCUMENT_ID",
            message=str(exc),
            suggestion="Call open_document first.",
        )

    if record["readonly"]:
        return build_tool_response(
            ok=False,
            error_code="READONLY_DOCUMENT",
            message="This document session is readonly.",
            suggestion="Re-open the document with readonly=False before editing.",
        )

    adapter = RHWPAdapter()
    working_text = DOCUMENT_STORE.get_working_text(resolved_document_id)
    if working_text is None:
        try:
            working_text = adapter.extract_text(record["path"]).text
        except RHWPAdapterError as exc:
            return build_tool_response(
                ok=False,
                error_code="DOCUMENT_EXTRACTION_FAILED",
                message=str(exc),
                suggestion="Make sure the source document can be read before editing.",
            )

    paragraphs = _ensure_working_paragraphs(resolved_document_id, record, adapter, working_text)
    if paragraph_index < 0 or paragraph_index >= len(paragraphs):
        return build_tool_response(
            ok=False,
            error_code="INVALID_PARAGRAPH_INDEX",
            message=f"paragraph_index {paragraph_index} is out of range.",
            suggestion="Call extract_document_structure first to inspect paragraph indexes.",
        )

    old_text = paragraphs[paragraph_index]["text"]
    paragraphs[paragraph_index]["text"] = new_text.strip()
    paragraphs[paragraph_index]["text_preview"] = new_text.strip().replace("\n", " ")[:120]
    paragraphs[paragraph_index]["char_count"] = len(new_text.strip())
    _reindex_paragraphs(paragraphs)
    DOCUMENT_STORE.set_working_paragraphs(resolved_document_id, paragraphs)
    updated_text = _paragraphs_to_text(paragraphs)
    _ = DOCUMENT_STORE.set_working_text(resolved_document_id, updated_text)

    if record["format"] in {"hwp", "hwpx"}:
        op: OperationRecord = {
            "type": "replace_paragraph_text",
            "section_index": paragraphs[paragraph_index]["section_index"],
            "para_index": paragraphs[paragraph_index]["section_para_index"],
            "new_text": new_text.strip(),
        }
        _ = DOCUMENT_STORE.append_operation(resolved_document_id, op)

    return build_tool_response(
        ok=True,
        message="paragraph replaced",
        data={
            "document_id": resolved_document_id,
            "paragraph_index": paragraph_index,
            "old_text_preview": old_text[:120],
            "new_text_preview": new_text.strip()[:120],
        },
    )


def _ensure_working_paragraphs(
    document_id: str,
    record: dict[str, object],
    adapter: RHWPAdapter,
    working_text: str,
) -> list[ParagraphRecord]:
    existing = DOCUMENT_STORE.get_working_paragraphs(document_id)
    if existing:
        return existing

    format_name = str(record["format"])
    if format_name in {"hwp", "hwpx"}:
        structure = adapter.extract_structure(str(record["path"]))
        raw_paragraphs = structure.get("paragraphs", [])
        paragraphs = _normalize_paragraph_records(raw_paragraphs)
    else:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", working_text) if block.strip()]
        paragraphs = []
        for index, block in enumerate(blocks):
            paragraphs.append(
                {
                    "paragraph_index": index,
                    "section_index": 0,
                    "section_para_index": index,
                    "text": block,
                    "text_preview": block.replace("\n", " ")[:120],
                    "char_count": len(block),
                }
            )
    DOCUMENT_STORE.set_working_paragraphs(document_id, paragraphs)
    return paragraphs


def _normalize_paragraph_records(raw_paragraphs: object) -> list[ParagraphRecord]:
    normalized: list[ParagraphRecord] = []
    if not isinstance(raw_paragraphs, list):
        return normalized
    section_counters: dict[int, int] = {}
    for index, item in enumerate(raw_paragraphs):
        if not isinstance(item, dict):
            continue
        section_index = int(item.get("section_index", 0)) if isinstance(item.get("section_index", 0), int) else 0
        section_para_index = section_counters.get(section_index, 0)
        section_counters[section_index] = section_para_index + 1
        text = str(item.get("text", ""))
        normalized.append(
            {
                "paragraph_index": index,
                "section_index": section_index,
                "section_para_index": section_para_index,
                "text": text,
                "text_preview": str(item.get("text_preview", text.replace("\n", " ")[:120])),
                "char_count": int(item.get("char_count", len(text))) if isinstance(item.get("char_count", len(text)), int) else len(text),
            }
        )
    return normalized


def _reindex_paragraphs(paragraphs: list[ParagraphRecord]) -> None:
    section_counters: dict[int, int] = {}
    for index, paragraph in enumerate(paragraphs):
        section_index = paragraph["section_index"]
        paragraph["paragraph_index"] = index
        paragraph["section_para_index"] = section_counters.get(section_index, 0)
        section_counters[section_index] = paragraph["section_para_index"] + 1


def _paragraphs_to_text(paragraphs: list[ParagraphRecord]) -> str:
    return "\n\n".join(paragraph["text"].strip() for paragraph in paragraphs if paragraph["text"].strip())
