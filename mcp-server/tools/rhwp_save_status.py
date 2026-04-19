from __future__ import annotations

import shlex
import shutil
from string import Formatter

from config import SETTINGS
from schemas.common import ToolResponseDict, build_tool_response


REQUIRED_PLACEHOLDERS = {"input", "output"}
NOT_IMPLEMENTED_MARKER = "BRIDGE_SAVE_NOT_IMPLEMENTED"


def rhwp_save_status_tool() -> ToolResponseDict:
    bridge_path = SETTINGS.project_root / "mcp-server" / "bridges" / "rhwp_save.mjs"
    node_path = shutil.which("node") or ""
    bridge_exists = bridge_path.exists()
    bridge_text = bridge_path.read_text(encoding="utf-8") if bridge_exists else ""
    implemented = bridge_exists and NOT_IMPLEMENTED_MARKER not in bridge_text

    command_template = (
        f'"{node_path}" "{bridge_path}" "{{input}}" "{{output}}"'
        if node_path and bridge_exists
        else ""
    )

    placeholder_names = {
        field_name
        for _, field_name, _, _ in Formatter().parse(command_template)
        if field_name
    }
    missing_placeholders = sorted(REQUIRED_PLACEHOLDERS - placeholder_names)

    ready = bool(command_template) and not missing_placeholders and implemented
    message = "rhwp save bridge is ready" if ready else "rhwp save bridge is not ready"
    suggestion = None
    if not bridge_exists:
        suggestion = "Create and implement mcp-server/bridges/rhwp_save.mjs with real rhwp-backed save logic."
    elif not implemented:
        suggestion = "Replace the placeholder implementation in mcp-server/bridges/rhwp_save.mjs with a real serializer-backed save path."

    return build_tool_response(
        ok=True,
        message=message,
        data={
            "ready": ready,
            "bridge_exists": bridge_exists,
            "implemented": implemented,
            "bridge_path": str(bridge_path),
            "node": node_path,
            "command_preview": shlex.split(command_template) if command_template else [],
            "missing_placeholders": missing_placeholders,
        },
        suggestion=suggestion,
    )
