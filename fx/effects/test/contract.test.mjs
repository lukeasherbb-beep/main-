// Contract tests: data replacement, required keys, schema enforcement, no-crash fuzz, --check / --fingerprint / --list-short.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { ROOT, catalog, createCanvas, environment } from '../runtime.mjs';
import { render } from '../engine.mjs';
import { prepare, loadSchema } from '../lib.mjs';
import { normalize } from '../base-engine.mjs';

const CLI = path.join(ROOT, 'render_effect.mjs');
const run = (args) => spawnSync(process.execPath, [CLI, ...args], { encoding: 'utf8', timeout: 180000 });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'effects-contract-'));
const wj = (name, o) => { const p = path.join(tmp, name); fs.writeFileSync(p, JSON.stringify(o)); return p; };
const probs = (id, overrides, extra = {}) => prepare({ id, overrides, assetsDir: ROOT, ...extra }).problems;
const keysOf = (ps) => ps.map((p) => p.key);

test('series data replaces the sample outright (no merging)', async () => {
  const given = [10, 20, 30, 40, 50].map((value, i) => ({ label: 'Item ' + i, value }));
  const r = prepare({ id: 'ranked-bars', overrides: { data: given }, assetsDir: ROOT });
  assert.deepEqual(r.problems, []);
  assert.deepEqual(r.q.data.map((d) => d.value), [10, 20, 30, 40, 50]);
  assert.deepEqual(r.q.data.map((d) => d.label), given.map((d) => d.label));
  // pixels: a 10% bar must not reach where the sample's 90% bar was
  const draw = async (data) => {
    const p = prepare({ id: 'ranked-bars', overrides: { data }, assetsDir: ROOT });
    const canvas = createCanvas(1920, 1080), c = canvas.getContext('2d');
    render(c, p.item, p.q, p.q.duration * 0.95, await environment(p.q));
    return c.getImageData(1000, 276, 1, 1).data; // row 1, x = 833/1600 of the way across
  };
  const small = await draw([{ label: 'A', value: 10 }]);
  const big = await draw([{ label: 'A', value: 90 }]);
  assert.notDeepEqual([...small], [...big]);
  // a single entry is supported (the engine used to draw 5 rows and crash on fewer)
  assert.equal(r.q.data.length, 5);
  assert.deepEqual(prepare({ id: 'ranked-bars', overrides: { data: [{ label: 'A', value: 10 }] }, assetsDir: ROOT }).problems, []);
  // line charts: values replace, value follows the last point, no stale sample figures
  const t = prepare({ id: 'single-trend', overrides: { data: [{ label: 'X', values: [1, 2, 3] }] }, assetsDir: ROOT });
  assert.deepEqual(t.q.data, [{ label: 'X', value: 3, values: [1, 2, 3] }]);
  // value vs values: using the wrong field is refused
  assert.ok(keysOf(probs('ranked-bars', { data: [{ label: 'A', values: [1, 2] }] })).includes('data[0].values'));
  assert.ok(keysOf(probs('single-trend', { data: [{ label: 'A', value: 5 }] })).includes('data[0].value'));
});

test('required keys are refused when missing', () => {
  const cases = [
    ['ranked-bars', {}, 'data'], ['percentage-ring', {}, 'number'], ['money-counter', {}, 'number'], ['population-count', {}, 'number'],
    ['wealth-network', {}, 'number'], ['brand-stat', {}, 'number'], ['crowd-callouts', {}, 'number'], ['distribution-map', {}, 'number'],
    ['image-to-crowd', {}, 'number'], ['regional-share', {}, 'number'], ['cost-arrow', {}, 'number'],
    ['year-slider', {}, 'yearStart'], ['year-slider', { yearStart: 2000 }, 'yearEnd'], ['paired-pies', {}, 'data'],
    ['quote-profile', { title: 'A. Person' }, 'images'], ['archive-profiles', {}, 'images'],
    ['flight-route', { points: [[0, 0], [10, 10]] }, 'mapBounds'], ['flight-route', { points: [[0, 0], [10, 10]], mapBounds: [-10, -10, 20, 20] }, 'pointLabels'],
    ['country-outlines', { countries: ['Japan'] }, 'mapBounds'],
  ];
  for (const [id, ov, key] of cases) {
    const ps = probs(id, ov);
    assert.ok(keysOf(ps).includes(key), `${id} ${JSON.stringify(ov)} should require ${key}; got ${JSON.stringify(ps)}`);
  }
  // the CLI refuses with exit 2 and a JSON error
  const r = run(['--id', 'percentage-ring', '--duration', '5', '--out', path.join(tmp, 'x.mp4')]);
  assert.equal(r.status, 2);
  assert.equal(JSON.parse(r.stderr).details[0].key, 'number');
  assert.ok(!fs.existsSync(path.join(tmp, 'x.mp4')));
  // every required key is announced in the schema and --list
  const list = JSON.parse(run(['--list']).stdout);
  assert.ok(list.find((e) => e.id === 'percentage-ring').required.includes('number'));
});

