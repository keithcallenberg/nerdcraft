# Nerdcraft Content Format Reference

> Last updated: 2026-03-25

All gameplay content is authored under `config/`.

## Core Files

- `game.json`
  - game loop, world dimensions, terrain depth, physics, save, water settings
- `blocks.json`
  - block render/collision/breakability/light + `required_mining_tier`
- `items.json`
  - item class (`material|consumable|tool|weapon|armor`)
  - display char/color
  - stats (`heal_amount`, `mining_tier`, `attack_damage`, `armor_slot`, `armor_defense`)
- `mobs.json`
  - health, hostility, detection, attack timing, move timing, `move_speed`, drops, spawn rules
- `recipes.json`
  - crafting inputs/outputs/station constraints
- `biomes.json`
  - surface/subsurface blocks, ore multipliers, tree density
  - smoothing controls (`surface_roughness`, `biome_size_weight`, top-level blend controls)
- `input.json`
  - action → key token mapping
- `ui.json`
  - HUD/status strings and panel sizes/labels
- `engine.json`
  - loop pacing, visual timers, night spawn pacing
- `menu.json`
  - ASCII title/header and menu labels
- `block_behaviors.json`
  - mine-time drop behavior overrides

## Key Naming Rules

- IDs are snake_case in JSON.
- Item/block references in recipes/drops must match registered names.
- Color names must match `colors.json` entries.

## Minimal Examples

### Armor item example (`items.json`)

```json
"iron_chestpiece": {
  "char": "c",
  "color": "white",
  "item_class": "armor",
  "armor_slot": "chestpiece",
  "armor_defense": 4
}
```

### Mob speed/timing example (`mobs.json`)

```json
"zombie": {
  "move_interval": 0.75,
  "idle_move_interval": 1.9,
  "move_speed": 1
}
```

### Water settings example (`game.json`)

```json
"water": {
  "flow_enabled": true,
  "flow_interval_ticks": 12,
  "max_flow_changes": 120,
  "max_breath_seconds": 12.0,
  "breath_recover_per_second": 2.5,
  "drowning_damage": 4,
  "drowning_interval_seconds": 1.0
}
```
