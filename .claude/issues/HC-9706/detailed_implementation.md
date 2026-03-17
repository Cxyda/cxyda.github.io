# Detailed Implementation Plan: ATH League Overview Screen (HC-9706)

## Overview + Prerequisites

**Goal**: Add a 3rd "League" tab to `TreasureHuntRankingPanelPresenter` showing all ATH leagues (Iron→Overlord) with rank-based rewards, highlighting the player's current league and auto-scrolling to it.

**Prerequisites**:
- BE data (HC-9705) is complete — `TreasureHuntComponent.Leagues` populated at login
- UI prefab changes done (hidden) — user assigns SerializeField references manually after code exists
- All display config exists in `AllianceTreasureHuntDisplayConfiguration.Leagues`
- **UI prefabs merged from master**:
  - `frontend/Assets/Content/UI/Prefabs/TreasureHunt/ATHTierCard.prefab` — league card template
  - `frontend/Assets/Content/UI/Prefabs/TreasureHunt/Panels/ATHTierPanel.prefab` — league panel
  - `frontend/Assets/Content/UI/Prefabs/TreasureHunt/TreasureHuntRankingPanel.prefab` — updated with hidden league tab
  - `frontend/Assets/Content/UI/Sprites/IconsATHTierCrests/icon_ath_tier_01..06.png` — league crest icons (Iron→Overlord)

**Files to create**:
1. `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntLeagueOverviewPresenter.cs`
2. `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Ui/Views/TreasureHuntLeagueCardView.cs`

**Files to modify**:
1. `frontend/Assets/Scripts/Game/Ui/UiMessages.cs` — add `League` to enum
2. `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingPanelPresenter.cs` — 3rd tab

---

## Phase 1: Enum + Panel Integration

### Step 1.1: Add `League` enum value
- **File**: `frontend/Assets/Scripts/Game/Ui/UiMessages.cs`
- **Pattern**: Existing `TreasureHuntRankingPanelTab` enum (line 68)
- **Goal**: Add `League` as 3rd value

```
TreasureHuntRankingPanelTab { Internal, Group, League }
```

### Step 1.2: Extend TreasureHuntRankingPanelPresenter
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntRankingPanelPresenter.cs`
- **Pattern**: Existing 2-tab structure (lines 16-98)
- **Goal**: Add 3rd tab with conditional visibility for league events

**New SerializeFields** (after line 21):
```
[SerializeField] private TabButtonView leagueTabView;
```
After line 28:
```
[SerializeField] private TreasureHuntLeagueOverviewPresenter leagueOverviewPresenter;
```

**New injected dependency** — need `ITreasureHuntDataProvider` to check `IsLeagueEvent`:
```
private ITreasureHuntDataProvider treasureHuntDataProvider;
// Add to Inject() parameters
```

**Pseudo-code**:
```
// SetupTabs() — add league tab + conditional visibility
SetupTabs():
  // existing tab setup unchanged
  internalTabView.SetActive(true)
  groupTabView.SetActive(true)
  internalTabView.OnClick += _ => SelectTab(Internal)
  groupTabView.OnClick += _ => SelectTab(Group)

  // NEW: league tab — only visible for league events
  if leagueTabView != null:
    var currentEvent = treasureHuntDataProvider.GetEvent()
    var isLeague = treasureHuntDataProvider.IsLeagueEvent(currentEvent)
    leagueTabView.SetActive(isLeague)
    if isLeague:
      leagueTabView.OnClick += _ => SelectTab(League)

// SelectTab() — add League case, null-guard league presenter
SelectTab(selectedTab):
  internalTabView.SetSelected(selectedTab == Internal)
  groupTabView.SetSelected(selectedTab == Group)
  if leagueTabView != null:
    leagueTabView.SetSelected(selectedTab == League)

  switch selectedTab:
    case Internal:
      allianceRankingPresenter.Close()
      leagueOverviewPresenter?.Close()
      playerRankingPresenter.Open()
    case Group:
      playerRankingPresenter.Close()
      leagueOverviewPresenter?.Close()
      allianceRankingPresenter.Open()
    case League:
      playerRankingPresenter.Close()
      allianceRankingPresenter.Close()
      leagueOverviewPresenter.Open()

// CloseAll() — add league presenter
CloseAll():
  allianceRankingPresenter.Close()
  playerRankingPresenter.Close()
  leagueOverviewPresenter?.Close()
  Close()

// OnSetInitialData() — handle League target tab
OnSetInitialData():
  if UiData?.TargetTab == League:
    // Defend: if not a league event, fall back to Internal
    var evt = treasureHuntDataProvider.GetEvent()
    if treasureHuntDataProvider.IsLeagueEvent(evt):
      SelectTab(League)
    else:
      SelectTab(Internal)
  else if UiData?.TargetTab == Group:
    SelectTab(Group)
  else:
    SelectTab(Internal)
