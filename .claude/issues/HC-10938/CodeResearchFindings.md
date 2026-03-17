# HC-10938: Code Research Findings

## Deletion Flow (Current)

```
BattlePresetsView.DeletePreset()           [UI Layer]
  └─> BattlePresetsService.DeletePreset()  [Service Layer]
        └─> HeroDeckService.RemoveDeck()   [Persistence Layer - BUG HERE]
              └─> HeroDeckModel.RemoveDeck()  [Local model only]
```

## Relevant Source Files

### Critical (needs change)
- `frontend/Assets/Scripts/Game/Features/Hero/Services/HeroDeckService.cs`
  - **Lines 77-80**: `RemoveDeck()` — missing `networkGateway.Request()` call
  - **Lines 33-46**: `SaveDeck()` — reference pattern that correctly sends network request

### Supporting (no changes needed)
- `frontend/Assets/Scripts/Game/Features/Hero/Services/IHeroDeckService.cs` — interface
- `frontend/Assets/Scripts/Game/Features/Hero/HeroDeckModel.cs:40-43` — `RemoveDeck()` local-only removal
- `frontend/Assets/Scripts/Game/Features/Battle/Ui/BattleSetup/BattlePresetsService.cs:72-75` — delegates to `heroDeckService.RemoveDeck()`
- `frontend/Assets/Scripts/Game/Features/Battle/Ui/BattleSetup/BattlePresetsView.cs:275-281` — UI delete handler

### Network Infrastructure (already exists)
- `frontend/Packages/com.innogames.herocity.generated/Runtime/Network/RequestMapping.cs:961-963` — `HeroDeleteDeck()` endpoint factory
- `frontend/Packages/com.innogames.herocity.generated/Runtime/Protobuf/Hero.cs` — generated `DeleteHeroDeckRequest` class
- `lib/protobuf/src/main/schema/hero.proto:84-86` — proto definition

## Working Pattern to Follow (SaveDeck)

```csharp
// HeroDeckService.SaveDeck() — Lines 33-46 (WORKS)
public void SaveDeck(DeckVO deck)
{
    model.AddDeck(deck);
    var request = new SaveHeroDeckRequestDTO
    {
        DefinitionId = deck.DefinitionId
    };
    foreach (var hero in deck.Heroes)
    {
        request.HeroDefinitionIds.Add(hero == null ? string.Empty : hero.DefinitionId);
    }
    networkGateway.Request(RequestMapping.HeroSaveDeck(request));
}
```

## Fix Required

```csharp
// HeroDeckService.RemoveDeck() — add network request
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

## Complexity Assessment
- **Scope**: Single method change in one file
- **Risk**: Low — uses existing, proven network infrastructure
- **Testing**: Verify preset deletion survives game reload
