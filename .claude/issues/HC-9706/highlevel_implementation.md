# High-Level Implementation Plan: ATH League Overview Screen

## Context
- **Current state**: The TreasureHunt ranking panel has 2 tabs (Internal player ranking + Group alliance ranking). Players can only see rewards for their current league. The BE data (HC-9705) is complete and UI prefab changes are done but hidden.
- **Goal**: Add a 3rd "League" tab showing all ATH leagues (Iron→Overlord) with rank-based rewards, highlighting the player's current league. Similar to the existing PvP Arena tier screen.

## Architecture

```
TreasureHuntRankingPanelPresenter (UiPresenter, existing)
├── [Tab: Internal] TreasureHuntPlayerRankingPresenter (MonoBehaviour)
├── [Tab: Group]    TreasureHuntAllianceRankingPresenter (MonoBehaviour)
└── [Tab: League]   TreasureHuntLeagueOverviewPresenter (MonoBehaviour) ← NEW
                    └── ScrollRect with LeagueCardViews
                        ├── LeagueCardView (Iron)      ← template-based
                        ├── LeagueCardView (Bronze)
                        ├── ...
                        └── LeagueCardView (Overlord)
                            └── RewardViews per rank bracket
```

**Data flow**:
```
TreasureHuntComponent.Leagues (game design, loaded at login)
  → ITreasureHuntDataProvider.GetEvent() + .GetCurrentLeague()
  → AllianceTreasureHuntDisplayConfiguration (icons/names per league)
  → TreasureHuntLeagueOverviewPresenter creates LeagueCardViews
  → Each LeagueCardView shows rewards via LeagueVO.AllianceRankingRewards
```

No new API calls needed — all data is already client-side from game design catalog.

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Add 3rd tab to existing `TreasureHuntRankingPanelPresenter` | Consistent with current 2-tab pattern; user already prepared prefab with hidden elements |
| 2 | Use plain `MonoBehaviour` with manual `Open()`/`Close()` (not `SubPresenter`) | Matches `TreasureHuntAllianceRankingPresenter` and `TreasureHuntPlayerRankingPresenter` pattern |
| 3 | Use `IChannel<HeroCity>` in new code (not `IDeprecatedChannel`) | ADR-0037 mandates new code uses `IChannel` |
| 4 | Template-based card instantiation via `DiContainer.InstantiatePrefabForComponent<T>()` | Matches PvpTierPresenter pattern; ADR-0038 mandates DI-aware instantiation |
| 5 | Use `ComponentPool` for reward views | Matches TreasureHuntAllianceRankingPresenter pattern for efficient view recycling |
| 6 | No new DI installer bindings needed | Presenter is MonoBehaviour (injected on GameObject), no new services/data providers required |
| 7 | Use UniTask for delayed scroll (not coroutines) | ADR-0015 mandates UniTask for new async code |

## Files to Create

| File | Purpose |
|------|---------|
| `Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntLeagueOverviewPresenter.cs` | Main presenter: iterates leagues, creates card views, highlights current league, scrolls to it |
| `Features/InGameEvent/TreasureHunt/Ui/Views/TreasureHuntLeagueCardView.cs` | Card view: displays league icon/name, rank brackets with rewards, highlight state |

All paths relative to `frontend/Assets/Scripts/Game/`.

## Files to Modify

| File | Changes |
|------|---------|
| `Ui/UiMessages.cs` | Add `League` value to `TreasureHuntRankingPanelTab` enum |
| `Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingPanelPresenter.cs` | Add `[SerializeField]` for league tab button + league presenter; extend `SetupTabs()` and `SelectTab()` for 3rd tab; hide league tab when not a league event |

## Phases

1. **Phase 1: Enum + Panel Integration** — Add `League` to `TreasureHuntRankingPanelTab`. Extend `TreasureHuntRankingPanelPresenter` with the 3rd tab button, serialized league presenter reference, and tab switching logic. Conditionally hide the league tab for non-league events.

2. **Phase 2: League Overview Presenter** — Create `TreasureHuntLeagueOverviewPresenter`. On `Open()`: get event and component, iterate `component.Leagues`, instantiate `TreasureHuntLeagueCardView` per league using template cloning, highlight current league, scroll to it via UniTask delayed frame.

3. **Phase 3: League Card View** — Create `TreasureHuntLeagueCardView`. `SetData()` receives `LeagueVO`, league index, display config, and whether it's the current league. Shows league icon/name, promotion/demotion rank thresholds, and reward brackets. For each entry in `AllianceRankingRewards`, instantiate `RewardView` from template.

## What This Does NOT Change
- No new backend API calls or endpoints
- No changes to `ITreasureHuntDataProvider` interface or `TreasureHuntDataProvider` implementation
- No changes to `TreasureHuntInstaller` DI bindings
- No app navigation handler changes (existing direct `uiService.OpenUi()` pattern preserved)
- No changes to `TreasureHuntAllianceRankingPresenter` or `TreasureHuntPlayerRankingPresenter`
- Prefab/UI changes are out of scope (user handles manually)

## Verification

### Automated Tests
| Test File | Verifies |
|-----------|----------|
| N/A — Presenters are MonoBehaviours tested manually | UI logic is view-bound; unit testing requires mocked DI container |

### Manual Tests
1. Open ATH ranking panel during an active league event → league tab should be visible
2. Tap league tab → league overview shows all 6 leagues (Iron through Overlord)
3. Current league is highlighted and auto-scrolled to
4. Each league card shows correct icon, name, and reward brackets
5. Tapping a reward shows reward info popup
6. Open ATH ranking panel during a non-league (single-league) event → league tab should be hidden
7. Switch between Internal/Group/League tabs → each tab opens/closes correctly
