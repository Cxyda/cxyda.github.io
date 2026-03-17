# Detailed Implementation Plan: Queue Chat Messages While Offline

## Overview

Remove the early-return guard in `AllianceChatService.SendMessage()` and instead queue messages locally when disconnected. Flush the queue on reconnect. This eliminates `ChatService.AssertSetup()` assertion errors at the root cause — `chatService.Send()` is never called while disconnected.

## Prerequisites

- HC-10858 StompState fix is in place (unconditional `DisconnectedFromWebSocket` publish + `ConnectedToWebSocket` restore in `OnChatConnected`)
- No package code changes needed

## Implementation Steps

### Step 1 — Add message queue and flush logic to AllianceChatService

**File:** `Assets/Scripts/Game/Features/Alliance/AllianceChat/AllianceChatService.cs`
**Goal:** Queue messages when offline, flush on reconnect.

**Edge Cases:**
- Queue overflow (user spams while offline) → cap at reasonable limit (e.g. 20), drop oldest
- Alliance change while messages queued → clear queue (messages were for old channel)
- Reconnect while not in alliance → don't flush (no channel to send to)
- `OnConnected` called multiple times rapidly → flush is idempotent (queue empties on first call)
- Dispose while queue has messages → just let GC collect (transient, no persistence needed)

**Pseudo-code:**
```
// New field
Queue<string> pendingMessages = new Queue<string>()
const int MaxPendingMessages = 20

SendMessage(message):
  if !IsChatConnected:
    if pendingMessages.Count >= MaxPendingMessages:
      pendingMessages.Dequeue()  // drop oldest
    pendingMessages.Enqueue(message)
    return
  chatService.Send(channelName, message)

OnConnected():
  IsChatConnected = true
  if !IsInAlliance -> return
  RegisterChannelCallback()
  RequestChannelHistory()
  FlushPendingMessages()

FlushPendingMessages():
  channelName = GetChannelName()
  while pendingMessages.Count > 0:
    chatService.Send(channelName, pendingMessages.Dequeue())

UpdateAllianceChannel(newAlliance, previousAlliance):
  // existing logic...
  if previousAlliance != null && previousAlliance.AllianceId != newAlliance.AllianceId:
    pendingMessages.Clear()  // messages were for old alliance
```

### Step 2 — Clean up unused imports and localization

**File:** `Assets/Scripts/Game/Features/Alliance/AllianceChat/AllianceChatService.cs`
**Goal:** Remove the `ChatOffline` floating text guard, its imports, and the `IApplicationDataProvider` dependency.

**Changes:**
- Remove `using Com.Innogames.Core.Frontend.Localization`
- Remove `using InnoGames.Game.Ui.Panels.FloatingText`
- Remove `using InnoGames.Modules.App`
- Remove `IApplicationDataProvider applicationDataProvider` field and injection
- Remove the `if (!applicationDataProvider.IsNetworkConnected || ...)` block entirely

**File:** `Assets/Content/Localization/loca.jsont`
**Goal:** Remove the `ChatOffline` key added in the previous commit (no longer used).

### Step 3 — Update StompStateTests

**File:** `Assets/Scripts/Game/Network/NetworkStateChart/States/Tests/Editor/StompStateTests.cs`
**Goal:** No changes needed — StompState tests are unaffected by AllianceChatService changes.

## Test Specifications

### Manual Test (no existing unit test infrastructure for AllianceChatService)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Connect to game, open alliance chat | Chat works normally |
| 2 | Trigger disconnect (airplane mode / heartbeat timeout) | Chat shows as disconnected in UI |
| 3 | Type and send 2-3 messages while disconnected | Messages appear to be "sent" (text field clears), no assertion errors in console |
| 4 | Restore connection / wait for reconnect | Queued messages are sent automatically, appear in chat history |
| 5 | Send a message after reconnect | Works normally, no assertion errors |
| 6 | Disconnect, send 25+ messages, reconnect | Only last 20 messages are sent (oldest dropped) |

## Verification Criteria

### Compilation
- [ ] No compilation errors or warnings
- [ ] No unused import warnings

### Tests
- [ ] All existing StompStateTests pass
- [ ] No regressions in any EditMode tests

### Runtime
- [ ] No `Debug.Assert` errors when sending while disconnected
- [ ] No `"not connected error"` from StompSocketService
- [ ] Messages sent while offline appear in chat after reconnect
- [ ] Normal send flow still works when connected

### Code Quality
- [ ] No `IApplicationDataProvider` dependency remaining in AllianceChatService
- [ ] Queue is bounded (MaxPendingMessages constant)
- [ ] Queue cleared on alliance change
