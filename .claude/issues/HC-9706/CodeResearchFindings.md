# HC-9706: Code Research Findings

## 1. Key Data Structures

### LeagueVO (league definition)
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/DefinitionObjects/TreasureHuntComponent.cs:43-62`
- **Fields**:
  - `int Index` — 0=Iron, 1=Bronze, 2=Silver, 3=Gold, 4=Platinum, 5=Overlord
  - `List<(int rank, ActionComponent reward)> AllianceRankingRewards` — rewards sorted by rank ascending
  - `int MaxPromotionRank` — highest rank value that gets promoted
  - `int MinDemotionRank` — lowest rank value that gets demoted
- **Access**: `TreasureHuntComponent.Leagues` (list of all LeagueVOs)

### AllianceTreasureHuntLeagueDisplayConfiguration
- **File**: `frontend/Assets/Scripts/Game/Ui/ScriptableObjects/AllianceTreasureHuntDisplayConfiguration.cs:59-71`
- **Fields**: `LeagueNameKey` (loca key), `LeagueIcon` (AssetReferenceT<Sprite>)
- **Access**: `displayConfiguration.GetLeagueDisplayConfiguration(leagueIndex)` returns config per league
- **Asset**: `frontend/Assets/Content/UI/ScriptableObjects/AllianceTreasureHuntDisplayConfiguration.asset`

## 2. Existing Data Provider Methods

**Interface**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/DataProviders/ITreasureHuntDataProvider.cs`

| Method | Line | Purpose |
|--------|------|---------|
| `GetEvent()` | 56 | Get current/recent event |
| `IsLeagueEvent(event)` | 314 | Check if event has multiple leagues |
| `GetCurrentLeague(event)` | 309 | Get player's current LeagueVO |
| `GetAllianceLeagueIndexForId(event, allianceId)` | 325 | Get league index for specific alliance |
| `GetLeagueChangeForAllianceId(event, allianceId)` | 319 | Get promote/demote/stay status |
| `GetAllianceRankingRewardForRank(rank, out event)` | 178 | Get reward for specific rank |

**Implementation**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/DataProviders/TreasureHuntDataProvider.cs`
- `GetCurrentLeague()` at line 463: handles single player, left alliance, and normal cases
- `IsLeagueEvent()` at line 457: returns `component.Leagues.Count > 1`
- League data comes from game design component (loaded at login), no separate API call needed

## 3. Reference Implementation: PvP Tier Screen

The PvP tier screen is the closest existing pattern to replicate.

### PvpTierPresenter
- **File**: `frontend/Assets/Scripts/Game/Features/Pvp/Presenters/PvpTierPresenter.cs`
- **Pattern**: `TabSubPresenter` with horizontal ScrollRect of card views
- **Key logic**:
  - `CreateViews()` (line 104): iterates tier definitions, instantiates card views from template using `container.InstantiatePrefabForComponent<TierCardView>`
  - `UpdateCurrentPoints()` (line 80): highlights current tier, scrolls to it
  - Template card hidden in Awake, cloned for each tier
  - Uses `CardViewEntry` struct for range tracking

### TierCardView
- **File**: `frontend/Assets/Scripts/Game/Features/Pvp/Views/TierCardView.cs`
- **Pattern**: `UiMonoBehaviour` with DI injection
- **Key logic**:
  - `SetData()`: sets crest, required points, instantiates RewardViews from template
  - `HighlightWithCurrentPoints()` / `HidePoints()`: toggle highlight state
  - Reward views instantiated via `container.InstantiatePrefabForComponent<RewardView>`

## 4. Existing Ranking Panel Structure

### TreasureHuntRankingPanelPresenter
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingPanelPresenter.cs`
- **Pattern**: `UiPresenter<TreasureHuntRankingUiData>` with 2 tabs (Internal + Group)
- **Current tabs**: `TreasureHuntPlayerRankingPresenter` and `TreasureHuntAllianceRankingPresenter`
- **Tab system**: Uses `TabButtonView` with click handlers, manually toggles presenters
- **Navigation**: pushed via nav bar with back button

