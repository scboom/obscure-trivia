const fs = require('fs');
const { chromium } = require('playwright');
const [,, texPath, outDir] = process.argv;
const T = JSON.parse(fs.readFileSync(texPath, 'utf8'));
const fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Inter:wght@500;700&family=Bree+Serif&family=Pixelify+Sans:wght@700&display=swap">';
const base = 'html,body{margin:0;width:1200px;height:630px;overflow:hidden}body{box-sizing:border-box;padding:70px 80px;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;font-family:Inter,system-ui,sans-serif}';
const pages = {
  'hub': `<style>${base}body{background:radial-gradient(ellipse at 20% -10%,#2a2636 0%,transparent 55%),#121117;color:#f2efe6;justify-content:center}
    .mark{width:84px;height:84px;border-radius:20px;background:#f2efe6;color:#121117;display:grid;place-items:center;font:800 56px 'Bricolage Grotesque';transform:rotate(-6deg)}
    h1{font:800 104px/1 'Bricolage Grotesque',sans-serif;letter-spacing:-.03em;margin:0}p{font-size:34px;color:#a7a3b5;margin:0}
    .tiles{display:flex;gap:18px}.t{height:70px;padding:0 26px;display:flex;align-items:center;font-size:28px;font-weight:700}
    .hs{border-radius:14px;background:linear-gradient(rgba(20,12,7,.35),rgba(20,12,7,.6)),url(${T.wood}) center/cover;color:#f6e7cf;font-family:'Bree Serif';font-weight:400}
    .mc{background:linear-gradient(rgba(0,0,0,.35),rgba(0,0,0,.55)),url(${T.grass_side}) 0 0/40px 40px;image-rendering:pixelated;color:#fff;font-family:'Pixelify Sans';box-shadow:inset 0 0 0 3px #0f0f10}</style>
    <div class="mark">?</div><h1>Obscure Trivia</h1><p>Trivia for the details only real players know.</p>
    <div class="tiles"><div class="t hs">Hearthstone Battlegrounds</div><div class="t mc">Minecraft</div></div>`,
  'hearthstone': `<style>${base}body{background:linear-gradient(180deg,rgba(20,12,7,.25),rgba(20,12,7,.88)),url(${T.wood}) center/cover;color:#f6e7cf}
    .coin{width:110px;height:110px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 35% 30%,#fff3c4 0 12%,#e8b450 38%,#a8721f 100%);color:#2a1b08;font:400 64px 'Bree Serif'}
    h1{font:400 92px/1.02 'Bree Serif',serif;margin:0}p{font-size:34px;color:#e3cfb2;margin:0}.by{font:800 26px 'Bricolage Grotesque';color:#e8b450;letter-spacing:.02em}</style>
    <div class="coin">?</div><h1>Hearthstone Battlegrounds Quiz</h1><p>1,000 questions · solo or co-op with a friend</p><div class="by">OBSCURE TRIVIA</div>`,
  'minecraft': `<style>${base}body{background:linear-gradient(180deg,rgba(0,0,0,.15) 20%,rgba(0,0,0,.82)),url(${T.grass_side}) 0 0/90px 90px;image-rendering:pixelated;color:#fff}
    h1{font:700 104px/1 'Pixelify Sans',monospace;margin:0;text-shadow:6px 6px 0 #1f1f1f}p{font-size:34px;margin:0;text-shadow:2px 2px 0 #000}
    .by{font:800 26px 'Bricolage Grotesque';color:#7ad155;letter-spacing:.02em;text-shadow:2px 2px 0 #000}</style>
    <h1>Minecraft Quiz</h1><p>Bedrock Edition · 1,000 questions · solo or co-op</p><div class="by">OBSCURE TRIVIA</div>`,
};
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, body] of Object.entries(pages)) {
    await p.setContent('<!doctype html><meta charset="utf-8">' + fonts + body, { waitUntil: 'load', timeout: 15000 }).catch(() => {});
    await p.waitForTimeout(600);
    const out = name === 'hub' ? `${outDir}/social.png` : `${outDir}/${name}/social.png`;
    await p.screenshot({ path: out, type: 'png' });
    console.log('wrote', out);
  }
  await b.close();
})();
