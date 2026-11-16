// node --test test/*.test.mjs   (from the effects folder; needs npm install + ffmpeg/ffprobe on PATH)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CLI = path.join(ROOT, 'render_effect.mjs');
const FFPROBE = process.env.MOTION_FFPROBE || 'ffprobe';
const run = (args, opts = {}) => spawnSync(process.execPath, [CLI, ...args], { encoding: 'utf8', timeout: 180000, ...opts });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'effects-test-'));
const writeJson = (name, obj) => { const p = path.join(tmp, name); fs.writeFileSync(p, JSON.stringify(obj)); return p; };
const probe = (file) => {
  const r = spawnSync(FFPROBE, ['-v', 'error', '-count_frames', '-show_entries', 'stream=codec_type,codec_name,width,height,pix_fmt,nb_read_frames,r_frame_rate', '-of', 'json', file], { encoding: 'utf8' });
  assert.equal(r.status, 0, 'ffprobe failed: ' + r.stderr);
  return JSON.parse(r.stdout).streams;
};

test('--list returns 108 effects, none with references', () => {
  const r = run(['--list']);
  assert.equal(r.status, 0, r.stderr);
  const list = JSON.parse(r.stdout);
  assert.equal(list.length, 108);
  assert.equal(new Set(list.map((x) => x.id)).size, 108);
  assert.ok(!/references?/i.test(r.stdout), 'list output must not mention references');
  for (const e of list) {
    for (const k of ['id', 'name', 'family', 'purpose', 'duration', 'editable']) assert.ok(k in e, `${e.id} missing ${k}`);
    assert.ok(Array.isArray(e.editable));
    assert.ok(fs.existsSync(path.join(ROOT, 'schema', e.id + '.json')), `schema for ${e.id}`);
    assert.ok(fs.existsSync(path.join(ROOT, 'presets', e.id + '.json')), `preset for ${e.id}`);
  }
  const fams = new Set(list.map((x) => x.family));
  for (const f of ['map', 'board', 'chart', 'title', 'gallery', 'article']) assert.ok(fams.has(f), 'family ' + f);
});

test('overrides validation: unknown key, bad colour, range, bad image paths', () => {
  const out = path.join(tmp, 'never.mp4');
  const cases = [
    [{ bogus: 1 }, 'bogus'],
    [{ accent: 'red' }, 'accent'],
    [{ title: 'x'.repeat(500) }, 'title'],
    [{ title: 5 }, 'title'],
  ];
  for (const [ov, key] of cases) {
    const r = run(['--id', 'country-trace', '--overrides', writeJson('ov.json', { country: 'Japan', ...ov }), '--duration', '4', '--out', out]);
    assert.notEqual(r.status, 0, 'should reject ' + JSON.stringify(ov));
    const err = JSON.parse(r.stderr.trim().split('\n').pop());
    assert.equal(err.error, 'invalid_input');
    assert.ok(err.details.some((d) => d.key === key), `error names key ${key}: ${r.stderr}`);
  }
  // duration range and unknown effect
  let r = run(['--id', 'country-trace', '--overrides', writeJson('c.json', { country: 'Japan' }), '--duration', '500', '--out', out]);
  assert.notEqual(r.status, 0); assert.equal(JSON.parse(r.stderr).details[0].key, 'duration');
  r = run(['--id', 'no-such-effect', '--out', out]);
  assert.notEqual(r.status, 0); assert.equal(JSON.parse(r.stderr).error, 'unknown_effect');
  // image slot problems
  fs.writeFileSync(path.join(tmp, 'notes.txt'), 'hi');
  fs.writeFileSync(path.join(tmp, 'fake.png'), 'this is not an image');
  for (const bad of ['missing.png', '../x.png', 'notes.txt', path.join(tmp, 'abs.png')]) {
    r = run(['--id', 'evidence-wall', '--overrides', writeJson('img.json', { images: [bad] }), '--duration', '5', '--out', out]);
    assert.notEqual(r.status, 0, 'should reject image ' + bad);
    assert.equal(JSON.parse(r.stderr).error, 'invalid_input');
  }
  r = run(['--id', 'evidence-wall', '--overrides', writeJson('img.json', { images: ['fake.png'] }), '--duration', '5', '--out', out]);
  assert.notEqual(r.status, 0, 'undecodable image must be rejected');
  assert.ok(!fs.existsSync(out), 'no output file after a rejected request');
});

