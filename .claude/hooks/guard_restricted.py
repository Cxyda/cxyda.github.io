#!/usr/bin/env python3
"""
Claude Code Security Hook - Enhanced Restricted Files Support

This hook extends the basic security functionality with support for a restricted.txt file
that uses gitignore-style patterns to block access to specific files and directories.

Features:
- Gitignore-style pattern matching
- Simple negation support with !
- Directory-only patterns ending with /
- Anchored vs unanchored patterns
- Integrates with comprehensive security validation from security_core
- Advanced security capabilities including command substitution bypass detection

Usage:
Create a restricted.txt file in your project root with patterns like:
  secret/
  *.key
  config.json
  !public.key

Updated to use shared security_core module with advanced security capabilities.
"""

import json
import os
import sys
import fnmatch
import shlex
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, Set, List, Tuple, Optional

# Import shared security functions from security_core
from security_core import (
    deny, is_relevant_tool, RELEVANT_TOOLS,
    extract_file_paths_comprehensive,
    is_protected_file, validate_path_comprehensive,
    validate_bash_command_advanced,
    get_project_root_from_config, SecurityConfigError,
    detect_variable_indirection_bypass, detect_glob_expansion_bypass,
    detect_partial_construction_bypass,
    parse_debug_flag, debug_log, init_debug_log,
    is_container_environment
)

# Cache configuration
CACHE_DIR = Path(".claude/.cache")
CACHE_FILE = CACHE_DIR / "restricted_rules_cache.json"


class DiscoveryTimeoutError(Exception):
    """Raised when restricted.txt discovery exceeds configured timeout."""

    def __init__(self, timeout: float, elapsed: float, dirs_scanned: int,
                 current_dir: str, files_found: int):
        """
        Initialize timeout error with diagnostic information.

        Args:
            timeout: Configured timeout in seconds
            elapsed: Actual elapsed time in seconds
            dirs_scanned: Number of directories scanned before timeout
            current_dir: Directory being scanned when timeout occurred
            files_found: Number of restricted.txt files found before timeout
        """
        self.timeout = timeout
        self.elapsed = elapsed
        self.dirs_scanned = dirs_scanned
        self.current_dir = current_dir
        self.files_found = files_found

        message = (
            f"Discovery timeout: Searched for restricted.txt files for {elapsed:.2f}s "
            f"(limit: {timeout}s). Scanned {dirs_scanned} directories, found {files_found} "
            f"restricted.txt files before timeout. Last directory: {current_dir}"
        )
        super().__init__(message)


class Rule:
    """Represents a gitignore-style rule from restricted.txt"""
    def __init__(self, original: str, pattern: str, neg: bool, anchored: bool, dir_only: bool, source_file: str = None):
        self.original = original
        self.pattern = pattern  # normalized POSIX-like (forward slashes)
        self.neg = neg
        self.anchored = anchored
        self.dir_only = dir_only
        self.source_file = source_file  # Absolute path to source restricted.txt


def to_posix(p: str) -> str:
    """Convert path to POSIX-style (forward slashes)"""
    return p.replace(os.sep, "/")


def get_cache_key(project_root: str) -> str:
    """Generate cache key from project root path."""
    return hashlib.md5(project_root.encode()).hexdigest()


def get_files_with_mtimes(files: List[Tuple[str, str]]) -> Dict[str, float]:
    """Get modification times for all restricted.txt files."""
    mtimes = {}
    for abs_path, _ in files:
        try:
            mtimes[abs_path] = os.path.getmtime(abs_path)
        except FileNotFoundError:
            pass  # File was deleted between discovery and stat
    return mtimes


def load_cached_rules(project_root: str, current_files: List[Tuple[str, str]], debug_enabled: bool = False) -> Optional[List[Rule]]:
    """Load rules from cache if valid."""
    if not CACHE_FILE.exists():
        debug_log("DEBUG", "guard_restricted", "Cache file not found")
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)

        cache_key = get_cache_key(project_root)
        if cache_key not in cache_data:
            debug_log("DEBUG", "guard_restricted", f"Cache key not found: {cache_key}")
            return None

        entry = cache_data[cache_key]

        # Validate: Check file list matches
        cached_paths = set(entry['mtimes'].keys())
        current_paths = {abs_path for abs_path, _ in current_files}

        if cached_paths != current_paths:
            debug_log("DEBUG", "guard_restricted", "Cache invalid - file list changed")
            return None  # File list changed (new or deleted files)

        # Validate: Check all mtimes match
        current_mtimes = get_files_with_mtimes(current_files)
        for path, cached_mtime in entry['mtimes'].items():
            if path not in current_mtimes or current_mtimes[path] != cached_mtime:
                debug_log("DEBUG", "guard_restricted", f"Cache invalid - file modified: {path}")
                return None  # File was modified or deleted

        # Cache valid - deserialize rules
        rules = []
        for r in entry['rules']:
            rule = Rule(
                original=r['original'],
                pattern=r['pattern'],
                neg=r['neg'],
                anchored=r['anchored'],
                dir_only=r['dir_only'],
                source_file=r.get('source_file')
            )
            rules.append(rule)

        return rules

    except Exception as e:
        debug_log("ERROR", "guard_restricted", f"Cache load failed: {e}")
        debug_log("DEBUG", "guard_restricted", "Continuing without cache")
        return None


