"""Minimal HWPX reader utilities backed by ZIP container inspection."""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from xml.etree import ElementTree

_SECTION_PART_PATTERN = re.compile(r"Contents/section\d+\.xml", re.IGNORECASE)
_SECTION_HREF_PATTERN = re.compile(r"(?:^|.*/)section\d+\.xml$", re.IGNORECASE)


class HwpxFormatError(ValueError):
    """Raised when raw bytes are not a readable HWPX/ZIP document."""


def count_sections(raw_bytes: bytes) -> int:
    """Return the number of section XML parts in a HWPX file.

    Args:
        raw_bytes: The exact bytes of a `.hwpx` ZIP container.

    Returns:
        The number of section XML parts declared by the archive.

    Raises:
        ValueError: If `raw_bytes` is empty.
        HwpxFormatError: If the payload is not a readable HWPX container or
            does not expose any section parts.
    """
    if not raw_bytes:
        raise ValueError("HWPX raw_bytes must not be empty.")

    try:
        with zipfile.ZipFile(BytesIO(raw_bytes)) as archive:
            section_count = _count_section_parts(archive.namelist())
            if section_count >= 1:
                return section_count
            manifest_bytes = _read_manifest_bytes(archive)
    except zipfile.BadZipFile as exc:
        raise HwpxFormatError(f"Not a valid HWPX (ZIP) container: {exc}") from exc
    except OSError as exc:
        raise HwpxFormatError(f"Failed to read HWPX container: {exc}") from exc

    section_count = _count_manifest_sections(manifest_bytes)
    if section_count < 1:
        raise HwpxFormatError("HWPX container has no Contents/sectionN.xml entries.")
    return section_count


def _count_section_parts(names: list[str]) -> int:
    return sum(1 for name in names if _SECTION_PART_PATTERN.fullmatch(name) is not None)


def _read_manifest_bytes(archive: zipfile.ZipFile) -> bytes:
    try:
        return archive.read("Contents/content.hpf")
    except KeyError as exc:
        raise HwpxFormatError(
            "HWPX container has no Contents/sectionN.xml entries or content.hpf " "manifest."
        ) from exc


def _count_manifest_sections(manifest_bytes: bytes) -> int:
    try:
        root = ElementTree.fromstring(manifest_bytes)
    except ElementTree.ParseError as exc:
        raise HwpxFormatError(f"Invalid HWPX content.hpf manifest: {exc}") from exc

    id_to_href = {
        element.attrib["id"]: element.attrib["href"]
        for element in root.iter()
        if _local_name(element.tag) == "item"
        and "id" in element.attrib
        and "href" in element.attrib
        and _SECTION_HREF_PATTERN.fullmatch(element.attrib["href"]) is not None
    }
    spine_count = sum(
        1
        for element in root.iter()
        if _local_name(element.tag) == "itemref" and element.attrib.get("idref") in id_to_href
    )
    if spine_count >= 1:
        return spine_count
    return len(id_to_href)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]
