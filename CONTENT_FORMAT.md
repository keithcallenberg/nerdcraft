# Nerdcraft Content Format Reference

> Last updated: 2026-03-09

All game content is defined in JSON files under `config/`.
This document describes each file's schema with examples.

---

## `config/game.json`

Top-level game constants.

```json
{
  "game_loop": {
    "tick_rate": 600,          // physics ticks per second
    "day_length_ticks": 36000  // full day+night cycle length in ticks
  },
  "world": {
    "chunk_size": 16,          // blocks per chunk edge
    "width_chunks": 64,        // world width in chunks
    "height_chunks": 16        // world height in chunks
  },
  "terrain": {
    "sea_level_ratio": 0.5,    // sea level as fraction of world height
    "dirt_depth": 6,           // blocks of dirt below grass
    "stone_depth": 25          // depth at which stone starts
  },
  "physics": {
    "gravity_interval": 0.1,   // seconds between gravity steps
    "jump_height": 5,          // max blocks per jump
    "safe_fall_distance": 6,   // blocks before fall damage
    "fall_damage_per_block": 5 // HP lost per excess block fallen
  },
  "player": {
    "char": "@"                // player ASCII character
  },
  "save": {
    "auto_save_ticks": 3600,   // ticks between auto-saves (6s at 600TPS)
    "save_dir": "saves"        // save directory name (relative to project root)
  }
}
```

---

## `config/blocks.json`

Defines every block type. The key must match a `BlockType` enum member (lowercase).

```json
{
  "blocks": {
    "<block_name>": {
      "char": "#",         // single ASCII character for rendering
      "solid": true,       // true = blocks movement
      "breakable": true,   // true = player can mine it
      "color": "green",   // key from colors.json
      "light_radius": 0    // optional, emits night light in block radius
    }
  }
}
```

### Block name rules
- Must be lowercase snake_case
- Must match a member of `BlockType` enum in `world/block.py`
- Adding a new block requires adding to both JSON and the enum
- `light_radius` defaults to `0` when omitted; set it on emitters (e.g. `torch`)

---

## `config/colors.json`

Defines curses color pairs. `pair_id` 0 is reserved (default terminal colors).

```json
{
  "colors": {
    "<color_name>": {
      "pair_id": 1,          // unique integer 1-255
      "foreground": "green", // terminal color name (see below)
      "background": "default",
      "bold": false          // apply bold/bright attribute
    }
  }
}
```

**Valid terminal color names:** `default`, `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`

---

## `config/mobs.json` *(Phase 2 — planned)*

Defines all mob types. Loaded by a `MobRegistry` at startup.

```json
{
  "mobs": {
    "<mob_id>": {
      "name": "Cow",          // display name
      "char": "C",            // single ASCII character
      "color": "white",       // key from colors.json
      "health": 10,           // starting HP
      "hostile": false,       // if true, will attack player
      "detection_range": 0,   // blocks — hostile mobs chase within this range
      "attack_damage": 0,     // HP dealt per attack
      "attack_interval": 1.0, // seconds between attacks
      "move_speed": 1,        // AI move frequency multiplier
      "drops": [
        { "item": "leather", "chance": 1.0, "count": 1 }
      ],
      "spawn": {
        "surface": true,      // can spawn on surface
        "underground": false, // can spawn underground
        "night_only": false   // only spawns at night (Phase 4)
      }
    }
  }
}
```

---

## `config/recipes.json`

Defines crafting recipes. Item IDs map to block/item names used by inventory and world content.

```json
{
  "recipes": [
    {
      "id": "wood_to_planks",      // unique recipe id (snake_case)
      "name": "Wood Planks",       // display name for UI
      "inputs": [
        { "item": "wood", "count": 1 }
      ],
      "outputs": [
        { "item": "wood_plank", "count": 4 }
      ],
      "station": null,               // null = hand-craft; "workbench" = needs workbench
      "description": "Craft basic planks from raw wood."
    }
  ]
}
```

---

## `config/biomes.json`

```json
{
  "biomes": {
    "<biome_id>": {
      "name": "Forest",
      "surface_block": "grass",
      "subsurface_block": "dirt",
      "tree_density": 0.4,      // 0.0–1.0
      "ore_multipliers": {
        "coal_ore": 1.0,
        "iron_ore": 1.2
      },
      "mob_spawn_table": [
        { "mob": "cow", "weight": 10 },
        { "mob": "zombie", "weight": 5 }
      ]
      // biome table is authoritative for biome spawns;
      // if a biome table exists, only listed mobs can spawn there
    }
  }
}
```

---

## `config/sounds.json`

Defines event-driven terminal SFX behaviour.

```json
{
  "events": {
    "<event_id>": {
      "enabled": true,   // false disables this event entirely
      "cooldown": 0.08,  // minimum seconds between plays for this event
      "beep_count": 1    // number of terminal beeps per trigger
    }
  }
}
```

Current built-in event IDs: `footstep`, `mining`, `hit`, `death`.
