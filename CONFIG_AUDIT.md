# Config Audit (Pass 2)

Goal: eliminate gameplay hardcoding and move behavior into JSON configs.

## ✅ Completed in Pass 1

- Input bindings moved to `config/input.json`
  - `input/handler.py` builds keymap from config.
- Combat core values moved to `config/combat.json`
  - max health
  - fist damage
  - tool damage
  - tool requirement status template
- Mining progression values moved to `config/mining.json`
  - required mining tier per block
  - tier display names
  - leaf apple drop chance

## ✅ Completed in Pass 2

- UI text + layout moved to `config/ui.json`
  - status bar text templates
  - inventory/crafting titles and footer strings
  - empty labels
  - death message
  - inventory/crafting box dimensions
- Engine pacing/timers moved to `config/engine.json`
  - frame cap
  - loop sleep duration
  - save/status/death timers
  - night spawn interval/cap/min distance

## 🚧 Remaining hardcoded areas

1. Crafting interaction keys in gameplay loop
   - Enter/Space craft trigger still in `game/engine.py`
   - Can be routed via action alias config to remove direct keycode checks.

2. World interaction behavior mapping
   - Direct behavior branches still code-defined:
     - trunk -> wood
     - leaves -> apple chance branch
   - Recommend `config/block_behaviors.json` / `config/drops.json` next.

3. Some structural constants
   - hotbar size (`HOTBAR_SIZE=5`) and slot labels are still code-level constants.

4. Semantic action routing
   - `use` behavior by item class is still logic code (expected), but can be partly config-parameterized.

## Suggested next files

- `config/block_behaviors.json` (or `config/drops.json`)
- optional `config/hotbar.json`
- optional crafting input action config for Enter/Space aliases