test('schema claims are enforced: integer, colour, bounds, counts, empty image lists', () => {
  const bad = (id, ov, key) => { const ps = probs(id, ov); assert.ok(keysOf(ps).some((k) => k === key || k.startsWith(key)), `${id} ${JSON.stringify(ov)} -> ${JSON.stringify(ps)}`); };
  const yr = { yearStart: 2000, yearEnd: 2010 };
  bad('year-slider', { yearStart: 2000.5, yearEnd: 2010 }, 'yearStart');
  bad('year-slider', { yearStart: 2010, yearEnd: 2005 }, 'yearEnd');
  bad('percentage-ring', { number: 120 }, 'number');
  bad('percentage-ring', { number: 50, accent: '#fff' }, 'accent');
  bad('percentage-ring', { number: 50, accent: 'blue' }, 'accent');
  bad('percentage-ring', { number: 50, accent: '#12345g' }, 'accent');
  const fr = { points: [[0, 0]], pointLabels: ['A'] };
  bad('flight-route', { ...fr, mapBounds: [10, 10, 5, 20] }, 'mapBounds');
  bad('flight-route', { ...fr, mapBounds: [-200, 0, 10, 20] }, 'mapBounds');
  bad('flight-route', { ...fr, mapBounds: [0, 0, 10, 90] }, 'mapBounds');
  bad('flight-route', { ...fr, mapBounds: [0, 0, 0.5, 20] }, 'mapBounds');
  bad('flight-route', { ...fr, mapBounds: [0, 0, 10] }, 'mapBounds');
  bad('flight-route', { ...fr, mapBounds: [0, 0, 10, 20], pointLabels: ['A', 'B'] }, 'pointLabels');
  bad('flight-route', { ...fr, mapBounds: [0, 0, 10, 20], points: [[0, 95]] }, 'points');
  const row = (n) => Array.from({ length: n }, (_, i) => ({ label: 'L' + i, value: 10 }));
  bad('ranked-bars', { data: row(6) }, 'data');
  bad('ranked-bars', { data: [] }, 'data');
  bad('paired-pies', { data: row(1) }, 'data');
  bad('paired-pies', { data: row(3) }, 'data');
  bad('paired-pies', { data: [{ label: 'A', value: 50 }, { label: 'B', value: 101 }] }, 'data[1].value');
  bad('single-trend', { data: [{ label: 'A', values: [1] }] }, 'data[0].values');
  bad('single-trend', { data: [{ label: 'A', values: [1, 2] }, { label: 'B', values: [1, 2] }] }, 'data');
  bad('two-trends', { data: [{ label: 'A', values: [1, 2] }] }, 'data');
  bad('country-labels', { countries: ['Japan', 'China'], mapBounds: [80, 10, 150, 55], data: [{ value: 1 }] }, 'data');
  bad('evidence-wall', { images: [] }, 'images');
  bad('evidence-wall', { images: Array(40).fill('assets/globe.png') }, 'images');
  bad('news-image', { title: 'x', images: [] }, 'images');
  bad('news-image', { title: 'x', bogus: 1 }, 'bogus');
  assert.deepEqual(probs('year-slider', { ...yr, backgroundImage: 'assets/landscape-3.png' }), []);
});

