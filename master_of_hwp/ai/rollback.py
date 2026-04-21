"""Rollback context manager for multi-step AI edits.

When an agent plans several operations, each can succeed or fail
independently. `RollbackTransaction` captures the document state
before the first operation so a single failed step can restore the
entire pre-edit state without partial writes leaking through.

Phase 2 scaffold: in v0.1 the transaction only records pre-edit bytes
and exposes a `rollback()` method; automatic retries / re-planning
land in v0.3.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from master_of_hwp.core.document import HwpDocument


class RollbackTransaction:
    """Context manager that preserves a document's pre-edit state.

    Usage:
        >>> with RollbackTransaction(doc) as tx:
        ...     doc = tx.apply(some_operation)
        ...     doc = tx.apply(another_operation)
        ... # On exception, tx.current is reverted to the snapshot.

    Attributes:
        snapshot: The `HwpDocument` as captured at transaction start.
        current: The document produced by the most recent `apply()`.
            Starts equal to `snapshot`.
    """

    def __init__(self, doc: HwpDocument) -> None:
        self.snapshot: HwpDocument = doc
        self.current: HwpDocument = doc

    def apply(self, operation: object) -> HwpDocument:
        """Apply an operation and update `current`.

        Args:
            operation: An object exposing `apply(doc) -> HwpDocument`
                (duck-typed to avoid a hard dependency on the protocol
                at this scaffold stage).

        Returns:
            The new document after applying the operation.

        Raises:
            NotImplementedError: Auto-rollback-on-exception is not yet
                wired in v0.1.
        """
        del operation
        raise NotImplementedError("Transactional apply pending v0.3")

    def rollback(self) -> HwpDocument:
        """Return the original snapshot, discarding any in-flight edits."""
        self.current = self.snapshot
        return self.snapshot

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.rollback()
