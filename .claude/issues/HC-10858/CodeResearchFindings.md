# HC-10858: Code Research Findings

## 1. Architecture Overview

### Message Send Chain
```
ChatContentPresenter.OnSendMessageClicked()          [UI layer]
  → AllianceChatService.SendMessage(message)          [Game feature layer]
    → chatService.Send(channelName, message)           [Core chat package]
      → AssertSetup()                                   [Debug.Assert — log only]
      → StompSocketService.SendMessage(StompMessage)   [Core network package]
        → ShouldAllowMessageToBeParsed(command)?
          → YES: _messageQueue.Enqueue() + coroutine
          → NO:  OnStompError("not connected error")   [Message discarded]
```

### Connection State Chain
```
StompState.OnDisconnected()
  → networkStateChart.CurrentNetworkStatus = DisconnectedFromWebSocket
    → publishes NetworkStatusChangedMessage
      → AllianceChatService.OnNetworkStatusChanged()
        → allianceChatModel.IsChatConnected = false
        → chatService.UnregisterChannelCallback()

StompState.OnChatConnected()
  → networkStateChart.CurrentNetworkStatus = ConnectedToWebSocket
    → publishes NetworkStatusChangedMessage
      → AllianceChatService.OnNetworkStatusChanged()
        → allianceChatModel.IsChatConnected = true
        → chatService.RegisterChannelCallback()
        → RequestChannelHistory()
```

## 2. Relevant Source Files

### AllianceChatService.cs
- **Path:** `Assets/Scripts/Game/Features/Alliance/AllianceChat/AllianceChatService.cs`
- **Why:** Main orchestrator — owns `SendMessage()`, handles connect/disconnect lifecycle
- **Key sections:**
  - Lines 104-115: `SendMessage()` — current early-return guard + send
  - Lines 80-90: `OnDisconnected()` — sets `IsChatConnected = false`, unregisters callback
  - Lines 92-103: `OnConnected()` — sets `IsChatConnected = true`, registers callback, requests history
- **Patterns:** Zenject DI, message hub pub/sub, `IChatChannelCallbacks` interface

### AllianceChatModel.cs
- **Path:** `Assets/Scripts/Game/Features/Alliance/AllianceChat/AllianceChatModel.cs`
- **Why:** State model — currently only has `IsChatConnected` bool
- **Key sections:** Line 10: `public bool IsChatConnected { get; set; }`
- **Patterns:** Simple POCO model, injected via Zenject

### ChatContentPresenter.cs
- **Path:** `Assets/Scripts/Game/Ui/Panels/ChatHud/ChatContentPresenter.cs`
- **Why:** UI layer that calls `SendMessage()` — clears text field immediately after send
- **Key sections:**
  - Lines 113-131: `OnSendMessageClicked()` — trims, sanitizes, sends, clears text field
  - Line 121: `messageTextField.text = null` — **clears before send completes**

### StompState.cs
- **Path:** `Assets/Scripts/Game/Network/NetworkStateChart/States/StompState.cs`
- **Why:** Network state machine — triggers connect/disconnect status
- **Key sections:**
  - Lines 180-215: `OnDisconnected()` — unconditional status publish (our fix)
  - Lines 271-278: `OnChatConnected()` — status restore + state event
  - Lines 160-178: `OnConnected()` — `chatService.Subscribe()` call

### ChatService.cs (package)
- **Path:** `Library/PackageCache/com.innogames.core.frontend.chat@.../Runtime/ChatService.cs`
- **Why:** Core chat layer — contains the `AssertSetup()` that fires the errors
- **Key sections:**
  - Lines 142-156: `Send()` — calls `AssertSetup()` then delegates to socket service
  - Lines 260-266: `AssertSetup()` — `[Conditional("UNITY_ASSERTIONS")]` Debug.Assert checks
  - Lines 24-32: `IsConnected` — checks `_socketService.IsConnected && _messageReceiver.WasConnectedReceived`
- **Cannot modify:** Package code

### StompSocketService.cs (package)
- **Path:** `Library/PackageCache/com.innogames.core.frontend.network@.../Runtime/SocketsStomp/StompSocketService.cs`
- **Why:** Lowest layer — has internal queue but rejects messages when disconnected
- **Key sections:**
  - `SendMessage()` → `ShouldAllowMessageToBeParsed()` → queue or `OnStompError()`
  - Internal `_messageQueue` only buffers connected-state messages for coroutine dispatch
- **Cannot modify:** Package code

## 3. Existing Patterns

### Message Queuing
- **No existing message queue pattern** in the alliance chat codebase
- `StompSocketService` has an internal `_messageQueue` but only for connected-state buffering
- Searched: `pendingMessages`, `messageQueue`, `queuedMessages`, `offlineMessages` — zero results

### Similar Reconnection Patterns
- `OnConnected()` in `AllianceChatService` already has a reconnect hook:
  - Registers channel callback
  - Requests channel history
  - This is the natural place to flush a message queue

### DI and Lifecycle
- Services use `IInitializable` / `IDisposable` from Zenject
- State communicated via `AllianceChatModel` (injected model)
- Events via `IDeprecatedChannel<HeroCity>` message hub

## 4. Key Constraints

1. **Package code is read-only** — cannot modify `ChatService.cs` or `StompSocketService.cs`
2. **`Debug.Assert` fires on any `chatService.Send()` while disconnected** — must prevent the call entirely
3. **`ChatContentPresenter` clears the text field immediately** (line 121) — user can't see their message after "send"
4. **No persistence needed** — queued messages can be lost on app restart (chat is transient)
5. **Queue should have reasonable limits** — prevent memory issues if user sends many messages offline

## 5. Root Cause Fix Strategy

The root cause is: `chatService.Send()` is called while the STOMP socket is disconnected. The fix should ensure this call never happens by **queuing at the `AllianceChatService` layer**:

1. When `IsChatConnected` is false: store message in a local queue instead of calling `chatService.Send()`
2. When `OnConnected()` fires: flush the queue by calling `chatService.Send()` for each queued message
3. Remove the early-return guard and floating text — the user's send action is always "accepted"
4. The `IsChatConnected` flag and `DisconnectedFromWebSocket` status publish remain (used by other consumers like `ChatHudPanelPresenter`)
