// Input validation and preset building shared by the CLI and the tests.
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, catalog, world, countryMaps } from './runtime.mjs';

export const IMAGE_EXT = new Set(['.png', '.jpg', '.jpeg', '.webp']);
const isObj = (v) => v && typeof v === 'object' && !Array.isArray(v);
const num = (v) => typeof v === 'number' && Number.isFinite(v);
const countryNames = new Set(world.features.flatMap((f) => [f.properties.ADMIN, f.properties.NAME, f.properties.ISO_A3]).filter(Boolean));

export function loadSchema(id) {
  if (!/^[a-z0-9-]+$/.test(id)) return null;
  const f = path.join(ROOT, 'schema', id + '.json');
  return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : null;
}
export const loadPreset = (id) => JSON.parse(fs.readFileSync(path.join(ROOT, 'presets', id + '.json'), 'utf8'));

// Returns { problems:[{key,message}], q, item, schema, imagePaths }.  Never throws on bad input.
export function prepare({ id, overrides = {}, duration, fps, assetsDir = process.cwd(), allowSample = false }) {
  const problems = [];
  const bad = (key, message) => { problems.push({ key, message }); };
  const item = catalog.find((c) => c.id === id);
  const schema = item && loadSchema(id);
  if (!schema) return { problems: [{ key: 'id', message: `no such effect: ${id}` }], unknown: true };
  const preset = loadPreset(id);

  const checkText = (key, v, spec) => {
    if (typeof v !== 'string') return bad(key, 'must be a string');
    if (v.length > spec.maxLength) bad(key, `too long (max ${spec.maxLength} characters)`);
    if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(v)) bad(key, 'contains control characters');
  };
  const checkNumber = (key, v, spec) => {
    if (!num(v)) return bad(key, 'must be a number');
    if (spec.integer && !Number.isInteger(v)) bad(key, 'must be a whole number');
    if (v < spec.min || v > spec.max) bad(key, `out of range (${spec.min} to ${spec.max})`);
  };
  const checkCountry = (key, v) => {
    if (typeof v !== 'string') return bad(key, 'must be a string');
    const ok = id === 'country-trace' ? Object.prototype.hasOwnProperty.call(countryMaps, v) : countryNames.has(v);
    if (!ok) bad(key, `unknown country "${v}" (use English names as listed in countries.json)`);
  };
  const checkList = (key, v, spec, each) => {
    if (!Array.isArray(v)) return bad(key, 'must be a list');
    const lo = spec.minItems ?? 0;
    if (v.length < lo || v.length > spec.maxItems) return bad(key, lo === spec.maxItems ? `needs exactly ${lo} items, got ${v.length}` : `needs ${lo} to ${spec.maxItems} items, got ${v.length}`);
    v.forEach((x, i) => each(`${key}[${i}]`, x));
  };
  const checkImagePath = (key, v) => {
    if (typeof v !== 'string' || !v) return bad(key, 'must be a file path string') || null;
    if (path.isAbsolute(v) || /^[a-zA-Z]:/.test(v) || v.split(/[\\/]/).includes('..')) return bad(key, 'must be a relative path inside the media folder (no absolute paths or "..")') || null;
    if (!IMAGE_EXT.has(path.extname(v).toLowerCase())) return bad(key, 'must be a .png, .jpg, .jpeg or .webp image') || null;
    const f = path.resolve(assetsDir, v);
    if (!fs.existsSync(f) || !fs.statSync(f).isFile()) return bad(key, `file not found: ${v}`) || null;
    return f;
  };

  if (!isObj(overrides)) return { problems: [{ key: 'overrides', message: 'must be a JSON object' }], item, schema };

  // required keys (data-bearing settings never fall back to the sample figures)
  const REQUIRED_MSG = (key, spec) => {
    if (spec.type === 'image_list' || spec.type === 'image') return `override ${key} must be set: this effect shows your own picture(s); the bundled sample image is never used in a render`;
    if (['country', 'country_list', 'bounds', 'point_list'].includes(spec.type) || key === 'pointLabels') return `${key} must be set: this effect shows the place(s) you give it; the sample region is never used in a render`;
    return `${key} must be set: this effect shows the figure/data you give it, so the sample has no usable default`;
  };
  if (!allowSample) for (const [key, spec] of Object.entries(schema.keys)) {
    if (spec.required && !(key in overrides)) bad(key, REQUIRED_MSG(key, spec));
  }
  if (!allowSample) for (const [trigger, needs] of Object.entries(schema.requires_with || {})) {
    if (!(trigger in overrides)) continue;
    for (const k of needs) if (!(k in overrides)) bad(k, `required when "${trigger}" is set (so your ${trigger} are on screen and not the sample's)`);
  }

  const resolved = {};
  for (const [key, v] of Object.entries(overrides)) {
    const spec = schema.keys[key];
    if (!spec) { bad(key, `unknown key for ${id}; allowed: ${Object.keys(schema.keys).join(', ') || '(none)'}`); continue; }
    switch (spec.type) {
      case 'text': checkText(key, v, spec); break;
      case 'color': if (typeof v !== 'string' || !/^#[0-9a-fA-F]{6}$/.test(v)) bad(key, 'must be a #rrggbb colour (6 hex digits)'); break;
      case 'number': checkNumber(key, v, spec); if (spec.greaterThan && num(v) && num(overrides[spec.greaterThan]) && v <= overrides[spec.greaterThan]) bad(key, 'must be greater than ' + spec.greaterThan); break;
      case 'text_list': checkList(key, v, spec, (k, x) => checkText(k, x, spec.item)); break;
      case 'country': checkCountry(key, v); break;
      case 'country_list': checkList(key, v, spec, (k, x) => checkCountry(k, x)); break;
      case 'bounds':
        if (!Array.isArray(v) || v.length !== 4 || !v.every(num)) bad(key, 'must be [west, south, east, north] numbers');
        else if (v[0] < -180 || v[2] > 180 || v[1] < -85 || v[3] > 85) bad(key, 'longitude must be -180..180 and latitude -85..85');
        else if (v[2] - v[0] < 2 || v[3] - v[1] < 2) bad(key, 'must be west<east and south<north, each at least 2 degrees wide');
        break;
      case 'point_list':
        checkList(key, v, spec, (k, p) => {
          if (!Array.isArray(p) || p.length !== 2 || !p.every(num)) return bad(k, 'must be [longitude, latitude]');
          if (p[0] < -180 || p[0] > 180 || p[1] < -85 || p[1] > 85) bad(k, 'longitude -180..180, latitude -85..85');
        }); break;
      case 'series_list':
        checkList(key, v, spec, (k, s) => {
          if (!isObj(s)) return bad(k, 'must be an object');
          const allowed = ['label', spec.mode];
          for (const sk of Object.keys(s)) if (!allowed.includes(sk)) bad(`${k}.${sk}`, `unknown key (this effect uses: ${allowed.join(', ')})`);
          if (spec.needLabel || 'label' in s) { if (!('label' in s) && spec.needLabel) bad(`${k}.label`, 'required'); else if ('label' in s) checkText(`${k}.label`, s.label, spec.label); }
          if (spec.mode === 'value') { if (!('value' in s)) bad(`${k}.value`, 'required'); else checkNumber(`${k}.value`, s.value, spec.number); }
          else if (!('values' in s)) bad(`${k}.values`, 'required');
          else checkList(`${k}.values`, s.values, spec.values, (kk, x) => checkNumber(kk, x, spec.number));
        });
        if (Array.isArray(v) && spec.matchCount) {
          const want = (overrides[spec.matchCount] ?? preset[spec.matchCount]).length;
          if (v.length !== want) bad(key, `needs one entry per item in "${spec.matchCount}" (${want}), got ${v.length}`);
        }
        break;
      case 'image_list':
        resolved[key] = null;
        if (!Array.isArray(v) || v.length < 1 || v.length > spec.maxItems) { bad(key, `needs 1 to ${spec.maxItems} image paths`); break; }
        resolved[key] = v.map((x, i) => checkImagePath(`${key}[${i}]`, x)); break;
      case 'image': resolved[key] = checkImagePath(key, v); break;
      case 'enum': if (!spec.values.includes(v)) bad(key, `must be one of ${spec.values.join(', ')}`); break;
      default: bad(key, 'unsupported schema type ' + spec.type);
    }
    if (spec.sameLengthAs && Array.isArray(v) && Array.isArray(overrides[spec.sameLengthAs]) && v.length !== overrides[spec.sameLengthAs].length) {
      bad(key, `needs one entry per item in "${spec.sameLengthAs}" (${overrides[spec.sameLengthAs].length}), got ${v.length}`);
    }
  }

  const f = fps === undefined ? 30 : Number(fps);
  if (!Number.isInteger(f) || f < schema.fps.min || f > schema.fps.max) bad('fps', `must be a whole number ${schema.fps.min} to ${schema.fps.max}`);
  const d = duration === undefined ? schema.duration.default : Number(duration);
  if (!num(d) || d < schema.duration.min || d > schema.duration.max) bad('duration', `must be ${schema.duration.min} to ${schema.duration.max} seconds for ${id}`);
  if (problems.length) return { problems, item, schema };

  // build the preset: member values replace the sample's outright (no merging)
  const q = JSON.parse(JSON.stringify(preset));
  for (const [key, v] of Object.entries(overrides)) {
    const spec = schema.keys[key];
    if (spec.type === 'image_list') {
      const given = resolved[key];
      q[key] = Array.from({ length: Math.max(spec.slots, given.length) }, (_, i) => given[i % given.length]); // fewer than the layout has: they repeat
    } else if (spec.type === 'image') q[key] = resolved[key];
    else if (spec.type === 'series_list') {
      q[key] = v.map((s) => spec.mode === 'value'
        ? { label: s.label ?? '', value: s.value, values: [0, s.value] }
        : { label: s.label ?? '', value: s.values[s.values.length - 1], values: s.values.slice() });
    } else if (spec.type === 'text_list' && spec.pad) q[key] = Array.from({ length: Math.max(v.length, spec.pad) }, (_, i) => v[i] ?? '');
    else q[key] = v;
  }
  q.duration = d;
  return { problems, item, schema, q, fps: f, duration: d, imagePaths: [...q.images, q.backgroundImage].filter(Boolean) };
}
