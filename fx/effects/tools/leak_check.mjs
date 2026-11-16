// Finds effects where the bundled mountain picture can still reach a render.
//   node tools/leak_check.mjs   -> prints "id: leakWithBackgroundSet leakWithoutBackground (backgroundImage editable?)"
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { ROOT, catalog, createCanvas, environment } from '../runtime.mjs';
import { render } from '../engine.mjs';
const blank = createCanvas(64, 36); { const c = blank.getContext('2d'); c.fillStyle = '#000'; c.fillRect(0, 0, 64, 36); }
async function sig(item, q, swap) {
  const env = await environment(q); if (swap) env.mountain = blank;
  const canvas = createCanvas(480, 270), c = canvas.getContext('2d'); const out = [];
  for (const f of [0.2, 0.5, 0.9]) { render(c, item, q, f * q.duration, env); out.push(crypto.createHash('md5').update(Buffer.from(c.getImageData(0, 0, 480, 270).data.buffer)).digest('hex')); }
  return out.join();
}
const res = {};
for (const item of catalog) {
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'schema', item.id + '.json'), 'utf8'));
  const q = JSON.parse(fs.readFileSync(path.join(ROOT, 'presets', item.id + '.json'), 'utf8'));
  if (schema.keys.images) q.images = q.images.map((_, i) => ['assets/globe.png', 'assets/rocket.png', 'assets/heart.png'][i % 3]);
  const qb = { ...q }; if (schema.keys.backgroundImage) qb.backgroundImage = 'assets/landscape-3.png';
  const withBg = (await sig(item, qb, false)) !== (await sig(item, qb, true));
  const noBg = (await sig(item, { ...q, backgroundImage: '' }, false)) !== (await sig(item, { ...q, backgroundImage: '' }, true));
  res[item.id] = { withBg, noBg, bgEditable: !!schema.keys.backgroundImage };
  if (withBg || noBg) console.log(item.id.padEnd(24), 'leakWithBgSet', withBg, 'leakNoBg', noBg, 'bgEditable', !!schema.keys.backgroundImage);
}
console.log('checked', Object.keys(res).length);