test('render: exact frame count, 1920x1080, silent H.264 yuv420p', () => {
  for (const [duration, fps] of [[3, 30], [3.4, 24]]) {
    const out = path.join(tmp, `ct-${fps}.mp4`);
    const r = run(['--id', 'country-trace', '--overrides', writeJson('t.json', { title: 'Test Title', accent: '#00ccff', country: 'Japan' }), '--duration', String(duration), '--fps', String(fps), '--out', out]);
    assert.equal(r.status, 0, r.stderr);
    const streams = probe(out);
    assert.equal(streams.filter((s) => s.codec_type === 'audio').length, 0, 'must be silent');
    const v = streams.find((s) => s.codec_type === 'video');
    assert.equal(v.codec_name, 'h264'); assert.equal(v.pix_fmt, 'yuv420p');
    assert.equal(v.width, 1920); assert.equal(v.height, 1080);
    assert.equal(Number(v.nb_read_frames), Math.round(duration * fps));
  }
});

test('image slot: member image replaces the sample and is used', () => {
  // make a plain magenta PNG with the library's own canvas module
  const mk = spawnSync(process.execPath, ['--input-type=module', '-e', `
    import { createCanvas } from '@napi-rs/canvas'; import fs from 'node:fs';
    const c = createCanvas(800, 450), x = c.getContext('2d'); x.fillStyle = '#ff00ff'; x.fillRect(0, 0, 800, 450);
    fs.writeFileSync(${JSON.stringify(path.join(tmp, 'magenta.png'))}, c.toBuffer('image/png'));`], { encoding: 'utf8', cwd: ROOT });
  assert.equal(mk.status, 0, mk.stderr);
  const a = path.join(tmp, 'wall-default.png'), b = path.join(tmp, 'wall-member.png');
  const base = run(['--id', 'evidence-wall', '--overrides', writeJson('wall0.json', { images: ['globe.png'] }), '--assets-dir', path.join(ROOT, 'assets'), '--frame', '3', '--out', a]);
  assert.equal(base.status, 0, base.stderr);
  const r = run(['--id', 'evidence-wall', '--overrides', writeJson('wall.json', { images: ['magenta.png'] }), '--frame', '3', '--out', b]);
  assert.equal(r.status, 0, r.stderr);
  assert.notDeepEqual(fs.readFileSync(a), fs.readFileSync(b));
  assert.ok(fs.statSync(b).size > 10000);
});

test('schema keys use known types and each duration range contains its default', () => {
  const types = new Set(['text', 'color', 'number', 'text_list', 'country', 'country_list', 'bounds', 'point_list', 'series_list', 'image_list', 'image', 'enum']);
  for (const f of fs.readdirSync(path.join(ROOT, 'schema'))) {
    const s = JSON.parse(fs.readFileSync(path.join(ROOT, 'schema', f), 'utf8'));
    assert.ok(s.duration.min <= s.duration.default && s.duration.default <= s.duration.max, s.id + ' duration range');
    for (const [k, spec] of Object.entries(s.keys)) assert.ok(types.has(spec.type), `${s.id}.${k} type ${spec.type}`);
  }
});

// ---- hygiene: nothing machine-specific, no system fonts, no reference material ----
const SKIP_DIRS = new Set(['node_modules', 'test']);
const SKIP_FILES = new Set(['world.geojson', 'country-maps.json', 'countries.json', 'package-lock.json']);
function* walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name)) yield* walk(path.join(dir, e.name)); }
    else yield path.join(dir, e.name);
  }
}
const textFiles = () => [...walk(ROOT)].filter((f) => /\.(mjs|js|json|md|txt)$/.test(f) && !SKIP_FILES.has(path.basename(f)) && !f.includes(path.sep + 'fonts' + path.sep));