// ---------- fuzz: schema-valid input must never crash the engine ----------
const SAMPLE_COUNTRIES = ['Japan', 'Brazil', 'Egypt', 'France', 'Germany', 'India', 'Kenya', 'Peru'];
const IMAGES = ['assets/globe.png', 'assets/rocket.png', 'assets/heart.png', 'assets/fuel.png', 'assets/truck.png', 'assets/crowd.png', 'assets/money.png', 'assets/object.png'];
function generate(schema, mode) { // mode: 'min' | 'max' | 'required'
  const ov = {}, hi = mode === 'max';
  const W = (n) => 'W'.repeat(n);
  const order = Object.keys(schema.keys).sort((a, b) => ['countries', 'points'].includes(b) - ['countries', 'points'].includes(a));
  for (const k of order) {
    const s = schema.keys[k];
    if (mode === 'required' && !s.required) continue;
    switch (s.type) {
      case 'text': ov[k] = hi ? W(s.maxLength) : ''; break;
      case 'color': ov[k] = hi ? '#ffffff' : '#000000'; break;
      case 'number': ov[k] = hi ? s.max : s.min; break;
      case 'enum': ov[k] = hi ? s.values.at(-1) : s.values[0]; break;
      case 'country': ov[k] = hi ? 'Brazil' : 'Japan'; break;
      case 'country_list': ov[k] = SAMPLE_COUNTRIES.slice(0, hi ? s.maxItems : s.minItems); break;
      case 'bounds': ov[k] = hi ? [-180, -85, 180, 85] : [10, 10, 12, 12]; break;
      case 'point_list': ov[k] = (hi ? [[-180, -85], [180, 85], [0, 0], [10, 10], [-10, 20], [30, -30], [100, 50], [-100, -50]] : [[0, 0]]).slice(0, hi ? s.maxItems : s.minItems); break;
      case 'image': ov[k] = IMAGES[0]; break;
      case 'image_list': ov[k] = IMAGES.slice(0, hi ? s.maxItems : 1); break;
      case 'text_list': ov[k] = Array.from({ length: hi ? s.maxItems : s.minItems }, () => (hi ? W(s.item.maxLength) : '')); break;
      case 'series_list': {
        let n = hi ? s.maxItems : s.minItems;
        if (s.matchCount) n = (ov[s.matchCount] ?? schema.keys[s.matchCount].default).length;
        ov[k] = Array.from({ length: n }, (_, i) => {
          const e = {}; if (s.needLabel) e.label = hi ? W(s.label.maxLength) : 'L' + i;
          const nv = (j) => (hi ? s.number.max : s.number.min) * (j % 2 ? 0.5 : 1);
          if (s.mode === 'value') e.value = nv(0);
          else e.values = Array.from({ length: hi ? s.values.maxItems : s.values.minItems }, (_, j) => nv(j));
          return e;
        }); break;
      }
      default: throw new Error('fuzz: type ' + s.type);
    }
  }
  if (ov.pointLabels && ov.points) ov.pointLabels = ov.pointLabels.slice(0, ov.points.length).concat(Array(Math.max(0, ov.points.length - ov.pointLabels.length)).fill(''));
  if (ov.yearEnd !== undefined && ov.yearStart !== undefined) { ov.yearStart = hi ? 2998 : 1; ov.yearEnd = hi ? 3000 : 2; }
  return ov;
}

test('fuzz: every effect renders at min / max / required-only settings and at min / max duration', async () => {
  const failures = [];
  for (const c of catalog) {
    const schema = loadSchema(c.id);
    for (const mode of ['min', 'max', 'required']) {
      const ov = generate(schema, mode);
      for (const dur of [schema.duration.min, schema.duration.max]) {
        const p = prepare({ id: c.id, overrides: ov, duration: dur, assetsDir: ROOT });
        if (p.problems.length) { failures.push(`${c.id} [${mode}] rejected its own generated input: ${JSON.stringify(p.problems)}`); continue; }
        try {
          const env = await environment(p.q);
          const canvas = createCanvas(480, 270), ctx = canvas.getContext('2d');
          for (const t of [0, dur * 0.5, dur]) render(ctx, p.item, p.q, t, env);
        } catch (e) { failures.push(`${c.id} [${mode}] dur=${dur} crashed: ${e.message}`); }
      }
    }
  }
  assert.deepEqual(failures, []);
});

test('series entries survive the engine normaliser unchanged (nothing silently dropped or clamped)', () => {
  let checked = 0;
  for (const c of catalog) {
    const schema = loadSchema(c.id);
    if (!schema.keys.data) continue;
    for (const mode of ['min', 'max']) {
      const p = prepare({ id: c.id, overrides: generate(schema, mode), assetsDir: ROOT });
      assert.deepEqual(p.problems, [], c.id);
      const n = normalize(p.item, p.q).data;
      assert.equal(n.length, p.q.data.length, `${c.id} [${mode}] entries dropped by the engine`);
      n.forEach((d, i) => { assert.equal(d.value, p.q.data[i].value, `${c.id} value ${i}`); assert.deepEqual(d.values, p.q.data[i].values, `${c.id} values ${i}`); });
      checked++;
    }
  }
  assert.ok(checked >= 20);
});