### TreasureHuntAllianceRankingPresenter (the "Group" tab)
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntAllianceRankingPresenter.cs`
- **Pattern**: Plain `MonoBehaviour` with `[Inject]`, manual Open/Close
- **Already shows**: league icon, league name, ranking entries with promote/demote indicators
- **Entry point**: This is where the "Tiers" button should connect from (or from the ranking panel itself)

### TreasureHuntRankingUiData
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingUiData.cs`
- Uses `TreasureHuntRankingPanelTab` enum for tab selection

## 5. Architecture Patterns to Follow

### ADR Rules (from `frontend/.claude/rules/architecture-decisions.md`)
- **IChannel<HeroCity>** for new code (not IDeprecatedChannel — though existing ATH code uses deprecated)
- **No LINQ** — use `JM.LinqFaster` with `F` suffix methods
- **No coroutines** — use `UniTask` for async
- **DI-aware instantiation only** — `diContainer.InstantiatePrefabForComponent<T>()`
- **Interface-first** for services/data providers
- **Constructor injection** for plain C# classes, `[Inject]` methods for MonoBehaviours

### Presenter Pattern
- MonoBehaviour with `[SerializeField]` for UI refs, `[Inject]` for DI
- Subscribe in `OnEnable()`, unsubscribe in `OnDisable()` (or OnUnloaded for UiPresenter)

### View Instantiation Pattern (from PvpTierPresenter)
- Template object hidden in prefab
- Clone via `container.InstantiatePrefabForComponent<T>(template, parent)`
- Set data on cloned view
- Track views for cleanup

## 6. Implementation Approach

Since the user said **UI prefab changes are already done** (hidden in prefab), the implementation needs:

1. **New presenter class** for the league overview (similar to PvpTierPresenter)
   - Placed in `Features/InGameEvent/TreasureHunt/Presenters/Ranking/`
   - Iterates all `TreasureHuntComponent.Leagues`
   - Creates card views for each league
   - Highlights current league

2. **New card view class** for individual league cards (similar to TierCardView)
   - Shows league icon, name, promotion/demotion ranks
   - Shows reward brackets (multiple RewardViews per rank bracket)
   - Highlight state for current league

3. **Integration with ranking panel** — either:
   - Add a third tab to `TreasureHuntRankingPanelPresenter`, or
   - Add a button on the alliance ranking tab that opens the overview

4. **Data flow**:
   ```
   TreasureHuntComponent.Leagues (from game design)
     → ITreasureHuntDataProvider.GetCurrentLeague() (for highlight)
     → AllianceTreasureHuntDisplayConfiguration (for icons/names)
     → LeagueOverviewPresenter creates LeagueCardViews
   ```

## 7. File Locations Summary

| Purpose | Path |
|---------|------|
| League data model | `Features/InGameEvent/TreasureHunt/DefinitionObjects/TreasureHuntComponent.cs` |
| Data provider interface | `Features/InGameEvent/TreasureHunt/DataProviders/ITreasureHuntDataProvider.cs` |
| Data provider impl | `Features/InGameEvent/TreasureHunt/DataProviders/TreasureHuntDataProvider.cs` |
| Display config | `Ui/ScriptableObjects/AllianceTreasureHuntDisplayConfiguration.cs` |
| Display config asset | `Content/UI/ScriptableObjects/AllianceTreasureHuntDisplayConfiguration.asset` |
| Ranking panel presenter | `Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingPanelPresenter.cs` |
| Alliance ranking presenter | `Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntAllianceRankingPresenter.cs` |
| PvP tier presenter (reference) | `Features/Pvp/Presenters/PvpTierPresenter.cs` |
| PvP tier card view (reference) | `Features/Pvp/Views/TierCardView.cs` |
| Reward view widget | `Ui/Widgets/RewardView.cs` |

All paths relative to `frontend/Assets/Scripts/Game/`.
