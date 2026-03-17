#!/usr/bin/env python3
"""
Shared security validation functions for Claude Code Security Hooks.
Provides centralized security analysis to prevent code duplication.
"""

import json
import sys
import re
import shlex
import os
from typing import List, Tuple, Set, Dict, Any

# ========================================================================
# DEBUG UTILITIES
# ========================================================================

# Global debug state (initialized once at module import)
_DEBUG_ENABLED = None
_LOG_FILE_PATH = None
_LOG_FILE_HANDLE = None

def parse_debug_flag() -> bool:
    """
    Parse debug flag from CLI arguments or environment variable.

    Priority: CLI flag > Environment variable > False (default)

    Returns:
        bool: True if debug mode is enabled, False otherwise
    """
    global _DEBUG_ENABLED

    # Return cached value if already parsed
    if _DEBUG_ENABLED is not None:
        return _DEBUG_ENABLED

    # Check CLI argument (highest priority)
    if '--debug' in sys.argv:
        _DEBUG_ENABLED = True
        return True

    # Check environment variable
    env_debug = os.environ.get('CLAUDE_HOOKS_DEBUG', '').strip()
    if env_debug in ('1', 'true', 'True', 'TRUE', 'yes', 'Yes', 'YES'):
        _DEBUG_ENABLED = True
        return True

    # Default: debug disabled
    _DEBUG_ENABLED = False
    return False


def init_debug_log(session_id: str, project_root: str) -> None:
    """
    Initialize debug log file for the current session.

    Args:
        session_id: Unique session identifier from Claude Code
        project_root: Absolute path to the project root directory
    """
    global _LOG_FILE_PATH, _LOG_FILE_HANDLE

    # Only initialize once per session
    if _LOG_FILE_PATH is not None:
        return

    try:
        # Create log directory if it doesn't exist
        log_dir = os.path.join(project_root, '.claude', 'tmp')
        os.makedirs(log_dir, exist_ok=True)

        # Create log file path with session ID
        _LOG_FILE_PATH = os.path.join(log_dir, f'log-{session_id}')

        # Open log file in append mode
        _LOG_FILE_HANDLE = open(_LOG_FILE_PATH, 'a', encoding='utf-8')

    except Exception as e:
        # Fallback to stderr if file creation fails
        print(f"[ERROR] security_core: Failed to initialize log file: {e}", file=sys.stderr)
        _LOG_FILE_PATH = None
        _LOG_FILE_HANDLE = None


def debug_log(level: str, hook_name: str, message: str) -> None:
    """
    Log a debug message to file with severity level.

    Args:
        level: Severity level - "DEBUG", "WARNING", or "ERROR"
        hook_name: Name of the hook (e.g., "guard_restricted", "guard_essential")
        message: The message to log

    Behavior:
        - DEBUG level: Only shown when debug is enabled
        - WARNING level: Only shown when debug is enabled
        - ERROR level: Always shown (even without debug flag)
        - Logs are written to PROJECT/.claude/tmp/log-{session_id}
    """
    debug_enabled = parse_debug_flag()

    # ERROR level always logs, others only in debug mode
    if level == "ERROR" or debug_enabled:
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_message = f"[{timestamp}] [{level}] {hook_name}: {message}\n"

        # Write to log file if initialized, otherwise fall back to stderr
        # Use global variable directly to avoid function call overhead
        global _LOG_FILE_HANDLE
        if _LOG_FILE_HANDLE is not None:
            try:
                _LOG_FILE_HANDLE.write(log_message)
                _LOG_FILE_HANDLE.flush()
            except Exception:
                # Fallback to stderr if write fails
                print(log_message.rstrip(), file=sys.stderr)
        else:
            # Fallback to stderr if log file not initialized
            print(log_message.rstrip(), file=sys.stderr)


def _get_caller_hook_name() -> str:
    """
    Detect which guard hook is calling (for debug logging).

    Returns:
        str: "guard_essential", "guard_restricted", or "security_core"
    """
    import inspect

    # Walk up the call stack to find the main module
    for frame_info in inspect.stack():
        module_name = frame_info.frame.f_globals.get('__name__', '')
        if 'guard_essential' in module_name:
            return "guard_essential"
        elif 'guard_restricted' in module_name:
            return "guard_restricted"

    return "security_core"

# ========================================================================
# CONTAINER ENVIRONMENT DETECTION
# ========================================================================

