#!/usr/bin/env python3
"""
Recursive Security Hooks Update Script.

Automatically discovers and updates all .claude folders in complex project hierarchies
by cloning the latest security hooks from GitLab and intelligently merging configurations
using git's three-way merge algorithm.

This script handles monorepo structures with dozens of .claude folders independently,
providing clear progress reporting and isolated error handling per folder.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, NamedTuple, Dict, Optional

from security_update_core import SecurityUpdateCore, MergeResult

# Optional import with fallback for bootstrap scenarios
try:
    from version_utils import get_version_from_file, parse_changelog_entries
    VERSION_UTILS_AVAILABLE = True
except ImportError:
    VERSION_UTILS_AVAILABLE = False

    def get_version_from_file(version_file):
        """Fallback when version_utils is not available."""
        return None

    def parse_changelog_entries(changelog_file, version):
        """Fallback when version_utils is not available."""
        return []


class UpdateResult(NamedTuple):
    """Result of updating a single .claude folder."""
    folder_path: Path
    success: bool
    has_conflicts: bool
    copied_files: List[str]
    error_message: Optional[str] = None


class BatchResult(NamedTuple):
    """Result of batch updating multiple .claude folders."""
    total_folders: int
    successful_updates: int
    folders_with_conflicts: int
    failed_updates: int
    results: List[UpdateResult]


def find_project_root_from_script() -> Path:
    """Find project root from the current script location.

    This script should be located at PROJECT_ROOT/.claude/update-tools/update_security_hooks.py
    So we go up 2 levels to find the project root.

    Returns:
        Path to the project root directory
    """
    script_path = Path(__file__).resolve()
    # Go up: update_security_hooks.py -> update-tools -> .claude -> PROJECT_ROOT
    return script_path.parent.parent.parent


def get_project_root_from_security_config(claude_path: Path) -> Optional[Path]:
    """Extract project root from security-config.json.

    Args:
        claude_path: Path to .claude directory

    Returns:
        Path to project root or None if cannot be determined
    """
    security_config = claude_path / "security-config.json"

    if not security_config.exists():
        return None

    try:
        with open(security_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        project_root = config.get("project_root", "")

        # Check if still using template value
        if project_root == "TEMPLATE_PROJECT_ROOT_REPLACE_WITH_YOUR_PROJECT_PATH":
            return None

        if project_root and Path(project_root).exists():
            return Path(project_root)

    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        pass

    return None


def validate_security_config_template(claude_path: Path) -> bool:
    """Check if security-config.json is still using template values.

    Args:
        claude_path: Path to .claude directory

    Returns:
        True if using template values, False otherwise
    """
    security_config = claude_path / "security-config.json"

    if not security_config.exists():
        return False

    try:
        with open(security_config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        project_root = config.get("project_root", "")
        return project_root == "TEMPLATE_PROJECT_ROOT_REPLACE_WITH_YOUR_PROJECT_PATH"

    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return False


def discover_claude_folders(root_path: Path) -> List[Path]:
    """Recursively discover all .claude directories in project hierarchy.

    Args:
        root_path: Root directory to search from

    Returns:
        Sorted list of all .claude directory paths
    """
    claude_dirs = []

    # Use Path.rglob() to find all .claude directories
    # Convert generator to list for multiple iterations
    for path in root_path.rglob(".claude"):
        if path.is_dir():
            claude_dirs.append(path)

    return sorted(claude_dirs)  # Consistent processing order


def clone_repository(temp_dir: Path, branch: Optional[str] = None) -> Optional[Path]:
    """Clone GitLab repository and return path to .claude.example.

    Args:
        temp_dir: Temporary directory to clone into
        branch: Git branch to clone from (default: None for default branch)

    Returns:
        Path to .claude.example directory or None if clone failed
    """
    repo_url = "git@gitlab.innogames.de:ai-taskforce/claude-code-base.git"
    clone_path = temp_dir / "claude-code-base"

    try:
        clone_cmd = ["git", "clone", "--depth", "1"]
        if branch:
            clone_cmd.extend(["--branch", branch])
        clone_cmd.extend([repo_url, str(clone_path)])

        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"Error cloning repository: {result.stderr}")
            return None

        claude_example_path = clone_path / ".claude.example"
        if not claude_example_path.exists():
            print(f"Error: .claude.example not found in cloned repository")
            return None

        return claude_example_path

    except subprocess.TimeoutExpired:
        print("Error: Repository clone timed out")
        return None
    except Exception as e:
        print(f"Error cloning repository: {str(e)}")
        return None


def update_folder_security(source_dir: Path, dest_dir: Path, core: SecurityUpdateCore, is_root_folder: bool = False) -> UpdateResult:
    """Apply security updates to single .claude folder using shared core logic.

    Args:
        source_dir: Source .claude.example directory
        dest_dir: Destination .claude directory to update
        core: SecurityUpdateCore instance for shared functionality
        is_root_folder: Whether this is the root .claude folder (affects file selection)

    Returns:
        UpdateResult with success status and details
    """
    try:
        # For subfolders, remove ROOT_ONLY files if they exist from older versions
        removed_files = []
        if not is_root_folder:
            removed_files = core.remove_root_only_files(dest_dir)
            if removed_files:
                print(f"  🧹 Cleaned up {len(removed_files)} root-only file(s)")

        # Copy appropriate files based on folder type
        file_category = "all" if is_root_folder else "universal"
        copied_files = core.copy_security_files(source_dir, dest_dir, file_category)

        # Handle settings.json with intelligent three-way merge
        current_settings = dest_dir / "settings.json"
        new_settings = source_dir / "settings.json"
        has_conflicts = False

        if current_settings.exists() and new_settings.exists():
            # Create empty base file for three-way merge
            base_file = core.create_empty_base_file()

            try:
                merge_result = core.merge_settings_json(current_settings, base_file, new_settings)

                if not merge_result.success:
                    return UpdateResult(
                        folder_path=dest_dir,
                        success=False,
                        has_conflicts=False,
                        copied_files=copied_files,
                        error_message=merge_result.error_message
                    )

                has_conflicts = merge_result.has_conflicts

            finally:
                # Clean up temporary base file
                if base_file.exists():
                    base_file.unlink()

        # Handle settings.local.json preserving permissions
        source_local_settings = source_dir / "settings.local.json"
        dest_local_settings = dest_dir / "settings.local.json"

        if source_local_settings.exists():
            core.merge_settings_local(source_local_settings, dest_local_settings)

        return UpdateResult(
            folder_path=dest_dir,
            success=True,
            has_conflicts=has_conflicts,
            copied_files=copied_files
        )

    except Exception as e:
        return UpdateResult(
            folder_path=dest_dir,
            success=False,
            has_conflicts=False,
            copied_files=[],
            error_message=str(e)
        )


def batch_update_folders(claude_folders: List[Path], source_dir: Path, project_root: Path) -> BatchResult:
    """Orchestrate updates across all discovered folders with independent error handling.

    Args:
        claude_folders: List of .claude directories to update
        source_dir: Source .claude.example directory
        project_root: Project root directory for detecting root folder

    Returns:
        BatchResult with summary of all update operations
    """
    core = SecurityUpdateCore()
    results = []
    successful_updates = 0
    folders_with_conflicts = 0
    failed_updates = 0

    # Determine root .claude folder
    root_claude_folder = project_root / ".claude"

    # Display version information with bootstrap awareness
    if not VERSION_UTILS_AVAILABLE:
        print(f"\n⚠️  Bootstrap Mode Active:")
        print(f"   Version utilities are not yet available.")
        print(f"   The update will download required files.")
        print(f"   Please run this script AGAIN after completion for full functionality.\n")
    else:
        new_version_file = source_dir / "VERSION"
        new_version = get_version_from_file(new_version_file)

        # Try to detect current version from first folder
        current_version = None
        if claude_folders:
            current_version_file = claude_folders[0] / "VERSION"
            current_version = get_version_from_file(current_version_file)

        print(f"\n📦 Version Information:")
        if current_version:
            print(f"  Current version: v{current_version}")
        else:
            print(f"  Current version: unknown (pre-versioning)")

        if new_version:
            print(f"  New version: v{new_version}")
        else:
            print(f"  New version: unknown")

    print(f"\nUpdating {len(claude_folders)} .claude folders...")

    for i, folder in enumerate(claude_folders, 1):
        print(f"[{i}/{len(claude_folders)}] Updating {folder}")

        # Detect if this is the root folder
        is_root_folder = folder.resolve() == root_claude_folder.resolve()

        if is_root_folder:
            print(f"  📍 Root folder - copying all files")
        else:
            print(f"  📁 Subfolder - copying universal files only")

        # Process each folder independently - failures don't block others
        result = update_folder_security(source_dir, folder, core, is_root_folder)
        results.append(result)

        if result.success:
            if result.has_conflicts:
                folders_with_conflicts += 1
                print(f"  ⚠ Updated with conflicts - manual resolution needed")
            else:
                successful_updates += 1
                print(f"  ✓ Updated successfully ({len(result.copied_files)} files)")
        else:
            failed_updates += 1
            print(f"  ✗ Failed: {result.error_message}")

    return BatchResult(
        total_folders=len(claude_folders),
        successful_updates=successful_updates,
        folders_with_conflicts=folders_with_conflicts,
        failed_updates=failed_updates,
        results=results
    )


def handle_conflicts(batch_result: BatchResult) -> None:
    """Provide guidance for resolving merge conflicts.

    Args:
        batch_result: Result of batch update operation
    """
    if batch_result.folders_with_conflicts == 0:
        return

    print(f"\n🚨 {batch_result.folders_with_conflicts} folders have merge conflicts:")

    for result in batch_result.results:
        if result.success and result.has_conflicts:
            settings_file = result.folder_path / "settings.json"
            print(f"  - {settings_file}")

    print(f"\nTo resolve conflicts:")
    print(f"1. Edit each settings.json file above")
    print(f"2. Look for conflict markers: <<<< ==== >>>>")
    print(f"3. Choose the desired configuration and remove markers")
    print(f"4. Re-run this script to verify clean merges")


def main():
    """Main entry point for the update script."""
    parser = argparse.ArgumentParser(
        description="Recursively update security hooks in all .claude folders"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Root directory to search for .claude folders (default: auto-detect from script location or security-config.json)"
    )
    parser.add_argument(
        "--branch",
        type=str,
        help="Git branch to clone from (default: master)"
    )

    args = parser.parse_args()

    try:
        # Determine project root
        project_root = None

        if args.root:
            # User explicitly provided root
            project_root = args.root
        else:
            # Try to auto-detect project root
            script_root = find_project_root_from_script()
            script_claude_path = script_root / ".claude"

            # First, check if we have a valid security-config.json
            if script_claude_path.exists():
                # Validate if security-config.json has template values
                if validate_security_config_template(script_claude_path):
                    print("⚠️  WARNING: security-config.json still contains template values!")
                    print(f"   Please update the project_root in: {script_claude_path / 'security-config.json'}")
                    print(f"   Change 'TEMPLATE_PROJECT_ROOT_REPLACE_WITH_YOUR_PROJECT_PATH' to: {script_root}")
                    print("   Then run this script again.\n")
                    sys.exit(1)

                # Try to get project root from security-config.json
                config_root = get_project_root_from_security_config(script_claude_path)
                if config_root:
                    project_root = config_root
                else:
                    # Fall back to script location
                    project_root = script_root
            else:
                # No .claude folder found, use script location
                project_root = script_root

        print(f"🔍 Using project root: {project_root}")

        # Discovery phase
        print("🔍 Discovering .claude folders...")
        claude_folders = discover_claude_folders(project_root)

        if not claude_folders:
            print("No .claude folders found with required structure (settings.json, hooks/ directory)")
            return

        print(f"Found {len(claude_folders)} .claude folders:")
        for folder in claude_folders:
            print(f"  - {folder}")

        # Repository phase
        branch_info = f" (branch: {args.branch})" if args.branch else ""
        print(f"\n📥 Cloning security hooks repository{branch_info}...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_dir = clone_repository(temp_path, args.branch)

            if not source_dir:
                print("Failed to clone repository. Check network connection and access permissions.")
                sys.exit(1)

            print(f"Repository cloned to: {source_dir}")

            # Batch update phase
            print(f"\n🔄 Processing updates...")
            batch_result = batch_update_folders(claude_folders, source_dir, project_root)

        # Results summary
        print(f"\n📊 Update Summary:")
        print(f"  Total folders processed: {batch_result.total_folders}")
        print(f"  Successful updates: {batch_result.successful_updates}")
        print(f"  Folders with conflicts: {batch_result.folders_with_conflicts}")
        print(f"  Failed updates: {batch_result.failed_updates}")

        # Display changelog for new version (only if VERSION_UTILS_AVAILABLE)
        if VERSION_UTILS_AVAILABLE and (batch_result.successful_updates > 0 or batch_result.folders_with_conflicts > 0):
            new_version_file = source_dir / "VERSION"
            new_version = get_version_from_file(new_version_file)

            if new_version:
                changelog_file = source_dir / "security-hooks-changelog.md"
                entries = parse_changelog_entries(changelog_file, new_version)

                if entries:
                    print(f"\n📝 What's New in v{new_version}:")
                    print("─" * 60)
                    for entry in entries:
                        print(f"  {entry}")
                    print("─" * 60)

        # Handle conflicts if any
        handle_conflicts(batch_result)

        # Next steps with bootstrap awareness
        if batch_result.successful_updates > 0 or batch_result.folders_with_conflicts > 0:
            print(f"\n✅ Next Steps:")
            if not VERSION_UTILS_AVAILABLE:
                print(f"1. Run this script AGAIN to activate version features:")
                print(f"   python3 .claude/update-tools/update_security_hooks.py")
                print(f"2. After second run, restart Claude Code for changes to take effect")
                print(f"3. Run '/check-security-setup' in each project folder to verify")
            else:
                print(f"1. Restart Claude Code for changes to take effect")
                print(f"2. Run '/check-security-setup' in each project folder to verify")

        # Exit with appropriate code
        if batch_result.failed_updates > 0:
            sys.exit(1)
        elif batch_result.folders_with_conflicts > 0:
            sys.exit(2)  # Conflicts need manual resolution

    except KeyboardInterrupt:
        print(f"\n⏹ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()