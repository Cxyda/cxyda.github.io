# Fix: ActionContext.empty() → ActionContext.test()

## Problem
Build fails because `ActionContext.empty()` method doesn't exist.

## Solution
Replace `ActionContext.empty()` with `ActionContext.test()` in the test file.

The `ActionContext` class has a `test()` static method (line 77-79) specifically for creating test contexts:
```java
public static ActionContext test() {
    return GeneralActions.TEST.at(Instant.now());
}
```

## File to Modify
- `backend/game/src/test/java/com/innogames/mobilecity/integration/preset_slot/Hc9669MigrateExistingPresetSlotsMigrationIntegrationTest.java`

## Changes
Replace 4 occurrences of `ActionContext.empty()` with `ActionContext.test()`:
- Line 46
- Line 69
- Line 83
- Line 88

## Verification
The build should pass after this change. The pattern `ActionContext.test()` is used extensively in other test files (confirmed in IncidentSpawnerTest.java and others).
