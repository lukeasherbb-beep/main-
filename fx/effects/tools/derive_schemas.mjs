// Derives schema/<id>.json for every effect.
// A preset key is "editable" only if changing it measurably changes the rendered frames (checked at three times),
// so the schema lists exactly the settings that do something for that effect.
//   node tools/derive_schemas.mjs [effect-id ...]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import { ROOT, catalog, createCanvas, environment, world } from '../runtime.mjs';
import { render } from '../engine.mjs';

try { os.setPriority(0, os.constants.priority.PRIORITY_BELOW_NORMAL); } catch {}

const SIZE = [960, 540];
const NEVER = new Set(['template', 'font', 'theme', 'transparent', 'duration', 'crops', 'mediaStart', 'backdrop', 'autoFit']);
const COLOR_KEYS = new Set(['accent', 'secondary', 'background', 'foreground']);
const TEXT = { title: 120, subtitle: 160, body: 600, label: 80, highlight: 160, chapter: 8, prefix: 8, suffix: 12, unit: 24 };
// a preset whose own sample text is longer than the general limit gets a limit that fits its sample
const PLACE_SAMPLE = { 'map-to-city': 'Harbor district' };
const TEXT_LONGER = { 'brand-stat': { suffix: 24 } };
const NUMBER = {
  number: { min: -1e9, max: 1e9 }, yearStart: { min: 0, max: 3000, integer: true }, yearEnd: { min: 0, max: 3000, integer: true },
  enter: { min: 0.03, max: 0.45 }, exit: { min: 0, max: 0.4 }, motion: { min: 0, max: 2 }, zoom: { min: 0.5, max: 6 },
  focusX: { min: 0, max: 1 }, focusY: { min: 0, max: 1 }, backgroundFocusY: { min: 0, max: 1 }, decimals: { min: 0, max: 6, integer: true },
};
const NUM_ALT = { enter: 0.4, exit: 0.3, motion: 1.8, zoom: null, focusX: null, focusY: null, decimals: 4 };
const SAMPLE_IMG = ['assets/globe.png', 'assets/rocket.png', 'assets/heart.png', 'assets/fuel.png', 'assets/truck.png', 'assets/crowd.png', 'assets/money.png', 'assets/object.png', 'assets/eclipse.png', 'assets/phases.png'];

function perturb(key, v, q) {
  if (COLOR_KEYS.has(key)) return v === '#12ab34' ? '#ab1234' : '#12ab34';
  if (key === 'images') return v.map((_, i) => SAMPLE_IMG[(i + 3) % SAMPLE_IMG.length]);
  if (key === 'backgroundImage') return 'assets/landscape-3.png';
  if (key === 'country') return v === 'Japan' ? 'Brazil' : 'Japan';
  if (key === 'countries') return v.length ? ['Japan', 'Brazil', 'Egypt'].slice(0, Math.max(1, v.length)) : ['Japan'];
  if (key === 'mapBounds') return [v[0] + 20, v[1] + 8, v[2] - 20, v[3] - 8];
  if (key === 'points') return v.map((p) => [p[0] + 9, p[1] - 4]);
  if (key === 'data') return v.map((s) => ({ ...s, label: (s.label || '') + ' Xq', value: (s.value ?? 10) * 0.5 + 3, values: (s.values || []).map((x) => x * 0.5 + 4) }));
  if (key === 'highlight') return 'Every|Follow|Replace|details';
  if (key === 'fit') return v === 'cover' ? 'contain' : 'cover';
  if (Array.isArray(v)) return v.length ? v.map((s) => String(s) + ' Xq') : ['Alpha', 'Beta', 'Gamma'];
  if (typeof v === 'number') {
    if (key in NUM_ALT && NUM_ALT[key] !== null) return NUM_ALT[key];
    if (key === 'zoom') return v * 1.35;
    if (key === 'focusX' || key === 'focusY' || key === 'backgroundFocusY') return v > 0.5 ? 0.15 : 0.85;
    if (key === 'yearStart' || key === 'yearEnd') return v - 7;
    return v * 1.5 + 7;
  }
  if (typeof v === 'string') return v ? v + ' Xq' : 'Test Xq';
  return undefined;
}