def is_container_environment() -> bool:
    """
    Detect if running inside a container environment.

    Checks indicators in priority order (short-circuits on first match):
    0. PYTEST_CURRENT_TEST exists (testing mode - always return False)
    1. DEVCONTAINER=true (standard devcontainer marker)
    2. CLAUDE_SECURITY_HOOKS_DISABLED=true (explicit disable signal)

    Returns:
        bool: True if running in container, False if running on host
    """
    # Check 0: Test mode - disable container detection during testing
    # pytest automatically sets PYTEST_CURRENT_TEST when running tests
    if 'PYTEST_CURRENT_TEST' in os.environ:
        debug_log("DEBUG", "security_core",
                 "Test mode detected: Container detection disabled")
        return False

    # Check 1: DEVCONTAINER environment variable
    devcontainer = os.environ.get('DEVCONTAINER', '').lower()
    if devcontainer in ('true', '1', 'yes'):
        debug_log("INFO", "security_core",
                 "Container detected: DEVCONTAINER environment variable is set")
        return True

    # Check 2: CLAUDE_SECURITY_HOOKS_DISABLED (explicit disable)
    hooks_disabled = os.environ.get('CLAUDE_SECURITY_HOOKS_DISABLED', '').lower()
    if hooks_disabled in ('true', '1', 'yes'):
        debug_log("INFO", "security_core",
                 "Hooks explicitly disabled: CLAUDE_SECURITY_HOOKS_DISABLED is set")
        return True

    # No container indicators - running on host
    debug_log("DEBUG", "security_core", "Host environment detected")
    return False

# ========================================================================
# SHARED CONSTANTS
# ========================================================================

# Tools that require security validation
RELEVANT_TOOLS = {
    "Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep"
}

# Protected files (relative to project root)
PROTECTED_FILES = {
    ".claude/hooks/guard_essential.py",
    ".claude/hooks/guard_projectFolder_simple.py",
    ".claude/hooks/guard_restricted.py",
    ".claude/hooks/guard_restricted_simple.py",
    ".claude/hooks/security_core.py",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/security-config.json",
    ".claude/secret_filter.js",
    "restricted.txt"
}

# Keys that typically contain file paths
FILE_PATH_KEYS = {
    'file_path', 'filepath', 'file', 'path', 'dir', 'directory',
    'source', 'target', 'input', 'output', 'source_path', 'target_path',
    'input_path', 'output_path', 'source_file', 'target_file',
    'input_file', 'output_file', 'backup', 'backup_path', 'backup_file'
}

# ========================================================================
# SHARED UTILITY FUNCTIONS
# ========================================================================

def deny(reason: str) -> None:
    """Deny operation with standard JSON output for PreToolUse hooks."""
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }
    print(json.dumps(out))
    sys.exit(0)




def is_relevant_tool(tool_name: str) -> bool:
    """Check if tool requires security validation."""
    if tool_name in RELEVANT_TOOLS:
        return True
    # Also guard MCP tools
    return tool_name.startswith("mcp__")


def is_file_key(key: str) -> bool:
    """Check if a key indicates a file parameter."""
    key_lower = key.lower()
    return (key_lower in FILE_PATH_KEYS or
            key_lower.endswith(('_path', '_file', '_dir', '_directory')))


# ========================================================================
# UNIFIED PATH EXTRACTION
# ========================================================================

def extract_file_paths_comprehensive(tool_name: str, tool_input: Dict[str, Any], cwd_real: str = None) -> Set[str]:
    """
    Unified path extraction combining guard_essential's recursive approach
    with guard_restricted's bash token analysis for maximum security.

    Features:
    - Recursive extraction from nested objects (from guard_essential)
    - Advanced key detection with is_file_key() (from guard_essential)
    - Glob pattern security analysis (from guard_essential)
    - Bash command token analysis (from guard_restricted)
    - Comprehensive coverage of all path access methods
    """
    paths = set()

    def extract_from_value(obj: Any, parent_key: str = None) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if is_file_key(key) and isinstance(value, str) and value.strip():
                    paths.add(value.strip())
                extract_from_value(value, key)
        elif isinstance(obj, list):
            for item in obj:
                extract_from_value(item, parent_key)

    # Use guard_essential's recursive extraction for all tools
    extract_from_value(tool_input)

    # Special handling for glob patterns - check pattern parameter
    if 'pattern' in tool_input and isinstance(tool_input['pattern'], str):
        pattern = tool_input['pattern'].strip()
        if pattern:
            # Check if glob pattern contains dangerous traversal
            if ('../' in pattern or pattern.startswith('..') or
                '~/' in pattern or pattern.startswith('~')):
                paths.add(pattern)  # Add dangerous patterns for validation

    # Enhanced bash token analysis (combining guard_restricted approach)
    if tool_name == "Bash":
        command = tool_input.get('command', '')
        if command:
            try:
                tokens = shlex.split(command)
            except Exception:
                # Fallback to simple split if shlex fails
                tokens = command.split()

            for token in tokens:
                if _looks_like_path_token(token) and not token.startswith("-"):
                    paths.add(token)
                    # Also add glob patterns as potential paths for restriction checking
                    if "*" in token or "?" in token:
                        paths.add(token)

    return paths


