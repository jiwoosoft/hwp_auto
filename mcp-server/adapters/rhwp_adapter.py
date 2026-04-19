from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

from config import SETTINGS


class RHWPAdapterError(Exception):
    """Raised when document extraction fails or configuration is invalid."""


class ExtractedText:
    text: str
    char_count: int
    truncated: bool
    source_format: str
    section_count: int | None
    paragraph_count: int | None
    paragraphs: list[dict[str, object]] | None
    tables: list[dict[str, object]] | None

    def __init__(
        self,
        *,
        text: str,
        char_count: int,
        truncated: bool,
        source_format: str,
        section_count: int | None = None,
        paragraph_count: int | None = None,
        paragraphs: list[dict[str, object]] | None = None,
        tables: list[dict[str, object]] | None = None,
    ) -> None:
        self.text = text
        self.char_count = char_count
        self.truncated = truncated
        self.source_format = source_format
        self.section_count = section_count
        self.paragraph_count = paragraph_count
        self.paragraphs = paragraphs
        self.tables = tables


class RHWPAdapter:
    """Thin adapter around local file reads and future rhwp extraction commands."""

    def __init__(self, allowed_workspace: Path | None = None) -> None:
        self.allowed_workspace: Path = allowed_workspace or SETTINGS.allowed_workspace
        self.rhwp_extract_command: str | None = SETTINGS.rhwp_extract_command

    def resolve_path(self, path: str) -> Path:
        candidate = Path(path).expanduser().resolve()
        if not candidate.exists():
            raise RHWPAdapterError(f"File not found: {candidate}")
        if not candidate.is_file():
            raise RHWPAdapterError(f"Not a file: {candidate}")
        try:
            _ = candidate.relative_to(self.allowed_workspace)
        except ValueError as exc:
            raise RHWPAdapterError(
                f"Path is outside the allowed workspace: {candidate}"
            ) from exc
        return candidate

    def extract_text(
        self,
        path: str,
        *,
        include_tables: bool = True,
        max_chars: int | None = None,
    ) -> ExtractedText:
        document_path = self.resolve_path(path)
        suffix = document_path.suffix.lower()
        limit = max_chars or SETTINGS.default_max_chars

        if suffix in {".txt", ".md"}:
            raw_text = document_path.read_text(encoding="utf-8")
            normalized_text = raw_text.strip()
            truncated = len(normalized_text) > limit
            final_text = normalized_text[:limit] if truncated else normalized_text
            return ExtractedText(
                text=final_text,
                char_count=len(normalized_text),
                truncated=truncated,
                source_format=suffix.lstrip("."),
            )

        if suffix in {".hwp", ".hwpx"}:
            payload = self._extract_with_rhwp(
                document_path,
                include_tables=include_tables,
                max_chars=limit,
            )
            return ExtractedText(
                text=str(payload.get("text", "")),
                char_count=self._to_int(payload.get("char_count"), 0),
                truncated=bool(payload.get("truncated", False)),
                source_format=str(payload.get("source_format", suffix.lstrip("."))),
                section_count=self._optional_int(payload.get("section_count")),
                paragraph_count=self._optional_int(payload.get("paragraph_count")),
                paragraphs=self._optional_paragraphs(payload.get("paragraphs")),
                tables=self._optional_tables(payload.get("tables")),
            )

        raise RHWPAdapterError(
            f"Unsupported format: {document_path.suffix or 'unknown'}"
        )

    def extract_structure(
        self,
        path: str,
        *,
        include_tables: bool = True,
        max_chars: int | None = None,
    ) -> dict[str, object]:
        extracted = self.extract_text(
            path,
            include_tables=include_tables,
            max_chars=max_chars,
        )
        return self.structure_from_extracted(
            extracted=extracted,
            path=path,
            max_chars=max_chars or SETTINGS.default_max_chars,
        )

    def structure_from_text(
        self,
        *,
        text: str,
        source_format: str,
        path: str,
        max_chars: int,
        truncated: bool = False,
    ) -> dict[str, object]:
        normalized_text = text.strip()
        effective_truncated = truncated or len(normalized_text) > max_chars
        final_text = normalized_text[:max_chars] if effective_truncated else normalized_text
        extracted = ExtractedText(
            text=final_text,
            char_count=len(normalized_text),
            truncated=effective_truncated,
            source_format=source_format,
        )
        return self.structure_from_extracted(
            extracted=extracted,
            path=path,
            max_chars=max_chars,
        )

    def structure_from_extracted(
        self,
        *,
        extracted: ExtractedText,
        path: str,
        max_chars: int,
    ) -> dict[str, object]:
        if extracted.paragraphs:
            paragraphs = self._normalize_bridge_paragraphs(extracted.paragraphs)
            sections = self._sections_from_bridge_paragraphs(paragraphs)
        else:
            normalized_text = extracted.text.strip()
            effective_truncated = extracted.truncated or len(normalized_text) > max_chars
            final_text = normalized_text[:max_chars] if effective_truncated else normalized_text
            paragraphs = self._split_paragraphs(final_text)
            sections = self._infer_sections(paragraphs, extracted.source_format)

        tables = extracted.tables or self._detect_tables(extracted.text, extracted.source_format)
        return {
            "paragraph_count": extracted.paragraph_count or len(paragraphs),
            "section_count": extracted.section_count or len(sections),
            "table_count": len(tables),
            "sections": sections,
            "paragraphs": paragraphs,
            "tables": tables,
            "source_format": extracted.source_format,
            "truncated": extracted.truncated,
            "path": path,
        }

    def write_text_file(self, output_path: str, text: str) -> Path:
        target_path = Path(output_path).expanduser().resolve()
        parent = target_path.parent
        if not parent.exists():
            raise RHWPAdapterError(f"Parent directory does not exist: {parent}")
        try:
            _ = target_path.relative_to(self.allowed_workspace)
        except ValueError as exc:
            raise RHWPAdapterError(
                f"Output path is outside the allowed workspace: {target_path}"
            ) from exc
        target_path.write_text(text, encoding="utf-8")
        return target_path

    def write_hwp_like_file(self, output_path: str, text: str) -> dict[str, object]:
        target_path = Path(output_path).expanduser().resolve()
        parent = target_path.parent
        if not parent.exists():
            raise RHWPAdapterError(f"Parent directory does not exist: {parent}")
        try:
            _ = target_path.relative_to(self.allowed_workspace)
        except ValueError as exc:
            raise RHWPAdapterError(
                f"Output path is outside the allowed workspace: {target_path}"
            ) from exc

        bridge_path = SETTINGS.project_root / "mcp-server" / "bridges" / "rhwp_save.mjs"
        if not bridge_path.exists():
            raise RHWPAdapterError("rhwp save bridge is not available")

        with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tmp:
            tmp.write(text)
            tmp_input = Path(tmp.name)

        command = f'node "{bridge_path}" "{tmp_input}" "{target_path}"'
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=False,
        )
        tmp_input.unlink(missing_ok=True)

        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr provided"
            raise RHWPAdapterError(f"rhwp save failed: {stderr}")

        payload = self._parse_json_payload(result.stdout, "rhwp save")
        return payload

    def write_hwp_roundtrip_file(
        self,
        *,
        source_path: str,
        output_path: str,
        operations_path: str,
    ) -> dict[str, object]:
        source = self.resolve_path(source_path)
        target_path = Path(output_path).expanduser().resolve()
        parent = target_path.parent
        if not parent.exists():
            raise RHWPAdapterError(f"Parent directory does not exist: {parent}")
        try:
            _ = target_path.relative_to(self.allowed_workspace)
        except ValueError as exc:
            raise RHWPAdapterError(
                f"Output path is outside the allowed workspace: {target_path}"
            ) from exc

        bridge_path = SETTINGS.project_root / "mcp-server" / "bridges" / "rhwp_save.mjs"
        if not bridge_path.exists():
            raise RHWPAdapterError("rhwp save bridge is not available")

        command = (
            f'node "{bridge_path}" "{source}" "{target_path}" '
            f'--ops-json="{Path(operations_path).expanduser().resolve()}"'
        )
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr provided"
            raise RHWPAdapterError(f"rhwp roundtrip save failed: {stderr}")

        payload = self._parse_json_payload(result.stdout, "rhwp roundtrip save")
        return payload

    def _split_paragraphs(self, text: str) -> list[dict[str, object]]:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        paragraphs: list[dict[str, object]] = []
        for index, block in enumerate(blocks):
            preview = block.replace("\n", " ")[:120]
            paragraphs.append(
                {
                    "paragraph_index": index,
                    "text": block,
                    "text_preview": preview,
                    "char_count": len(block),
                }
            )
        return paragraphs

    def _normalize_bridge_paragraphs(
        self, paragraphs: list[dict[str, object]]
    ) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for index, paragraph in enumerate(paragraphs):
            text = str(paragraph.get("text", "")).strip()
            preview = text.replace("\n", " ")[:120]
            normalized.append(
                {
                    "paragraph_index": index,
                    "section_index": self._optional_int(paragraph.get("section")) or 0,
                    "source_paragraph_index": self._optional_int(paragraph.get("paragraph")) or index,
                    "text": text,
                    "text_preview": preview,
                    "char_count": len(text),
                }
            )
        return normalized

    def _sections_from_bridge_paragraphs(
        self, paragraphs: list[dict[str, object]]
    ) -> list[dict[str, object]]:
        by_section: dict[int, dict[str, object]] = {}
        for paragraph in paragraphs:
            section_index = self._to_int(paragraph.get("section_index"), 0)
            if section_index in by_section:
                continue
            raw_text = str(paragraph.get("text", "")).strip()
            title = raw_text.splitlines()[0].strip() if raw_text else f"Section {section_index}"
            by_section[section_index] = {
                "section_index": section_index,
                "title": title,
                "paragraph_index": self._to_int(paragraph.get("paragraph_index"), 0),
            }
        return [by_section[key] for key in sorted(by_section)]

    def _infer_sections(
        self,
        paragraphs: list[dict[str, object]],
        source_format: str,
    ) -> list[dict[str, object]]:
        sections: list[dict[str, object]] = []
        for paragraph in paragraphs:
            paragraph_text = str(paragraph["text"])
            if self._looks_like_heading(paragraph_text, source_format):
                sections.append(
                    {
                        "section_index": len(sections),
                        "title": paragraph_text.splitlines()[0].strip(),
                        "paragraph_index": paragraph["paragraph_index"],
                    }
                )
        if not sections and paragraphs:
            first_paragraph = paragraphs[0]
            sections.append(
                {
                    "section_index": 0,
                    "title": str(first_paragraph["text"]).splitlines()[0].strip(),
                    "paragraph_index": first_paragraph["paragraph_index"],
                }
            )
        return sections

    def _looks_like_heading(self, paragraph_text: str, source_format: str) -> bool:
        first_line = paragraph_text.splitlines()[0].strip()
        if not first_line:
            return False
        if source_format == "md" and first_line.startswith("#"):
            return True
        if re.match(r"^\d+[\.)]\s+", first_line):
            return True
        if len(paragraph_text.splitlines()) == 1 and len(first_line) <= 60:
            if not first_line.endswith((".", "다", ":")):
                return True
        return False

    def _detect_tables(self, text: str, source_format: str) -> list[dict[str, object]]:
        tables: list[dict[str, object]] = []
        if source_format != "md":
            return tables

        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.count("|") >= 2:
                tables.append(
                    {
                        "table_id": f"table_{len(tables) + 1:03d}",
                        "line_index": index,
                        "preview": line.strip()[:120],
                    }
                )
        return tables

    def _extract_with_rhwp(
        self,
        path: Path,
        *,
        include_tables: bool,
        max_chars: int,
    ) -> dict[str, object]:
        if not self.rhwp_extract_command:
            raise RHWPAdapterError(
                "RHWP_EXTRACT_COMMAND is not configured. Set a local extraction command before reading .hwp or .hwpx files."
            )

        command = self.rhwp_extract_command.format(
            input=str(path),
            include_tables=str(include_tables).lower(),
            max_chars=max_chars,
        )
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or "no stderr provided"
            raise RHWPAdapterError(f"rhwp extraction failed: {stderr}")

        payload = self._parse_json_payload(result.stdout, "rhwp extraction")
        if "text" not in payload:
            raise RHWPAdapterError("rhwp extraction JSON did not include text")
        return payload

    def _parse_json_payload(self, raw: str, label: str) -> dict[str, object]:
        stdout = raw.strip()
        if not stdout:
            raise RHWPAdapterError(f"{label} returned empty output")

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RHWPAdapterError(f"{label} returned invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise RHWPAdapterError(f"{label} returned a non-object JSON payload")
        if not payload.get("ok", True):
            raise RHWPAdapterError(str(payload.get("message", f"{label} failed")))
        return payload

    def _optional_int(self, value: object) -> int | None:
        if isinstance(value, int):
            return value
        return None

    def _to_int(self, value: object, default: int) -> int:
        if isinstance(value, int):
            return value
        return default

    def _optional_paragraphs(
        self, value: object
    ) -> list[dict[str, object]] | None:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return None

    def _optional_tables(self, value: object) -> list[dict[str, object]] | None:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return None
