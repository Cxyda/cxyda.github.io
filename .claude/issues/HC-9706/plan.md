# HC-9706: Research Complete — Implement League Overview Screen

## Research Summary

Research findings saved to `.claude/issues/HC-9706/`. Key discoveries:

### Data is Already Available
- League definitions live in `TreasureHuntComponent.Leagues` (List<LeagueVO>), loaded from game design at login
- `ITreasureHuntDataProvider` has all needed methods: `GetCurrentLeague()`, `IsLeagueEvent()`, `GetAllianceLeagueIndexForId()`
- Display config (icons/names per league) in `AllianceTreasureHuntDisplayConfiguration` ScriptableObject
- **No new API call needed** — all data is already client-side

### Reference Pattern: PvP Tier Screen
- `PvpTierPresenter` (TabSubPresenter) + `TierCardView` is the closest existing pattern
- Horizontal scroll of card views, template-based instantiation, current tier highlight with auto-scroll

### Entry Point: TreasureHunt Ranking Panel
- `TreasureHuntRankingPanelPresenter` has 2 tabs (Internal + Group)
- The "Tiers" button needs to be added — either as a 3rd tab or a button within the alliance ranking area
- UI prefab changes are already done (user will assign references manually)

### Architecture Rules
- Use `IChannel<HeroCity>` (not deprecated), no LINQ (use LinqFaster), no coroutines (use UniTask)
- DI-aware instantiation only, interface-first design
- `[Inject]` methods for MonoBehaviours

## Quality Gate: PASSED_WITH_NOTES
Minor: Read `TreasureHunt.md` feature doc and reference ADR-0018/ADR-0017 during implementation.
