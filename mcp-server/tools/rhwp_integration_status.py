from __future__ import annotations

import shlex
import shutil
from string import Formatter

from config import SETTINGS
from schemas.common import ToolResponseDict, build_tool_response


REQUIRED_PLACEHOLDERS = {"input", "include_tables"}


def rhwp_integration_status_tool() -> ToolResponseDict:
    command_template = SETTINGS.rhwp_extract_command or ""
    available_commands = {
        "rhwp": shutil.which("rhwp") or "",
        "rhwp-studio": shutil.which("rhwp-studio") or "",
    }

    placeholder_names = {
        field_name
        for _, field_name, _, _ in Formatter().parse(command_template)
        if field_name
    }
    missing_placeholders = sorted(REQUIRED_PLACEHOLDERS - placeholder_names)
    command_preview = shlex.split(command_template) if command_template else []

    configured = bool(command_template)
    ready = configured and not missing_placeholders

    message = "rhwp integration is ready" if ready else "rhwp integration is not ready"
    suggestion = None
    if not configured:
        suggestion = (
            "Set RHWP_EXTRACT_COMMAND to a local extraction command, for example a python wrapper or rhwp CLI invocation using {input} and {include_tables}."
        )
    elif missing_placeholders:
        suggestion = (
            "Update RHWP_EXTRACT_COMMAND so it includes the placeholders: {input} and {include_tables}."
        )

    return build_tool_response(
        ok=True,
        message=message,
        data={
            "ready": ready,
            "configured": configured,
            "rhwp_extract_command": command_template,
            "command_preview": command_preview,
            "available_commands": available_commands,
            "missing_placeholders": missing_placeholders,
            "allowed_workspace": str(SETTINGS.allowed_workspace),
        },
        suggestion=suggestion,
    )
