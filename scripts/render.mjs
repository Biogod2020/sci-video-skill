// Render a deterministic canvas film (film.html defines renderAt(t) and DURATION) with headless Chrome.
// Run from the film folder:
//   node render.mjs stills 3,8,14.5        -> stills/t<time>.png      (look at these before any full render)
//   node render.mjs frames [fps] [workers] -> frames/f%05d.jpg        (one Chrome per worker; 8 workers ~ 8x faster)
// Env: FILM (default film.html), CHROME (Chrome binary; default: puppeteer's own),
//      PUPPETEER_DIR (a node_modules folder that holds puppeteer, if it is not installed next to the film)
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
const here = process.cwd();
const require = createRequire(process.env.PUPPETEER_DIR ? path.join(process.env.PUPPETEER_DIR, '/') : path.join(here, '/'));
const puppeteer = require('puppeteer');
const url = 'file://' + path.join(here, process.env.FILM || 'film.html') + '?t=0';

const [mode, a, b] = process.argv.slice(2);
const launch = () => puppeteer.launch({ executablePath: process.env.CHROME || undefined, headless: true, protocolTimeout: 900000, timeout: 300000,
  args: ['--no-sandbox', '--allow-file-access-from-files', '--force-device-scale-factor=1', '--font-render-hinting=none'] });
const browser = await launch();
async function page(br = browser) {
  const p = await br.newPage();
  await p.setViewport({ width: 1920, height: 1080 });
  await p.goto(url, { waitUntil: 'load' });
  // fonts and images must be loaded before the first frame, or early frames are drawn in a fallback font
  await p.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map((i) => i.decode().catch(() => 0))); });
  return p;
}
if (mode === 'stills') {
  const p = await page(); fs.mkdirSync(path.join(here, 'stills'), { recursive: true });
  for (const t of a.split(',').map(Number)) {
    await p.evaluate((t) => renderAt(t), t);
    await p.screenshot({ path: path.join(here, 'stills', `t${String(t).padStart(5, '0')}.png`) });
  }
} else if (mode === 'frames') {
  const fps = +(a || 30), workers = +(b || 8), out = path.join(here, 'frames');
  fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
  const p0 = await page(); const dur = await p0.evaluate(() => DURATION); await p0.close();
  const n = Math.round(dur * fps); let next = 0;
  const brs = []; for (let w = 0; w < workers; w++) brs.push(await launch());
  await Promise.all(brs.map(async (br) => {
    const p = await page(br);
    for (let i = next++; i < n; i = next++) {
      await p.evaluate((t) => renderAt(t), i / fps);
      await p.screenshot({ path: path.join(out, `f${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 95 });
    }
    await br.close();
  }));
  console.log('frames', n, 'duration', dur);
} else { console.error('usage: node render.mjs stills t1,t2,... | frames [fps] [workers]'); process.exitCode = 2; }
await browser.close();
