# Plan: Fix Inconsistencies in feature_overview.md

## Context

The `feature_overview.md` documents 91 features but has several inconsistencies:
- 3 feature directories exist in the codebase but are not documented
- InGameEvent sub-features are referenced in dependencies and `overview.md` but not documented
- ~20 dependency references point to names that don't match any documented section
- No standard notation for framework/infrastructure vs feature dependencies

**File to edit:** `obsidian/Heroes of History/Technical Documentation/feature_overview.md`

---

## Changes

### 1. Add Dependency Notation Legend (after Backend Legend, ~line 127)

Add a new section explaining how dependencies are categorized:
- Feature names match section headings exactly
- `FeatureName (SubComponent)` for sub-components within a feature
- `*(framework)*` for core infrastructure (not a standalone feature)
- `*(package)*` for core frontend packages under `Packages/`
- `*(engine)*` / `*(external)*` for Unity engine / third-party dependencies
- Note: All `Backend: Yes` features implicitly depend on Network infrastructure

### 2. Add 3 Missing Feature Sections (append as #92-#94)

Append at end to avoid renumbering cascade. Update ToC to show them alphabetically.

| # | Feature | Files | Complexity | Backend | Key Reason |
|---|---------|-------|-----------|---------|------------|
| 92 | Fonts | ~1 | Simple | No | Exists as dir, comparable to GamePhysics |
| 93 | InGameShop | ~6 | Simple | Yes | Exists as dir, referenced in overview.md |
| 94 | JoystickBattleTutorial | ~7 | Simple | No | Exists as dir, extends BattleService |

### 3. Expand InGameEvent Section (#41)

- Update file count from `~100+` to `~278`
- Add **Sub-Features (Event Types)** table documenting 12 event types:
  - TreasureHunt (~83 files) - exploration event, largest sub-feature
  - MergeEvent (~21) - merge-puzzle event
  - Pvp (~21) - PvP event variant (distinct from standalone PvP #57)
  - PiggyBank (~14) - savings-style accumulation event
  - LeaderboardEvent (~12) - competitive leaderboard event
  - EventCity (~12) - event-specific city variant
  - ChestEvent (~10) - chest-opening event
  - LoginEvent (~8) - login-reward event
  - QuestlineEvent (~2), DailySpecial (~2), EventSubscription (~2), TaskPool (~2) - minimal sub-components

### 4. Fix Dependency Naming (~20 edits across the document)

| Current | Fix To | Features Affected |
|---------|--------|-------------------|
| `Player` | `PlayerProfile` | Alliance |
| `TaskPool` | `InGameEvent (TaskPool)` | SeasonPass |
| `Building` | `City (Building)` | Rewards, VisitCity |
| `Wonders` | `WondersRework` | Rewards |
| `Incidents` | `Incident` | Rewards |
| `Feature Flags` | `UnlockableFeature` | WoA |
| `Traits` | `GameDesign (Traits)` | Resource |
| `StateChart` | Remove (framework) | VisitCity |
| `City.States` | `City` | Battle |
| `InGameEvent.Pvp` | `InGameEvent (Pvp)` | Battle |
| `Payment` / `Payment systems` | `Payment *(package)*` | GrowthFund, Shop, Subscriptions |
| `MessageHub` | Remove (implicit framework) | Ranking, Resource, StatusIndicator, Story, TaskSystem, Tutorial, UnlockableFeature, WorldInfo |
| `Animation system` | `Animation *(engine)*` | WorkerSystem |
| `UI System` / `UI/Popup system` | `UI *(framework)*` | Indicators, AppNavigation |
| `Ads SDK (IronSource)` | `IronSource *(external)*` | VideoRewards |
| `Core authentication frameworks` | `SSO *(package)*` | SingleSignOn |
| `Core framework` | `None` (matching AppRating pattern) | TimelineGrowthFund, Voucher |
| `Input Management` | `Input *(framework)*` | InputRestriction |
| `Unity Physics` | `Unity Physics *(engine)*` | GamePhysics |

### 5. Update Table of Contents

- Add rows for Fonts, InGameShop, JoystickBattleTutorial
- Update InGameEvent file count to ~278

### 6. Update Summary Statistics

- Total Feature Count: 91 → 94
- Simple count: 46 → 49
- Backend Yes: 58 → 59 (add InGameShop)
- Backend No: 24 → 26 (add Fonts, JoystickBattleTutorial)
- Add new features to the appropriate lists
- Moderate count: 25 → 27 (the existing table already lists 27 features but says "25" - fix the count)
- Simple count: existing count says 46, but with 10+10+27=47 non-simple, that leaves 91-47=44 simple (already wrong). After adding 3 new: 94-47=47 simple. Recount and correct.

---

## Implementation Order

1. Add dependency notation legend
2. Fix all dependency naming inconsistencies (small text edits)
3. Expand InGameEvent section with sub-feature table
4. Add 3 new feature sections at end
5. Update Table of Contents
6. Update Summary Statistics

## Verification

- Search the document for each old dependency name to confirm all instances are fixed
- Count all `### N.` headings to verify total matches updated count
- Compare ToC rows against section headings for consistency
- Grep for any remaining unmatched dependency references
