# Config Audit

> Last updated: 2026-03-25

## Current State

Nerdcraft is largely JSON-driven for gameplay tuning and content.

### Implemented config domains

- Input (`config/input.json`)
- UI text/layout (`config/ui.json`)
- Engine timing/pacing (`config/engine.json`)
- World/physics/water/save (`config/game.json`)
- Blocks + mining tiers (`config/blocks.json`)
- Items + equipment stats (`config/items.json`)
- Recipes (`config/recipes.json`)
- Mobs (`config/mobs.json`)
- Biomes (`config/biomes.json`)
- Block mine behavior (`config/block_behaviors.json`)
- Menu labels/ASCII header (`config/menu.json`)

## Remaining non-config logic

These are intentional code-side systems (not content tuning):

- State machines (mob AI transitions, overlay/menu state transitions)
- Physics/collision algorithms
- World generation procedural algorithms
- Render pipeline and curses drawing primitives

## Suggested Next Hardening Step

- Add strict config validation/fail-fast startup checks for:
  - unknown item/block IDs
  - invalid color references
  - invalid action names/key tokens
  - malformed recipe station/item references
