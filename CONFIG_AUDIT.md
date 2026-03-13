# Config Audit (Pass 3)

Goal: eliminate gameplay hardcoding and move behavior into JSON configs.

## ✅ Completed

- **Input bindings** (`config/input.json`)
  - Movement/use/hotbar/inventory/craft/quit
  - Craft confirm now config-driven (`craft_confirm`), used by crafting UI logic

- **Combat config** (`config/combat.json`)
  - max health
  - fist/tool attack damage
  - tool requirement status template

- **Mining + progression config**
  - per-block mining tier in `config/blocks.json` (`required_mining_tier`)
  - tier display names + leaf fallback apple chance in `config/mining.json`

- **UI config** (`config/ui.json`)
  - status strings/templates
  - inventory/crafting titles/footers/labels
  - inventory/crafting box dimensions
  - death message

- **Engine pacing config** (`config/engine.json`)
  - frame cap/sleep
  - save/status/death timers
  - night spawn interval/cap/min distance

- **Block behavior config** (`config/block_behaviors.json`)
  - on-mine drop behavior (replace/custom/default)
  - configurable trunk replacement drops and leaves custom drops

## Notes

At this point, major gameplay/configurable values are JSON-driven.
Remaining code-level logic is mostly structural flow (state machine + control flow),
not tuning data.