test('no Windows system fonts in font settings or code', () => {
  const banned = /\b(Impact|Arial|Georgia|Courier(?: New)?|Segoe(?: UI)?|Cambria|Consolas|Bahnschrift|Ink Free|Times New Roman|Calibri|Verdana|Tahoma)\b/;
  const hits = [];
  for (const f of textFiles()) { const t = fs.readFileSync(f, 'utf8'); const m = t.match(banned); if (m) hits.push(`${path.relative(ROOT, f)}: ${m[0]}`); }
  assert.deepEqual(hits, []);
  const bundled = new Set(['Anton', 'Arimo', 'Gelasio']);
  for (const f of fs.readdirSync(path.join(ROOT, 'presets'))) {
    const q = JSON.parse(fs.readFileSync(path.join(ROOT, 'presets', f), 'utf8'));
    assert.ok(bundled.has(q.font), `${f} font ${q.font}`);
  }
  for (const n of ['Anton', 'Arimo', 'Gelasio']) assert.ok(fs.existsSync(path.join(ROOT, 'fonts', `OFL-${n}.txt`)), 'licence for ' + n);
});

test('no source-video / reference material and no absolute paths', () => {
  for (const n of ['by-video', 'COVERAGE.csv', 'appearance-index.json', 'manifest.json', 'review']) assert.ok(!fs.existsSync(path.join(ROOT, n)), n + ' must not ship');
  const ref = /by-video|COVERAGE|appearance-index|storyblocks|"references"|source video|reference video/i;
  const abs = /(?<![A-Za-z])[A-Za-z]:[\\/]|\/Users\/|\/home\/|\\Users\\/;
  const hits = [];
  for (const f of textFiles()) {
    const t = fs.readFileSync(f, 'utf8');
    if (ref.test(t)) hits.push(`${path.relative(ROOT, f)}: reference text`);
    if (abs.test(t)) hits.push(`${path.relative(ROOT, f)}: absolute path`);
  }
  assert.deepEqual(hits, []);
  const rows = JSON.parse(fs.readFileSync(path.join(ROOT, 'catalog.json'), 'utf8'));
  assert.equal(rows.length, 121);                                   // 108 effects + 13 templates (v4)
  const catalog = rows.filter((c) => c.kind !== 'template');
  assert.equal(catalog.length, 108);
  assert.ok(catalog.every((c) => !('references' in c)));
});

test('only the documented bundled assets ship', () => {
  const listed = fs.readFileSync(path.join(ROOT, 'ASSET-SOURCES.md'), 'utf8');
  for (const f of fs.readdirSync(path.join(ROOT, 'assets'))) assert.ok(listed.includes(f), `${f} is documented in ASSET-SOURCES.md`);
  assert.ok(!fs.existsSync(path.join(ROOT, 'assets', 'anchored-callouts-source.png')));
});

test("every effect's own sample values pass the renderer's validation", async () => {
  // The schema default of each key is the effect's sample. Feeding all of them back must be accepted, so the samples
  // shown in the schema never teach a value the validator refuses (empty labels, series with both value and values,
  // negative figures, text longer than its own limit). A required picture with no bundled sample gets a bundled one.
  const { prepare } = await import('../lib.mjs');
  const list = JSON.parse(run(['--list']).stdout);
  const failures = [];
  for (const e of list) {
    const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'schema', e.id + '.json'), 'utf8'));
    const overrides = {};
    for (const [key, spec] of Object.entries(schema.keys)) {
      if (!('default' in spec)) continue;
      overrides[key] = spec.type === 'image' && !spec.default ? 'assets/original-highland.png' : spec.default;
    }
    const prep = prepare({ id: e.id, overrides, assetsDir: ROOT });
    if (prep.problems.length) failures.push(`${e.id}: ` + prep.problems.map((p) => `${p.key} ${p.message}`).join('; '));
  }
  assert.deepEqual(failures, []);
});

