# HC-10858: Queue Chat Messages While Offline

## Context
The early-return guard in `SendMessage()` prevents `Debug.Assert` errors but drops the user's message. The user wants messages queued and sent on reconnect instead.

## Approach
Add a bounded `Queue<string>` to `AllianceChatService`. When disconnected, enqueue instead of calling `chatService.Send()`. On `OnConnected()`, flush the queue. Remove the guard, floating text, and `IApplicationDataProvider` dependency.

## Files Modified
- `AllianceChatService.cs` — queue + flush logic, remove guard and unused deps
- `loca.jsont` — remove unused `ChatOffline` key

## Key Decisions
- Queue cap: 20 messages (drop oldest on overflow)
- Queue cleared on alliance change (messages were for old channel)
- Queue lives in service (transient, not model — no persistence needed)
- No unit tests for AllianceChatService (no existing test infrastructure; manual test plan provided)

## Detailed plan
`.claude/issues/HC-10858/detailed_implementation.md`
