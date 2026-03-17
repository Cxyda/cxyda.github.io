# HC-9706 Jira Data

## Issue Details
- **Key**: HC-9706
- **Type**: Sub-Task
- **Parent**: HC-9703 (Story: ATH - Create League & Rewards Overview Screen)
- **Component**: FE
- **Status**: Open
- **Priority**: N/A
- **Assignee**: Daniel Steegmüller
- **Reporter**: Salvatore Calì
- **Created**: 2025-12-17
- **Updated**: 2026-03-09
- **Sprint**: HoH Sprint 1.41 (Active: 2026-03-02 to 2026-03-16)
- **URL**: https://jira.innogames.de/browse/HC-9706

## Full Description
Build the new client-side screen and the logic to display the full league progression.

### Requirements:
1. Implement Entry Point: Add the new "Tiers" button/tab to the Alliance Rank screen and make it open the new overview screen.
2. Build Screen Component: Build the new "ATH League Overview" screen component based on the UI design.
3. API Call & Data Population: Call the new backend endpoint to get the full league structure and populate the screen with this data.
4. Highlight Current League: The client must check the player's current alliance league and apply the "highlighted" visual state to the corresponding league in the list.

---

## Parent Story: HC-9703 - ATH - Create League & Rewards Overview Screen
- **Status**: Ready
- **Components**: FE, UI
- **Epic**: HC-225
- **URL**: https://jira.innogames.de/browse/HC-9703

### Parent Description
This story covers the creation of a new overview screen that displays all ATH leagues and their associated rank-based rewards. Currently, players can only see the rewards for their current league, which limits their motivation to climb. This feature will provide a full, transparent view of the entire competitive ladder, similar to the existing PvP Arena "Tier" screen.

### User Story
"As a player, I want to see a full overview of all ATH leagues and their rank-based rewards, so I can understand what my alliance is competing for and be motivated to climb to higher leagues."

### Acceptance Criteria
- A new "Tiers" or "Leagues" button/tab is added to the Alliance Rank screen.
- Tapping this button opens a new screen that displays a list of all ATH leagues (Iron, Bronze, Silver, Gold, Platinum, Overlord).
- The player's current league is clearly highlighted in this list.
- For each league, the screen displays the different reward brackets based on final rank (e.g., Rank 1, Ranks 2-5, etc.).
- The rewards for each rank bracket are clearly visualized.

### UI Documentation
- Miro board: https://miro.com/app/board/uXjVGITMA-w=/?moveToWidget=3458764661060152289&cot=14

---

## Sibling Subtasks

| Key | Summary | Status |
|---|---|---|
| HC-9704 | Design ATH League Overview Screen | Design (in progress) |
| HC-9705 | Provide Full League Structure Data (BE) | Closed (done) |
| HC-9706 | Implement League Overview Screen (FE) | In Progress (this ticket) |

**Key insight**: The BE endpoint (HC-9705) is already done and available. The design (HC-9704) is still in progress.
