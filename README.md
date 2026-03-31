# Nerdcraft

ASCII 2D sandbox/survival inspired by Terraria.

## Current Features

- Procedural world generation with biome support
  - Biome smoothing/blending (`surface_roughness`, `biome_size_weight`, blend fraction)
  - Blended biome border materials for smoother transitions
- Save/load system with named save slots
- Main menu with configurable ASCII header (`config/menu.json`)
  - Generate new world
  - Load saved world
  - World-size selection (Small/Medium/Large)
  - World generation progress screen with percentage
- Mining, placement, inventory, hotbar, crafting
- JSON-driven items, tools, weapons, armor, mobs, recipes, biomes, colors, controls
- Tiered progression (tools/weapons/armor)
- Auto-jump (player + mobs)
- Day/night cycle, night spawns, torch lighting
- Water systems (first pass)
  - Swimming
  - Local water flow simulation
  - Breath / drowning
- Mobs with data-driven AI and drops

## Screenshot

<pre style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; line-height: 1.1;">
<span style="color:#ff4d6d;">♥ 39</span>  <span style="color:#9aa0a6;">☾</span>                                                  <span style="color:#cccccc;">1[/] 2[T] 3[=] 4[#] 5</span>

                                          <span style="color:#e5e5e5;">==</span>
<span style="color:#27c93f;">&&&</span>                                      <span style="color:#e5e5e5;">=##=</span>
<span style="color:#27c93f;">&&&&</span>                <span style="color:#27c93f;">&&</span>                  <span style="color:#e5e5e5;">=#  #=</span>
<span style="color:#27c93f;">&&&&&</span>             <span style="color:#27c93f;">&&&&&</span>                <span style="color:#e5e5e5;">=#    #=</span>
<span style="color:#27c93f;">&amp; &amp;&amp;&amp;&amp;</span>           <span style="color:#27c93f;">&amp;&amp;&amp;&amp;&amp;&amp;&amp;&amp;</span>             <span style="color:#e5e5e5;">=#      #=</span>
 <span style="color:#8b5a2b;">|</span>               <span style="color:#27c93f;">&amp;&amp;&amp;&amp;&amp;&amp;&amp;&amp;</span>            <span style="color:#e5e5e5;">=#        #=</span>        <span style="color:#f0f0f0;">K</span>
                    <span style="color:#8b5a2b;">|</span>                 <span style="color:#9e9e9e;">#        #</span>
                    <span style="color:#8b5a2b;">|</span>                 <span style="color:#9e9e9e;">#        #</span>        <span style="color:#9e9e9e;">##</span><span style="color:#4fc3f7;">WW</span><span style="color:#9e9e9e;">#####</span><span style="color:#4fc3f7;">WWWWWWW</span><span style="color:#9e9e9e;">###</span><span style="color:#4fc3f7;">WWWWWWWW</span>
<span style="color:#9e9e9e;">#############</span>       <span style="color:#8b5a2b;">|</span>       <span style="color:#9e9e9e;">####</span>      <span style="color:#8b5a2b;">|</span>   <span style="color:#ff6b6b;">@</span>    <span style="color:#9e9e9e;">#</span>      <span style="color:#9e9e9e;">####</span><span style="color:#4fc3f7;">WW</span><span style="color:#9e9e9e;">#####</span><span style="color:#4fc3f7;">WWWWWWW</span><span style="color:#9e9e9e;">###</span><span style="color:#4fc3f7;">WWWWWWWW</span>
<span style="color:#9e9e9e;">############################################## ###########</span><span style="color:#4fc3f7;">WW</span><span style="color:#9e9e9e;">#####</span><span style="color:#4fc3f7;">WWWWWWW</span><span style="color:#9e9e9e;">###</span><span style="color:#4fc3f7;">WWWWWWWW</span>
<span style="color:#9e9e9e;">##############################################  ##########</span><span style="color:#4fc3f7;">WW</span><span style="color:#9e9e9e;">#####</span><span style="color:#4fc3f7;">WWWWWWW</span><span style="color:#9e9e9e;">###</span><span style="color:#4fc3f7;">WWWWWWWW</span>
<span style="color:#9e9e9e;">###############################################  #########</span><span style="color:#4fc3f7;">WW</span><span style="color:#9e9e9e;">######</span><span style="color:#4fc3f7;">WWWWWW</span><span style="color:#9e9e9e;">##</span><span style="color:#4fc3f7;">WWWWWWWWW</span>
<span style="color:#9e9e9e;">################################################  ########</span><span style="color:#27c93f;">Z</span><span style="color:#4fc3f7;">W</span><span style="color:#9e9e9e;">#######</span><span style="color:#4fc3f7;">WWWWWWWWWWWWWWWW</span>
<span style="color:#9e9e9e;">#################################################  ################################</span>
<span style="color:#9e9e9e;">##################################################  ###############################</span>
<span style="color:#9e9e9e;">###################################################  ##############################</span>
<span style="color:#9e9e9e;">####################################################  #############</span><span style="color:#4fc3f7;">W</span><span style="color:#9e9e9e;">###############</span>
<span style="color:#9e9e9e;">#####################################                 ###########</span><span style="color:#4fc3f7;">WWWW</span><span style="color:#9e9e9e;">##############</span>
<span style="color:#9e9e9e;">###############</span><span style="color:#4fc3f7;">WWWWW</span><span style="color:#9e9e9e;">############################################</span><span style="color:#4fc3f7;">WWWWWW</span><span style="color:#9e9e9e;">#############</span>
<span style="color:#9e9e9e;">################</span><span style="color:#4fc3f7;">WWW</span><span style="color:#9e9e9e;">############################################</span><span style="color:#4fc3f7;">WWWWWWWW</span><span style="color:#9e9e9e;">############</span>
 <span style="color:#7bd88f;">✓ World saved!</span>  <span style="color:#9aa0a6;">|  A/D:Move  W:Jump  Space:Use  1-5/E/R:Hotbar  I:Inv  C:Craft</span>
</pre>

## Controls

- `A / D` (or arrows): move
- `W` (or up): jump / swim stroke
- `Space`: use selected hotbar item
  - Consumables/armor use immediately
  - Tools/weapons/blocks/fist: directional use (press direction next)
- `1..5`: select hotbar slot
- `E / R`: next/prev hotbar slot
- `I` or `Tab`: inventory
- `C`: crafting
- `Q` / `Esc`: quit

## Running

```bash
python3 main.py
```

CLI options(Optional, as the game now has a main menu):

```bash
python3 main.py --seed 123 --save myworld --new
```

- `--seed`: world seed
- `--save`: save slot name
- `--new`: force fresh generation

## Configuration

Core files in `config/`:

- `game.json` – world/physics/water/save/day-night
- `blocks.json` – block defs + mining tiers
- `items.json` – item defs + classes/stats/colors
- `mobs.json` – mob defs, timings, movement speed, drops, spawn rules
- `recipes.json` – crafting recipes
- `biomes.json` – biome generation rules/blending
- `menu.json` – main menu labels + ASCII header
- `input.json` – key bindings
- `ui.json` – UI strings/layout
- `engine.json` – engine timing knobs
- `block_behaviors.json` – on-mine drop behaviors

Detailed schemas: see `CONTENT_FORMAT.md`.

## License

This project uses a custom **Attribution + Non-Commercial** license.

- You may use, modify, and redistribute the code with attribution.
- Commercial use requires prior permission from the project owner.

See `LICENSE` for full terms.

## Docs

- Architecture: `ARCHITECTURE.md`
- Roadmap: `PLAN.md`
- Task tracker: `TASKS.md`
- Config progress audit: `CONFIG_AUDIT.md`
