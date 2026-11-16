# Effects library (108 effects)

In the member kit this folder ships as `.claude/effects/`. Run every command from the kit folder, for example
`node .claude/effects/render_effect.mjs --list` (and `npm --prefix .claude/effects install` once). Examples below
are written from inside the effects folder; prefix the script path with `.claude/effects/` when running from the kit.

Silent 1920x1080 H.264 clips of animated graphics (maps, boards, charts, titles, photo layouts, news/article
cards, diagrams) with editable text, colours, numbers, data and image slots.

## Setup (once)

```
cd effects
npm install            # installs @napi-rs/canvas (pinned in package.json)
```

Needs Node 20+ and `ffmpeg` on PATH (or set `MOTION_FFMPEG` to its full path). Fonts are bundled (`fonts/`).

## Use

```
node render_effect.mjs --list              # JSON: every effect, its editable keys, its required keys
node render_effect.mjs --list-short        # one line per effect: id | name | purpose | default_s | min_s-max_s | images: required/optional/none
node render_effect.mjs --schema <effect-id>
node render_effect.mjs --check --id <effect-id> --overrides overrides.json --duration 6   # validate only: {"ok":true} or a JSON error
node render_effect.mjs --fingerprint       # {"fingerprint":"<sha256>"} of the code, data, assets, fonts and canvas version
node render_effect.mjs --id <effect-id> --overrides overrides.json --duration 6 --out clip.mp4 [--fps 30]
node render_effect.mjs --id <effect-id> --overrides overrides.json --frame 2.5 --out preview.png
```

`overrides.json` may only contain keys listed for that effect (`editable` in `--list`, `keys` in the schema).
Image slots are file paths relative to the folder that holds `overrides.json` (or `--assets-dir`); fewer
images than the layout has are repeated. Duration must be inside the effect's range (see the schema).
Output is exactly `round(duration x fps)` frames; the JSON printed on success has `clip_seconds` (length of the clip) and `render_seconds` (time it took). Errors: one JSON object on stderr and a non-zero exit
(2 = invalid input, 1 = render failure, 3 = setup problem such as missing ffmpeg or `npm install`).

Every picture slot is required: an effect that shows pictures (`images`, or a `backgroundImage` behind its content) refuses to render until you supply your own, so the bundled sample pictures never appear in a render. Map effects likewise require their `country`, `countries`, `points` and `mapBounds`. To see an effect's sample look only, use `--frame <seconds> --preview-sample --out preview.png` (never allowed for `--check` or a clip).

Settings marked `required` in the schema (see `required` in `--list`) have no usable sample value and must be supplied:
data-bearing numbers (percentage, counts, money, year range), chart `data`, and the `images` of any effect that shows a
specific person or subject (so the bundled placeholder faces never appear next to a real name). Rendering is refused
with a JSON error if one is missing.

Chart `data` replaces the sample data completely (it is never merged). Bar/pie/table style effects take
`[{"label": "...", "value": 12}]`; line/area/scatter effects take `[{"label": "...", "values": [1, 2, 3]}]`.
The schema says which one each effect uses and how many entries it supports (for example `ranked-bars` 1-5,
`paired-pies` exactly 2). The engine clamps data at zero, so negative values are not accepted.

Maps: `points` are `[longitude, latitude]` pairs, longitude first (London is `[-0.12, 51.5]`), and `mapBounds` is
`[west, south, east, north]` in degrees (latitude -85 to 85, at least 2 degrees wide). When you set `points`,
`countries` or `country` on an effect that has `mapBounds`, you must also set `mapBounds` so your places are on
screen, and `pointLabels` must have one entry per point.

Colours are `#rrggbb` only (six hex digits).

Country names are the English names in `countries.json`. `points` are `[longitude, latitude]`; `mapBounds` is
`[west, south, east, north]`. 

## Layout

`render_effect.mjs` CLI, `runtime.mjs` canvas/font/ffmpeg setup, `engine.mjs` + `base-engine.mjs` +
`three-engine.mjs` + `country-engine.mjs` drawing code, `presets/` full default settings,
`schema/` what members may set, `catalog.json` effect list, `assets/` sample media and map data,
`fonts/` bundled open fonts, `test/` tests (`npm test`), `tools/derive_schemas.mjs` regenerates the schemas
by checking which settings actually change each effect's frames.

Provenance and licences: `ASSET-SOURCES.md`, `fonts/OFL-*.txt`.
