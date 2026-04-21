"""Concrete edit operations that the AI agent can request.

Each `*Operation` dataclass describes an atomic, reversible change.
The agent's plan step produces a list of these; the execute step
dispatches them against `HwpDocument`, producing a new document.

In v0.1 only `ReplaceOperation` has a live backing implementation
(via `HwpDocument.replace_paragraph`). `InsertOperation` and
`DeleteOperation` are scaffolds for v0.2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from master_of_hwp.ai.locator import ParagraphLocator
from master_of_hwp.core.document import HwpDocument


@runtime_checkable
class EditOperation(Protocol):
    """Marker protocol for edit operations.

    Implementations must be immutable dataclasses and must implement
    `apply(doc)` returning a new `HwpDocument`.
    """

    def apply(self, doc: HwpDocument) -> HwpDocument: ...


@dataclass(frozen=True)
class ReplaceOperation:
    """Replace the text of a targeted paragraph.

    Attributes:
        locator: Target pointer (must have `scope == PARAGRAPH`).
        new_text: Replacement text.
    """

    locator: ParagraphLocator
    new_text: str

    def apply(self, doc: HwpDocument) -> HwpDocument:
        """Dispatch to `HwpDocument.replace_paragraph`.

        Raises:
            ValueError: If `locator.paragraph_index` is `None`.
        """
        if self.locator.paragraph_index is None:
            raise ValueError("ReplaceOperation requires a paragraph-scoped locator")
        return doc.replace_paragraph(
            self.locator.section_index,
            self.locator.paragraph_index,
            self.new_text,
        )


@dataclass(frozen=True)
class InsertOperation:
    """Insert a new paragraph at the targeted position.

    Attributes:
        locator: Target pointer; the new paragraph is inserted *before*
            the pointed paragraph.
        text: The paragraph text to insert.
    """

    locator: ParagraphLocator
    text: str

    def apply(self, doc: HwpDocument) -> HwpDocument:
        """Raises `NotImplementedError` until v0.2 ships insert writer."""
        del doc
        raise NotImplementedError("InsertOperation pending v0.2 write path")


@dataclass(frozen=True)
class DeleteOperation:
    """Delete the targeted paragraph.

    Attributes:
        locator: Target pointer (paragraph-scoped).
    """

    locator: ParagraphLocator

    def apply(self, doc: HwpDocument) -> HwpDocument:
        """Raises `NotImplementedError` until v0.2 ships delete writer."""
        del doc
        raise NotImplementedError("DeleteOperation pending v0.2 write path")
