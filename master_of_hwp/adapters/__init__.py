"""Adapters bridge Core API to external engines and consumers.

    * hwp5_reader — HWP 5.0 compound-file introspection (via olefile)
    * hwpx_reader — HWPX (OOXML/ZIP) introspection (stdlib zipfile + ElementTree)
    * rhwp_bridge — invokes the Rust-based rhwp engine for parsing/saving
    * mcp_adapter — exposes Core API as an MCP server surface

Keeping these thin isolates Core from engine churn.

Both readers expose a same-named `count_sections(bytes) -> int`; to avoid a
name clash when both are re-exported here, we surface the format-discriminated
aliases `hwp5_count_sections` and `hwpx_count_sections`.
"""

from master_of_hwp.adapters.hwp5_reader import Hwp5FormatError
from master_of_hwp.adapters.hwp5_reader import count_sections as hwp5_count_sections
from master_of_hwp.adapters.hwpx_reader import HwpxFormatError
from master_of_hwp.adapters.hwpx_reader import count_sections as hwpx_count_sections

__all__ = [
    "Hwp5FormatError",
    "HwpxFormatError",
    "hwp5_count_sections",
    "hwpx_count_sections",
]
