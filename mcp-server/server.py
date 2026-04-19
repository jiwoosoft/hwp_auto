from __future__ import annotations

from importlib import import_module
from typing import Any

from tools.extract_document_structure import extract_document_structure_tool
from tools.extract_document_text import extract_document_text_tool
from tools.insert_paragraph_after import insert_paragraph_after_tool
from tools.open_document import open_document_tool
from tools.replace_paragraph_text import replace_paragraph_text_tool
from tools.rhwp_integration_status import rhwp_integration_status_tool
from tools.rhwp_save_status import rhwp_save_status_tool
from tools.save_as import save_as_tool
from tools.validate_document import validate_document_tool


def _load_fastmcp_class() -> Any:
    module = import_module("fastmcp")
    return getattr(module, "FastMCP")


FastMCP: Any = _load_fastmcp_class()
mcp: Any = FastMCP("master-of-hwp")


@mcp.tool()
def health_check() -> dict[str, object]:
    """Return a simple server status payload."""
    return {
        "ok": True,
        "message": "master-of-hwp MCP server is ready",
        "data": {
            "phase": "phase-1-reading-and-text-editing-poc",
            "implemented_tools": [
                "health_check",
                "rhwp_integration_status",
                "rhwp_save_status",
                "open_document",
                "extract_document_text",
                "extract_document_structure",
                "replace_paragraph_text",
                "insert_paragraph_after",
                "save_as",
                "validate_document",
            ],
            "positioning": "general-purpose CLI wrapper core",
        },
    }


@mcp.tool()
def rhwp_integration_status() -> dict[str, object]:
    """Report whether real local rhwp extraction is wired into the current environment."""
    return dict(rhwp_integration_status_tool())


@mcp.tool()
def rhwp_save_status() -> dict[str, object]:
    """Report whether a real HWP/HWPX save bridge is implemented and ready."""
    return dict(rhwp_save_status_tool())


@mcp.tool()
def open_document(path: str, readonly: bool = True) -> dict[str, object]:
    """Open a local document and return a reusable document_id."""
    return dict(open_document_tool(path=path, readonly=readonly))


@mcp.tool()
def extract_document_text(
    path: str = "",
    document_id: str = "",
    include_tables: bool = True,
    max_chars: int = 50_000,
) -> dict[str, object]:
    return dict(
        extract_document_text_tool(
            path=path,
            document_id=document_id,
            include_tables=include_tables,
            max_chars=max_chars,
        )
    )


@mcp.tool()
def extract_document_structure(
    path: str = "",
    document_id: str = "",
    include_tables: bool = True,
    max_chars: int = 50_000,
) -> dict[str, object]:
    return dict(
        extract_document_structure_tool(
            path=path,
            document_id=document_id,
            include_tables=include_tables,
            max_chars=max_chars,
        )
    )


@mcp.tool()
def replace_paragraph_text(
    document_id: str,
    paragraph_index: int,
    new_text: str,
) -> dict[str, object]:
    return dict(
        replace_paragraph_text_tool(
            document_id=document_id,
            paragraph_index=paragraph_index,
            new_text=new_text,
        )
    )


@mcp.tool()
def insert_paragraph_after(
    document_id: str,
    after_paragraph_index: int,
    text: str,
) -> dict[str, object]:
    return dict(
        insert_paragraph_after_tool(
            document_id=document_id,
            after_paragraph_index=after_paragraph_index,
            text=text,
        )
    )


@mcp.tool()
def save_as(document_id: str, output_path: str) -> dict[str, object]:
    return dict(save_as_tool(document_id=document_id, output_path=output_path))


@mcp.tool()
def validate_document(path: str) -> dict[str, object]:
    return dict(validate_document_tool(path=path))


if __name__ == "__main__":
    mcp.run()