```

**Edge cases**:
- **leagueTabView/leagueOverviewPresenter is null** (older prefab): Null guards throughout — backward-compatible.
- **Non-league event**: Tab hidden via `SetActive(false)`. `OnSetInitialData` with `League` target falls back to `Internal`.
- **SetSelected on hidden tab**: Safe even when inactive.

---

## Phase 2: League Overview Presenter

### Step 2.1: Create TreasureHuntLeagueOverviewPresenter
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Presenters/Ranking/TreasureHuntLeagueOverviewPresenter.cs`
- **Pattern**: `TreasureHuntAllianceRankingPresenter` (MonoBehaviour with Open/Close, ComponentPool)
- **Goal**: On `Open()`, iterate all leagues, instantiate card views, highlight current league, scroll to it

**Dependencies** (via `[Inject]`):
- `ITreasureHuntDataProvider` — `GetEvent()`, `GetCurrentLeague()`, `IsLeagueEvent()`
- `IRewardDataProvider` — resolve rewards from `ActionComponent`
- `IActionChangeService` — for `GetFlattenedRewards()`
- `IChannel<HeroCity>` — for publishing `RewardMessages.ShowItemRewardInfo` (ADR-0037)
- `DiContainer` — for `ComponentPool` creation

**SerializeFields**:
- `ScrollRect scrollRect`
- `GameObject leagueCardPrefab` — template for `TreasureHuntLeagueCardView`
- `GameObject rewardViewPrefab` — template for `RewardView`
- `AllianceTreasureHuntDisplayConfiguration displayConfiguration`

**State fields**:
- `ComponentPool<TreasureHuntLeagueCardView> cardPool`
- `ComponentPool<RewardView> rewardViewPool`
- `TreasureHuntLeagueCardView currentLeagueCardView` — scroll target

**Pseudo-code**:
```
[Inject]
Inject(treasureHuntDataProvider, rewardDataProvider, actionChangeService,
       IChannel<HeroCity> channel, DiContainer diContainer):
  store dependencies
  cardPool = new ComponentPool<TreasureHuntLeagueCardView>(
    diContainer, leagueCardPrefab, scrollRect.content, hidePrefab: true)
  rewardViewPool = new ComponentPool<RewardView>(
    diContainer, rewardViewPrefab, hidePrefab: true)

Open():
  gameObject.SetActive(true)
  PopulateLeagues()

PopulateLeagues():
  rewardViewPool.ReturnAllPooledObjects()
  cardPool.ReturnAllPooledObjects()
  currentLeagueCardView = null

  var currentEvent = treasureHuntDataProvider.GetEvent()
  if currentEvent == null: return

  var component = currentEvent.Definition.GetFirstEventComponentOfType<TreasureHuntComponent>()
  if component?.Leagues == null || component.Leagues.Count == 0: return

  var currentLeague = treasureHuntDataProvider.GetCurrentLeague(currentEvent)
  var currentLeagueIndex = currentLeague?.Index ?? 0

  for i = 0; i < component.Leagues.Count; i++:
    var league = component.Leagues[i]
    var cardView = cardPool.GetPooledObject()
    var leagueDisplay = displayConfiguration.GetLeagueDisplayConfiguration(league.Index)
    var isCurrentLeague = (league.Index == currentLeagueIndex)

    // Build flattened reward list per rank bracket
    var rewardBrackets = new List<(int rank, List<IReward> rewards)>()
    for each (rank, actionComponent) in league.AllianceRankingRewards:
      var reward = actionComponent.GetRewards(rewardDataProvider, currentEvent)
                                  .FirstOrDefaultF()
      if reward != null:
        var flatRewards = reward.GetFlattenedRewards(
          rewardDataProvider, actionChangeService, currentEvent)
        rewardBrackets.Add((rank, flatRewards))

    cardView.SetData(league, leagueDisplay, isCurrentLeague,
                     rewardBrackets, rewardViewPool, OnRewardClicked)
    cardView.transform.SetSiblingIndex(i)

    if isCurrentLeague:
      currentLeagueCardView = cardView

  // Scroll to current league after layout pass (ADR-0016: UniTask)
  if currentLeagueCardView != null:
    ScrollToCurrentLeagueAsync().Forget()

async UniTask ScrollToCurrentLeagueAsync():
  await UniTask.Yield(PlayerLoopTiming.PostLateUpdate)
  if currentLeagueCardView != null:
    scrollRect.ScrollVerticallyTo(
      currentLeagueCardView.GetComponent<RectTransform>())

OnRewardClicked(IReward reward):
  channel.Publish(new RewardMessages.ShowItemRewardInfo(reward))

Close():
  rewardViewPool.ReturnAllPooledObjects()
  cardPool.ReturnAllPooledObjects()
  gameObject.SetActive(false)
```

