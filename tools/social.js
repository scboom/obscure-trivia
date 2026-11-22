const fs = require('fs');
const { chromium } = require('playwright');
const [,, texPath, outDir] = process.argv;
const T = JSON.parse(fs.readFileSync(texPath, 'utf8'));
const MONO = 'data:font/woff2;base64,' + fs.readFileSync(require('path').join(require('path').dirname(texPath), 'fonts', 'Monocraft.woff2')).toString('base64');
const EMBLEM = 'data:image/svg+xml;base64,' + fs.readFileSync(outDir + '/hearthstone/emblem.svg').toString('base64');
const SHEEP = 'data:image/png;base64,' + fs.readFileSync(outDir + '/minecraft/sheep.png').toString('base64');
const EARTH = 'data:image/jpeg;base64,' + fs.readFileSync(require('path').join(require('path').dirname(texPath), 'world', 'earth-social.jpg')).toString('base64');
const fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Inter:wght@500;700&family=Bree+Serif&family=Outfit:wght@800&family=Oswald:wght@700&family=Lilita+One&family=Rubik:wght@500&family=Chakra+Petch:ital,wght@1,700&family=Titillium+Web:wght@600&display=swap">';
const base = '@font-face{font-family:Monocraft;src:url(' + MONO + ')}html,body{margin:0;width:1200px;height:630px;overflow:hidden}body{box-sizing:border-box;padding:70px 80px;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;font-family:Inter,system-ui,sans-serif}';
const pages = {
  'hub': `<style>${base}body{background:radial-gradient(ellipse at 20% -10%,#2a2636 0%,transparent 55%),#121117;color:#f2efe6;justify-content:center}
    .mark{width:84px;height:84px;border-radius:20px;background:#f2efe6;color:#121117;display:grid;place-items:center;font:800 56px 'Bricolage Grotesque';transform:rotate(-6deg)}
    h1{font:800 104px/1 'Bricolage Grotesque',sans-serif;letter-spacing:-.03em;margin:0}p{font-size:34px;color:#a7a3b5;margin:0}
    .tiles{display:flex;gap:18px}.t{height:70px;padding:0 26px;display:flex;align-items:center;font-size:28px;font-weight:700}
    .hs{border-radius:14px;background:url(${EMBLEM}) right 10px center/auto 76% no-repeat,radial-gradient(circle at 85% 20%,rgba(255,196,96,.45),transparent 50%),linear-gradient(180deg,#4b2e19,#2a190e);padding-right:70px!important;color:#f6e7cf;font-family:'Bree Serif';font-weight:400;box-shadow:inset 0 0 0 1px rgba(232,180,80,.5)}
    .fb{border-radius:10px;background:repeating-linear-gradient(90deg,#1d6a35 0 20px,#22783c 20px 40px);color:#fff;font-family:Oswald,sans-serif;text-transform:uppercase}
    .gk{border-radius:999px;background:linear-gradient(90deg,#123f8a,#2f7fd0);color:#fff;font-family:Outfit,sans-serif;font-weight:800}
    .mc{background:linear-gradient(180deg,#70b540,#4a8627);image-rendering:pixelated;color:#fff;font-family:Monocraft;text-shadow:2px 2px 0 #1f1f1f;box-shadow:inset 0 0 0 3px #0f0f10}
    .wb{border-radius:14px;background:linear-gradient(115deg,#ff8a78 0 50%,#6d9bff 50% 100%);color:#1b1b2f;font-family:'Lilita One';font-weight:400;border:3px solid #1b1b2f}
    .cr{border-radius:10px;background:linear-gradient(100deg,#202227 0 74%,#e10600 74% 84%,#202227 84% 88%,#f3f4f6 88% 92%,#202227 92%);color:#fff;font-family:'Chakra Petch';font-style:italic;font-weight:700;text-transform:uppercase}
    .tiles{flex-wrap:wrap;max-width:1040px}</style>
    <div class="mark">?</div><h1>Obscure Trivia</h1><p>Trivia for the details only real players know.</p>
    <div class="tiles"><div class="t hs">Hearthstone Battlegrounds</div><div class="t mc">Minecraft</div><div class="t gk">General Knowledge</div><div class="t fb">Football</div><div class="t cr">Cars</div><div class="t wb">This or That</div></div>`,
  'hearthstone': `<style>${base}body{background:radial-gradient(circle at 84% 26%,rgba(255,196,96,.5) 0,rgba(255,150,50,.18) 22%,transparent 46%),radial-gradient(ellipse at 8% 115%,rgba(255,120,40,.25),transparent 55%),repeating-linear-gradient(180deg,transparent 0 102px,rgba(0,0,0,.22) 102px 106px),linear-gradient(180deg,#4b2e19,#301d10 55%,#1b100a);color:#f6e7cf;box-shadow:inset 0 0 0 3px rgba(232,180,80,.45)}
    .coin{background:url(${EMBLEM}) center/100% 100% !important;filter:drop-shadow(0 0 40px rgba(255,170,70,.55));position:absolute;top:60px;right:100px;box-shadow:inset 0 -5px 0 rgba(0,0,0,.25),0 0 0 10px rgba(232,180,80,.16),0 0 80px rgba(255,180,80,.6);width:250px;height:250px;font-size:84px!important;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 35% 30%,#fff3c4 0 12%,#e8b450 38%,#a8721f 100%);color:#2a1b08;font:400 64px 'Bree Serif'}
    h1{font:400 92px/1.02 'Bree Serif',serif;margin:0}p{font-size:34px;color:#e3cfb2;margin:0}.by{font:800 26px 'Bricolage Grotesque';color:#e8b450;letter-spacing:.02em}</style>
    <div class="coin"></div><h1>Hearthstone Battlegrounds Quiz</h1><p>20 questions · solo or party mode</p><div class="by">OBSCURE TRIVIA</div>`,
  'general-knowledge': `<style>${base}body{background:linear-gradient(90deg,rgba(5,10,24,.85) 0%,rgba(5,10,24,.35) 55%,rgba(5,10,24,0) 75%),url(${EARTH}) center/cover;color:#f2f7ff;justify-content:center}
    h1{font:800 96px/1 Outfit,sans-serif;margin:0;letter-spacing:-.02em;max-width:9ch}p{font-size:34px;margin:0;color:#cfe0f5}
    .by{font:800 26px 'Bricolage Grotesque';color:#8edbff;letter-spacing:.02em}</style>
    <h1>General Knowledge Quiz</h1><p>20 questions · solo or party</p><div class="by">OBSCURE TRIVIA</div>`,
  'football': `<style>${base}body{background:linear-gradient(180deg,rgba(0,0,0,0) 20%,rgba(4,18,9,.85)),radial-gradient(circle at 78% 42%,transparent 0 120px,rgba(255,255,255,.6) 121px 126px,transparent 127px),linear-gradient(90deg,transparent calc(78% - 3px),rgba(255,255,255,.6) calc(78% - 3px) calc(78% + 3px),transparent calc(78% + 3px)),repeating-linear-gradient(90deg,#1d6a35 0 80px,#22783c 80px 160px);color:#fff}
    h1{font:700 120px/1 Oswald,sans-serif;margin:0;text-transform:uppercase;letter-spacing:.01em}p{font-size:34px;margin:0}
    .by{font:800 26px 'Bricolage Grotesque';color:#ffd84a;letter-spacing:.02em}</style>
    <h1>Football Quiz</h1><p>Premier League · World Cup · 20 questions · solo or party</p><div class="by">OBSCURE TRIVIA</div>`,
  'this-or-that': `<style>${base}body{background:radial-gradient(circle,rgba(27,27,47,.12) 2px,transparent 2.6px) 0 0/28px 28px,linear-gradient(115deg,#ffb4a6 0 50%,#a9c4ff 50% 100%);color:#1b1b2f;justify-content:center}
    .vs{position:absolute;bottom:80px;right:110px;width:170px;height:170px;border-radius:50%;background:#1b1b2f;color:#ffcd29;display:grid;place-items:center;font:400 76px 'Lilita One';transform:rotate(-8deg);box-shadow:10px 10px 0 #c2410c}
    h1{font:400 128px/1 'Lilita One',sans-serif;margin:0}p{font:500 34px Rubik,sans-serif;margin:0;max-width:20ch}
    .by{font:800 26px 'Bricolage Grotesque';color:#1b1b2f;letter-spacing:.02em}</style>
    <div class="vs">VS</div><h1>This or That</h1><p>Two things go head to head. Pick the right one.</p><div class="by">OBSCURE TRIVIA</div>`,
  'cars': `<style>${base}body{background:radial-gradient(ellipse at 30% -10%,rgba(225,6,0,.45),transparent 60%),linear-gradient(100deg,transparent 0 70%,#e10600 70% 77%,transparent 77% 79.5%,#f3f4f6 79.5% 82%,transparent 82%),linear-gradient(45deg,#111215 25%,transparent 25%,transparent 75%,#111215 75%) 0 0/16px 16px,linear-gradient(45deg,#111215 25%,transparent 25%,transparent 75%,#111215 75%) 8px 8px/16px 16px,linear-gradient(#202227,#16171a);color:#fff}
    h1{font:italic 700 132px/1 'Chakra Petch',sans-serif;margin:0;text-transform:uppercase;letter-spacing:.01em}p{font:600 36px 'Titillium Web',sans-serif;margin:0;color:#d4d7dd}
    .by{font:800 26px 'Bricolage Grotesque';color:#ff5a4d;letter-spacing:.02em}</style>
    <h1>Car Quiz</h1><p>Horsepower · top speeds · badges · 20 questions · solo or party</p><div class="by">OBSCURE TRIVIA</div>`,
  'minecraft': `<style>${base}body{background:linear-gradient(180deg,rgba(0,0,0,0) 50%,rgba(14,34,8,.6)),url(${SHEEP}) right 80px top 40px/auto 44% no-repeat,repeating-conic-gradient(rgba(255,255,255,.05) 0 25%,rgba(0,0,0,0) 0 50%) 0 0/52px 52px,linear-gradient(180deg,#70b540,#5b9d32 60%,#4a8627);color:#fff}
    h1{font:400 110px/1 Monocraft,monospace;margin:0;text-shadow:6px 6px 0 #1f1f1f}p{font-size:34px;margin:0;text-shadow:2px 2px 0 #000}
    .by{font:800 26px 'Bricolage Grotesque';color:#7ad155;letter-spacing:.02em;text-shadow:2px 2px 0 #000}</style>
    <h1>Minecraft Quiz</h1><p>Bedrock Edition · 20 questions · solo or party</p><div class="by">OBSCURE TRIVIA</div>`,
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
