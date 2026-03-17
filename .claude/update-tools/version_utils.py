#!/usr/bin/env python3
"""Version management utilities for security hooks."""

from pathlib import Path
from typing import Optional, List, Tuple
import subprocess


def get_version_from_file(version_file: Path) -> Optional[str]:
    """Read version from VERSION file.

    Args:
        version_file: Path to VERSION file

    Returns:
        Version string (e.g., "0.2.0") or None if file doesn't exist
    """
    if not version_file.exists():
        return None

    try:
        return version_file.read_text().strip()
    except Exception:
        return None


def get_latest_git_tag(repo_path: Path) -> Optional[str]:
    """Get the latest git tag from repository.

    Args:
        repo_path: Path to git repository

    Returns:
        Latest tag (e.g., "v0.2.0") or None if no tags exist
    """
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "--sort=-version:refname"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            tags = result.stdout.strip().split('\n')
            return tags[0] if tags else None
    except Exception:
        pass
    return None


def get_commits_since_tag(repo_path: Path, tag: str) -> List[Tuple[str, str]]:
    """Get list of commits since specified tag.

    Args:
        repo_path: Path to git repository
        tag: Git tag to start from (e.g., "v0.2.0")

    Returns:
        List of (commit_hash, commit_message) tuples
    """
    commits = []
    try:
        result = subprocess.run(
            ["git", "log", f"{tag}..HEAD", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append((parts[0], parts[1]))
    except Exception:
        pass
    return commits


def parse_changelog_entries(changelog_path: Path, version: str) -> List[str]:
    """Extract changelog entries for a specific version.

    Args:
        changelog_path: Path to CHANGELOG.md file
        version: Version to extract entries for (e.g., "0.2.0")

    Returns:
        List of changelog entry lines for that version
    """
    if not changelog_path.exists():
        return []

    entries = []
    in_version_section = False

    try:
        content = changelog_path.read_text()
        for line in content.split('\n'):
            # Start of version section (e.g., "## [0.2.0]" or "## v0.2.0")
            if line.startswith('## ') and version in line:
                in_version_section = True
                continue

            # Next version section - stop collecting
            if in_version_section and line.startswith('## '):
                break

            # Collect lines in this version section
            if in_version_section and line.strip():
                entries.append(line)

    except Exception:
        pass

    return entries


def get_current_branch(repo_path: Path) -> Optional[str]:
    """Get current git branch name.

    Args:
        repo_path: Path to git repository

    Returns:
        Branch name or None if cannot determine
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None