const BLANK = createCanvas(64, 36); { const x = BLANK.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, 64, 36); }
// true when the bundled mountain picture still shows with no backgroundImage set
async function mountainLeaks(item, base, times) {
  const q = JSON.parse(JSON.stringify(base)); q.backgroundImage = '';
  q.images = q.images.map((_, i) => SAMPLE_IMG[i % SAMPLE_IMG.length]);
  const a = await frames(item, q, await environment(q), times);
  const env2 = await environment(q); env2.mountain = BLANK;
  const b = await frames(item, q, env2, times);
  return a.some((x, i) => x !== b[i]);
}
async function frames(item, q, env, times) {
  const canvas = createCanvas(SIZE[0], SIZE[1]), c = canvas.getContext('2d');
  return times.map((t) => {
    render(c, item, q, t, env);
    return crypto.createHash('md5').update(Buffer.from(c.getImageData(0, 0, SIZE[0], SIZE[1]).data.buffer)).digest('hex');
  });
}

const only = process.argv.slice(2);
const countries = [...new Set(world.features.map((f) => f.properties.ADMIN))].sort();
fs.writeFileSync(path.join(ROOT, 'countries.json'), JSON.stringify(countries));
fs.mkdirSync(path.join(ROOT, 'schema'), { recursive: true });
const report = {};

