# HC-10938: Fix battle preset deletion not persisting to backend

## Context
Deleting a battle preset only removes it from the in-memory model — the deletion is never sent to the backend. On reload, the preset reappears. The backend endpoint (`POST /game/hero/delete-deck`) and protobuf message (`DeleteHeroDeckRequest`) already exist but are unused.

## Fix

**File**: `frontend/Assets/Scripts/Game/Features/Hero/Services/HeroDeckService.cs`

Add a `networkGateway.Request()` call to `RemoveDeck()`, mirroring the pattern used in `SaveDeck()`:

```csharp
public void RemoveDeck(DeckDefinition presetDefinition)
{
    model.RemoveDeck(presetDefinition);

    var request = new DeleteHeroDeckRequest
    {
        DefinitionId = presetDefinition.DefinitionId
    };
    networkGateway.Request(RequestMapping.HeroDeleteDeck(request));
}
```

## Verification
1. Compile — verify zero errors via Unity MCP `read_console`
2. Run existing tests related to HeroDeck / BattlePresets
3. Manual: delete a preset, reload, confirm it stays deleted

## Research Documents
- `.claude/issues/HC-10938/ResearchTaskSummary.md`
- `.claude/issues/HC-10938/CodeResearchFindings.md`
