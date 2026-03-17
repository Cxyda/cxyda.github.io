# Security Hooks Changelog

All notable changes to the Claude Code Security Hooks will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.5] - 2026-01-19

### Added
- **Container Environment Auto-Disable**: Security hooks now automatically detect and disable themselves when running inside containers
  - Checks `DEVCONTAINER=true` environment variable (standard devcontainer marker)
  - Checks `CLAUDE_SECURITY_HOOKS_DISABLED=true` environment variable (explicit disable signal)
  - Falls back to `/.dockerenv` file detection for Docker containers
  - Short-circuit evaluation for optimal performance (< 1ms overhead)
  - Debug logging available with `--debug` flag to troubleshoot detection

### Changed
- Both `guard_essential.py` and `guard_restricted.py` now check for container environment at startup
- Added `is_container_environment()` function to `security_core.py` for centralized detection logic
- Host machine behavior unchanged - full security validation maintained outside containers

## [0.4.4] - 2025-12-04

### Changed
- **Smart File Distribution**: Update tool now only deploys necessary files to subfolder `.claude` directories
  - Root-only files (VERSION, changelog, update tools, commands) no longer copied to subfolders
  - Reduces clutter in multi-repository projects with nested .claude folders
  - Automatic cleanup of previously distributed unnecessary files during updates

### Fixed
- Multi-repository projects no longer have duplicate documentation files in every subfolder
- Subfolder .claude directories now contain only essential hooks and configuration files

## [0.4.3] - 2025-12-01

### Added
- **Timeout Protection**: Added 1-second timeout to restricted.txt discovery to prevent infinite hangs
  - New `DiscoveryTimeoutError` exception with diagnostic information
  - Configurable via `CLAUDE_RESTRICTED_DISCOVERY_TIMEOUT` environment variable
  - Fail-safe behavior: blocks all operations if timeout occurs
- **Enhanced Debug Logging**: Added detailed discovery progress logging when `--debug` flag is used
  - Logs each directory being scanned with timing information
  - Logs skip decisions and performance metrics
  - Logs timeout diagnostic information (directories scanned, last directory, files found)
- **Configurable Skip Directories**: Users can now customize skip directories via `skip_dirs.txt` file
  - Copy `.claude/skip_dirs.txt.example` to project root as `skip_dirs.txt`
  - Add custom directory names (one per line) to skip during discovery
  - Automatically merges with built-in skip directories
  - No need to edit Python code anymore

### Changed
- Renamed `SKIP_DIRS` to `BUILTIN_SKIP_DIRS` for clarity
- Skip directories now loaded dynamically via `load_skip_dirs()` function
- Enhanced error messages to guide users to resolution steps
- Removed redundant `if debug_enabled:` checks before `debug_log()` calls (optimization)

### Fixed
- Prevents infinite hangs during restricted.txt discovery on slow filesystems
- Provides actionable diagnostic information for performance issues

## [0.4.2] - 2025-11-27

### Added
- Debug mode support for troubleshooting hook execution issues
- Enable via `--debug` flag or `CLAUDE_HOOKS_DEBUG=1` environment variable
- Debug logs reveal when restricted.txt is missing, empty, or not loading properly
- Performance diagnostics show cache hits/misses and rule loading statistics
- Logs written to `.claude/tmp/log-{session_id}` files for post-session review

### Changed
- File discovery uses more reliable directory traversal to prevent hangs in deep trees

### Fixed
- Potential infinite loop when scanning deeply nested directories for restricted.txt files
- Silent failures during rule loading now logged with clear error messages

## [0.4.1] - 2025-11-20

### Fixed
- Update script now self-heals when version utilities are missing during installation
- Bootstrap mode displays clear warnings and guidance when dependencies need to be downloaded
- Script no longer crashes with ImportError during fresh installations or version transitions

### Changed
- Update script intelligently detects missing dependencies and prompts for a second run after downloading them
- Version and changelog information gracefully skipped during bootstrap mode

### What This Fixes
If you previously encountered `ModuleNotFoundError: No module named 'version_utils'` when running the update script, this release resolves that issue. The script now:
1. Runs successfully even when missing dependencies
2. Downloads required files automatically
3. Prompts you to run it again to activate full version features

## [0.4.0] - 2025-11-20

### Added
- Secret filter now automatically distributed with security hooks updates
- New Section 4 in `/check-security-setup` verifies if filter is actively protecting your session
- README includes complete secret filter setup and usage guide

### What You Need to Do
- **To activate the filter**, add this alias to your shell profile (`~/.bashrc` or `~/.zshrc`):
  ```bash
  alias claude='NODE_OPTIONS=--require=${PWD}/.claude/secret_filter.js claude'
  ```
- **To verify it's working**, run `/check-security-setup` and check Section 4
- Filter is **opt-in** for performance reasons - activate only if you need credential protection

### Security
- Filter intercepts credentials before they reach the Claude API
- Test uses fake AWS key (not real secrets) for verification
- No secrets are logged or stored - only redacted in transit

## [0.3.0] - 2025-11-10

### Added
- Version management system with VERSION file and changelog integration
- Automatic version and changelog display during security hook updates

### Fixed
- Glob pattern matching with absolute file paths (issue #13)

### Security
- Fixed security bypass vulnerability in bash commands with bare directory names

## [0.2.0] - 2025-01-10

### Added
- Multi-repository support with context-aware patterns in restricted.txt
- Automatic pattern scoping for subdirectory restricted.txt files
- Performance caching for restriction rules (~90% speedup)
- Enhanced error messages showing which restricted.txt blocked access

### Changed
- Improved restricted.txt file discovery and rule processing
- Updated documentation for multi-repository setups

### Fixed
- Python executable typo in update scripts
- Environment variable discovery issues
- Repository isolation for backend/mobile service patterns

## [0.1.0] - 2025-01-10

### Added
- Initial release of security hooks
- Essential guard (guard_essential.py) for project boundary protection
- Restricted guard (guard_restricted.py) for sensitive file protection
- Automatic update mechanism with GitLab integration
- Settings merge with conflict detection
- Sub-folder support for monorepo structures
- Security verification command (/check-security-setup)
- Pattern-based file restriction using gitignore syntax

### Security
- Directory traversal prevention (../ and ~/ blocking)
- Protected file defense for .claude/hooks/ files
- Path normalization and validation
