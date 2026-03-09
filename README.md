# Nerdcraft

A 2D side-scroller sandbox game in the spirit of Terraria, rendered entirely in ASCII art.

```
 ♥ 100                              1[#] 2[ ] 3[ ] 4[ ] 5[ ]

         &&&
        &&&&&
          |
##########|############################################
###########################################################
```

## Features

- **Procedural world generation** — noise-based terrain with ores, trees, caves and water pockets
- **Block mining & placement** — mine blocks into your inventory, place them back
- **Physics** — gravity, jumping, fall damage
- **Inventory & hotbar** — 5-slot hotbar, full inventory overlay (I key)
- **Mobs** — passive and hostile creatures defined in JSON
  - 🐄 **Cow** — passive, wanders randomly, drops leather
  - 🧟 **Zombie** — hostile, night-only surface spawns, deals melee damage
  - 🕷 **Spider** — hostile, fast, spawns underground
  - 💀 **Skeleton** — hostile, night-only surface spawns, long detection range
- **Combat** — mine/attack key (M) hits mobs, hostile mobs chase and attack player
- **Death & respawn** — death screen, automatic respawn at spawn point
- **Save / Load** — world and player state persisted to disk automatically
  - Auto-saves every 6 seconds (3600 ticks)
  - Saves on quit
  - Loads automatically on next launch
- **Crafting UI panel** — side-by-side inventory + craftable recipe browser
  - Current crafted blocks: `wood_plank`, `workbench`, `torch`, `stone_brick`
- **JSON-driven content** — blocks, colors, physics, mobs, and recipes configured via JSON
- **Day/night visuals** — world blocks are dimmed at night based on the global day clock
- **Night spawning** — mobs with `spawn.night_only: true` can spawn on the surface during night
- **Torch lighting** — placed torches emit a configurable local light radius at night

## Requirements

- Linux
- Python 3.10+
- A terminal that supports curses (virtually any Linux terminal)

## Setup

```bash
cd /path/to/nerdcraft
python3 -m venv venv
source venv/bin/activate
# No external dependencies required — uses only stdlib
python3 main.py
```

## Command-Line Options

```
python3 main.py [OPTIONS]

Options:
  --seed INT, -s INT   World generation seed (random if not specified)
  --save NAME, -n NAME Save slot name (default: "default")
  --new                Force a fresh world (ignore existing save)
```

Examples:
```bash
# Start or resume the default save
python3 main.py

# Force a new world with a specific seed
python3 main.py --new --seed 12345

# Use a named save slot
python3 main.py --save myadventure
```

## Controls

| Key | Action |
|-----|--------|
| A / ← | Move left |
| D / → | Move right |
| W / ↑ / Space | Jump |
| M then direction | Mine block / attack mob |
| P then direction | Place block |
| 1–5 | Select hotbar slot |
| E / R | Cycle hotbar next/prev |
| I / Tab | Open inventory |
| C | Open/close crafting panel |
| Q / Esc | Quit (auto-saves) |

In the crafting panel: **W/S** selects recipes, **Enter/Space** crafts, **C** closes.

## World & Content Configuration

All game content lives in `config/`:

| File | What it controls |
|------|------------------|
| `config/game.json` | Physics, world size, terrain, save settings, day/night timing |
| `config/blocks.json` | Block characters, colors, solid/breakable flags, optional `light_radius` |
| `config/colors.json` | Curses color pair definitions |
| `config/mobs.json` | Mob types, AI behavior, drops, spawn weights |
| `config/recipes.json` | Crafting recipe definitions (hand + workbench) |

See [CONTENT_FORMAT.md](CONTENT_FORMAT.md) for full schema documentation.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for a full description of all modules.

## Testing

Run the automated crafting progression test:

```bash
cd nerdcraft
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current integration-style coverage includes:
- chop wood → craft planks → craft workbench
- day/night clock tick progression and wraparound behavior

## Roadmap

See [PLAN.md](PLAN.md) for the full development roadmap.

Next up: **Day/Night Cycle** follow-up (HUD time icon).

## Inspiration

- [Cursedcraft](https://codeberg.org/mueller_minki/cursedcraft/) — portable TTY voxel sandbox in C99/ncurses
- [Terraria](https://terraria.org/) — 2D side-scroller sandbox