**Edge cases**:
- **currentLeague is null** (no alliance or joined after event): Default to index 0 (Iron). Matches `TreasureHuntAllianceRankingPresenter` line 146-150.
- **component.Leagues empty/null**: Early return — card pool stays empty, presenter shows nothing.
- **displayConfiguration returns null** (invalid index): Logged by config. Pass null to card view; card guards with null check.
- **No rewards for a rank bracket**: Card shows league identity with no reward views.
- **Scroll target destroyed before async**: Null-check after yield.
- **Open() called multiple times without Close()**: `ReturnAllPooledObjects()` at start ensures clean state.

---

## Phase 3: League Card View

### Step 3.1: Create TreasureHuntLeagueCardView
- **File**: `frontend/Assets/Scripts/Game/Features/InGameEvent/TreasureHunt/Ui/Views/TreasureHuntLeagueCardView.cs`
- **Pattern**: `TreasureHuntAllianceRankingEntryView` (MonoBehaviour, Setup method, reward pool)
- **Goal**: Display a single league card: icon, name, highlight, reward brackets

**SerializeFields**:
- `Image leagueIcon`
- `LocalizedText leagueNameLabel`
- `GameObject[] highlightObjects` — activated for current league
- `RectTransform rewardContainer` — parent for pooled reward views
- `float localViewScale` — scale for reward views (default 1f)

**Pseudo-code**:
```
SetData(LeagueVO league,
        AllianceTreasureHuntLeagueDisplayConfiguration displayConfig,
        bool isCurrentLeague,
        List<(int rank, List<IReward> rewards)> rewardBrackets,
        ComponentPool<RewardView> rewardPool,
        Action<IReward> onRewardClicked):

  // League identity
  if displayConfig != null:
    leagueIcon.LoadAndSetIconByKeyAsync(displayConfig.LeagueIcon)
    leagueNameLabel.Key = displayConfig.LeagueNameKey

  // Highlight
  for each obj in highlightObjects:
    obj.SetActive(isCurrentLeague)

  // Rewards
  for each (rank, rewards) in rewardBrackets:
    for each reward in rewards:
      var rewardView = rewardPool.GetPooledObject()
      rewardView.SetReward(reward)
      rewardView.OnRewardClicked = onRewardClicked
      rewardView.transform.SetParent(rewardContainer)
      rewardView.transform.localScale = Vector3.one * localViewScale
      rewardView.transform.SetAsLastSibling()

Reset():
  localViewScale = 1f
```

**Edge cases**:
- **displayConfig is null**: Guard — skip icon/name. Card still shows rewards.
- **rewardBrackets is empty**: Card shows league identity with no rewards. Valid state.
- **LoadAndSetIconByKeyAsync fails**: Handled by async image system — shows fallback.

**Design note**: Exact layout of rank brackets within each card depends on prefab structure (user controls). Initial implementation uses single `rewardContainer`. If prefab has per-bracket containers, view can be extended with `RectTransform[] rewardSlots` later.

---

## Test Specifications

| Method | Scenario | Assertion |
|--------|----------|-----------|
| N/A — MonoBehaviour presenters | Unit tests require mocked DI + Unity UI | Manual testing per verification criteria |

Matches existing pattern: `TreasureHuntAllianceRankingPresenter` and `TreasureHuntPlayerRankingPresenter` have no unit tests.

---

## Verification Criteria

### Compilation
- [ ] Zero compilation errors after all changes
- [ ] Zero new warnings introduced

### Code Quality
- [ ] `IChannel<HeroCity>` used (not `IDeprecatedChannel`) in new presenter (ADR-0037)
- [ ] `ComponentPool` used for view instantiation (ADR-0038)
- [ ] `UniTask.Yield()` for delayed scroll (ADR-0016, not coroutines)
- [ ] No `System.Linq` — use `JM.LinqFaster` if needed (ADR-0014)
- [ ] `[Inject]` method for MonoBehaviour injection (ADR-0008)
- [ ] Null guards for backward-compatible prefab support

### Runtime (Manual)
- [ ] Open ATH ranking panel during active league event → league tab visible
- [ ] Tap league tab → all leagues displayed (Iron through Overlord)
- [ ] Current league highlighted and auto-scrolled to
- [ ] Each league card shows correct icon and name
- [ ] Each league card shows reward brackets with correct reward views
- [ ] Tapping a reward shows reward info popup
- [ ] Open ranking panel during non-league event → league tab hidden
- [ ] Switch between Internal/Group/League tabs → each opens/closes correctly
- [ ] No errors in console during all interactions
