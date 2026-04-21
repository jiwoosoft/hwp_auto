"""Resolve an `EditIntent` to concrete document coordinates.

Given a parsed intent (which only knows *what* the user said) and a
document, the locator decides *where* in the document the edit should
apply. Phase 2 will replace the stub with a content-aware targeter
that combines `HwpDocument.find_paragraphs` with LLM re-ranking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from master_of_hwp.ai.intent import EditIntent
from master_of_hwp.core.document import HwpDocument


class LocatorScope(StrEnum):
    """Where in the document a located target lives."""

    PARAGRAPH = "paragraph"
    TABLE_CELL = "table_cell"
    SECTION = "section"


@dataclass(frozen=True)
class ParagraphLocator:
    """Structured pointer to a paragraph or cell inside a document.

    Attributes:
        scope: Whether the target is a paragraph, a table cell, or an
            entire section.
        section_index: Zero-based section index.
        paragraph_index: Zero-based paragraph index within the section;
            `None` when `scope` is `SECTION`.
        table_index: Zero-based table index, when `scope` is `TABLE_CELL`.
        row_index: Zero-based row index, when `scope` is `TABLE_CELL`.
        cell_index: Zero-based cell index, when `scope` is `TABLE_CELL`.
        confidence: Locator's confidence that this is the intended
            target (0.0–1.0). Callers should refuse to execute below a
            configured threshold.
    """

    scope: LocatorScope
    section_index: int
    paragraph_index: int | None = None
    table_index: int | None = None
    row_index: int | None = None
    cell_index: int | None = None
    confidence: float = 0.0


def locate_targets(intent: EditIntent, doc: HwpDocument) -> list[ParagraphLocator]:
    """Resolve an `EditIntent` into candidate target locations.

    Phase 2 scaffold: not implemented. The v0.3 implementation will
    combine substring / regex matching (already available via
    `HwpDocument.find_paragraphs`) with LLM re-ranking to choose the
    most likely target(s).

    Args:
        intent: A parsed `EditIntent`.
        doc: The document to locate targets within.

    Returns:
        A list of `ParagraphLocator` candidates sorted by confidence
        (highest first). An empty list indicates no match above the
        implementation-defined confidence floor.

    Raises:
        NotImplementedError: Always, until v0.3 ships.
    """
    del intent, doc
    raise NotImplementedError("AI target location pending v0.3")
