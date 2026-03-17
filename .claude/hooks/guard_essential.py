#!/usr/bin/env python3
"""
Claude Code Security Hook - Simplified Project Folder Protection

Provides essential security validation for Claude Code file operations to prevent:
- Path traversal attacks outside project boundaries
- Access to protected configuration files
- Dangerous bash command execution

This simplified implementation focuses on core security requirements:
preventing access to files outside the current project directory.

Updated to use shared security_core module to eliminate code duplication.
"""

import json
import os
import sys
from typing import Dict, Any

# Import shared security functions from security_core
from security_core import (
    deny, is_relevant_tool, RELEVANT_TOOLS,
    extract_file_paths_comprehensive,
    is_protected_file, validate_path_comprehensive,
    validate_bash_command_advanced,
    get_project_root_from_config, SecurityConfigError,
    parse_debug_flag, debug_log, init_debug_log,
    is_container_environment
)


# ========================================================================
# MAIN VALIDATION LOGIC
# ========================================================================

def main() -> None:
    """Main hook execution - validate tool operations for security compliance."""
    debug_enabled = parse_debug_flag()

    # Check if running in container - hooks auto-disable in containers
    if is_container_environment():
        debug_log("INFO", "guard_essential",
                 "Security hooks disabled: Running in container environment")
        sys.exit(0)  # Allow all operations in containers

    # Load and validate input
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            deny("Input must be a JSON object")
    except json.JSONDecodeError as e:
        deny(f"Invalid JSON input: {e}")
    except Exception as e:
        deny(f"Failed to load input: {e}")

    # Get project root from security configuration (not CWD)
    try:
        project_root = get_project_root_from_config()
    except SecurityConfigError as e:
        deny(f"Security configuration error: {e}. All operations blocked until security-config.json is properly configured.")

    # Initialize debug logging with session ID and project root
    session_id = data.get('session_id', 'unknown')
    if debug_enabled:
        init_debug_log(session_id, project_root)

    tool_name = data.get('tool_name', 'unknown')
    cwd = data.get('cwd', 'unknown')
    debug_log("DEBUG", "guard_essential", f"Hook started - Tool: {tool_name}, CWD: {cwd}")

    # Check if tool needs validation
    if not is_relevant_tool(tool_name):
        debug_log("DEBUG", "guard_essential", f"Tool '{tool_name}' does not require validation - skipping")
        sys.exit(0)

    debug_log("DEBUG", "guard_essential", f"Project root: {project_root}")

    tool_input = data.get('tool_input', {}) or {}

    violations = []

    # Validate based on tool type
    if tool_name == 'Bash':
        # Special handling for bash commands
        command = tool_input.get('command', '')
        if command:
            valid, reason = validate_bash_command_advanced(command, project_root)
            if not valid:
                debug_log("DEBUG", "guard_essential", f"Bash command blocked: {reason}")
                violations.append(reason)
    else:
        # Handle file-based tools using comprehensive path extraction
        file_paths = extract_file_paths_comprehensive(tool_name, tool_input, project_root)

        debug_log("DEBUG", "guard_essential", f"Extracted {len(file_paths)} file paths for validation")

        for path in file_paths:
            # Check if accessing protected files
            if is_protected_file(path, project_root):
                debug_log("DEBUG", "guard_essential", f"Protected file access blocked: {path}")
                violations.append(f"Access denied: Attempted access to protected security file '{path}' is not allowed.")
                continue

            # Validate path security
            valid, reason = validate_path_comprehensive(path, project_root)
            if not valid:
                debug_log("DEBUG", "guard_essential", f"Path validation failed: {reason}")
                violations.append(reason)

    # Deny if any violations found
    if violations:
        reason = "Security policy violations:\n- " + "\n- ".join(violations)
        deny(reason)

    debug_log("DEBUG", "guard_essential", "Operation allowed")

    # Allow operation
    sys.exit(0)


if __name__ == "__main__":
    main()