def _looks_like_path_token(token: str) -> bool:
    """Check if a token looks like a file path (internal helper)."""
    if token in (".", ".."):
        return True
    if token.startswith(("~/", "./", "../", "/")):
        return True
    if "/" in token:
        return True
    # Also consider glob patterns as path tokens
    if "*" in token or "?" in token:
        return True
    # Consider file extensions as potential paths
    if "." in token and not token.startswith("-") and len(token.split(".")) == 2:
        return True
    return False


# ========================================================================
# ADVANCED SECURITY ANALYSIS (From guard_essential.py)
# ========================================================================

def extract_command_substitutions(command: str) -> List[str]:
    """Extract all command substitutions from bash command: $(cmd) and `cmd`."""
    substitutions = []

    # Find $(command) patterns
    dollar_subs = re.findall(r'\$\(([^)]+)\)', command)
    substitutions.extend(dollar_subs)

    # Find `command` patterns (backticks)
    backtick_subs = re.findall(r'`([^`]+)`', command)
    substitutions.extend(backtick_subs)

    return substitutions


def extract_variable_assignments(command: str) -> List[Tuple[str, str]]:
    """Extract variable assignments: VAR=value or VAR=$(cmd)."""
    assignments = []

    # Match variable assignments in order of specificity
    # More specific patterns first to avoid partial matches
    patterns = [
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\$\([^)]+\))',  # VAR=$(cmd)
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(`[^`]+`)',  # VAR=`cmd`
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"([^"]*)"',  # VAR="value"
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\'([^\']*)\'',  # VAR='value'
        r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s;&|"\']+)',  # VAR=unquoted_value (no quotes)
    ]

    used_positions = set()  # Track used character positions to avoid overlaps

    for pattern in patterns:
        for match in re.finditer(pattern, command):
            start, end = match.span()
            # Check if this match overlaps with a previously found match
            if not any(pos in used_positions for pos in range(start, end)):
                assignments.append((match.group(1), match.group(2)))
                used_positions.update(range(start, end))

    return assignments


def extract_variable_usage(command: str) -> List[str]:
    """Extract variable references: $VAR or ${VAR}."""
    # Find $VAR and ${VAR} patterns
    var_refs = re.findall(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', command)
    return var_refs


def contains_dangerous_pattern(text: str) -> bool:
    """Check if text contains dangerous path patterns."""
    dangerous_patterns = ['..', '~', '~/', '../', '/etc/', '/usr/', '/var/', '/tmp/', 'C:\\', 'D:\\', '/proc/', '/sys/']

    # Check if any dangerous pattern is present
    for pattern in dangerous_patterns:
        if pattern in text:
            return True
    return False


def analyze_bash_command_patterns(command: str) -> List[str]:
    """
    Analyze bash command for potential dangerous patterns that could be constructed
    dynamically through variables, command substitution, or other bash features.

    Returns list of potentially dangerous patterns found.
    """
    dangerous_patterns = []

    # 1. Extract and analyze all command substitutions $(cmd) and `cmd`
    substitutions = extract_command_substitutions(command)
    for sub in substitutions:
        if contains_dangerous_pattern(sub):
            dangerous_patterns.append(f"Command substitution contains dangerous pattern: {sub}")

    # 2. Extract and analyze all variable assignments VAR=value or VAR=$(cmd)
    assignments = extract_variable_assignments(command)
    for var, value in assignments:
        if contains_dangerous_pattern(value):
            dangerous_patterns.append(f"Variable assignment contains dangerous pattern: {var}={value}")

    # 3. Check if variables with dangerous content are being used
    # This requires tracking what variables contain dangerous patterns
    var_usage = extract_variable_usage(command)
    dangerous_vars = set()

    # Build set of variables that contain dangerous patterns
    for var, value in assignments:
        if contains_dangerous_pattern(value):
            dangerous_vars.add(var)

    # Check if any dangerous variables are being used
    for var in var_usage:
        if var in dangerous_vars:
            dangerous_patterns.append(f"Usage of variable containing dangerous pattern: ${var}")

    return dangerous_patterns


# ========================================================================
# PATH VALIDATION
# ========================================================================

def is_protected_file(file_path: str, project_root: str = None) -> bool:
    """Check if file path matches any protected file with case-insensitive comparison."""
    if not file_path:
        return False

    # Normalize path separators and remove leading "./"
    normalized_path = file_path.replace('\\', '/')
    if normalized_path.startswith('./'):
        normalized_path = normalized_path[2:]

    # Always convert to lowercase for case-insensitive comparison
    normalized_path_lower = normalized_path.lower()

    # Handle absolute paths by extracting the relative part
    if os.path.isabs(normalized_path):
        try:
            # Use project_root if provided, otherwise current working directory
            current_dir = (project_root or os.getcwd()).replace('\\', '/')
            if normalized_path.startswith(current_dir + '/'):
                # Extract relative part
                relative_part = normalized_path[len(current_dir) + 1:]
                return relative_part.lower() in {p.lower() for p in PROTECTED_FILES}
            # If not within current directory, check if it ends with any protected file pattern
            for protected in PROTECTED_FILES:
                if normalized_path_lower.endswith('/' + protected.lower()):
                    return True
        except Exception:
            # If path operations fail, be safe and check ending patterns
            for protected in PROTECTED_FILES:
                if normalized_path_lower.endswith('/' + protected.lower()):
                    return True

    # Convert protected files set to lowercase for consistent case-insensitive security
    protected_lower = {p.lower() for p in PROTECTED_FILES}
    return normalized_path_lower in protected_lower


def validate_path_comprehensive(path: str, project_root: str) -> Tuple[bool, str]:
    """Enhanced path validation that properly handles paths within project bounds."""
    if not path or not isinstance(path, str):
        return True, ""

    path = path.strip()
    if not path:
        return True, ""

    # Quick dangerous pattern checks
    if path.startswith('~'):
        return False, f"Access denied: Path '{path}' attempts to access home directory (~) which is outside the project scope. Use absolute paths within the project or paths relative to project root instead."

    # Only flag .. if it's actually used for traversal (with path separators or at boundaries)
    # But allow special cases like ./... (Go build syntax)
    if path == './...':  # Go build syntax - allow this specific case
        return True, ""
    if ('../' in path or path.startswith('..') or path.endswith('/..') or
        '\\..\\' in path or path.endswith('\\..') or '/..' in path or '\\..' in path):
        return False, f"Access denied: Path '{path}' contains directory traversal pattern (..) which is blocked for security. Use absolute paths or paths relative to project root instead. Absolute paths within the project bounds are allowed."

    # Check for Windows absolute paths (drive letters and UNC)
    if re.match(r'^[A-Za-z]:[/\\]', path) or path.startswith('\\\\'):
        # On Windows systems, Windows paths can be legitimate project paths, so validate through normal path resolution
        # On Unix systems, Windows absolute paths are never valid project paths, so block them for security
        if os.name != 'nt':  # Unix/Linux/macOS system
            return False, f"Access denied: Path '{path}' is a Windows absolute path that would access system directories outside the project scope. Use paths relative to project root or absolute paths within the project instead."
        # On Windows, allow Windows paths to go through normal path resolution

    # Check for Windows reserved device names
    base_name = path.upper().split('.')[0].split('\\')[-1].split('/')[-1]
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    if base_name in reserved_names:
        return False, f"Access denied: Path '{path}' references a Windows reserved device name ({base_name}) which is not allowed for security reasons."

    # Resolve path and verify it stays within project bounds
    try:
        if not os.path.isabs(path):
            abs_path = os.path.abspath(os.path.join(project_root, path))
        else:
            abs_path = os.path.abspath(path)

        real_path = os.path.realpath(abs_path)
        real_project = os.path.realpath(project_root)

        # Check if resolved path is within project bounds
        if not real_path.startswith(real_project + os.sep) and real_path != real_project:
            return False, f"Access denied: Path '{path}' resolves to '{real_path}' which is outside the project directory '{real_project}'. Only paths within the project bounds are allowed. You can use absolute paths as long as they resolve within the project."

        return True, ""

    except Exception as e:
        return False, f"Path resolution failed: {e}"


def looks_like_file_path(token: str, project_root: str = None) -> bool:
    """Simple heuristic for file path detection in bash tokens."""
    if not token or len(token) < 2:
        return False

    # Skip tokens that are clearly quoted strings (content, not paths)
    if (token.count(' ') > 2 or  # Long descriptive text
        'test of' in token.lower() or 'error:' in token.lower() or
        'config at' in token.lower() or 'file not found' in token.lower()):
        return False

    # Check if it's a path-like token
    has_path_chars = (
        '/' in token or '\\' in token or
        token.startswith(('./', '../', '~')) or
        token in ('.', '..')
    )

    # Also check if it's a protected filename (even without path separators)
    is_protected = is_protected_file(token, project_root) or is_protected_file('./' + token, project_root)

    return has_path_chars or is_protected


# ========================================================================
# ENHANCED BASH BYPASS DETECTION
# ========================================================================

def simulate_bash_expansion(command: str, project_root: str) -> List[str]:
    """Simulate bash variable expansion and glob patterns to detect potential security bypasses.

    Returns list of potentially dangerous expanded commands that could access restricted files.
    """
    dangerous_expansions = []

    # Extract variable assignments to track what variables contain
    assignments = extract_variable_assignments(command)
    variable_values = {}

    for var_name, var_value in assignments:
        # Remove quotes from values for simulation
        clean_value = var_value.strip('"\'')
        variable_values[var_name] = clean_value

        # Check if variable contains potentially restricted content
        if contains_dangerous_pattern(clean_value) or any(restricted in clean_value.lower() for restricted in ['restricted', '.key', '.pem', '.env', 'secret']):
            dangerous_expansions.append(f"Variable {var_name} contains potentially restricted content: {clean_value}")

    # Simulate variable expansion in the command
    expanded_command = command
    for var_name, var_value in variable_values.items():
        # Simulate various expansion patterns
        patterns = [f"${var_name}", f"${{{var_name}}}"]
        for pattern in patterns:
            if pattern in expanded_command:
                expanded_command = expanded_command.replace(pattern, var_value)

    # Check if expanded command would access dangerous paths
    if expanded_command != command:
        try:
            tokens = shlex.split(expanded_command)
            for token in tokens:
                if looks_like_file_path(token, project_root) and contains_dangerous_pattern(token):
                    dangerous_expansions.append(f"Expanded command would access dangerous path: {token}")
        except Exception:
            pass

    # Check for glob patterns that might expand to restricted files
    import glob
    try:
        tokens = shlex.split(command)
        for token in tokens:
            if '*' in token or '?' in token:
                # Check if glob pattern could match restricted files
                if any(restricted in token.lower() for restricted in ['restricted', '.key', '.pem', '.env', 'secret']):
                    dangerous_expansions.append(f"Glob pattern may match restricted files: {token}")

                # Try to simulate glob expansion within project bounds
                if not contains_dangerous_pattern(token):
                    try:
                        full_pattern = os.path.join(project_root, token) if not os.path.isabs(token) else token
                        matches = glob.glob(full_pattern)
                        for match in matches:
                            if any(restricted in match.lower() for restricted in ['restricted', '.key', '.pem', '.env', 'secret']):
                                dangerous_expansions.append(f"Glob pattern {token} matches restricted file: {match}")
                    except Exception:
                        pass
    except Exception:
        pass

    return dangerous_expansions


def detect_variable_indirection_bypass(command: str, restricted_patterns: List[str]) -> List[str]:
    """Detect variable-based bypass attempts: VAR=restricted.txt && cat "$VAR" """
    bypass_patterns = []
    import fnmatch

    # Extract variable assignments and usage
    assignments = extract_variable_assignments(command)
    var_usage = extract_variable_usage(command)

    # Create a map of variables to their values
    variable_values = {}
    for var_name, var_value in assignments:
        # Remove quotes for pattern matching
        clean_value = var_value.strip('"\'')
        variable_values[var_name] = clean_value

    # Check if any assigned variables contain restricted patterns
    for var_name, var_value in variable_values.items():
        var_value_lower = var_value.lower()

        # Check against restricted patterns (case-insensitive)
        for pattern in restricted_patterns:
            pattern_lower = pattern.lower()

            # Check for exact match, contains match, or glob pattern match
            if (pattern_lower in var_value_lower or
                var_value_lower == pattern_lower or
                var_value_lower.endswith(pattern_lower) or
                fnmatch.fnmatch(var_value_lower, pattern_lower)):

                # Check if this variable is used in the command
                if var_name in var_usage:
                    bypass_patterns.append(f"Variable indirection bypass: {var_name}={var_value} used in command")

    # Also check for partial filename construction in brace expansions
    # Look for patterns like ${var}.extension or $var.extension
    brace_constructions = re.findall(r'\$\{([^}]+)\}\.(\w+)', command)
    simple_constructions = re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)[.](\w+)', command)

    all_constructions = brace_constructions + simple_constructions

    for var_name, extension in all_constructions:
        if var_name in variable_values:
            var_value = variable_values[var_name]
            if extension:
                # Variable + extension construction
                constructed = f"{var_value}.{extension}"
                constructed_lower = constructed.lower()

                for pattern in restricted_patterns:
                    pattern_lower = pattern.lower()
                    if (constructed_lower == pattern_lower or
                        fnmatch.fnmatch(constructed_lower, pattern_lower)):
                        bypass_patterns.append(f"Variable construction bypass: {var_name}={var_value} + .{extension} -> {constructed} matches {pattern}")

    # Also check for simple partial construction where var value is part of restricted pattern
    for var_name in var_usage:
        if var_name in variable_values:
            var_value = variable_values[var_name]
            # Look for patterns where variable + extension might create restricted files
            for pattern in restricted_patterns:
                if var_value in pattern and len(var_value) > 2:
                    bypass_patterns.append(f"Variable may construct restricted filename: {var_name}={var_value} -> {pattern}")

    return bypass_patterns


def detect_glob_expansion_bypass(command: str, project_root: str, restricted_patterns: List[str]) -> List[str]:
    """Detect glob patterns that could match restricted files: cat restricted.*, cat rest* """
    glob_patterns = []
    import fnmatch

    try:
        tokens = shlex.split(command)
    except Exception:
        tokens = command.split()

    for token in tokens:
        if '*' in token or '?' in token:
            token_lower = token.lower()

            # Check if glob pattern could match restricted patterns directly
            for pattern in restricted_patterns:
                pattern_lower = pattern.lower()

                # Only flag patterns that are clearly dangerous:
                # 1. Exact pattern matches (e.g., *.key matches *.key)
                if token_lower == pattern_lower:
                    glob_patterns.append(f"Glob pattern {token} exactly matches restricted pattern {pattern}")
                    continue

                # 2. Check if glob pattern could match restricted/protected files
                if fnmatch.fnmatch(pattern_lower, token_lower):
                    # Only flag if it's clearly targeting sensitive files, not incidental matches
                    is_targeting_sensitive = (
                        token_lower.startswith('.claude/') or  # Directly targeting .claude files
                        'guard' in token_lower or              # Targeting guard files
                        'restricted' in token_lower or         # Targeting restricted files
                        'secret' in token_lower or             # Targeting secret files
                        'private' in token_lower               # Targeting private files
                    )
                    if is_targeting_sensitive:
                        glob_patterns.append(f"Glob pattern {token} could match restricted file {pattern}")

                # 3. Check if restricted pattern is a glob that would match our token
                if fnmatch.fnmatch(token_lower, pattern_lower):
                    glob_patterns.append(f"Glob pattern {token} matches restricted pattern {pattern}")

                # 4. Check for targeted partial matches (only for specific dangerous prefixes)
                dangerous_prefixes = ['restricted', 'secret', 'private', '.env', 'config', 'security', 'guard', 'key', 'password']
                if ('*' in token_lower and
                    any(prefix in token_lower for prefix in dangerous_prefixes) and
                    any(part in pattern_lower for part in token_lower.split('*') if part and len(part) > 2)):
                    glob_patterns.append(f"Glob pattern {token} may partially match restricted file {pattern}")

                # 5. Check for wildcards that could match sensitive files based on pattern content
                if '*' in token_lower and '*' not in pattern_lower:
                    # Extract the non-wildcard parts of the glob pattern
                    glob_parts = [part for part in token_lower.split('*') if part and len(part) > 1]
                    # Check if any part could be targeting this restricted file
                    for part in glob_parts:
                        # Only flag if the pattern part is significant AND the file contains sensitive keywords
                        if (part in pattern_lower and len(part) > 2 and
                            any(keyword in pattern_lower for keyword in dangerous_prefixes) and
                            # Don't flag common extensions unless they're very targeted
                            not (part.startswith('.') and len(part) <= 5 and part in ['.json', '.txt', '.log', '.csv', '.py', '.js', '.html'])):
                            glob_patterns.append(f"Glob pattern {token} targets sensitive file {pattern} via pattern part '{part}'")

    return glob_patterns


def detect_partial_construction_bypass(command: str, restricted_patterns: List[str]) -> List[str]:
    """Detect dynamic path construction: filename=restricted && cat ${filename}.txt """
    construction_patterns = []

    # Extract variable assignments and usage
    assignments = extract_variable_assignments(command)
    var_usage = extract_variable_usage(command)

    # Look for variable usage in string concatenation contexts
    variable_values = {}
    for var_name, var_value in assignments:
        clean_value = var_value.strip('"\'')
        variable_values[var_name] = clean_value

    # Check for brace expansion and concatenation patterns
    brace_patterns = re.findall(r'\$\{([^}]+)\}[.\w]*', command)
    for match in brace_patterns:
        var_name = match
        if var_name in variable_values:
            var_value = variable_values[var_name]

            # Try to find the full constructed path
            construction_context = re.search(r'\$\{' + re.escape(var_name) + r'\}[.\w]*', command)
            if construction_context:
                full_construct = construction_context.group(0)

                # Simulate the construction
                simulated = full_construct.replace(f'${{{var_name}}}', var_value)
                simulated_lower = simulated.lower()

                # Check if constructed path matches restricted patterns
                for pattern in restricted_patterns:
                    pattern_lower = pattern.lower()
                    if (simulated_lower == pattern_lower or
                        simulated_lower in pattern_lower or
                        pattern_lower in simulated_lower):
                        construction_patterns.append(f"Path construction {full_construct} resolves to restricted file {simulated}")

    # Also check for simple concatenation patterns
    for var_name in var_usage:
        if var_name in variable_values:
            var_value = variable_values[var_name]

            # Look for patterns where the variable appears next to file extensions or path components
            concat_patterns = [
                rf'\${var_name}\.[\w]+',  # $var.extension
                rf'\${{{var_name}}}\.[\w]+',  # ${var}.extension
                rf'[\w]+\${var_name}',  # prefix$var
                rf'[\w]+\${{{var_name}}}'  # prefix${var}
            ]

            for pattern_regex in concat_patterns:
                matches = re.findall(pattern_regex, command)
                for match in matches:
                    # Simulate the construction
                    simulated = match.replace(f'${var_name}', var_value).replace(f'${{{var_name}}}', var_value)
                    simulated_lower = simulated.lower()

                    # Check against restricted patterns
                    for restricted in restricted_patterns:
                        restricted_lower = restricted.lower()
                        if (simulated_lower == restricted_lower or
                            restricted_lower in simulated_lower):
                            construction_patterns.append(f"String concatenation {match} constructs restricted path {simulated}")

    return construction_patterns


# ========================================================================
# BASH COMMAND VALIDATION
# ========================================================================

def validate_bash_command_advanced(command: str, project_root: str, skip_dynamic_analysis: bool = False, additional_restricted_patterns: List[str] = None) -> Tuple[bool, str]:
    """Advanced bash validation with bypass detection combining both guard approaches."""
    if not command:
        return True, ""

    # Quick dangerous pattern checks - be more precise about what's dangerous
    dangerous_patterns = [
        ('~/', 'home directory access'),
        ('../', 'parent directory traversal'),
        ('/etc/', 'system configuration access'),
        ('/usr/', 'system directory access'),
        ('/var/', 'system directory access'),
        ('/tmp/', 'system temporary directory'),
        ('C:\\', 'Windows system drive'),
        ('D:\\', 'Windows drive access'),
        ('/proc/', 'Linux process filesystem'),
        ('/sys/', 'Linux system filesystem')
    ]

    # Don't flag patterns inside quoted strings
    # Remove quoted strings temporarily for pattern checking
    command_no_quotes = re.sub(r"'[^']*'", "", command)  # Remove single quotes
    command_no_quotes = re.sub(r'"[^"]*"', "", command_no_quotes)  # Remove double quotes

    for pattern, description in dangerous_patterns:
        if pattern in command_no_quotes:
            return False, f"Access denied: Command contains '{pattern}' which would access {description} outside the project scope. Use paths relative to project root or absolute paths within the project bounds instead."

    # Simple token analysis for file paths
    try:
        tokens = shlex.split(command)
    except Exception:
        # Fallback to simple split if shlex fails
        tokens = command.split()

    for token in tokens:
        # Skip command flags and quoted strings
        if token.startswith('-') or (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            continue

        if looks_like_file_path(token, project_root):
            # Check if this path-like token is protected (handle simple filenames too)
            if is_protected_file(token, project_root) or is_protected_file('./' + token, project_root):
                return False, f"Access denied: Command attempts to access protected security file '{token}' which is not allowed."

            # Validate the path
            valid, reason = validate_path_comprehensive(token, project_root)
            if not valid:
                return False, f"Command contains invalid path: {reason}"

    # Add dynamic pattern analysis to detect command substitution and variable bypasses
    # Skip for git metadata commands as they work with repository metadata, not system files
    if not skip_dynamic_analysis:
        dynamic_patterns = analyze_bash_command_patterns(command)
        if dynamic_patterns:
            # Create a comprehensive error message explaining the security violation
            pattern_details = "; ".join(dynamic_patterns)
            return False, f"Access denied: Command uses dynamic construction that could bypass security checks. {pattern_details}. This type of pattern construction is blocked to prevent directory traversal attacks."

        # Enhanced bypass detection after existing dynamic analysis
        # Combine protected files with additional restricted patterns
        all_restricted_patterns = list(PROTECTED_FILES)
        if additional_restricted_patterns:
            all_restricted_patterns.extend(additional_restricted_patterns)

        bypass_patterns = detect_variable_indirection_bypass(command, all_restricted_patterns)
        if bypass_patterns:
            return False, f"Access denied: Command uses variable indirection to bypass security: {'; '.join(bypass_patterns)}"

        glob_patterns = detect_glob_expansion_bypass(command, project_root, all_restricted_patterns)
        if glob_patterns:
            return False, f"Access denied: Command uses glob patterns that could access restricted files: {'; '.join(glob_patterns)}"

        construction_patterns = detect_partial_construction_bypass(command, all_restricted_patterns)
        if construction_patterns:
            return False, f"Access denied: Command uses dynamic path construction to bypass security: {'; '.join(construction_patterns)}"

    return True, ""


# ========================================================================
# SECURITY CONFIGURATION LOADING
# ========================================================================

class SecurityConfigError(Exception):
    """Exception for security configuration errors"""
    pass


def load_security_config(config_path: str) -> Dict[str, Any]:
    """Load and validate security configuration from JSON file"""
    if not os.path.exists(config_path):
        raise SecurityConfigError(f"security-config.json missing at {config_path}")

    if not os.path.isfile(config_path):
        raise SecurityConfigError(f"security-config.json path exists but is not a file: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise SecurityConfigError(f"security-config.json contains invalid JSON: {e}")
    except Exception as e:
        raise SecurityConfigError(f"Failed to read security-config.json: {e}")

    # Validate config structure
    validate_security_config(config)

    return config


def validate_security_config(config: Dict[str, Any]) -> None:
    """Validate security config structure and values"""
    required = ["project_root", "version", "locked"]

    for field in required:
        if field not in config:
            raise SecurityConfigError(f"Missing required field: {field}")

    project_root = config["project_root"]
    if not os.path.exists(project_root):
        raise SecurityConfigError(f"Project root does not exist: {project_root}")

    if not os.path.isdir(project_root):
        raise SecurityConfigError(f"Project root is not a directory: {project_root}")


def get_project_root_from_config() -> str:
    """Get fixed project root from security config"""
    debug_enabled = parse_debug_flag()

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up from .claude.example/hooks to .claude.example
    claude_dir = os.path.dirname(script_dir)

    # Look for security-config.json in .claude.example directory
    config_path = os.path.join(claude_dir, "security-config.json")

    if debug_enabled:
        caller_hook = _get_caller_hook_name()
        debug_log("DEBUG", caller_hook, f"Reading security config: {config_path}")

    # Use security-config.json if it exists
    if os.path.exists(config_path):
        try:
            config = load_security_config(config_path)
            project_root = config["project_root"]

            if debug_enabled:
                caller_hook = _get_caller_hook_name()
                debug_log("DEBUG", caller_hook, f"Project root: {project_root}")

            # Validate that the project root actually exists and is accessible
            if not os.path.exists(project_root):
                raise SecurityConfigError(f"Configured project root does not exist: {project_root}")

            if not os.path.isdir(project_root):
                raise SecurityConfigError(f"Configured project root is not a directory: {project_root}")

            return os.path.realpath(project_root)

        except SecurityConfigError as e:
            # Fail-safe behavior: block all operations with clear error message
            debug_log("ERROR", _get_caller_hook_name(), str(e))
            raise SecurityConfigError(f"Security configuration error: {e}. All operations blocked until security-config.json is properly configured.")

    # No security-config.json found - fail-safe by blocking all operations
    else:
        debug_log("ERROR", _get_caller_hook_name(), "security-config.json not found")
        raise SecurityConfigError("security-config.json not found. All operations blocked until security configuration is properly set up.")