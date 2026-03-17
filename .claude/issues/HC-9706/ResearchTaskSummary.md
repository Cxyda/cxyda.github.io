# HC-9706: Implement League Overview Screen - Task Summary

## Overview
Build a new client-side screen that displays the full ATH (Alliance Tournament Hall) league progression. This screen shows all leagues (Iron through Overlord), their rank-based rewards, and highlights the player's current league.

## Parent Story
HC-9703: ATH - Create League & Rewards Overview Screen (Story, FE+UI)

## Sibling Tasks
| Ticket | Summary | Status |
|--------|---------|--------|
| HC-9704 | Design ATH League Overview Screen | Design (in progress) |
| HC-9705 | Provide Full League Structure Data (BE) | **Closed (done)** |
| HC-9706 | Implement League Overview Screen (FE) | In Progress |

## Requirements
1. **Entry Point**: Add "Tiers" button/tab to the TreasureHunt Ranking Panel (alliance ranking tab area)
2. **Screen Component**: Build the "ATH League Overview" screen showing all leagues in a scrollable list
3. **Data Population**: Use existing league data from `TreasureHuntComponent.Leagues` (already available via game design catalog — no new API call needed)
4. **Highlight Current League**: Identify and visually highlight the player's current alliance league

## User Notes
- UI prefab changes are already done (hidden in prefab). User will assign SerializeField references manually.
- Backend work (HC-9705) is complete — league structure data already available.
- Design (HC-9704) is still in progress but UI prefab exists.

## Acceptance Criteria (from parent HC-9703)
- "Tiers"/"Leagues" button on Alliance Rank screen
- Screen displays all ATH leagues (Iron, Bronze, Silver, Gold, Platinum, Overlord)
- Player's current league is highlighted
- Each league shows reward brackets by rank (Rank 1, Ranks 2-5, etc.)
- Rewards are clearly visualized
