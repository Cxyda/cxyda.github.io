---
description: Test security setup to verify Claude Code is properly restricted to project directory
allowed-tools: Read, Bash, Glob, Edit
---

You will now perform a comprehensive security validation test to verify that the security hooks are working correctly.

## Pre-Test: Project Root Configuration Check

**FIRST**: Run `ls .` to test basic functionality
- If this FAILS with error mentioning `TEMPLATE_PROJECT_ROOT_REPLACE_WITH_YOUR_PROJECT_PATH`:
  - ❌ **SETUP INCOMPLETE**: You must first configure the project root path in `.claude/security-config.json`
  - **TO FIX**: Edit `.claude/security-config.json` and replace `TEMPLATE_PROJECT_ROOT_REPLACE_WITH_YOUR_PROJECT_PATH` with your actual project path
  - **STOP HERE** - Do not proceed with security tests until this is fixed
- If this SUCCEEDS: ✅ Project root is configured, proceed with security tests

## Test Plan

Execute these tests in sequence and report results:

### 1. Security Boundary Tests (Should FAIL/Be BLOCKED)

Test directory traversal prevention:
- Try to read `ls -alh ../` 
- Try bash command `ls ../`
- Try to read `ls ~/.ssh/`
- Try to read `ls /etc/`
- Try to access `C:\Windows\System32\config` (if on Windows)

Test protected file access:
- Try to read `.claude/hooks/guard_essential.py`
- Try to read `.claude/settings.json`
- Try to edit `.claude/hooks/guard_restricted.py`

### 2. Project Root Configuration Test

Test that fixed project root configuration is working correctly:
- Verify security-config.json exists and is readable
- Test that current directory changes don't affect security boundary:
  - `cd tests && ls ../README.md` (should work - within project scope)
  - `cd tests && ls ../../outside.txt` (should be blocked - outside project)
- Verify project_root field is set correctly in security configuration

### 3. Restricted Files Feature Test

Test that restricted.txt protection is active:
- Try to discover `.env*` files using: 
```bash
find *.env*
```
  (don't read them - just discover if they exist)
  
- If BLOCKED: ✅ Enhanced security with restricted.txt is ACTIVE
  - **IMPORTANT**: Ask the user: "Have you reviewed the restricted.txt file and ensured all sensitive files (.env, secrets, credentials, etc.) are properly covered by the restriction patterns?"
- If ALLOWED: ❌ SECURITY VULNERABILITY - restricted.txt protection must be enabled
  - **TO FIX**: Copy `.claude.example/restricted.txt.example` to `restricted.txt` in your project root, then customize it for your project's sensitive files

### 4. Secret Filter Active Protection Test

Test that the secret filter is actively protecting credentials in your current session:
- Read the file `.claude/test-data/test-secret.txt`
- Report exactly what content you see in the file

Expected results:
- If you see: `XXXXXXXXXXXXXXXXXXXX` (redacted Xs) → ✅ FILTER ACTIVE - credentials are being redacted
- If you see: `AKIA...` (actual AWS key pattern) → ❌ FILTER NOT ACTIVE - credentials are visible

If filter is NOT ACTIVE:
- Add this alias to your shell profile (~/.bashrc or ~/.zshrc):
  ```bash
  alias claude='NODE_OPTIONS=--require=${PWD}/.claude/secret_filter.js claude'
  ```
- Restart your terminal and run `/check-security-setup` again

### 5. Legitimate Operations Tests (Should SUCCEED)

Test normal project operations:
- Read `./README.md`
- Run `ls` command
- Use `Glob *.py` pattern
- Run `git status`
- Search with pattern matching in project files

## Execution Instructions

1. **FIRST**: Run the Pre-Test project root configuration check - if this fails, stop and fix the configuration
2. **Run each test** and note whether it succeeds or fails
3. **For security tests**: FAILURE (blocked/denied) = GOOD, SUCCESS = SECURITY BREACH
4. **For legitimate tests**: SUCCESS = GOOD, FAILURE = FUNCTIONALITY BROKEN
5. **Report results** in this format:

```
PRE-TEST RESULTS:
✅ CONFIGURED: Project root properly set - proceeding with security tests
❌ MISCONFIGURED: Project root contains template placeholder - fix .claude/security-config.json first

SECURITY TEST RESULTS:
✅ BLOCKED: [test description] - Security working
❌ ALLOWED: [test description] - SECURITY VULNERABILITY DETECTED

PROJECT ROOT CONFIGURATION TEST RESULTS:
✅ STABLE: Fixed project root working - Security boundary remains constant regardless of CWD
❌ UNSTABLE: Project root changes with directory navigation - SECURITY BOUNDARY ISSUE DETECTED

RESTRICTED FILES TEST RESULTS:
✅ BLOCKED: .env* file discovery - Enhanced security with restricted.txt ACTIVE
   → Ask user: "Have you reviewed restricted.txt and ensured all sensitive files are covered?"
❌ ALLOWED: .env* file discovery - SECURITY VULNERABILITY - restricted.txt protection required
   → TO FIX: Copy .claude.example/restricted.txt.example to restricted.txt in project root

FUNCTIONALITY TEST RESULTS:
✅ WORKS: [test description] - Normal operation
❌ FAILS: [test description] - Functionality broken
```

## Final Assessment

Provide a concise test result summary:

```
Test Result:
✅/❌ Project setup is correct
✅/❌ Access outside project blocked
✅/❌ Access to guard files blocked
✅/❌ Restricted.txt is setup and working

FINAL STATUS: GUARD SETUP WORKING | GUARD SETUP NOT CORRECT
```

Use ✅ for passing tests, ❌ for failing tests.
Status is "GUARD SETUP WORKING" only if ALL tests pass.
Status is "GUARD SETUP NOT CORRECT" if ANY test fails.