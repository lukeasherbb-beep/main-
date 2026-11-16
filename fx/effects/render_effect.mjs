#!/usr/bin/env node
// Effects renderer CLI (run from the kit as: node .claude/effects/render_effect.mjs ...).
//   --list                      JSON array of every effect
//   --list-short                one line per effect: id | name | purpose | default_s | min_s-max_s | images: required/none
//   --schema <id>               print one effect's schema
//   --fingerprint               {"fingerprint":"<sha256>"} over all code, data, assets, fonts and the installed canvas version
//   --check --id X --overrides f.json --duration s [--fps n] [--assets-dir d]
//                               full validation exactly as a render does, no output; {"ok":true} or a JSON error (exit 2)
//   --id X --overrides f.json --duration s --out clip.mp4 [--fps 30]      render a clip
//   --preview-sample (only with --frame): preview the effect with its bundled sample content (never allowed for a render or --check)
//   --id X [--overrides f] [--duration s] --frame <seconds> --out still.png|.jpg   one preview frame
// Image slots are file paths relative to the folder holding the overrides file (or --assets-dir).
// Errors: one JSON object on stderr, non-zero exit (2 invalid input, 1 render failure, 3 setup problem).
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { ROOT, catalog, createCanvas, loadImage, environment, FFMPEG } from './runtime.mjs';
import { render } from './engine.mjs';
import { prepare, loadSchema } from './lib.mjs';

const W = 1920, H = 1080;

function fail(code, error, message, details) {
  process.stderr.write(JSON.stringify({ error, message, ...(details ? { details } : {}) }) + '\n');
  process.exit(code);
}
process.on('uncaughtException', (e) => fail(1, 'render_failed', String(e && e.stack || e)));
process.on('unhandledRejection', (e) => fail(1, 'render_failed', String(e && e.stack || e)));

const FLAGS = new Set(['list', 'list-short', 'fingerprint', 'check', 'preview-sample']);
function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) { out._.push(a); continue; }
    const k = a.slice(2);
    if (FLAGS.has(k)) { out[k] = true; continue; }
    const v = argv[i + 1];
    if (v === undefined || v.startsWith('--')) fail(2, 'bad_arguments', `option --${k} needs a value`);
    out[k] = v; i++;
  }
  const known = new Set(['_', ...FLAGS, 'id', 'overrides', 'duration', 'out', 'fps', 'frame', 'schema', 'assets-dir']);
  for (const k of Object.keys(out)) if (!known.has(k)) fail(2, 'bad_arguments', `unknown option --${k}`);
  if (out._.length) fail(2, 'bad_arguments', `unexpected argument ${out._[0]}`);
  return out;
}
const args = parseArgs(process.argv.slice(2));

const imagesState = (s) => (s.keys.images?.required || s.keys.backgroundImage?.required ? 'required' : 'none');

if (args.list) {
  const rows = catalog.map((c) => {
    const s = loadSchema(c.id);
    return { id: c.id, name: c.name, family: c.family, purpose: c.purpose, duration: s.duration.default,
      duration_range: [s.duration.min, s.duration.max], image_slots: s.imageSlots, images: imagesState(s),
      editable: Object.keys(s.keys), required: Object.keys(s.keys).filter((k) => s.keys[k].required) };
  });
  process.stdout.write(JSON.stringify(rows, null, 1) + '\n');
  process.exit(0);
}
if (args['list-short']) {
  const lines = catalog.map((c) => {
    const s = loadSchema(c.id);
    return `${c.id} | ${c.name} | ${c.purpose} | ${s.duration.default} | ${s.duration.min}-${s.duration.max} | images: ${imagesState(s)}`;
  });
  process.stdout.write(lines.join('\n') + '\n');
  process.exit(0);
}
if (args.schema) {
  const s = loadSchema(args.schema);
  if (!s) fail(2, 'unknown_effect', `no such effect: ${args.schema}`, { hint: 'run --list' });
  process.stdout.write(JSON.stringify(s, null, 1) + '\n');
  process.exit(0);
}
if (args.fingerprint) {
  const h = crypto.createHash('sha256');
  const files = [];
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p); else files.push(p);
    }
  };
  for (const e of fs.readdirSync(ROOT, { withFileTypes: true })) {
    const p = path.join(ROOT, e.name);
    if (e.isDirectory()) { if (['presets', 'schema', 'assets', 'fonts'].includes(e.name)) walk(p); }
    else if (/\.mjs$/.test(e.name) || ['package.json', 'catalog.json', 'countries.json'].includes(e.name)) files.push(p);
  }
  for (const p of files.map((f) => path.relative(ROOT, f).split(path.sep).join('/')).sort()) {
    h.update(p + '\0'); h.update(fs.readFileSync(path.join(ROOT, p))); h.update('\0');
  }
  let canvasVersion = 'unknown';
  try { canvasVersion = JSON.parse(fs.readFileSync(path.join(ROOT, 'node_modules/@napi-rs/canvas/package.json'), 'utf8')).version; } catch {}
  h.update('canvas@' + canvasVersion);
  process.stdout.write(JSON.stringify({ fingerprint: h.digest('hex') }) + '\n');
  process.exit(0);
}

