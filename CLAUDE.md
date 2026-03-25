# CLAUDE.md

Quick contributor guidance for code assistants working in this repo.

## Project Snapshot

Nerdcraft is a curses-based ASCII 2D sandbox/survival game in Python.
It is heavily config-driven through JSON under `config/`.

## Contribution Priorities

1. Keep gameplay stable (avoid regressions in loop/input/save/worldgen).
2. Prefer config-driven tuning over hardcoded constants.
3. Preserve performance in the main loop (especially generation/water/mob logic).
4. Run compile/tests before committing.

## Important Paths

- Entry: `main.py`
- Core loop: `game/engine.py`
- Generation: `world/generator.py`
- Data model: `entity/`
- Rendering: `render/`
- Config loader: `config/__init__.py`
- Content: `config/*.json`

## Before Commit

- `python3 -m compileall .`
- sanity scan for merge artifacts
- keep commits focused and descriptive