test('an empty badge/label text draws no box', async () => {
  const draw = async (label) => {
    const p = prepare({ id: 'news-lower-third', overrides: { label, backgroundImage: 'assets/landscape-3.png' }, assetsDir: ROOT });
    const canvas = createCanvas(960, 540), c = canvas.getContext('2d');
    render(c, p.item, p.q, p.q.duration * 0.9, await environment(p.q));
    return Buffer.from(c.getImageData(0, 0, 960, 540).data.buffer).toString('base64');
  };
  const empty = await draw(''), spaces = await draw('   '), some = await draw('LIVE');
  assert.equal(empty, spaces);
  assert.notEqual(empty, some);
});

test('--check validates like a render and writes nothing', () => {
  const out = path.join(tmp, 'check-out.mp4');
  const good = wj('good.json', { number: 64 });
  let r = run(['--check', '--id', 'percentage-ring', '--overrides', good, '--duration', '6']);
  assert.equal(r.status, 0, r.stderr); assert.deepEqual(JSON.parse(r.stdout), { ok: true });
  r = run(['--check', '--id', 'percentage-ring', '--overrides', wj('b1.json', {}), '--duration', '6']);
  assert.equal(r.status, 2); assert.equal(JSON.parse(r.stderr).error, 'invalid_input');
  r = run(['--check', '--id', 'percentage-ring', '--overrides', good, '--duration', '600']);
  assert.equal(r.status, 2);
  r = run(['--check', '--id', 'percentage-ring', '--overrides', good, '--fps', '7']);
  assert.equal(r.status, 2);
  r = run(['--check', '--id', 'evidence-wall', '--overrides', wj('b2.json', { images: ['nope.png'] })]);
  assert.equal(r.status, 2);
  r = run(['--check', '--id', 'evidence-wall', '--overrides', wj('b3.json', { images: ['globe.png'] }), '--assets-dir', path.join(ROOT, 'assets')]);
  assert.equal(r.status, 0, r.stderr);
  assert.ok(!fs.existsSync(out));
});

test('--fingerprint is a stable sha256 of the library', () => {
  const a = JSON.parse(run(['--fingerprint']).stdout).fingerprint, b = JSON.parse(run(['--fingerprint']).stdout).fingerprint;
  assert.match(a, /^[0-9a-f]{64}$/); assert.equal(a, b);
});

test('--list-short has 108 lines in the agreed format (images: required|none)', () => {
  const r = run(['--list-short']);
  assert.equal(r.status, 0, r.stderr);
  const lines = r.stdout.trimEnd().split('\n');
  assert.equal(lines.length, 108);
  for (const l of lines) assert.match(l, /^[a-z0-9-]+ \| .+ \| .+ \| \d+(\.\d+)? \| \d+-\d+ \| images: (required|none)$/, l);
  assert.ok(lines.some((l) => l.endsWith('images: required')) && lines.some((l) => l.endsWith('images: none')));
  assert.ok(!r.stdout.includes('optional'));
});

test('--frame reports errors as JSON too', () => {
  const r = run(['--id', 'percentage-ring', '--frame', '1', '--out', path.join(tmp, 'f.png')]);
  assert.equal(r.status, 2); assert.equal(JSON.parse(r.stderr).error, 'invalid_input');
  const ok = run(['--id', 'percentage-ring', '--overrides', wj('f.json', { number: 40 }), '--frame', '2', '--out', path.join(tmp, 'f2.png')]);
  assert.equal(ok.status, 0, ok.stderr);
  const badT = run(['--id', 'percentage-ring', '--overrides', wj('f.json', { number: 40 }), '--frame', '-3', '--out', path.join(tmp, 'f3.png')]);
  assert.equal(badT.status, 2);
});

test('no sample real-world names remain in presets', () => {
  const banned = /\b(FBI|Bitcoin|Falcon Heavy|Trump|Iraq|Reuters|Guardian|Qaboos|Tehran|Wuhan|Huanan)\b/i;
  for (const f of fs.readdirSync(path.join(ROOT, 'presets'))) assert.ok(!banned.test(fs.readFileSync(path.join(ROOT, 'presets', f), 'utf8')), f);
});

