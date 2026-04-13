# Nerdcraft Development Plan

> Last updated: 2026-03-25

## Near-Term Priorities

1. **Stability + performance pass**
   - Continue profiling update-loop hotspots (water, mob updates, generation)
   - Add guardrails for config values that can destabilize gameplay
   - Keep active-chunk optimizations from breaking mob gravity or AI feel

2. **Gameplay balancing + content pass**
   - Tune passive mob wandering and hostile pacing
   - Balance bows, spears, armor, and mob drops
   - Expand utility/building blocks like doors

3. **Worldgen pass 2**
   - Improve lake shaping and shoreline polish
   - Expand biome-specific surface details and resources

4. **Config hardening**
   - Validation/fail-fast for bad IDs/colors/actions
   - Better diagnostics for config authoring

5. **Documentation sync**
   - Keep README/task/architecture docs aligned with shipped gameplay changes

6. **Multiplayer foundations (Phase 7)**
   - Networking skeleton and state model

## Mid-Term

- Expand content tiers and crafting depth
- Better worldgen controls and presets
- Quality-of-life UI improvements (equipment panel, richer HUD, menu polish)

## Long-Term

- Full multiplayer feature set
- More biome/content variety
- Wider platform/runtime support
