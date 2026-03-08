# Nerdcraft Architecture

> Last updated: 2026-03-07

## Overview

Nerdcraft is a 2D ASCII side-scroller implemented in Python using curses for rendering.
Systems are cleanly separated and communicate through well-defined interfaces.

```
┌─────────────────────────────────────────────┐
│                  main.py                    │
│   Entry point, curses.wrapper, CLI args     │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│             game/engine.py                  │
│   GameEngine — orchestrates all systems     │
│   Fixed-timestep game loop (600 TPS cap)    │
│   Input → Update → Render cycle             │
└──┬──────────┬──────────┬────────────┬───────┘
   │          │          │            │
┌──▼───┐  ┌──▼───┐  ┌───▼──┐  ┌─────▼─────┐
│World │  │Entity│  │Render│  │  Input    │
│Layer │  │Layer │  │Layer │  │  Handler  │
└──┬───┘  └──┬───┘  └───┬──┘  └───────────┘
   │         │           │
  Chunks   Player      Camera
  Generator  Mob       Renderer
  Block      Physics   HUD
  Save/Load  Inventory Death/Inv screens
```

## Module Descriptions

### `main.py`
- Entry point
- Parses CLI args: `--seed`, `--new`
- Wraps `GameEngine.run()` in `curses.wrapper()`

### `game/engine.py` — GameEngine
- Central orchestrator
- Owns: World, Player, mobs list, PhysicsEngine, Renderer, InputHandler
- Hotbar (5 slots), pending action state machine
- Death timer → respawn flow
- Inventory overlay mode
- `_handle_input()` → `_update(dt)` → `_render()`

### `game/config.py`
- Exposes constants loaded from JSON via `GameConfig` singleton
- All physics, world-size, terrain constants live here

### `world/world.py` — World
- Chunk-based block storage: `dict[(cx,cy)] → Chunk`
- World/chunk coordinate conversion
- `get_block()`, `set_block()`, `is_solid()` public API

### `world/chunk.py` — Chunk
- 16×16 grid of `BlockType` values
- Stores `chunk_x, chunk_y` for world-coordinate helpers

### `world/generator.py` — WorldGenerator
- Seeded PRNG + permutation table
- 1D FBM noise → terrain height
- 2D value noise → caves, ore veins
- Tree placement via cell-based algorithm
- `generate_world(world)` fills all chunks
- `spawn_mobs(world)` → list of Mob instances

### `world/save.py` — SaveManager *(Phase 1, new)*
- Saves/loads world chunk data + player state
- Format: `saves/<name>/world.pkl` + `saves/<name>/player.json`
- Auto-save every N ticks; save-on-quit

### `world/block.py` — BlockType + BlockProperties
- `BlockType` enum (maps to JSON config keys)
- `BlockProperties` dataclass: char, solid, breakable, color_pair
- Registry initialized lazily from `GameConfig`

### `entity/player.py` — Player
- Integer grid position (x, y)
- health, on_ground, jump_remaining, fall_distance, facing_right
- Owns `Inventory`
- Helper methods for adjacent block positions

### `entity/mob.py` — Mob
- Duck-typed with Player for PhysicsEngine compatibility
- `mob_type` string key into mob registry
- Simple state-machine AI: idle / walk / [chase / attack — Phase 2]
- `drops` list loaded from mob config

### `entity/physics.py` — PhysicsEngine
- Discrete grid-based gravity (timer-driven steps)
- `try_move(entity, dx, dy)` — collision check
- Fall damage accumulation
- Per-entity gravity timer dict (works for player + all mobs)

### `entity/inventory.py` — Inventory
- `dict[BlockType → count]` storage
- `add()`, `remove()`, `count()`, `items()`

### `render/renderer.py` — Renderer
- Curses-based rendering
- HUD row (top): health + hotbar
- World rows: block chars with color pairs
- Mob and player overlaid
- Status bar (bottom): position + controls hint
- Inventory overlay (modal)
- Death screen (modal)

### `render/camera.py` — Camera
- Viewport tracking player center
- `world_to_screen()` / `screen_to_world()` (Y-flip: world Y up, screen Y down)

### `input/handler.py` — InputHandler
- Key → `Action` enum mapping
- WASD + arrows, M/P, 1-5, E/R, I, Q/Esc

### `config/__init__.py` — GameConfig
- Singleton loading `game.json`, `blocks.json`, `colors.json`
- Typed dataclasses: `BlockConfig`, `ColorConfig`
- `get_block(name)`, `get_color(name)`, `get_block_color_pair(name)`

## Data Flow

```
JSON configs ──► GameConfig (singleton)
                    │
          ┌─────────┼──────────┐
      BlockType   Colors    Physics/World constants
      properties  pairs

GameEngine.run()
  loop:
    getch() → InputHandler.process_key() → Action
    Action → engine state mutations (move, mine, place…)
    accumulator >= TICK_DURATION:
      PhysicsEngine.update(player, dt)
      PhysicsEngine.update(mob, dt) × N
      mob.update_ai(world, dt) → dx → try_move
    Renderer.render(world, player, mobs, hotbar…)
```

## Key Design Decisions

1. **Integer grid coordinates** — all entities snap to whole-block positions.
   Physics is discrete (step-based), not continuous.
2. **JSON-driven content** — blocks, colors, game constants, (Phase 2) mobs all in JSON.
3. **Chunk-based world** — enables partial loading and future infinite world.
4. **Fixed-timestep loop** — physics ticks decouple from render framerate.
5. **Duck-typed entities** — `PhysicsEngine` works on any object with the right attributes,
   so mobs and player share the same physics without inheritance.
