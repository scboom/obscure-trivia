// Render an original picture of Earth from Natural Earth map data (public domain, via world-atlas).
// Output: a space scene with a lit globe, clouds and an atmosphere glow.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const W = process.argv[2];               // folder with node_modules (world-atlas, d3-geo, d3-array, topojson-client)
const OUT = process.argv[3];
const nm = p => fs.readFileSync(path.join(W, 'node_modules', p), 'utf8');
const land = nm('world-atlas/land-50m.json');
const countries = nm('world-atlas/countries-50m.json');

const page = (w, h, cx, cy, r, rotate, stars) => `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#04070f">
<canvas id="c" width="${w}" height="${h}"></canvas>
<script>${nm('d3-array/dist/d3-array.min.js')}</script>
<script>${nm('d3-geo/dist/d3-geo.min.js')}</script>
<script>${nm('topojson-client/dist/topojson-client.min.js')}</script>
<script>
const W=${w}, H=${h}, CX=${cx}, CY=${cy}, R=${r};
const ctx = document.getElementById('c').getContext('2d');
let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
// space: deep gradient and stars
const bg = ctx.createRadialGradient(CX, CY, R * 0.6, CX, CY, Math.max(W, H));
bg.addColorStop(0, '#0b1a3a'); bg.addColorStop(0.5, '#060d1f'); bg.addColorStop(1, '#03060d');
ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
for (let i = 0; i < ${stars}; i++) {
  const x = rnd() * W, y = rnd() * H, s = rnd();
  ctx.fillStyle = 'rgba(255,255,255,' + (0.25 + s * 0.65) + ')';
  ctx.beginPath(); ctx.arc(x, y, s < 0.92 ? 0.6 + s * 0.6 : 1.6, 0, Math.PI * 2); ctx.fill();
}
// atmosphere glow
const glow = ctx.createRadialGradient(CX, CY, R * 0.98, CX, CY, R * 1.16);
glow.addColorStop(0, 'rgba(120,190,255,0.55)'); glow.addColorStop(0.4, 'rgba(70,140,255,0.18)'); glow.addColorStop(1, 'rgba(40,90,255,0)');
ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(CX, CY, R * 1.16, 0, Math.PI * 2); ctx.fill();
// ocean
const proj = d3.geoOrthographic().scale(R).translate([CX, CY]).rotate(${JSON.stringify(rotate)}).clipAngle(90).precision(0.3);
const gp = d3.geoPath(proj, ctx);
ctx.save(); ctx.beginPath(); ctx.arc(CX, CY, R, 0, Math.PI * 2); ctx.clip();
const sea = ctx.createRadialGradient(CX - R * 0.35, CY - R * 0.35, R * 0.1, CX, CY, R);
sea.addColorStop(0, '#2f7fd0'); sea.addColorStop(0.55, '#1b5aa8'); sea.addColorStop(1, '#0c2f6b');
ctx.fillStyle = sea; ctx.fillRect(CX - R, CY - R, R * 2, R * 2);
// land: draw a mask, then colour each land pixel by where it is (ice, desert, forest)
const landGeo = topojson.feature(${land}, ${land}.objects.land);
// a flat (equirectangular) land map, sampled per globe pixel: robust at the globe's edge
const EW = 4096, EH = 2048;
const eq = document.createElement('canvas'); eq.width = EW; eq.height = EH;
const eqx = eq.getContext('2d');
eqx.fillStyle = '#fff'; eqx.beginPath();
d3.geoPath(d3.geoEquirectangular().scale(EW / (2 * Math.PI)).translate([EW / 2, EH / 2]).precision(0.1), eqx)(landGeo); eqx.fill();
const emask = eqx.getImageData(0, 0, EW, EH).data;
const landAt = (lon, lat) => emask[((Math.min(EH - 1, Math.max(0, ((90 - lat) / 180 * EH) | 0)) * EW) + Math.min(EW - 1, Math.max(0, ((lon + 180) / 360 * EW) | 0))) * 4 + 3] / 255;
const x0 = Math.max(0, CX - R) | 0, y0 = Math.max(0, CY - R) | 0, x1 = Math.min(W, CX + R) | 0, y1 = Math.min(H, CY + R) | 0;
const img = ctx.getImageData(x0, y0, x1 - x0, y1 - y0);
const px = img.data;
const smooth = (e0, e1, x) => { const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t); };
const hash = (x, y) => { const h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return h - Math.floor(h); };
const vnoise = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return (hash(xi, yi) * (1 - u) + hash(xi + 1, yi) * u) * (1 - v) + (hash(xi, yi + 1) * (1 - u) + hash(xi + 1, yi + 1) * u) * v; };
const DRY = [[20, 12, 14], [24, 45, 9], [-25, 133, 10], [43, 103, 8], [33, -112, 6], [-23, 21, 6], [-24, -69, 4], [40, 62, 7]];
const dryness = (lon, lat) => Math.max(...DRY.map(([la, lo, s]) => Math.exp(-(((lat - la) ** 2) + ((lon - lo) * Math.cos(la * Math.PI / 180)) ** 2) / (2 * s * s))));
for (let y = 0; y < y1 - y0; y++) for (let x = 0; x < x1 - x0; x++) {
  const gx = x + x0, gy = y + y0;
  if ((gx - CX) ** 2 + (gy - CY) ** 2 > R * R) continue;
  const ll = proj.invert([gx, gy]); if (!ll) continue;
  const [lon, lat] = ll, al = Math.abs(lat);
  const i = (y * (x1 - x0) + x) * 4, a = landAt(lon, lat);
  if (a < 0.05) continue;
  const n = vnoise(lon / 4, lat / 4) * 0.7 + vnoise(lon / 1.3, lat / 1.3) * 0.3 - 0.5;
  const t = smooth(10, 55, al);
  const green = [42 + 50 * t, 104 + 22 * t - 10 * smooth(50, 65, al), 46 + 30 * t];
  const d = Math.min(1, dryness(lon, lat) * 1.3), sand = [208, 180, 124];
  let c = green.map((v, k) => v * (1 - d) + sand[k] * d + n * 22);
  const ice = Math.max(smooth(66, 76, al), lat > 59 && lon > -58 && lon < -11 ? smooth(59, 62, lat) : 0, lat < -60 ? 1 : 0);
  c = c.map((v, k) => v * (1 - ice) + [236, 241, 245][k] * ice);
  px[i] = px[i] * (1 - a) + c[0] * a; px[i + 1] = px[i + 1] * (1 - a) + c[1] * a; px[i + 2] = px[i + 2] * (1 - a) + c[2] * a;
}
ctx.putImageData(img, x0, y0);
// soft clouds
ctx.globalCompositeOperation = 'source-over';
ctx.filter = 'blur(' + Math.max(2, R / 110) + 'px)';
for (let i = 0; i < 170; i++) {
  const lon = rnd() * 360 - 180, lat = (rnd() - 0.5) * 150;
  const p = proj([lon, lat]); if (!p) continue;
  const d = Math.hypot(p[0] - CX, p[1] - CY) / R; if (d > 0.98) continue;
  const rr = R * (0.02 + rnd() * 0.06) * (1 - d * 0.5);
  const g = ctx.createRadialGradient(p[0], p[1], 0, p[0], p[1], rr * 2.2);
  g.addColorStop(0, 'rgba(255,255,255,' + (0.18 + rnd() * 0.22) + ')'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(p[0], p[1], rr * 3.4, rr * 0.9, (rnd() - 0.5) * 0.6, 0, Math.PI * 2); ctx.fill();
}
ctx.filter = 'none';
// sunlight from the upper left, night side to the lower right
const shade = ctx.createLinearGradient(CX - R * 0.9, CY - R * 0.9, CX + R, CY + R);
shade.addColorStop(0, 'rgba(255,255,255,0.10)'); shade.addColorStop(0.5, 'rgba(0,0,0,0)'); shade.addColorStop(0.8, 'rgba(2,6,20,0.55)'); shade.addColorStop(1, 'rgba(2,6,20,0.85)');
ctx.fillStyle = shade; ctx.fillRect(CX - R, CY - R, R * 2, R * 2);
const rim = ctx.createRadialGradient(CX, CY, R * 0.82, CX, CY, R);
rim.addColorStop(0, 'rgba(0,0,0,0)'); rim.addColorStop(1, 'rgba(150,210,255,0.35)');
ctx.fillStyle = rim; ctx.fillRect(CX - R, CY - R, R * 2, R * 2);
ctx.restore();
document.title = 'done';
</script>`;

(async () => {
  const b = await chromium.launch();
  const shots = [
    // page background: wide scene, Earth rising from the bottom (Africa, Europe and the Atlantic)
    { name: 'earth-bg.jpg', w: 1800, h: 1100, cx: 900, cy: 1560, r: 900, rotate: [38, -6, 0], stars: 900 },
    // hub tile: the whole globe (the Americas)
    { name: 'earth-tile.jpg', w: 900, h: 600, cx: 560, cy: 330, r: 250, rotate: [75, -12, 0], stars: 300 },
    // share image
    { name: 'earth-social.jpg', w: 1200, h: 630, cx: 900, cy: 380, r: 330, rotate: [-20, -15, 0], stars: 400 },
  ];
  for (const s of shots) {
    const p = await b.newPage({ viewport: { width: s.w, height: s.h } });
    await p.setContent(page(s.w, s.h, s.cx, s.cy, s.r, s.rotate, s.stars));
    await p.waitForFunction(() => document.title === 'done', null, { timeout: 30000 });
    await p.locator('#c').screenshot({ path: path.join(OUT, s.name), type: 'jpeg', quality: 84 });
    console.log('wrote', s.name, fs.statSync(path.join(OUT, s.name)).size);
    await p.close();
  }
  await b.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
