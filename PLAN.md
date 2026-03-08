# Nerdcraft Development Plan

> Last updated: 2026-03-07

## Current State

Nerdcraft is a playable 2D ASCII side-scroller with:
- Procedural terrain generation (noise-based, with ores, trees, caves)
- Player movement, jumping, fall damage, health
- Block mining and placement
- Basic inventory system with hotbar UI
- Passive mob (cow) with random-walk AI
- JSON-driven block, color, and game config
- Curses-based renderer with camera, HUD, and inventory overlay
- Death screen and respawn

## Identified Gaps

- No save/load — world resets every run
- Mobs are not data-driven (hardcoded cow only)
- No hostile mobs or real combat
- No crafting system
- No day/night cycle or lighting
- No biomes
- No sound
- No multiplayer

---

## Roadmap

### Phase 1 — Save / Load System ✳️ CURRENT

Foundational persistence layer. Without it no other feature can compound.

**Goals:**
- Save world state (all chunk block data) to disk
- Save player state (position, health, inventory)
- Auto-save every N ticks and on quit
- Load on startup if a save exists
- CLI flag `--new` to force a fresh world
- Simple binary/JSON format using pickle + JSON sidecar

**Files to touch:**
- `world/save.py` (new)
- `game/engine.py` (wire in auto-save, load on init)
- `main.py` (add `--new` / `--load` flags)

---

### Phase 2 — Data-Driven Mobs + Hostile Enemies

Move mob definitions into JSON. Add hostile mob types that pursue the player
and deal damage, making the game feel like Terraria.

**Goals:**
- `config/mobs.json` defines all mob types (char, color, health, speed, behavior, drops, spawn conditions)
- Hostile mob behavior: detect player in range, chase, attack
- New mob types: zombie (slow, hits hard), skeleton (ranged placeholder)
- Mob spawning system: surface at night, caves always
- Mob factory loaded from JSON config

**Files to touch:**
- `config/mobs.json` (new)
- `entity/mob.py` (refactor to be data-driven, add hostile AI)
- `world/generator.py` (update spawn to use JSON definitions)
- `game/engine.py` (mob attack logic)

---

### Phase 3 — Crafting System

Core Terraria progression loop: mine resources → craft tools/items → unlock new blocks.

**Goals:**
- `config/recipes.json` defines all crafting recipes (input items → output item)
- Crafting table UI accessible from inventory screen
- Tool items that increase mining range or speed
- Smelting recipes (iron ore → iron ingot)

**Files to touch:**
- `config/recipes.json` (new)
- `entity/crafting.py` (new — recipe engine)
- `render/renderer.py` (crafting UI panel)
- `game/engine.py` (wire crafting action)

---

### Phase 4 — Day/Night Cycle + Lighting

Visual identity and gameplay driver — hostile mobs spawn at night.

**Goals:**
- Configurable day length (in game ticks)
- Ambient darkness at night (dimmed block rendering)
- Torches placeable, emit local light radius
- Hostile mob spawning tied to night
- HUD shows time-of-day icon/bar

**Files to touch:**
- `game/time.py` (new — day/night clock)
- `render/renderer.py` (apply darkness overlay at night)
- `config/game.json` (add day_length_ticks)
- `world/block.py` / `config/blocks.json` (torch block, light-emitting flag)

---

### Phase 5 — Biomes

Variety in worldgen — different surface blocks, trees, ores, and mobs per biome.

**Goals:**
- Biome definitions in `config/biomes.json`
- Biome map generated alongside terrain (second noise pass)
- Forest, Desert, Snow, Underground biomes
- Different block palettes, mob spawn tables, ore distributions per biome
- Visual differentiation via block color config

**Files to touch:**
- `config/biomes.json` (new)
- `world/generator.py` (biome noise layer, per-biome block selection)
- `config/blocks.json` (sand, snow, cactus, etc.)

---

### Phase 6 — Sound / Procedural Audio (Stretch Goal)

**Goals:**
- Event-driven sound: footsteps, mining, mob hit, death
- Procedural ambient music using tone synthesis
- Pure Python implementation using `sounddevice` + numpy wave gen
- Config-driven sound definitions

---

### Phase 7 — Multiplayer (Local Network)

**Goals:**
- Server/client architecture using asyncio sockets
- Multiple players visible in world
- Shared world state with delta sync
- Simple lobby/connect by IP

---

## Current Sprint: Phase 1 — Save / Load

See TASKS.md for step-by-step implementation checklist.
