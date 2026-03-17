# HC-11015: Equipment Count Mismatch — Bug Investigation

## Bug Summary
- **Source**: HC-11015 / Sentry #294283
- **Symptom**: On `POST /game/startup`, server detects `EquipmentState.equipmentCount` (cached count of unequipped items) is higher than the actual DB count
- **Reproduction**: Occurs every time a player swaps equipment (equip an item into a slot already occupied by another)
- **Frequency**: ~14 errors/hour, 99 affected players (as of 2026-03-04)
- **Severity**: Medium — self-healing on startup corrects the drift, but the inflated cache can incorrectly block equipment rewards between logins

## Execution Trace

```
1. Player swaps equipment (equip item A into slot occupied by item B)
   File: EquipmentService.java:72 → equip()

2. unequip() called for [itemA, itemB]
   File: EquipmentService.java:132 → private unequip()
   - itemA: from inventory, no equippedOnHero → SKIP
   - itemB: on hero, equippedOnHero present → unequip, count++
   - count += 1 (item B returns to inventory)

3. Back in equip(): equippedOnHeroOpt is present (swap) → SKIP -1
   File: EquipmentService.java:90
   ★ BUG: Should still do -1 (item A leaving inventory)

4. Net effect: +1 per swap (should be 0)
   Over time, count drifts upward. Self-heal on startup catches and logs the mismatch.
```

## Root Cause Analysis

### Root Cause
In `EquipmentService.equip()` (line 88-93), the count decrement was guarded by `if (equippedOnHeroOpt.isEmpty())` — meaning it only decremented when there was NO swap. The comment explained: "In swap case: one item goes to hero (-1), one returns to inventory (+1) = net 0". But this reasoning was **flawed** because `unequip()` already handles the +1 for the returning item separately. The -1 for the going item was still needed.

### Introduced By
Commit `c2a5924edf2` (HC-10142) which changed counting from total items to unequipped-only items.

### Affected Files
- `EquipmentService.java:88-93` — buggy conditional decrement in `equip()`

### All Equip Scenarios (verified)

| Scenario | unequip() | -1 | Net | Correct? |
|---|---|---|---|---|
| A: Inventory → hero (no swap) | 0 | -1 | -1 | ✓ |
| B: Inventory → hero (swap) | +1 | -1 | 0 | ✓ |
| C1: Hero → different hero (no swap) | +1 | -1 | 0 | ✓ |
| C2: Hero → hero (3-way swap) | +2 | -1 | +1 | ✓ |

## Why Existing Tests Didn't Catch It

1. **`testEquipmentSwap()`**: Tested swap behavior but only asserted push responses and unequip costs. Never checked `equipmentCount` cache.

2. **`testEquipDecreasesUnequippedCount()`**: Verified count works for equip-from-inventory WITHOUT swap (Scenario A). The swap case was never tested for count correctness.

3. **`EquipmentAssert.unequippedAmount()`**: Counted actual DB rows (always correct), NOT the `EquipmentState.equipmentCount` cache (which drifts). No assertion existed to verify cache consistency.

## Proposed Fix
Remove the `if (equippedOnHeroOpt.isEmpty())` condition and always decrement by 1.

## Risk Assessment
- **Blast radius**: Only affects the `equipmentCount` cache; DB data is always correct. Self-healing already corrects drift on startup.
- **Regression risk**: Very low — the fix simplifies logic and all 4 scenarios produce correct counts.
- **Test coverage**: Added `cachedCountMatchesActual()` assertion and two new regression tests.

## Regression Test

- **Type**: Backend integration test
- **File**: `backend/game/src/test/java/com/innogames/mobilecity/domain/equipment/EquipmentServiceTest.java`
- **Methods**:
  - `testSwapFromInventoryDoesNotInflateCount` — Scenario B (inventory → hero swap)
  - `testSwapBetweenHeroesDoesNotInflateCount` — Scenario C2 (hero → hero 3-way swap)
- **Assertion infrastructure**: Added `cachedCountMatchesActual()` and `cachedUnequippedCount(int)` to `EquipmentAssert` via new `EquipmentStateTestRepository`
- **Verifies**: After any swap operation, `EquipmentState.equipmentCount` cache matches actual unequipped DB row count
- **Would fail if reverted**: Yes — without the fix, cache inflates by +1 per swap, causing assertion failure

## Fix Summary

### Files Changed
- `EquipmentService.java` — Removed conditional guard on count decrement in `equip()`, always decrements by 1
- `EquipmentStateTestRepository.java` — NEW: Test repository to query cached equipment count via JPQL
- `EquipmentAssert.java` — Added `cachedUnequippedCount(int)` and `cachedCountMatchesActual()` assertions
- `EquipmentServiceTest.java` — Added 2 regression tests + `cachedCountMatchesActual()` to existing equip/swap tests

### Review Status
Pending

### Notes
- Existing players with drifted counts will self-heal on their next startup (existing self-heal logic in `getAll()`)
- No migration needed — the fix prevents future drift, existing drift is auto-corrected