test('territory-date draws its title even when a pin label is given', () => {
  // The title used to be only the pin label's fallback, so with pointLabels supplied (required by the schema) it never showed.
  const base = { subtitle: 'Palo Alto track', country: 'United States of America', points: [[-122.14, 37.44]], pointLabels: ['Palo Alto'] };
  const still = (name, title) => {
    const out = path.join(tmp, name);
    const r = run(['--id', 'territory-date', '--overrides', writeJson(name + '.json', { ...base, title }), '--duration', '4', '--frame', '1.5', '--out', out]);
    assert.equal(r.status, 0, r.stderr || r.stdout);
    return fs.readFileSync(out);
  };
  const a = still('td-a.png', 'June 19, 1878');
  const b = still('td-b.png', 'March 3, 1901');
  assert.ok(!a.equals(b), 'changing the title must change the frame');
});

test.after(() => { try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {} });

test('the number formatter groups thousands (en-US) and keeps the decimals given', async () => {
  const { fmt, fmtAs } = await import(new URL('../base-engine.mjs', import.meta.url));
  assert.equal(fmt(407000, 0), '407,000');
  assert.equal(fmt(407000, 2), '407,000.00');
  assert.equal(fmt(5.5, 2), '5.50');
  assert.equal(fmt(1234567.891, 2), '1,234,567.89');
  assert.equal(fmt(999, 0), '999');
  assert.equal(fmt(7500000, 0), '7,500,000');
  assert.equal(fmtAs(407000), '407,000');
  assert.equal(fmtAs('1500.5'), '1,500.5');
  assert.equal(fmtAs('n/a'), 'n/a');
  // money-counter and cost-arrow print through it: no raw toFixed / toLocaleString() left in the engines
  for (const f of ['engine.mjs', 'base-engine.mjs']) {
    const src = fs.readFileSync(path.join(ROOT, f), 'utf8').split(/\r?\n/).filter((l) => !l.startsWith('export const fmt')).join(' ');
    assert.ok(!/\.toFixed\(q\.decimals/.test(src), f + ' still prints money with toFixed');
    assert.ok(!/\.toLocaleString\(\)/.test(src), f + ' still uses the machine locale');
  }
  const eng = fs.readFileSync(path.join(ROOT, 'engine.mjs'), 'utf8');
  assert.ok(/v==='money'\)\{tx\(c,q\.prefix\+fmt\(/.test(eng));
  assert.ok(/v==='cost'\)\{label\(c,q\.prefix\+fmt\(/.test(eng));
});

test('circled-caption keeps its text and ring inside the safe area and the text sits inside the ring', async () => {
  const { createCanvas, loadImage } = await import('@napi-rs/canvas');
  fs.copyFileSync(path.join(ROOT, 'assets', 'original-person-b.png'), path.join(tmp, 'circ-bg.png'));
  const measure = async (title) => {
    const ov = writeJson('circ-' + title.length + '.json', { title, backgroundImage: 'circ-bg.png' });
    const out = path.join(tmp, 'circ-' + title.length + '.png');
    const r = run(['--id', 'circled-caption', '--overrides', ov, '--duration', '4', '--frame', '3', '--out', out]);
    assert.equal(r.status, 0, r.stderr);
    const img = await loadImage(out);
    const cv = createCanvas(img.width, img.height), cx = cv.getContext('2d');
    cx.drawImage(img, 0, 0);
    const { data, width, height } = cx.getImageData(0, 0, img.width, img.height);
    const near = (i, rgb, tol) => Math.abs(data[i] - rgb[0]) <= tol && Math.abs(data[i + 1] - rgb[1]) <= tol && Math.abs(data[i + 2] - rgb[2]) <= tol;
    const box = (rgb, tol) => {
      const cols = new Array(width).fill(0), rows = new Array(height).fill(0);
      for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) if (near((y * width + x) * 4, rgb, tol)) { cols[x]++; rows[y]++; }
      const lo = (a) => a.findIndex((n) => n >= 4), hi = (a) => a.length - 1 - [...a].reverse().findIndex((n) => n >= 4);
      return { x0: lo(cols), x1: hi(cols), y0: lo(rows), y1: hi(rows) };
    };
    return { text: box([250, 250, 250], 6), ring: box([0xac, 0xc2, 0x33], 10), width, height };
  };
  const inside = (t, g) => {                                  // the four corners of the text box lie inside the ring's bounding ellipse
    const cx = (g.x0 + g.x1) / 2, cy = (g.y0 + g.y1) / 2, rx = (g.x1 - g.x0) / 2 - 3, ry = (g.y1 - g.y0) / 2 - 3;
    return [[t.x0, t.y0], [t.x1, t.y0], [t.x0, t.y1], [t.x1, t.y1]].every(([x, y]) => ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1);
  };
  for (const title of ['Liman called her filing a blunderbuss approach, which swept in hours that had nothing to do with the claim',
                       'Liman called her filing a blunderbuss approach, which swept in hours that had nothing to do with the defamation claim',
                       'Blake Lively', 'The judge said the hours were unreasonable']) {
    const m = await measure(title);
    assert.ok(Math.min(m.text.x0, m.ring.x0) > 40, title.length + ': leftmost column ' + Math.min(m.text.x0, m.ring.x0));
    assert.ok(Math.max(m.text.x1, m.ring.x1) < m.width - 40, title.length + ': rightmost column');
    assert.ok(m.ring.y1 < m.height, title.length + ': ring runs off the bottom');
    assert.ok(inside(m.text, m.ring), title.length + ': the ring crosses the text ' + JSON.stringify(m));
  }
});

test('circled-caption keeps the face of a tall portrait: the crop starts below the headroom (Windows 4.1.1 finding 13)', async () => {
  const { createCanvas, loadImage } = await import('@napi-rs/canvas');
  // a 800x1600 portrait: red headroom (hair) 0-8%, blue face 8-45%, green body below
  const cv = createCanvas(800, 1600), cx = cv.getContext('2d');
  cx.fillStyle = '#00ff00'; cx.fillRect(0, 0, 800, 1600);
  cx.fillStyle = '#ff0000'; cx.fillRect(0, 0, 800, 128);
  cx.fillStyle = '#0000ff'; cx.fillRect(0, 128, 800, 592);
  fs.writeFileSync(path.join(tmp, 'tall.png'), cv.toBuffer('image/png'));
  const top = async (extra) => {
    const ov = writeJson('tall-' + Object.keys(extra).length + '.json', { title: 'Lewis Liman', backgroundImage: 'tall.png', ...extra });
    const out = path.join(tmp, 'tall-' + Object.keys(extra).length + '.png');
    const r = run(['--id', 'circled-caption', '--overrides', ov, '--duration', '4', '--frame', '3', '--out', out]);
    assert.equal(r.status, 0, r.stderr);
    const img = await loadImage(out), c2 = createCanvas(img.width, img.height).getContext('2d');
    c2.drawImage(img, 0, 0);
    const d = c2.getImageData(Math.floor(img.width / 2), 6, 1, 1).data;       // the first rows of the frame, middle column
    return { r: d[0], g: d[1], b: d[2] };
  };
  const auto = await top({});
  assert.ok(auto.b > auto.r * 3 && auto.b > 60, 'the top of the frame is the face, not the hair: ' + JSON.stringify(auto));
  const lower = await top({ backgroundFocusY: 0.9 });                       // an explicit lower focus still wins
  assert.ok(lower.g > lower.b, 'an explicit backgroundFocusY below the face band is honoured: ' + JSON.stringify(lower));
});