def save_cached_rules(project_root: str, files: List[Tuple[str, str]], rules: List[Rule], debug_enabled: bool = False):
    """Save rules to cache with mtime tracking."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        cache_data = {}
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
            except:
                cache_data = {}

        # Update cache entry for this project
        cache_key = get_cache_key(project_root)
        cache_data[cache_key] = {
            'mtimes': get_files_with_mtimes(files),
            'rules': [
                {
                    'original': r.original,
                    'pattern': r.pattern,
                    'neg': r.neg,
                    'anchored': r.anchored,
                    'dir_only': r.dir_only,
                    'source_file': r.source_file
                }
                for r in rules
            ],
            'timestamp': time.time()
        }

        # Write atomically (temp file + rename)
        temp_fd, temp_path = tempfile.mkstemp(dir=CACHE_DIR, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(cache_data, f)
            os.replace(temp_path, CACHE_FILE)

            debug_log("DEBUG", "guard_restricted", f"Cache saved successfully ({len(rules)} rules)")
        except:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        debug_log("ERROR", "guard_restricted", f"Cache save failed: {e}")
        debug_log("WARNING", "guard_restricted", "Continuing without cache (performance may be slower)")
        # Continue without cache - not a fatal error


# Built-in directories to skip during both:
# 1. restricted.txt discovery (find_all_restricted_files)
# 2. skip_dirs.txt search (find_skip_dirs_file)
BUILTIN_SKIP_DIRS = {
    '.git',           # Git repository data
    'node_modules',   # Node.js dependencies
    'venv',           # Python virtual environment
    '__pycache__',    # Python bytecode cache
    'dist',           # Build outputs
    'build',          # Build outputs
    '.venv',          # Alternative venv naming
    'env',            # Alternative venv naming
}


def count_subdirs(directory: Path) -> int:
    """
    Count immediate subdirectories (not recursive).

    Args:
        directory: Path to directory to count subdirectories in

    Returns:
        Number of immediate subdirectories, or 999999 if inaccessible
    """
    try:
        count = sum(1 for entry in directory.iterdir()
                   if entry.is_dir() and not entry.is_symlink())
        return count
    except (PermissionError, OSError):
        return 999999  # Large number to deprioritize inaccessible dirs


def find_skip_dirs_file(project_root: str, max_depth: int = 4, debug_enabled: bool = False) -> Optional[Path]:
    """
    Find skip_dirs.txt using smart BFS search with subfolder count prioritization.

    This function searches for skip_dirs.txt starting at project_root, then searching
    subdirectories in order of subfolder count (smallest first) up to max_depth.

    Args:
        project_root: Absolute path to project root
        max_depth: Maximum depth to search (0 = only check project_root)
        debug_enabled: Whether debug logging is enabled

    Returns:
        Path to skip_dirs.txt if found, None otherwise

    Algorithm:
        1. Check project_root/skip_dirs.txt first (fast path)
        2. If not found and max_depth > 0, perform smart BFS:
           - Sort subdirectories by subfolder count (ascending)
           - Directories with fewer subfolders searched first
           - Skip symlinks and handle permission errors gracefully
           - Stop immediately once skip_dirs.txt is found
    """
    from collections import deque

    start_time = time.time()
    dirs_searched = 0
    dirs_skipped = 0

    # Fast path: Check project root first
    root_file = Path(project_root) / "skip_dirs.txt"
    if root_file.exists():
        elapsed = time.time() - start_time
        debug_log("DEBUG", "guard_restricted",
                 f"Found skip_dirs.txt at project root in {elapsed*1000:.2f}ms")
        return root_file

    dirs_searched += 1

    # If max_depth is 0, only check root
    if max_depth == 0:
        debug_log("DEBUG", "guard_restricted",
                 "max_depth=0, only checked project root")
        return None

    debug_log("DEBUG", "guard_restricted",
             f"Starting subdirectory search (max_depth={max_depth})")

    # Smart BFS with subfolder counting
    queue = deque([(Path(project_root), 0)])

    while queue:
        current_dir, depth = queue.popleft()

        if depth >= max_depth:
            continue

        # Get all subdirectories
        try:
            subdirs = [entry for entry in current_dir.iterdir()
                      if entry.is_dir() and not entry.is_symlink()]
        except (PermissionError, OSError) as e:
            debug_log("WARNING", "guard_restricted",
                     f"Permission denied accessing {current_dir}: {e}")
            dirs_skipped += 1
            continue

        # Skip built-in directories
        filtered_subdirs = []
        for subdir in subdirs:
            if subdir.name in BUILTIN_SKIP_DIRS:
                dirs_skipped += 1
                continue
            filtered_subdirs.append(subdir)

        # Count subfolders in each subdir
        subdir_with_counts = []
        for subdir in filtered_subdirs:
            count = count_subdirs(subdir)
            subdir_with_counts.append((subdir, count))

        # Sort by subfolder count (ascending) - small dirs first
        subdir_with_counts.sort(key=lambda x: x[1])

        # Search in sorted order
        for subdir, count in subdir_with_counts:
            dirs_searched += 1

            # Check for skip_dirs.txt
            skip_file = subdir / "skip_dirs.txt"
            if skip_file.exists():
                elapsed = time.time() - start_time
                debug_log("DEBUG", "guard_restricted",
                         f"Found skip_dirs.txt at {skip_file} (depth={depth+1}, "
                         f"searched {dirs_searched} dirs, skipped {dirs_skipped} dirs, "
                         f"elapsed {elapsed*1000:.2f}ms)")

                if elapsed > 1.0:
                    debug_log("WARNING", "guard_restricted",
                             f"skip_dirs.txt search took {elapsed:.2f}s (>1s threshold)")

                return skip_file  # STOP IMMEDIATELY

            # Add to queue for deeper search
            queue.append((subdir, depth + 1))

    # Not found
    elapsed = time.time() - start_time
    debug_log("DEBUG", "guard_restricted",
             f"skip_dirs.txt not found after searching {dirs_searched} dirs "
             f"(skipped {dirs_skipped} dirs) in {elapsed*1000:.2f}ms")

    if elapsed > 1.0:
        debug_log("WARNING", "guard_restricted",
                 f"skip_dirs.txt search took {elapsed:.2f}s (>1s threshold)")

    return None


def load_skip_dirs(project_root: str) -> set:
    """
    Load skip directories from skip_dirs.txt file and merge with built-in dirs.

    Args:
        project_root: Absolute path to project root

    Returns:
        Set of directory names to skip during discovery

    File format (skip_dirs.txt):
        - One directory name per line
        - Lines starting with # are comments
        - Empty lines are ignored
        - Directory names are relative (e.g., "vendor", "cache", ".mydir")
    """
    skip_dirs = BUILTIN_SKIP_DIRS.copy()

    skip_file = Path(project_root) / "skip_dirs.txt"
    if not skip_file.exists():
        return skip_dirs

    try:
        with open(skip_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Add directory name to skip set
                skip_dirs.add(line)

        debug_log("DEBUG", "guard_restricted",
                 f"Loaded {len(skip_dirs) - len(BUILTIN_SKIP_DIRS)} additional "
                 f"skip directories from skip_dirs.txt")

    except Exception as e:
        debug_log("WARNING", "guard_restricted",
                 f"Failed to load skip_dirs.txt: {e}. Using built-in skip directories only.")

    return skip_dirs


def load_skip_rules(project_root: str, debug_enabled: bool = False) -> List[Rule]:
    """
    Load skip directory patterns from skip_dirs.txt and convert to Rule objects.

    This function parses skip_dirs.txt into Rule objects to enable pattern matching
    for directory skipping (similar to restricted.txt pattern matching).

    Args:
        project_root: Absolute path to project root
        debug_enabled: Whether debug logging is enabled

    Returns:
        List of Rule objects (built-in directories + custom patterns from skip_dirs.txt)

    File format (skip_dirs.txt):
        - One pattern per line
        - Lines starting with # are comments
        - Empty lines are ignored
        - Supports glob patterns: test_*, *_cache, tmp_*_old
        - Supports anchored patterns: /tmp/ (only at project root)
        - Supports relative paths: test-repo/parent_project
        - Trailing slashes are normalized automatically
        - Negation (!) is NOT supported and will be rejected with warning

    Pattern examples:
        vendor               # Skip any directory named "vendor"
        test_*               # Skip directories starting with "test_"
        *_cache              # Skip directories ending with "_cache"
        /tmp/                # Skip "tmp" only at project root
        build/dist/          # Skip "build/dist" directory path
        test-repo/           # Skip "test-repo" directory (trailing / normalized)
    """
    # Get max_depth from environment variable
    max_depth = int(os.environ.get('CLAUDE_SKIP_SEARCH_DEPTH', '4'))
    if max_depth < 0:
        debug_log("WARNING", "guard_restricted", f"Invalid CLAUDE_SKIP_SEARCH_DEPTH={max_depth}, using 0")
        max_depth = 0

    rules = []

    # Add built-in directories as unanchored rules
    for dirname in BUILTIN_SKIP_DIRS:
        rule = Rule(
            original=dirname,
            pattern=dirname,
            neg=False,
            anchored=False,
            dir_only=True,
            source_file=None  # Built-in, not from file
        )
        rules.append(rule)

    # Use smart BFS to find skip_dirs.txt
    skip_file_path = find_skip_dirs_file(project_root, max_depth, debug_enabled)

    if skip_file_path is None:
        debug_log("DEBUG", "guard_restricted",
                 f"No skip_dirs.txt found, using {len(rules)} built-in rules only")
        return rules

    # Parse skip_dirs.txt
    custom_count = 0
    warnings = []

    try:
        with open(skip_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                original_line = line.rstrip('\n')
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Reject negation patterns (not supported for skip_dirs)
                if line.startswith('!'):
                    warning_msg = f"Negation patterns not supported in skip_dirs.txt (line {line_num}: {line})"
                    warnings.append(warning_msg)
                    debug_log("WARNING", "guard_restricted", warning_msg)
                    continue

                # Detect directory-only pattern (trailing /)
                dir_only = line.endswith('/')
                if dir_only:
                    # Remove trailing slash for pattern matching
                    line = line.rstrip('/')

                # Detect anchored pattern (leading /)
                anchored = line.startswith('/')
                if anchored:
                    # Remove leading slash
                    line = line[1:]

                # Normalize to POSIX path
                pattern = to_posix(line)

                # Create Rule object
                rule = Rule(
                    original=original_line,
                    pattern=pattern,
                    neg=False,  # Never negated for skip_dirs
                    anchored=anchored,
                    dir_only=True,  # All skip patterns are directory-only
                    source_file=str(skip_file_path)
                )
                rules.append(rule)
                custom_count += 1

        debug_log("DEBUG", "guard_restricted",
                 f"Loaded {custom_count} custom skip rules from skip_dirs.txt "
                 f"(total: {len(rules)} rules including built-in)")

        if warnings:
            debug_log("WARNING", "guard_restricted",
                     f"Found {len(warnings)} warnings while parsing skip_dirs.txt")

    except Exception as e:
        debug_log("WARNING", "guard_restricted",
                 f"Failed to load skip_dirs.txt: {e}. Using {len(rules)} built-in rules only.")

    return rules


def should_skip_directory(dir_path: str, project_root: str, skip_rules: List[Rule]) -> bool:
    """
    Check if a directory should be skipped based on skip rules.

    Uses pattern matching with Rule objects (similar to restricted.txt matching).
    Supports glob patterns, anchored patterns, and relative paths.

    Args:
        dir_path: Absolute path to the directory to check
        project_root: Absolute path to project root
        skip_rules: List of Rule objects from load_skip_rules()

    Returns:
        True if directory should be skipped, False otherwise

    Backward compatibility:
        - Unanchored simple patterns (no "/" in pattern) check basename
        - This ensures existing skip_dirs.txt files continue to work
        - Example: "node_modules" matches any directory named "node_modules"

    Pattern matching:
        - Full relative path matching: "test-repo/parent_project"
        - Glob patterns: "test_*", "*_cache"
        - Anchored patterns: "/tmp/" (only at project root)
        - Case-insensitive matching (for security)
    """
    try:
        # Calculate relative path from project root
        rel_path = os.path.relpath(dir_path, project_root)

        # Normalize to POSIX for pattern matching
        rel_posix = to_posix(rel_path)

        # Get basename for backward compatibility with simple patterns
        basename = os.path.basename(dir_path)

        # Check each skip rule
        for rule in skip_rules:
            # Check full relative path match
            if rule_matches(rule, rel_posix, is_dir=True):
                return True

        return False

    except Exception as e:
        # Fail open: if we can't determine, don't skip (safer)
        debug_log("WARNING", "guard_restricted",
                 f"Error checking skip rules for {dir_path}: {e}")
        return False


def find_all_restricted_files(
    project_root: str,
    max_depth: int = 10,
    debug_enabled: bool = False,
    timeout: float = 1.0
) -> List[Tuple[str, str]]:
    """
    Recursively find all restricted.txt files under project root with timeout protection.

    Uses pattern matching for directory skipping (supports glob patterns, anchored patterns,
    and relative paths via skip_dirs.txt).

    Args:
        project_root: Absolute path to project root
        max_depth: Maximum directory depth to search
        debug_enabled: Whether debug logging is enabled
        timeout: Maximum time in seconds for discovery (default: 1.0)

    Returns:
        List of (absolute_path, relative_dir) tuples for each restricted.txt found

    Raises:
        DiscoveryTimeoutError: If discovery exceeds timeout limit
    """
    # Timing and tracking variables
    start_time = time.monotonic()
    dirs_scanned = 0
    current_scanning_dir = project_root

    results = []
    visited = set()  # Track visited paths to avoid symlink loops

    try:
        project_path = Path(project_root).resolve()

        # Load skip rules (built-in + custom from skip_dirs.txt) with pattern support
        skip_rules = load_skip_rules(project_root, debug_enabled)

        # Debug: Log discovery start
        debug_log("DEBUG", "guard_restricted",
                 f"Starting restricted.txt discovery in {project_root} (timeout: {timeout}s, "
                 f"skip_rules: {len(skip_rules)})")

        # Use os.walk for efficient recursive search with directory filtering
        for root, dirs, files in os.walk(project_root):
            # CHECK TIMEOUT at start of each directory
            elapsed = time.monotonic() - start_time
            if elapsed > timeout:
                raise DiscoveryTimeoutError(
                    timeout=timeout,
                    elapsed=elapsed,
                    dirs_scanned=dirs_scanned,
                    current_dir=current_scanning_dir,
                    files_found=len(results)
                )

            current_scanning_dir = root
            dirs_scanned += 1

            # Debug: Log directory entry
            debug_log("DEBUG", "guard_restricted",
                     f"Scanning directory {dirs_scanned}: {root} "
                     f"(elapsed: {elapsed*1000:.1f}ms, files in dir: {len(files)})")

            # Skip directories BEFORE traversing them by modifying dirs in-place
            # Use pattern matching for skip_dirs.txt support
            original_dir_count = len(dirs)
            filtered_dirs = []

            for d in dirs:
                # Construct absolute path for directory
                dir_abs_path = os.path.join(root, d)

                # Check if should skip based on rules (pattern matching)
                if should_skip_directory(dir_abs_path, project_root, skip_rules):
                    debug_log("DEBUG", "guard_restricted",
                             f"Skipping directory: {d} (matched skip rule)")
                    continue

                # Skip hidden directories except .claude*
                if d.startswith('.') and d not in {'.claude', '.claude.example'}:
                    debug_log("DEBUG", "guard_restricted",
                             f"Skipping hidden directory: {d}")
                    continue

                filtered_dirs.append(d)

            # Update dirs in-place (required by os.walk)
            dirs[:] = filtered_dirs

            # Debug: Log skip decisions
            if len(dirs) < original_dir_count:
                skipped = original_dir_count - len(dirs)
                debug_log("DEBUG", "guard_restricted",
                         f"Skipped {skipped} directories in {root}")

            # Check if restricted.txt exists in current directory
            if 'restricted.txt' not in files:
                continue

            file_path = Path(root) / 'restricted.txt'
            abs_path = file_path.resolve()

            # Avoid symlink loops
            if abs_path in visited:
                debug_log("DEBUG", "guard_restricted",
                         f"Skipping duplicate restricted.txt (symlink): {abs_path}")
                continue
            visited.add(abs_path)

            # Calculate depth and skip if too deep
            try:
                rel_path = abs_path.parent.relative_to(project_path)
                depth = len(rel_path.parts)
                if depth > max_depth:
                    debug_log("WARNING", "guard_restricted",
                             f"Skipping {abs_path} (depth {depth} > {max_depth})")
                    continue

                # Convert to relative directory string
                rel_dir = str(rel_path) if rel_path != Path('.') else ""
                results.append((str(abs_path), rel_dir))

                debug_log("DEBUG", "guard_restricted",
                         f"Found restricted.txt: {abs_path} (context: {rel_dir or 'root'})")

            except ValueError:
                # File not under project root
                debug_log("DEBUG", "guard_restricted",
                         f"Skipping {abs_path} (not under project root)")
                continue

        # Debug: Log discovery summary
        elapsed = time.monotonic() - start_time
        debug_log("DEBUG", "guard_restricted",
                 f"Discovery complete: scanned {dirs_scanned} directories, "
                 f"found {len(results)} restricted.txt files in {elapsed*1000:.1f}ms")

        # Warn if too many files found
        if len(results) > 100:
            debug_log("WARNING", "guard_restricted",
                     f"Warning - found {len(results)} restricted.txt files")

        # Sort by depth (root first) for predictable precedence
        results.sort(key=lambda x: x[1].count(os.sep))

    except DiscoveryTimeoutError:
        # Re-raise timeout errors (don't catch them here)
        raise

    except Exception as e:
        debug_log("ERROR", "guard_restricted", f"File discovery failed: {e}")
        debug_log("WARNING", "guard_restricted", "File protection NOT active due to discovery failure")
        return []

    return results


def adjust_pattern_for_context(pattern: str, restricted_file_relpath: str) -> str:
    """Adjust pattern to be relative to project root based on restricted.txt location."""
    # Root level file - no adjustment needed
    if not restricted_file_relpath or restricted_file_relpath == ".":
        return pattern

    # Prepend subdirectory to pattern and normalize to POSIX
    adjusted = os.path.join(restricted_file_relpath, pattern).replace(os.sep, "/")
    return adjusted


def is_git_metadata_command(cmd: str) -> bool:
    """Check if git command only works with metadata, not project files.

    Returns True for git commands that operate on repository metadata
    (commits, logs, config) and don't access project files directly.

    Handles various git command formats and focuses on metadata operations.
    """
    git_metadata_commands = [
        "git commit", "git log", "git show", "git config",
        "git remote", "git branch", "git tag", "git status",
        "git diff", "git push", "git pull", "git fetch"
    ]
    cmd_stripped = cmd.strip()
    return any(cmd_stripped.startswith(gc) for gc in git_metadata_commands)




def load_restricted_rules_single(restricted_path: str, debug_enabled: bool = False) -> List[Rule]:
    """Load and parse rules from a single restricted.txt file (no context adjustment)."""
    rules = []
    if not (restricted_path and os.path.exists(restricted_path)):
        debug_log("DEBUG", "guard_restricted", f"File does not exist: {restricted_path}")
        return rules

    try:
        with open(restricted_path, "r", encoding="utf-8") as f:
            line_count = 0
            comment_count = 0
            blank_count = 0

            for line in f:
                raw = line.rstrip("\n")
                s = raw.strip()

                if not s:
                    blank_count += 1
                    continue

                if s.startswith("#"):
                    comment_count += 1
                    continue

                line_count += 1

                # Handle negation
                neg = False
                if s.startswith("\\!"):
                    s = s[1:]  # literal !
                elif s.startswith("!"):
                    neg = True
                    s = s[1:].lstrip()

                # Handle directory-only patterns
                dir_only = s.endswith("/")
                if dir_only:
                    s = s.rstrip("/")

                # Handle anchored patterns (start with /)
                anchored = s.startswith("/")
                if anchored:
                    s = s.lstrip("/")

                # Store POSIX-like pattern
                rules.append(Rule(original=raw, pattern=s, neg=neg, anchored=anchored, dir_only=dir_only))

            if line_count == 0:
                debug_log("WARNING", "guard_restricted",
                          f"File {restricted_path} contains no valid rules "
                          f"({blank_count} blank lines, {comment_count} comments)")

    except Exception as e:
        # If we cannot read it, fail open (do not block)
        debug_log("ERROR", "guard_restricted", f"Could not read {restricted_path}: {e}")
        return []

    return rules


def load_restricted_rules_multi(project_root: str, debug_enabled: bool = False) -> List[Rule]:
    """Load and merge rules from all restricted.txt files with context-aware adjustment and caching."""
    try:
        debug_log("DEBUG", "guard_restricted", "Searching for restricted.txt files...")

        # Get timeout from environment variable (default 1.0 second)
        timeout = float(os.environ.get('CLAUDE_RESTRICTED_DISCOVERY_TIMEOUT', '1.0'))

        # Step 1: Discover restricted.txt files with timeout protection
        try:
            restricted_files = find_all_restricted_files(
                project_root,
                debug_enabled=debug_enabled,
                timeout=timeout
            )
        except DiscoveryTimeoutError as e:
            # Log detailed timeout diagnostic information
            debug_log("ERROR", "guard_restricted",
                     f"Timeout during restricted.txt discovery: {str(e)}")
            debug_log("ERROR", "guard_restricted",
                     f"  Timeout limit: {e.timeout}s")
            debug_log("ERROR", "guard_restricted",
                     f"  Elapsed time: {e.elapsed:.2f}s")
            debug_log("ERROR", "guard_restricted",
                     f"  Directories scanned: {e.dirs_scanned}")
            debug_log("ERROR", "guard_restricted",
                     f"  Last directory: {e.current_dir}")
            debug_log("ERROR", "guard_restricted",
                     f"  Files found before timeout: {e.files_found}")
            debug_log("ERROR", "guard_restricted",
                     "FAIL-SAFE: Blocking all operations due to discovery timeout")
            debug_log("ERROR", "guard_restricted",
                     f"To resolve: Add slow directories to SKIP_DIRS in guard_restricted.py "
                     f"or increase timeout with CLAUDE_RESTRICTED_DISCOVERY_TIMEOUT env var")

            # Fail-safe: return empty list to block operations
            return []

        if not restricted_files:
            # Fallback to single file at root for backward compatibility
            try:
                single_file = os.path.join(project_root, "restricted.txt")
                if os.path.exists(single_file):
                    restricted_files = [(single_file, "")]
            except Exception as e:
                debug_log("ERROR", "guard_restricted", f"Fallback file check failed: {e}")
                # Continue with empty restricted_files

        if not restricted_files:
            debug_log("WARNING", "guard_restricted", "No restricted.txt found - file protection NOT active")
            return []

        debug_log("DEBUG", "guard_restricted", f"Found {len(restricted_files)} restricted.txt file(s):")
        for abs_path, rel_dir in restricted_files:
            context = f"(context: {rel_dir})" if rel_dir else "(root)"
            debug_log("DEBUG", "guard_restricted", f"  - {abs_path} {context}")

        # Step 2: Try cache with validation
        cached_rules = load_cached_rules(project_root, restricted_files, debug_enabled)
        if cached_rules is not None:
            debug_log("DEBUG", "guard_restricted", f"Cache hit - loaded {len(cached_rules)} rules from cache")
            return cached_rules  # Cache hit - fast path (~12ms total)

        debug_log("DEBUG", "guard_restricted", "Cache miss - building rules from scratch")

        # Step 3: Cache miss - build from scratch
        merged_rules = []

        # Load and adjust rules from each file
        for abs_path, rel_dir in restricted_files:
            debug_log("DEBUG", "guard_restricted", f"Loading rules from {abs_path}")

            # Load raw rules from file
            raw_rules = load_restricted_rules_single(abs_path, debug_enabled)

            debug_log("DEBUG", "guard_restricted", f"  Loaded {len(raw_rules)} raw rules")

            # Adjust each rule for its context
            for rule in raw_rules:
                adjusted_pattern = adjust_pattern_for_context(rule.pattern, rel_dir)

                # Create new rule with adjusted pattern and source tracking
                adjusted_rule = Rule(
                    original=rule.original,
                    pattern=adjusted_pattern,
                    neg=rule.neg,
                    anchored=rule.anchored,
                    dir_only=rule.dir_only,
                    source_file=abs_path
                )
                merged_rules.append(adjusted_rule)

        if not merged_rules:
            debug_log("WARNING", "guard_restricted",
                      f"Found {len(restricted_files)} restricted.txt file(s) but no valid rules - file protection NOT active")

        # Step 4: Save to cache for next time
        save_cached_rules(project_root, restricted_files, merged_rules, debug_enabled)

        return merged_rules

    except Exception as e:
        debug_log("ERROR", "guard_restricted", f"Critical error in load_restricted_rules_multi: {e}")
        debug_log("WARNING", "guard_restricted", "File protection NOT active due to critical error")
        return []


def rule_matches(rule: Rule, rel_posix: str, is_dir: bool) -> bool:
    """Check if a rule matches the given path with case-insensitive comparison"""
    # Always normalize both path and pattern to lowercase for consistent security
    # This prevents case-based bypass attempts on all platforms
    rel_posix_lower = rel_posix.lower()

    if rule.dir_only:
        # Directory-only rule (ends with /) matches:
        # 1. The directory itself
        # 2. Any files/dirs inside that directory
        dir_pattern_lower = rule.pattern.lower()

        if rule.anchored:
            # Anchored pattern like "/config/" matches "config/" and "config/file.txt"
            if rel_posix_lower == dir_pattern_lower or rel_posix_lower.startswith(dir_pattern_lower + "/"):
                return True
        else:
            # Unanchored pattern like "secrets/" matches "secrets/", "path/secrets/", "secrets/file.txt", "path/secrets/file.txt"
            # Check if path starts with the directory pattern
            if rel_posix_lower.startswith(dir_pattern_lower + "/") or rel_posix_lower == dir_pattern_lower:
                return True
            # Check if any part of the path matches (e.g., "nested/secrets/file.txt")
            path_parts = rel_posix_lower.split("/")
            for i, part in enumerate(path_parts):
                if fnmatch.fnmatch(part, dir_pattern_lower):
                    # Found matching directory, check if there are more parts after it
                    if i < len(path_parts) - 1:  # There are more parts, so this is inside the directory
                        return True
                    elif is_dir:  # This is the directory itself
                        return True
        return False

    # Regular pattern matching (not directory-only)
    pat_lower = rule.pattern.lower()
    if rule.anchored:
        return fnmatch.fnmatch(rel_posix_lower, pat_lower)
    else:
        # For unanchored patterns, check if pattern matches any part or the whole path
        if fnmatch.fnmatch(rel_posix_lower, pat_lower):
            return True
        # Also check if the pattern matches just the filename
        filename = rel_posix_lower.split("/")[-1]
        return fnmatch.fnmatch(filename, pat_lower)


def commonpath_is_parent(child: str, parent: str) -> bool:
    """Check if parent is a parent directory of child"""
    try:
        return os.path.commonpath([child, parent]) == parent
    except Exception:
        return False


def to_abs_real(candidate: str, cwd_real: str) -> str:
    """Convert path to absolute real path"""
    if candidate.startswith("~"):
        candidate = os.path.expanduser(candidate)
    if not os.path.isabs(candidate):
        candidate = os.path.abspath(os.path.join(cwd_real, candidate))
    return os.path.realpath(candidate)


def looks_like_path_token(tok: str) -> bool:
    """Check if a token looks like a file path"""
    if tok in (".", ".."):
        return True
    if tok.startswith(("~/", "./", "../", "/")):
        return True
    if "/" in tok:
        return True
    # Also consider glob patterns as path tokens
    if "*" in tok or "?" in tok:
        return True
    # Consider file extensions as potential paths
    if "." in tok and not tok.startswith("-") and len(tok.split(".")) == 2:
        return True
    return False


def collect_explicit_paths(tool: str, tool_input: dict, cwd_real: str) -> List[Tuple[str, str]]:
    """Collect file paths that the tool might access"""
    paths = set()

    # File operation commands where non-flag arguments are likely paths
    FILE_OPS = {
        'ls', 'cat', 'less', 'more', 'head', 'tail', 'grep', 'find',
        'rm', 'mv', 'cp', 'chmod', 'chown', 'touch', 'mkdir', 'rmdir',
        'cd', 'stat', 'file', 'du', 'df', 'tree', 'rsync', 'tar', 'zip',
        'unzip', 'diff', 'wc', 'sort', 'cut', 'sed', 'awk', 'xargs'
    }

    def visit(obj, path_hint=False):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                hint = path_hint or any(h in kl for h in ("path", "file", "dir", "directory"))
                visit(v, hint)
        elif isinstance(obj, list):
            for v in obj:
                visit(v, path_hint)
        elif isinstance(obj, str) and path_hint:
            s = obj.strip()
            if s:
                paths.add(s)

    if tool == "Bash":
        cmd = (tool_input or {}).get("command", "")
        if not cmd:
            return []
        try:
            tokens = shlex.split(cmd)
        except Exception:
            tokens = cmd.split()

        # Check if this is a file operation command
        command_is_file_op = False
        if tokens:
            base_cmd = tokens[0].split('/')[-1]  # Handle paths like /usr/bin/ls
            command_is_file_op = base_cmd in FILE_OPS

        for i, tok in enumerate(tokens):
            # Skip the command itself and flags
            if i == 0 or tok.startswith("-"):
                continue

            # For file operations, treat all non-flag tokens as paths
            if command_is_file_op:
                paths.add(tok)
            # For other commands, use the heuristic
            elif looks_like_path_token(tok):
                paths.add(tok)
    else:
        visit(tool_input, False)

    # Resolve to absolute real paths, but keep original patterns for restriction checking
    abs_reals = []
    for p in sorted(paths):
        if "*" in p or "?" in p:
            # For glob patterns, use the pattern itself as both original and "resolved"
            # The rule matching will handle pattern vs pattern comparison
            abs_reals.append((p, p))
        else:
            abs_reals.append((p, to_abs_real(p, cwd_real)))
    return abs_reals


def check_bash_restricted_bypasses(command: str, rules: List[Rule], project_root: str) -> List[str]:
    """Check bash command for bypass attempts against restricted.txt patterns."""
    violations = []

    # Extract patterns from rules for bypass detection
    restricted_patterns = []
    for rule in rules:
        if not rule.neg:  # Only check against blocking rules, not negation rules
            restricted_patterns.append(rule.pattern)

    if not restricted_patterns:
        return violations

    # Check for variable indirection bypasses
    variable_bypasses = detect_variable_indirection_bypass(command, restricted_patterns)
    for bypass in variable_bypasses:
        violations.append(f"Restricted file bypass detected: {bypass}")

    # Check for glob expansion bypasses
    glob_bypasses = detect_glob_expansion_bypass(command, project_root, restricted_patterns)
    for bypass in glob_bypasses:
        violations.append(f"Restricted file bypass via glob: {bypass}")

    # Check for partial construction bypasses
    construction_bypasses = detect_partial_construction_bypass(command, restricted_patterns)
    for bypass in construction_bypasses:
        violations.append(f"Restricted file bypass via path construction: {bypass}")

    return violations


def main():
    """Main hook execution - validate tool operations for restricted file access"""
    debug_enabled = parse_debug_flag()

    # Check if running in container - hooks auto-disable in containers
    if is_container_environment():
        debug_log("INFO", "guard_restricted",
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

    # Get project directory from security configuration (not CWD)
    try:
        proj_real = get_project_root_from_config()
    except SecurityConfigError as e:
        deny(f"Security configuration error: {e}. All operations blocked until security-config.json is properly configured.")

    # Initialize debug logging with session ID and project root
    session_id = data.get('session_id', 'unknown')
    if debug_enabled:
        init_debug_log(session_id, proj_real)
        tool_name = data.get('tool_name', 'unknown')
        cwd = data.get('cwd', 'unknown')
        debug_log("DEBUG", "guard_restricted", f"Hook started - Tool: {tool_name}, CWD: {cwd}")

    # Check if tool needs validation
    tool_name = data.get('tool_name', '')
    if not is_relevant_tool(tool_name):
        debug_log("DEBUG", "guard_restricted", f"Tool '{tool_name}' does not require validation - skipping")
        sys.exit(0)

    debug_log("DEBUG", "guard_restricted", f"Project root: {proj_real}")

    cwd_real = os.path.realpath(data.get("cwd") or os.getcwd())
    tool_input = data.get('tool_input', {}) or {}

    # Load restricted rules from all restricted.txt files
    rules = load_restricted_rules_multi(proj_real, debug_enabled)

    debug_log("DEBUG", "guard_restricted", f"Loaded {len(rules)} restriction rules")

    # If no restricted.txt file or no rules, perform comprehensive validation only
    violations = []

    # Always perform comprehensive security validation first
    if tool_name == 'Bash':
        command = tool_input.get('command', '')
        if command:
            # NEW: Check for git metadata commands early in bash processing
            if is_git_metadata_command(command):
                # Skip all path-based security checks for git metadata commands
                # but still perform basic security validation from security_core
                # Skip dynamic pattern analysis for git commands as they work with repo metadata
                valid, reason = validate_bash_command_advanced(command, proj_real, skip_dynamic_analysis=True)
                if not valid:
                    # Even git commands can't do system directory traversal
                    deny(reason)
                sys.exit(0)  # Allow git metadata operations

            # Extract patterns from rules for enhanced validation
            restricted_patterns = []
            for rule in rules:
                if not rule.neg:  # Only blocking rules, not negation rules
                    restricted_patterns.append(rule.pattern)

            # Regular bash command validation with restricted patterns
            valid, reason = validate_bash_command_advanced(command, proj_real, additional_restricted_patterns=restricted_patterns)
            if not valid:
                violations.append(reason)

            # Enhanced restricted.txt bypass detection for bash commands
            bypass_violations = check_bash_restricted_bypasses(command, rules, proj_real)
            violations.extend(bypass_violations)
    else:
        # Handle file-based tools using comprehensive path extraction
        file_paths = extract_file_paths_comprehensive(tool_name, tool_input, cwd_real)

        for path in file_paths:
            # Check if accessing protected files
            if is_protected_file(path, proj_real):
                violations.append(f"Access denied: Attempted access to protected security file '{path}' is not allowed.")
                continue

            # Comprehensive path validation
            valid, reason = validate_path_comprehensive(path, proj_real)
            if not valid:
                violations.append(reason)

    # If no restricted rules, just do comprehensive validation
    if not rules:
        if violations:
            reason = "Security policy violations:\n- " + "\n- ".join(violations)
            deny(reason)
        sys.exit(0)

    # Collect candidate paths for restricted.txt validation
    candidates = collect_explicit_paths(tool_name, tool_input, cwd_real)

    if not candidates:
        # No paths to validate against restricted.txt, but check basic violations
        if violations:
            reason = "Security policy violations:\n- " + "\n- ".join(violations)
            deny(reason)
        sys.exit(0)

    # Check candidates against restricted rules
    blocked = []
    for raw, abs_real in candidates:
        # Handle glob patterns differently
        if "*" in raw or "?" in raw:
            # For glob patterns, check if the pattern itself matches any restricted pattern
            matched = None
            allow = True
            for r in rules:
                # Check if the glob pattern matches the restricted pattern (case-insensitive)
                raw_lower = raw.lower()
                pattern_lower = r.pattern.lower()
                if not r.dir_only and fnmatch.fnmatch(raw_lower, pattern_lower):
                    matched = r
                    allow = r.neg
                # Also check if any file matching this glob would be restricted (case-insensitive)
                elif pattern_lower in raw_lower or fnmatch.fnmatch(raw_lower, "*" + pattern_lower + "*"):
                    matched = r
                    allow = r.neg

            if matched and not allow:
                blocked.append((raw, raw, matched.original, matched.source_file))
            continue

        # Regular path handling
        # Only consider paths under current working directory for non-glob patterns
        if abs_real != raw and not commonpath_is_parent(abs_real, cwd_real):
            continue

        # Get relative path to project root for pattern matching
        try:
            # Distinguish between glob patterns and real paths
            # Glob patterns contain wildcards and should be kept as-is
            # Real paths (absolute or relative) must be converted to relative for pattern matching
            is_glob_pattern = "*" in raw or "?" in raw

            if is_glob_pattern and abs_real == raw:
                # This is a pattern, not a resolved path - use as-is
                rel_posix = raw
                is_dir = False
            else:
                # Always convert real paths (including absolute paths) to relative
                rel = os.path.relpath(abs_real, proj_real)
                rel_posix = to_posix(rel)
                is_dir = os.path.isdir(abs_real)
        except ValueError:
            # If path is not under project dir, skip (basic validation should have caught this)
            continue

        # Check against all rules (last match wins)
        matched = None
        allow = True  # default: allow unless matched by a blocking rule
        for r in rules:
            if rule_matches(r, rel_posix, is_dir):
                matched = r
                allow = r.neg  # negation flips to allow

        if matched and not allow:
            blocked.append((raw, abs_real, matched.original, matched.source_file))

    # Combine violations
    if blocked:
        # Add restricted.txt violations with clear messaging
        if len(blocked) == 1:
            raw, resolved, rule, source_file = blocked[0]
            source_info = ""
            if source_file:
                rel_source = os.path.relpath(source_file, proj_real)
                source_info = f" (from {rel_source})"
            violations.append(f"Access denied: Trying to access a restricted file '{raw}' blocked by rule: {rule}{source_info}")
        else:
            lines = ["Access denied: Trying to access restricted files:"]
            for i, (raw, resolved, rule, source_file) in enumerate(blocked[:5], start=1):
                source_info = ""
                if source_file:
                    rel_source = os.path.relpath(source_file, proj_real)
                    source_info = f" (from {rel_source})"
                lines.append(f"  {i}. '{raw}' blocked by rule: {rule}{source_info}")

            if len(blocked) > 5:
                lines.append(f"  ... and {len(blocked) - 5} more")

            violations.append("\n".join(lines))

    # Deny if any violations found
    if violations:
        reason = "Security policy violations:\n- " + "\n- ".join(violations)
        deny(reason)

    # Allow operation
    sys.exit(0)


if __name__ == "__main__":
    main()