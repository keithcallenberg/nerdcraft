# Config Audit (Pass 1)

Goal: eliminate gameplay hardcoding and move behavior into JSON configs.

## ✅ Completed in this pass

- Input bindings moved to `config/input.json`
  - `input/handler.py` now builds keymap from config instead of hardcoded `ord(...)` table.
- Combat core values moved to `config/combat.json`
  - max health
  - fist damage
  - tool damage
  - "need tool" status template
- Mining progression values moved to `config/mining.json`
  - required mining tier per block
  - tier display names
  - leaf apple drop chance

## 🚧 Remaining hardcoded areas (next passes)

1. UI text/layout constants
   - Status/help text strings in `render/renderer.py`
   - Overlay box widths/heights/padding in `render/renderer.py`

2. Engine loop/system constants
   - sleep cap and frame cap values in `game/engine.py`
   - death screen duration and status flash duration
   - night spawn pacing/cap values

3. Crafting UI interaction keys
   - Enter/Space handling in crafting panel currently in `game/engine.py`
   - Could be migrated into input config aliases or UI config.

4. World interaction rules
   - some direct behavior branches (e.g., trunk => wood) still code-defined
   - can be moved to a `drops.json` / block behavior config.

5. Action routing semantics
   - logic for what `use` does by item class is in code (expected),
     but can still be parameterized further via config if desired.

## Suggested next files

- `config/ui.json`
- `config/engine.json`
- `config/block_behaviors.json` (or `config/drops.json`)