// ---------- render / check / frame ----------
if (!args.id) fail(2, 'bad_arguments', '--id is required (or use --list)');
if (args['preview-sample'] && (args.frame === undefined || args.check)) fail(2, 'bad_arguments', '--preview-sample only works with --frame (a render or --check never uses sample content)');
if (!args.check && !args.out) fail(2, 'bad_arguments', '--out is required');
if (!catalog.some((c) => c.id === args.id)) fail(2, 'unknown_effect', `no such effect: ${args.id}`, { hint: 'run --list' });

let overrides = {};
let assetsDir = process.cwd();
if (args.overrides) {
  let raw;
  try { raw = fs.readFileSync(args.overrides, 'utf8'); } catch { fail(2, 'bad_overrides', `cannot read overrides file: ${args.overrides}`); }
  try { overrides = JSON.parse(raw.replace(/^﻿/, '')); } catch { fail(2, 'bad_overrides', 'overrides file is not valid JSON'); }
  assetsDir = path.dirname(path.resolve(args.overrides));
}
if (args['assets-dir']) assetsDir = path.resolve(args['assets-dir']);
const stillT = args.frame === undefined ? null : Number(args.frame);

const prep = prepare({ id: args.id, overrides, duration: args.duration, fps: args.fps, assetsDir, allowSample: !!args['preview-sample'] });
const problems = [...prep.problems];
if (stillT !== null && !(Number.isFinite(stillT) && stillT >= 0)) problems.push({ key: 'frame', message: 'must be a time in seconds >= 0' });
if (!problems.length) {
  try { for (const p of prep.imagePaths) await loadImage(path.resolve(ROOT, p)); }
  catch (e) { problems.push({ key: 'images', message: 'an image file could not be decoded: ' + String(e.message || e) }); }
}
if (problems.length) fail(2, 'invalid_input', `${problems.length} problem(s) in input`, problems);
if (args.check) { process.stdout.write('{"ok":true}\n'); process.exit(0); }

const { item, q, fps, duration } = prep;
let env, canvas, c;
try {
  env = await environment(q);
  canvas = createCanvas(W, H); c = canvas.getContext('2d');
  fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
} catch (e) { fail(1, 'render_failed', 'setup failed: ' + (e.stack || e.message)); }

if (stillT !== null) {
  try {
    render(c, item, q, stillT, env);
    const ext = path.extname(args.out).toLowerCase();
    fs.writeFileSync(args.out, ext === '.jpg' || ext === '.jpeg' ? canvas.toBuffer('image/jpeg', 92) : canvas.toBuffer('image/png'));
  } catch (e) { fail(1, 'render_failed', 'effect drawing failed: ' + (e.stack || e.message)); }
  process.stdout.write(JSON.stringify({ id: item.id, out: args.out, frame_time: stillT }) + '\n');
  process.exit(0);
}

if (process.env.MOTION_LOW_PRIORITY === '1') { try { os.setPriority(0, os.constants.priority.PRIORITY_BELOW_NORMAL); } catch {} }

const total = Math.round(duration * fps);
const proc = spawn(FFMPEG, ['-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pixel_format', 'rgba', '-video_size', `${W}x${H}`,
  '-framerate', String(fps), '-i', 'pipe:0', '-an', '-frames:v', String(total), '-c:v', 'libx264', '-threads', '4', '-preset', 'fast', '-crf', '18',
  '-pix_fmt', 'yuv420p', '-r', String(fps), '-movflags', '+faststart', '-y', args.out], { windowsHide: true, stdio: ['pipe', 'ignore', 'pipe'] });
let errText = '', spawnErr = null;
proc.stderr.on('data', (d) => (errText += d));
proc.on('error', (e) => { spawnErr = e; });
proc.stdin.on('error', () => {});
const closed = once(proc, 'close').catch(() => [-1]);
const t0 = Date.now();
try {
  for (let i = 0; i < total && !spawnErr; i++) {
    render(c, item, q, i / fps, env);
    const d = c.getImageData(0, 0, W, H).data;
    if (!proc.stdin.write(Buffer.from(d.buffer, d.byteOffset, d.byteLength))) await Promise.race([once(proc.stdin, 'drain'), closed]);
  }
} catch (e) {
  proc.stdin.destroy(); proc.kill();
  try { fs.unlinkSync(args.out); } catch {}
  fail(1, 'render_failed', 'effect drawing failed: ' + (e.stack || e.message));
}
proc.stdin.end();
const [code] = await closed;
if (spawnErr) fail(3, 'ffmpeg_missing', `could not start ffmpeg (${FFMPEG}). Install ffmpeg and put it on PATH, or set MOTION_FFMPEG to its full path.`, [{ message: spawnErr.message }]);
if (code) { try { fs.unlinkSync(args.out); } catch {} fail(1, 'encode_failed', 'ffmpeg failed', [{ message: errText.trim().slice(0, 2000) }]); }
process.stdout.write(JSON.stringify({ id: item.id, out: args.out, frames: total, fps, width: W, height: H, clip_seconds: total / fps, render_seconds: +((Date.now() - t0) / 1000).toFixed(1) }) + '\n');
