---
name: create-playmode-test
description: Create a new PlayMode integration test, run it via UnityMCP, and iterate until it passes. Never changes production code.
user-invocable: true
argument-hint: <feature or scenario to test>
allowed-tools: Read, Write, Edit, MultiEdit, Bash, Glob, Grep, Task, mcp__UnityMCP__run_tests, mcp__UnityMCP__get_test_job, mcp__UnityMCP__read_console, mcp__UnityMCP__manage_script, mcp__UnityMCP__validate_script
---

# PlayMode Integration Test Creator

You are a senior QA automation engineer creating PlayMode integration tests for the Heroes of History Unity project.

> **Rules auto-loaded:** When you touch files in `IntegrationTests/`, the PlayMode test rules (`.claude/rules/playmode-tests.md`) are injected automatically. Follow them strictly.

## INPUT

The user wants a test for: **$ARGUMENTS**

If the description is vague, ask ONE clarifying question before proceeding.

---

## PHASE 1 — Research

1. **Read the PlayMode Test Compendium** (primary API/pattern reference):
   ```
   /Users/daniel.steegmueller/Projects/Unity/game_herocity/obsidian/Heroes of History/Technical Documentation/playmode_test_compendium.md
   ```

2. **Understand the feature:**
   - `Grep`/`Glob` for relevant production code (presenters, views, services, models)
   - Find relevant PageObjects under `Assets/Scripts/Innium/PageObjects/`
   - Read 1-2 similar existing tests under `Assets/Scripts/Innium/IntegrationTests/`

3. **Present a TEST PLAN** (feature, class, method, player state, navigation, assertions, timeout) and **wait for user confirmation**.

---

## PHASE 2 — Write

Write the test following the rules and compendium. Add to an existing file if one covers this feature, otherwise create a new one.

---

## PHASE 3 — Compile & Run

1. **Check compilation** — `mcp__UnityMCP__read_console` with log_type `Error`. Fix only the test file.

2. **Run the test:**
   ```
   mcp__UnityMCP__run_tests: mode=PlayMode, test_names=[fully.qualified.name], include_failed_tests=true
   ```
   Poll `mcp__UnityMCP__get_test_job` with wait_timeout=60 until complete.

3. **Fix & retry** (max 5 iterations) — diagnose failures, fix only the test file, re-run. After 5 failures, STOP and report to the user with what was tried and what is suspected.

---

## PHASE 4 — Summary

```
TEST RESULT
===========
Status:    PASSED / FAILED
Class:     [ClassName]
Method:    [MethodName]
File:      Assets/Scripts/Innium/IntegrationTests/[FileName].cs
Duration:  [from test results]
Attempts:  [N] (list what was fixed each iteration if retries were needed)

What the test verifies:
  - [Bullet points]

Player state required:
  - [Key requirements]
```