for (const item of catalog) {
  if (only.length && !only.includes(item.id)) continue;
  const base = JSON.parse(fs.readFileSync(path.join(ROOT, 'presets', item.id + '.json'), 'utf8'));
  const times = [0.3, 0.6, 0.92].map((f) => f * base.duration);
  const candidates = Object.keys(base).filter((k) => !NEVER.has(k));
  if (['stat', 'cost'].includes(item.variant) || !('decimals' in base)) candidates.push('decimals');
  const baseEnv = await environment(base);
  const ref = await frames(item, base, baseEnv, times);
  const used = [], failed = [];
  for (const key of candidates) {
    const q = JSON.parse(JSON.stringify(base));
    const cur = key in base ? base[key] : 2;
    const alt = perturb(key, cur, base);
    if (alt === undefined) continue;
    q[key] = alt;
    try {
      const env = (key === 'images' || key === 'backgroundImage') ? await environment(q) : baseEnv;
      const h = await frames(item, q, env, times);
      if (h.some((x, i) => x !== ref[i])) used.push(key);
    } catch (e) { failed.push(key + ': ' + e.message); }
  }
  const leaks = await mountainLeaks(item, base, times);
  const keys = {};
  const SERIES = {
    horizontal: { mode: 'value', min: 1, max: 5, needLabel: true, num: [0, 100] },
    table: { mode: 'value', min: 1, max: 4, needLabel: false, num: [0, 1e12] },
    pies: { mode: 'value', min: 2, max: 2, needLabel: true, num: [0, 100] },
    portraits: { mode: 'value', min: 1, max: 3, needLabel: false, num: [0, 1e12] },
    bars: { mode: 'value', min: 1, max: 2, needLabel: true, num: [0, 1e12] },
    labels: { mode: 'value', min: 1, max: 8, needLabel: false, num: [0, 1e9], matchCount: 'countries' },
    scatter: { mode: 'values', min: 1, max: 1, needLabel: true }, single: { mode: 'values', min: 1, max: 1, needLabel: true },
    'logo-line': { mode: 'values', min: 1, max: 1, needLabel: true }, area: { mode: 'values', min: 1, max: 1, needLabel: true },
    lines: { mode: 'values', min: 2, max: 2, needLabel: true }, panel: { mode: 'values', min: 2, max: 2, needLabel: true },
    'three-lines': { mode: 'values', min: 3, max: 3, needLabel: true },
  };
  const REQUIRED_NUMBER = new Set(['percentage-ring', 'money-counter', 'population-count', 'wealth-network', 'brand-stat', 'crowd-callouts', 'distribution-map', 'image-to-crowd', 'regional-share', 'cost-arrow']);
  const PERCENT = new Set(['percentage-ring', 'regional-share']);
  const personImages = base.images.some((i) => /person/.test(i));
  for (const key of used) {
    const v = key in base ? base[key] : 2;
    if (key in TEXT) keys[key] = { type: 'text', maxLength: TEXT_LONGER[item.id]?.[key] ?? TEXT[key], default: v };
    else if (COLOR_KEYS.has(key)) keys[key] = { type: 'color', format: '#rrggbb', default: v };
    else if (key === 'number') keys[key] = { type: 'number', min: 0, max: PERCENT.has(item.id) ? 100 : 1e15, required: REQUIRED_NUMBER.has(item.id) || undefined, default: v };
    else if (key === 'yearStart') keys[key] = { type: 'number', integer: true, min: 1, max: 3000, required: true, default: v };
    else if (key === 'yearEnd') keys[key] = { type: 'number', integer: true, min: 2, max: 3000, greaterThan: 'yearStart', required: true, default: v };
    else if (key in NUMBER) keys[key] = { type: 'number', ...NUMBER[key], default: v };
    else if (key === 'images') keys[key] = { type: 'image_list', maxItems: Math.max(base.images.length, item.slots), slots: base.images.length, required: true, default: base.images };
    else if (key === 'backgroundImage') keys[key] = { type: 'image', required: leaks || undefined, default: v };
    else if (key === 'country') keys[key] = { type: 'country', required: true, default: v };
    else if (key === 'countries') keys[key] = { type: 'country_list', required: true, minItems: 1, maxItems: Math.max(v.length, 8), default: v };
    else if (key === 'mapBounds') keys[key] = { type: 'bounds', required: true, format: '[west, south, east, north] in degrees', default: v };
    else if (key === 'points') keys[key] = { type: 'point_list', required: true, format: '[longitude, latitude] pairs, longitude first', minItems: 1, maxItems: Math.max(v.length, 8), default: v };
    else if (key === 'fit') keys[key] = { type: 'enum', values: ['cover', 'contain'], default: v };
    else if (key === 'data') {
      const sp = SERIES[item.variant];
      if (!sp) throw new Error('no series rule for ' + item.id + ' variant ' + item.variant);
      keys[key] = { type: 'series_list', mode: sp.mode, required: true, minItems: sp.min, maxItems: sp.max, needLabel: sp.needLabel,
        label: { maxLength: 40 }, number: sp.mode === 'value' ? { min: sp.num[0], max: sp.num[1] } : { min: 0, max: 1e9 },
        ...(sp.mode === 'values' ? { values: { minItems: 2, maxItems: 24 } } : {}), ...(sp.matchCount ? { matchCount: sp.matchCount } : {}),
        note: sp.mode === 'value' ? 'each entry is {label, value}; replaces the sample data entirely' : 'each series is {label, values:[numbers]}; replaces the sample data entirely',
        // the sample must itself pass validation: a value-mode series carries `value` only (the renderer adds its own `values`)
        default: sp.mode === 'value' ? v.map((s) => ({ ...(s.label !== undefined ? { label: s.label } : {}), value: s.value })) : v };
    } else if (key === 'backgroundFocusY') keys[key] = { type: 'number', min: 0, max: 1, default: v };
    else if (key === 'pointLabels') keys[key] = { type: 'text_list', minItems: 1, maxItems: 8, item: { maxLength: 40 }, sameLengthAs: 'points', required: keys.points ? true : undefined,
      // a preset with no labels shows the title instead; the schema sample still needs one label so it passes validation
      default: v.length ? v : [PLACE_SAMPLE[item.id] || 'Sample place'] };
    else if (key === 'axisLabels') keys[key] = { type: 'text_list', minItems: 1, maxItems: 8, item: { maxLength: 24 }, default: v };
    else if (Array.isArray(v)) keys[key] = { type: 'text_list', minItems: 1, maxItems: v.length ? v.length : 8, pad: v.length || undefined, item: { maxLength: 100 }, default: v };
    else keys[key] = { type: 'text', maxLength: 100, default: v };
    if (keys[key].required === undefined) delete keys[key].required;
  }
  const d = Math.round(base.duration * 10) / 10;
  const schema = {
    id: item.id, name: item.name, family: item.family, purpose: item.purpose,
    duration: { default: d, min: Math.max(2, Math.round(d * 0.5)), max: Math.min(30, Math.round(d * 3)) },
    fps: { default: 30, min: 10, max: 60 },
    imageSlots: keys.images ? keys.images.slots : 0,
    notes: 'Image paths are relative to the folder holding the overrides file. Fewer images than the layout has: they repeat. Keys marked required have no usable sample figure and must be supplied. Text may use "|" as a line break where the sample does.',
    keys,
  };
  fs.writeFileSync(path.join(ROOT, 'schema', item.id + '.json'), JSON.stringify(schema, null, 1));
  report[item.id] = { used: used.length, keys: used, failed };
  console.log(item.id.padEnd(28), String(used.length).padStart(2), used.join(','), failed.length ? 'FAILED: ' + failed.join(' | ') : '');
}
if (!only.length) fs.writeFileSync(path.join(ROOT, 'tools', 'derive_report.json'), JSON.stringify(report, null, 1));
