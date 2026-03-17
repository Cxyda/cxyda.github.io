# Plan: Wait for All Unit Views Before Starting Battle

## Problem Summary

After making unit instantiation async (`Object.InstantiateAsync()`), there are scattered defensive checks like "if view not ready, return" throughout the codebase. These should not be needed - the battle should wait for ALL units and views to be fully instantiated before starting.

**Key insight from user:** Once the battle waits for all views to be ready, missing views/units become **unexpected errors**, not something to gracefully handle.

## Current Issues

### 1. Defensive TryGetValue checks in UnitPresenter.cs
These log exceptions and return early when entity view is not found:
- `OnStartAttacking()` (line 307)
- `OnNextActiveSpecialUpdated()` (line 318)
- `OnStartSpecialAttacking()` (line 340)
- `OnStartWaiting()` (line 397)
- `OnStartSeekingTarget()` (line 408)
- `OnUnitEntityDestroyed()` (line 419)
- `OnUnitDeath()` (line 431)
- `OnEffectApplied()` (line 538)
- `OnEffectRemoved()` (line 567) - silent return

### 2. Pending graphics storage in HeroUnitView.cs
Queues graphics to apply retroactively after instantiation:
- `pendingMainGraphics`, `pendingSupportGraphics` (lines 77-78)
- `pendingMainGraphicsPool`, `pendingSupportGraphicsPool` (lines 81-82)

### 3. Single coroutine tracking in BattleSimulationController.cs
Only tracks ONE `registerEntityViewWaitHandle` - multiple squads overwrite each other (line 61).

## Root Cause

The battle flow has a race condition:
1. `BattleInitCombatState.OnDoActivity()` calls `simulationController.PrepareBattle()`
2. `PrepareBattle()` calls `simulation.StartBattle()` which creates all squads
3. `OnSquadCreated()` starts async instantiation for each squad
4. State completes immediately, transitions to `BattleStartSimulationState`
5. `StartBattleLoop()` is called - battle starts ticking
6. Events fire before views are ready

## Solution

### Phase 1: Track ALL pending instantiations (BattleSimulationController.cs)

**Changes:**
1. Replace single coroutine handle with a HashSet to track pending views:
```csharp
// REMOVE: private Coroutine registerEntityViewWaitHandle;
// ADD:
private readonly HashSet<HeroUnitView> pendingInitialSquadViews = new();
private bool battleStarted;
```

2. Add property to check readiness:
```csharp
public bool AreAllInitialSquadsReady => pendingInitialSquadViews.Count == 0;
```

3. Add method to wait for all squads:
```csharp
public IEnumerator WaitForAllInitialSquadsReady()
{
    while (pendingInitialSquadViews.Count > 0)
    {
        yield return null;
    }
}
```

4. Modify `PrepareBattle()` to reset tracking state

5. Modify `OnSquadCreated()` to add to `pendingInitialSquadViews` if `!battleStarted`

6. Modify `WaitForInstantiationAndRegister()` to remove from set after registration

7. Modify `StartBattleLoop()` to set `battleStarted = true`

8. Update `Dispose()` to clear the HashSet

### Phase 2: Wait before completing state (BattleInitCombatState.cs)

**Change the `OpenUi()` coroutine to wait for all squads:**
```csharp
private IEnumerator OpenUi()
{
    // Wait for all initial squads to complete instantiation
    yield return simulationController.WaitForAllInitialSquadsReady();

    var uiData = new BattleAbilitiesPanelPresenterUiData
    {
        BattleSimulationController = simulationController
    };
    yield return uiService.OpenUiAsync(UiViews.Catalogue.BattleAbilitiesPanel, UiLayers.Panels, uiData);
    Complete();
}
```

### Phase 3: Convert graceful failures to hard errors (UnitPresenter.cs)

Since views are now guaranteed to be ready, missing views are bugs. Convert `TryGetValue` + return patterns to direct dictionary access that throws `KeyNotFoundException`:

**Example transformation:**
```csharp
// BEFORE (graceful failure):
if (!unitViewModel.UnitEntityViews.TryGetValue(message.UnitEntity, out var entityView))
{
    CoreLogger.Exception(LoggerGame.Game_Error,
        new Exception($"Unable to find EntityView by Entity {message.UnitEntity}"));
    return;
}

// AFTER (expected to exist):
var entityView = unitViewModel.UnitEntityViews[message.UnitEntity];
```

**Methods to update:**
- `OnStartAttacking()`
- `OnNextActiveSpecialUpdated()`
- `OnStartSpecialAttacking()`
- `OnStartWaiting()`
- `OnStartSeekingTarget()`
- `OnUnitEntityDestroyed()`
- `OnUnitDeath()`
- `OnEffectApplied()`

**Exception:** `OnEffectRemoved()` (line 567) may legitimately miss views for units that were destroyed, so keep TryGetValue there.

### Phase 4: Remove pending graphics storage (HeroUnitView.cs)

Since graphics are loaded and instantiation completes before battle starts, pending storage is no longer needed for initial squads.

**Remove:**
- `pendingMainGraphics`, `pendingSupportGraphics` fields
- `pendingMainGraphicsPool`, `pendingSupportGraphicsPool` fields
- Queuing logic in `SetMainUnitGraphicPrefab()`, `SetMainUnitGraphicPool()`, `SetSupportUnitGraphicPrefab()`, `SetSupportUnitGraphicPool()`
- Application logic in `OnMainUnitInstantiated()` and `OnSupportUnitsInstantiated()`

**Note:** Temporary squads spawned mid-battle (via abilities) still need async handling. However, for these rare cases, the current logging + skip approach is acceptable since missing one frame for a temporary unit is not noticeable.

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/Assets/Scripts/Game/Features/Battle/Controllers/BattleSimulationController.cs` | Add pending views tracking, wait method |
| `frontend/Assets/Scripts/Game/Features/Battle/States/BattleInitCombatState.cs` | Wait for all squads before completing |
| `frontend/Assets/Scripts/Game/Features/Battle/Presenters/UnitPresenter.cs` | Convert TryGetValue to direct access |
| `frontend/Assets/Scripts/Game/Features/Battle/Views/HeroUnitView/HeroUnitView.cs` | Remove pending graphics storage |

## Mid-Battle Temporary Squads

Squads spawned during battle (via `TemporarySquadEffect`) are handled separately:
- They're NOT added to `pendingInitialSquadViews` (because `battleStarted = true`)
- They may still experience brief race conditions
- Current graceful handling (log + skip) is acceptable for these rare cases
- Consider adding a separate flag/tracking if this becomes problematic

## Verification

1. **Manual Testing:**
   - Start battles with multiple squads (player + enemies)
   - Verify no `KeyNotFoundException` exceptions
   - Test abilities that spawn temporary units
   - Test multi-wave battles

2. **Watch for regressions:**
   - Units not appearing
   - Animation events not triggering
   - Health bars not showing

3. **Expected behavior after fix:**
   - Battle starts only after ALL initial unit views are ready
   - Missing view for an initial unit = crash (bug to fix)
   - Missing view for temporary mid-battle unit = logged warning (acceptable)
