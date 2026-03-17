# HC-10858: Chat Not Reconnected After Disconnect — Root Cause Fix

## Task Summary

The initial fix for HC-10858 added:
1. An early-return guard in `AllianceChatService.SendMessage()` that blocks sends when `IsChatConnected` is false
2. Unconditional `DisconnectedFromWebSocket` status publish in `StompState.OnDisconnected()` for all disconnect types
3. Status restore in `OnChatConnected()` for internal retry recovery

**The guard works but is undesirable.** The user wants messages typed while offline to be queued and automatically sent when the connection is restored — not dropped with a "you're offline" message. Removing the early return brings back `Debug.Assert` errors from `ChatService.AssertSetup()`.

## Root Cause

The `Debug.Assert` errors originate from `ChatService.AssertSetup()` (package code, line 260-266). When `AllianceChatService.SendMessage()` calls `chatService.Send()` while the STOMP socket is disconnected:

1. `ChatService.Send()` calls `AssertSetup()` — fires two `Debug.Assert` failures (log errors, no throw)
2. `ChatService.Send()` continues to `StompSocketService.SendMessage()`
3. `StompSocketService.ShouldAllowMessageToBeParsed()` returns `false` (not connected)
4. `OnStompError("not connected error", ...)` is called — message is **silently discarded**

The assertions are `[Conditional("UNITY_ASSERTIONS")]` — debug-only, but they pollute logs and signal a programming error.

## Desired Behavior

- User can type and "send" messages while offline
- Messages are queued locally in `AllianceChatService`
- When connection is restored (`OnConnected()`), queued messages are flushed in order via `chatService.Send()`
- No `Debug.Assert` errors because `chatService.Send()` is never called while disconnected
- No early return needed — the guard becomes unnecessary

## Scope

- `AllianceChatService.cs` — add message queue, flush on reconnect
- `AllianceChatModel.cs` — optionally store pending messages (or keep queue in service)
- Remove the early-return guard and `ChatOffline` floating text from `SendMessage()`
- Keep the `IsChatConnected` flag and status publish fix (those are still valuable for other consumers)
