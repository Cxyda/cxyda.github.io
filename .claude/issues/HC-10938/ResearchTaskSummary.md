# HC-10938: Research Task Summary

## Bug Summary
**Deleting battle presets only deletes them for the session** — the deletion is not persisted to the backend.

## Root Cause
`HeroDeckService.RemoveDeck()` only removes the preset from the local in-memory model (`HeroDeckModel.Decks` dictionary). It does **not** send a network request to the backend, unlike `SaveDeck()` which correctly calls `networkGateway.Request(RequestMapping.HeroSaveDeck(...))`.

## Key Finding
The backend endpoint and protobuf message already exist:
- **Endpoint**: `POST /game/hero/delete-deck` via `RequestMapping.HeroDeleteDeck()`
- **Proto message**: `DeleteHeroDeckRequest { string definition_id = 1; }`

The fix is a **one-line addition** to `HeroDeckService.RemoveDeck()`.

## Reproduction
1. Delete a battle preset
2. Reload the game
3. Observe the preset is back (deletion was only in-memory)
