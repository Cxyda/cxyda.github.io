# Issue HC-10938: [FE] Deleting battle presets only deletes them for the session

## Overview
- **Issue ID**: HC-10938
- **Title**: [FE] Deleting battle presets only deletes them for the session
- **Type**: Bug
- **Priority**: Minor
- **Created**: 2026-03-02
- **Status**: open
- **Assignee**: Daniel Steegmueller
- **Reporter**: Oliver Busch
- **Sprint**: HoH Sprint 1.41
- **Labels**: hoh_battle
- **Components**: FE
- **Source**: Jira via /hc-workflow:add-issue command

## Description

**Reproduction Steps:**
1. Delete a battle preset
2. Reload
3. Observe it's back

**Actual Behavior:**
Deleting battle presets only deletes them for the session

**Expected Behavior:**
We should not only delete it for the session but also persist it with a call to BE

## Research Notes
_Add research findings and analysis here_

## Implementation Planning
_Add implementation planning notes here_

## Progress Tracking
- [ ] Research phase
- [ ] Implementation planning
- [ ] Code implementation
- [ ] Testing and validation
- [ ] Code review
- [ ] Completion
