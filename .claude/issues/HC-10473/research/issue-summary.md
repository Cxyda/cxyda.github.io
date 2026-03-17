# Issue HC-10473: Treasure hunt rejected by the game

## Overview
- **Issue ID**: HC-10473
- **Title**: Treasure hunt rejected by the game
- **Type**: Bug (Minor)
- **Component**: FE
- **Labels**: hoh_chat
- **Assignee**: Daniel Steegmüller
- **Reporter**: Axel Giraud
- **Created**: 2026-02-08
- **Status**: In Progress
- **Sprint**: HoH Sprint 1.41
- **Affects Version**: 1.37
- **Player**: ZZ1-15045

## Description
Players see "Treasure hunt rejected by the game" / "TreasureHuntDismissed" message in the chat history after a treasure hunt ends. This is the wrong localization key — the chat notification should show the ranking/result instead.

**Reproduction Steps** (from Jira — cannot reliably reproduce):
1. Event 1 ends → state becomes ENDED
2. Event 2 starts while player is offline or hasn't interacted
3. Player comes online → receives event pushes
4. Notifications get scheduled (or re-scheduled if already in the past)
5. Player opens Event 2 start panel → closes it
6. `OnClosed()` triggers → dismisses all ENDED treasure hunts
7. `eventVO.State` locally set to DISMISSED
8. If the chat notification hasn't been displayed yet, it reads the **current** `eventVO.State`
9. Shows "TreasureHuntDismissed" instead of ranking

**Root cause hypothesis** (from Kim Rohlfs' analysis):
The notification doesn't capture a snapshot of the state — it holds a reference to the `InGameEventVO` object. If that object's `State` property is mutated before the notification is rendered, the notification shows the current state (DISMISSED), not the state at scheduling time (ENDED with ranking).

## Attachment
- Screenshot: `attachments/HC-10473/12cd03ebe397ce0bfaf424c4cd51779039334d7f39be1705f20094ce13fc89b9.jpg`
  - Shows Dutch chat with "de schattenjacht werd door het spel afgewezen" (wrong dismissed message)

## Research Notes
_Add research findings and analysis here_

## Implementation Planning
_Add implementation planning notes here_

## Progress Tracking
- [x] Research phase (Jira data fetched)
- [ ] Codebase research
- [ ] Implementation planning
- [ ] Code implementation
- [ ] Testing and validation
- [ ] Code review
- [ ] Completion
