#!/usr/bin/env python3
"""
Shared core functionality for security hooks updates.

This module provides common functionality used by both deploy.py and update_security_hooks.py
for copying security files, merging configurations, and managing settings updates.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, NamedTuple, List, Optional


class MergeResult(NamedTuple):
    """Result of a merge operation."""
    success: bool
    has_conflicts: bool
    error_message: Optional[str] = None


class SecurityUpdateCore:
    """Shared functionality for security hooks updates."""

    # Files that MUST be in every .claude folder for hooks to function
    UNIVERSAL_FILES = [
        "settings.json",
        "security-config.json",
        "hooks/guard_essential.py",
        "hooks/guard_restricted.py",
        "hooks/security_core.py",
        "secret_filter.js",
    ]

    # Files that should ONLY be at the project root .claude folder
    ROOT_ONLY_FILES = [
        "VERSION",
        "security-hooks-changelog.md",
        "commands/check-security-setup.md",
        "test-data/test-secret.txt",
        "update-tools/version_utils.py",
        "update-tools/security_update_core.py",
        "update-tools/update_security_hooks.py"
    ]

    # Legacy: Combined list for backward compatibility
    SECURITY_FILES = [
        "settings.json",
        "security-config.json",
        "hooks/guard_essential.py",
        "hooks/guard_restricted.py",
        "hooks/security_core.py",
        "secret_filter.js",
        "VERSION",
        "security-hooks-changelog.md",
        "commands/check-security-setup.md",
        "test-data/test-secret.txt",
        "update-tools/version_utils.py",
        "update-tools/security_update_core.py",
        "update-tools/update_security_hooks.py"
    ]

    def remove_root_only_files(self, dest_dir: Path) -> List[str]:
        """Remove ROOT_ONLY files from destination if they exist.

        Used to clean up subfolders that may have these files from older versions.

        Args:
            dest_dir: Directory to clean up ROOT_ONLY files from

        Returns:
            List of successfully removed file paths
        """
        removed_files = []
        for file_path in self.ROOT_ONLY_FILES:
            dest_file = dest_dir / file_path
            if dest_file.exists():
                try:
                    dest_file.unlink()
                    removed_files.append(file_path)
                    # Clean up empty directories
                    parent = dest_file.parent
                    if parent != dest_dir and not any(parent.iterdir()):
                        parent.rmdir()
                except Exception:
                    # Continue removing other files even if one fails
                    continue
        return removed_files

    def copy_security_files(self, source_dir: Path, dest_dir: Path, file_category: str = "all") -> List[str]:
        """Copy security files from source to destination preserving structure.

        Args:
            source_dir: Source directory containing security files
            dest_dir: Destination directory to copy files to
            file_category: Which files to copy - "all", "universal", or "root_only"

        Returns:
            List of successfully copied file paths

        Raises:
            ValueError: If file_category is not valid
        """
        # Select files based on category
        if file_category == "all":
            files_to_copy = self.SECURITY_FILES
        elif file_category == "universal":
            files_to_copy = self.UNIVERSAL_FILES
        elif file_category == "root_only":
            files_to_copy = self.ROOT_ONLY_FILES
        else:
            raise ValueError(f"Invalid file_category: {file_category}. Must be 'all', 'universal', or 'root_only'")

        copied_files = []
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file_path in files_to_copy:
            source_file = source_dir / file_path
            if not source_file.exists():
                continue

            dest_file = dest_dir / file_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Skip copying security-config.json if it already exists to preserve user configuration
            if file_path == "security-config.json" and dest_file.exists():
                continue

            try:
                shutil.copy2(source_file, dest_file)
                copied_files.append(file_path)
            except Exception:
                # Continue copying other files even if one fails
                continue

        return copied_files

    def merge_settings_json(self, current: Path, base: Path, new: Path) -> MergeResult:
        """Git merge-file three-way merge for settings.json with conflict detection.

        Args:
            current: User's current settings.json file
            base: Base file for three-way merge (empty for new merges)
            new: New security hooks settings from repository

        Returns:
            MergeResult with success status and conflict information
        """
        try:
            # Use git merge-file for intelligent three-way merging
            result = subprocess.run([
                "git", "merge-file",
                str(current),  # User's current settings.json
                str(base),     # Base (original state)
                str(new)       # New security hooks from repository
            ], capture_output=True, text=True, timeout=10)

            # Exit code interpretation:
            # 0: Clean merge - settings updated automatically
            # 1-127: Conflicts present - conflict markers added to file
            # 255: Git error - merge failed

            if result.returncode == 0:
                return MergeResult(success=True, has_conflicts=False)
            elif 1 <= result.returncode <= 127:
                return MergeResult(success=True, has_conflicts=True)
            else:
                return MergeResult(
                    success=False,
                    has_conflicts=False,
                    error_message=f"Git merge failed with exit code {result.returncode}: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            return MergeResult(
                success=False,
                has_conflicts=False,
                error_message="Git merge timed out"
            )
        except Exception as e:
            return MergeResult(
                success=False,
                has_conflicts=False,
                error_message=f"Git merge error: {str(e)}"
            )

    def merge_settings_local(self, source_file: Path, dest_file: Path) -> None:
        """Merge settings.local.json preserving existing permissions.

        This preserves the existing permissions arrays (allow/deny/ask) from the destination
        while merging in any new configuration from the source.

        Args:
            source_file: Source settings.local.json file
            dest_file: Destination settings.local.json file to merge into
        """
        source_data = {}
        if source_file.exists():
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)
            except (json.JSONDecodeError, PermissionError, FileNotFoundError):
                source_data = {}

        dest_data = {}
        if dest_file.exists():
            try:
                with open(dest_file, 'r', encoding='utf-8') as f:
                    dest_data = json.load(f)
            except (json.JSONDecodeError, PermissionError, FileNotFoundError):
                dest_data = {}

        # Merge permissions from both files
        merged_data = source_data.copy()

        if "permissions" in dest_data:
            if "permissions" not in merged_data:
                merged_data["permissions"] = {}

            for key in ["allow", "deny", "ask"]:
                if key in dest_data["permissions"]:
                    if key not in merged_data["permissions"]:
                        merged_data["permissions"][key] = []

                    # Merge arrays, removing duplicates
                    existing_items = set(merged_data["permissions"][key])
                    for item in dest_data["permissions"][key]:
                        if item not in existing_items:
                            merged_data["permissions"][key].append(item)

        # Ensure parent directory exists
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2)

    def create_empty_base_file(self) -> Path:
        """Create a temporary empty file for use as base in three-way merge.

        Returns:
            Path to temporary empty file
        """
        temp_file = Path(tempfile.mktemp(suffix='.json'))
        temp_file.write_text('{}')
        return temp_file