// Portable runtime for the effects library: canvas from this folder's node_modules, bundled open fonts,
// ffmpeg from env MOTION_FFMPEG or PATH. No machine-specific paths.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = path.dirname(fileURLToPath(import.meta.url));

let canvasMod;
try {
  canvasMod = await import('@napi-rs/canvas');
} catch (e) {
  process.stderr.write(JSON.stringify({ error: 'canvas_missing', message: 'Run "npm --prefix .claude/effects install" from the studio folder first (installs @napi-rs/canvas).', detail: String(e.message || e) }) + '\n');
  process.exit(3);
}
export const { createCanvas, loadImage, GlobalFonts } = canvasMod;

// Bundled open fonts (SIL OFL, see fonts/OFL-*.txt). Names the engine code uses:
//   Anton (display headings), Arimo (clean sans), Gelasio (serif).
const FONT_FILES = [
  ['Anton-Regular.ttf', 'Anton'],
  ['Arimo-Variable.ttf', 'Arimo'],
  ['Arimo-Italic-Variable.ttf', 'Arimo'],
  ['Gelasio-Variable.ttf', 'Gelasio'],
  ['Gelasio-Italic-Variable.ttf', 'Gelasio'],
];
for (const [file, family] of FONT_FILES) {
  const p = path.join(ROOT, 'fonts', file);
  if (!fs.existsSync(p)) throw new Error('bundled font missing: fonts/' + file);
  GlobalFonts.registerFromPath(p, family);
}

// ffmpeg: MOTION_FFMPEG, else the one on PATH. On a Mac, Claude Desktop's PATH often lacks Homebrew, so look there too.
function findFfmpeg() {
  if (process.env.MOTION_FFMPEG) return process.env.MOTION_FFMPEG;
  if (process.platform === 'darwin') {
    const onPath = (process.env.PATH || '').split(path.delimiter).some((d) => d && fs.existsSync(path.join(d, 'ffmpeg')));
    if (!onPath) {
      for (const p of ['/opt/homebrew/bin/ffmpeg', '/usr/local/bin/ffmpeg']) if (fs.existsSync(p)) return p;
    }
  }
  return 'ffmpeg';
}
export const FFMPEG = findFfmpeg();

// catalog.json also lists the 13 word-timed templates (kind "template", rendered by member_edit.py, not here): skip them
export const catalog = JSON.parse(fs.readFileSync(path.join(ROOT, 'catalog.json'), 'utf8')).filter((c) => c.kind !== 'template');

const cache = new Map();
export async function image(p) {
  if (!p) return null;
  const file = path.resolve(ROOT, p);
  if (!cache.has(file)) cache.set(file, await loadImage(file));
  return cache.get(file);
}

const world = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/world.geojson'), 'utf8'));
const countryMaps = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/country-maps.json'), 'utf8'));
export { world, countryMaps };

export async function environment(q) {
  return {
    images: await Promise.all(q.images.map(image)),
    background: q.backgroundImage ? await image(q.backgroundImage) : null,
    mountain: await image('assets/original-highland.png'),
    paper: await image('assets/paper.png'),
    world, countryMaps, createCanvas, surfaces: {},
  };
}