test('every image slot is required, and bundled pictures never reach a render', async () => {
  const blank = createCanvas(64, 36); { const x = blank.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, 64, 36); }
  let slots = 0, bg = 0;
  for (const c of catalog) {
    const schema = loadSchema(c.id);
    if (schema.keys.images) { slots++; assert.equal(schema.keys.images.required, true, c.id + ' images must be required'); }
    // member config with only the required keys: the bundled mountain picture must not change a single pixel
    const p = prepare({ id: c.id, overrides: generate(schema, 'required'), assetsDir: ROOT });
    assert.deepEqual(p.problems, [], c.id);
    const frames = async (swap) => {
      const env = await environment(p.q); if (swap) env.mountain = blank;
      const canvas = createCanvas(480, 270), ctx = canvas.getContext('2d'); const out = [];
      for (const f of [0.3, 0.9]) { render(ctx, p.item, p.q, f * p.q.duration, env); out.push(Buffer.from(ctx.getImageData(0, 0, 480, 270).data.buffer).toString('base64')); }
      return out.join();
    };
    assert.equal(await frames(false), await frames(true), c.id + ': the bundled mountain image still reaches a render');
    if (schema.keys.backgroundImage?.required) bg++;
  }
  assert.equal(slots, 57); assert.ok(bg >= 25);
  // no image slot is optional: --list-short never says so, and every effect with a slot is "required"
  for (const id of ['question-focus', 'feature-card']) assert.equal(loadSchema(id).keys.backgroundImage.required, true, id);
});

test('map effects: every default region is required to be replaced', () => {
  for (const c of catalog) {
    const s = loadSchema(c.id);
    for (const k of ['mapBounds', 'country', 'countries', 'points']) if (s.keys[k]) assert.equal(s.keys[k].required, true, c.id + ':' + k);
  }
  const ps = prepare({ id: 'regional-share', overrides: { number: 30 }, assetsDir: ROOT }).problems;
  assert.deepEqual(keysOf(ps), ['mapBounds']);
  const msg = prepare({ id: 'question-focus', overrides: {}, assetsDir: ROOT }).problems.find((p) => p.key === 'backgroundImage').message;
  assert.equal(msg, 'override backgroundImage must be set: this effect shows your own picture(s); the bundled sample image is never used in a render');
  const m2 = prepare({ id: 'evidence-wall', overrides: {}, assetsDir: ROOT }).problems[0].message;
  assert.match(m2, /override images must be set: this effect shows your own picture/);
});

test('--preview-sample: sample look only for --frame; plain --frame follows the render rules', () => {
  const f = path.join(tmp, 'sample.png');
  let r = run(['--id', 'question-focus', '--frame', '2', '--out', f]);
  assert.equal(r.status, 2); assert.ok(!fs.existsSync(f));
  r = run(['--id', 'question-focus', '--frame', '2', '--preview-sample', '--out', f]);
  assert.equal(r.status, 0, r.stderr); assert.ok(fs.statSync(f).size > 10000);
  r = run(['--id', 'question-focus', '--preview-sample', '--out', path.join(tmp, 'x.mp4')]);
  assert.equal(r.status, 2); assert.equal(JSON.parse(r.stderr).error, 'bad_arguments');
  r = run(['--check', '--id', 'question-focus', '--frame', '1', '--preview-sample']);
  assert.equal(r.status, 2);
});

test('render JSON reports clip_seconds and render_seconds; default durations are tidy', () => {
  const out = path.join(tmp, 'tidy.mp4');
  const r = run(['--id', 'percentage-ring', '--overrides', wj('pr.json', { number: 50 }), '--duration', '3', '--out', out]);
  assert.equal(r.status, 0, r.stderr);
  const j = JSON.parse(r.stdout);
  assert.equal(j.clip_seconds, 3); assert.equal(typeof j.render_seconds, 'number'); assert.ok(!('seconds' in j));
  for (const c of catalog) {
    const d = loadSchema(c.id).duration;
    for (const k of ['default', 'min', 'max']) assert.equal(Math.round(d[k] * 10) / 10, d[k], c.id + ' ' + k);
  }
});

test.after(() => { try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {} });
