# Nerdcraft Task Tracker

> Last updated: 2026-03-09

## Phase 1 — Save / Load System ✅ COMPLETE

- [x] Analyze codebase and document architecture
- [x] Write PLAN.md, ARCHITECTURE.md, CONTENT_FORMAT.md
- [x] Fix `sys.path` hack in `main.py` (now uses `Path(__file__).parent.resolve()`)
- [x] Add `save` section to `config/game.json`
- [x] Create `world/save.py` — SaveManager class
  - [x] `save(world, player, seed)` — serialize world (pickle) + player (JSON) + meta
  - [x] `load(world, player)` — deserialize from disk, returns seed
  - [x] `save_exists()` — checks for meta + world + player files
  - [x] World saved as pickle of chunk block int arrays
  - [x] Player state saved as human-readable JSON sidecar
  - [x] Saves stored in `saves/<name>/` relative to project root
- [x] Wire auto-save into `game/engine.py`
  - [x] Auto-save every 3600 ticks (~6 seconds at 600 TPS)
  - [x] Save on clean quit
- [x] Wire load into `game/engine.py` init
  - [x] If save exists and `--new` not passed → load
  - [x] Otherwise generate fresh world
- [x] Add `--new` CLI flag to `main.py`
- [x] Add `--save NAME` CLI flag to name save slot
- [x] Show "✓ World saved!" flash in status bar for 2 seconds after save
- [x] Update `config/__init__.py` to expose SaveConfig dataclass

## Phase 2 — Data-Driven Mobs + Hostile Enemies ✅ COMPLETE

- [x] Create `config/mobs.json` with cow, zombie, spider, skeleton
- [x] Create `entity/mob_registry.py` — MobRegistry singleton from JSON
- [x] Refactor `entity/mob.py` to be fully data-driven
  - [x] AI state machine: idle → walk → chase → attack
  - [x] Hostile detection range — switch to chase state
  - [x] Adjacent attack with configurable damage + cooldown
  - [x] Probabilistic drops from config
  - [x] Per-mob RNG for varied behaviour
- [x] Update `world/generator.py` spawn to use MobRegistry weighted selection
- [x] Update `game/engine.py` — pass player coords to `update_ai()`
- [x] Update `game/engine.py` — hostile mobs deal damage to adjacent player
- [x] Update `config/colors.json` — add magenta for spider
- [x] Update `README.md` with full feature list, controls, CLI docs

## Phase 3 — Crafting System *(next)*

- [x] Design and create `config/recipes.json`
  - [x] Hand-craft recipes (no station needed)
  - [x] Workbench recipes
- [x] Create `entity/crafting.py` — RecipeEngine
  - [x] `available_recipes(inventory)` → list of craftable recipes
  - [x] `craft(inventory, recipe_id)` → mutates inventory
- [x] Add `CRAFT` action to `input/handler.py` (C key)
- [x] Add crafting UI panel to `render/renderer.py`
  - [x] Side-by-side with inventory: left=items, right=available recipes
  - [x] Select recipe with W/S, craft with Enter/Space
- [x] Wire crafting into `game/engine.py`
- [x] Add new block types: `wood_plank`, `torch`, `stone_brick`, `workbench`
- [x] Test: chop wood → craft planks → craft workbench

## Phase 4 — Day/Night Cycle + Lighting *(future)*

- [x] Create `game/clock.py` — DayClock tracking ticks → time of day
- [x] Add `day_length_ticks` to `config/game.json`
- [x] Apply darkness attribute to blocks at night in renderer
- [x] Add torch block with `light_radius` property
- [x] Spawn hostile mobs at night (use `night_only` flag from mobs.json)
- [x] HUD: time-of-day icon (☀ / ☾)

## Phase 5 — Biomes *(future)*

- [x] Create `config/biomes.json`
- [x] Add second noise pass for biome map in generator
- [x] Per-biome surface/sub-surface blocks, tree density, ore multipliers
- [ ] New blocks: sand, cactus, snow, ice
- [ ] Mob spawn tables per biome

## Phase 6 — Sound / Procedural Audio *(stretch)*

- [ ] Event-driven sound (footsteps, mining, hit, death)
- [ ] Procedural ambient music via numpy + sounddevice
- [ ] `config/sounds.json` definitions

## Phase 7 — Multiplayer *(future)*

- [ ] asyncio server/client architecture
- [ ] Delta world sync
- [ ] Multiple player entities visible
- [ ] Simple connect-by-IP lobby

## Completed

- [x] Initial game engine with fixed-timestep loop
- [x] Procedural terrain generation (noise + FBM)
- [x] Chunk-based world storage
- [x] Player movement, jump, fall damage
- [x] Block mining and placement
- [x] Inventory system + hotbar UI
- [x] Death screen + respawn
- [x] JSON-driven blocks, colors, physics config
- [x] Curses renderer with HUD, camera, inventory overlay
- [x] Save / Load system (Phase 1)
- [x] Data-driven mobs with hostile AI (Phase 2)
