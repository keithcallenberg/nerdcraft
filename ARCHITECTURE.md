# Nerdcraft Architecture

> Last updated: 2026-03-25

## High-Level Structure

- `main.py`
  - CLI parsing
  - curses bootstrap
  - main menu entry
- `game/engine.py`
  - primary game loop orchestration
  - input/update/render sequencing
  - save/load, spawning, overlays, water/breath integration
  - weapon reach handling, inventory use/equip actions, active-chunk mob simulation
- `world/`
  - `world.py` chunked storage + block access
  - `chunk.py` runtime-config chunk container
  - `generator.py` procedural generation + biomes + blending + lakes/clay
  - `save.py` world/player serialization
- `entity/`
  - `player.py` player state (health, inventory, armor, breath)
  - `mob.py` AI entity behavior
  - `mob_registry.py` data-driven mob definitions
  - `physics.py` movement/gravity/jump/autojump core
  - `crafting.py` recipe engine
  - `item.py` JSON-driven item registry with weapon range support
- `render/`
  - `renderer.py` curses drawing + HUD/panels
  - `camera.py` world-to-screen mapping
- `input/`
  - `handler.py` configurable key binding mapping
- `config/`
  - all gameplay/content tuning via JSON

## Data-Driven Core

Most tunable content and behavior is configured through JSON files:

- World/physics/water/save timing: `config/game.json`
- Engine pacing: `config/engine.json`
- UI strings/layout: `config/ui.json`
- Input bindings: `config/input.json`
- Blocks/tiers/colors: `config/blocks.json`, `config/colors.json`
- Items: `config/items.json`
- Mobs: `config/mobs.json`
- Recipes: `config/recipes.json`
- Biomes: `config/biomes.json`
- Block mine behavior: `config/block_behaviors.json`
- Main menu text/header: `config/menu.json`

## Runtime Flow

1. Start via menu or CLI world settings
2. Load save or generate new world
3. Tick loop:
   - input handling
   - fixed-step updates (physics, mobs, water/breath, clock)
   - rendering
   - autosave cadence

## Notable Systems

- **World-size override at new-world creation**
- **Directional use model for non-consumables**
- **Armor slots + mitigation**
- **Biome transition smoothing**
- **Biome-configured surface lakes with clay bottoms**
- **Performance-focused local water simulation**
- **Entity-aware solidity for player-only door traversal**
