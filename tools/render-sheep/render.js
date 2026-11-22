const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const [,, out, yaw, pitch] = process.argv;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1100, height: 900 } });
  const dir = __dirname;
  await p.route('http://local/**', r => { const f = path.join(dir, new URL(r.request().url()).pathname); r.fulfill({ path: f }); });
  await p.goto('http://local/render.html'); 
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const geo = JSON.parse(fs.readFileSync(path.join(dir, 'sheep.geo.json'), 'utf8'));
  const info = await p.evaluate(([geo, yaw, pitch]) => window.renderSheep('http://local/sheep_opaque.png', geo, { W: 1100, H: 900, yaw: +yaw, pitch: +pitch }), [geo, yaw, pitch]);
  const el = await p.$('#c'); await el.screenshot({ path: out, omitBackground: true });
  console.log(JSON.stringify(info), errs);
  await b.close();
})();
