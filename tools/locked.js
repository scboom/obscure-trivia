// The locked area (locked/index.html): a password page whose contents are encrypted with that password.
// The password is never stored in the page or in this repository: it comes from the LOCKED_PASSWORD environment variable.
// The page only holds a salt, an IV and the AES-256-GCM ciphertext; the browser derives the key with PBKDF2 (SHA-256).
//
//   LOCKED_PASSWORD=… node locked.js seal SRC_DIR OUT.html   encrypt SRC_DIR/lab.html, lab.css and lab.js into the page
//   LOCKED_PASSWORD=… node locked.js open IN.html OUT_DIR    decrypt the page back into lab.html, lab.css and lab.js to edit them
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ITER = 600000;
const [, , cmd, a, b] = process.argv;
const pw = (process.env.LOCKED_PASSWORD || '').trim();
if (!pw || !/^(seal|open)$/.test(cmd || '') || !a || !b) {
  console.error('usage: LOCKED_PASSWORD=… node locked.js seal SRC_DIR OUT.html | open IN.html OUT_DIR');
  process.exit(2);
}
const readSeal = file => {
  const m = fs.existsSync(file) && fs.readFileSync(file, 'utf8').match(/<script id="sealed" type="application\/json">([^<]*)<\/script>/);
  return m ? JSON.parse(m[1]) : null;
};
const keyFor = (salt, iter) => crypto.pbkdf2Sync(pw, salt, iter, 32, 'sha256');

if (cmd === 'open') {
  const s = readSeal(a);
  if (!s) { console.error('no sealed data in', a); process.exit(1); }
  const raw = Buffer.from(s.data, 'base64');
  const d = crypto.createDecipheriv('aes-256-gcm', keyFor(Buffer.from(s.salt, 'base64'), s.iter), Buffer.from(s.iv, 'base64'));
  d.setAuthTag(raw.subarray(raw.length - 16));
  let bundle;
  try { bundle = JSON.parse(Buffer.concat([d.update(raw.subarray(0, raw.length - 16)), d.final()]).toString('utf8')); }
  catch (e) { console.error('wrong password'); process.exit(1); }
  fs.mkdirSync(b, { recursive: true });
  for (const [k, f] of [['html', 'lab.html'], ['css', 'lab.css'], ['js', 'lab.js']]) fs.writeFileSync(path.join(b, f), bundle[k]);
  console.log('opened', a, '->', b);
  process.exit(0);
}

// seal: keep the old salt so a browser that chose "keep this device unlocked" stays unlocked after an update
const old = readSeal(b);
const salt = old && old.iter === ITER ? Buffer.from(old.salt, 'base64') : crypto.randomBytes(16);
const iv = crypto.randomBytes(12);
const bundle = { v: 1, html: fs.readFileSync(path.join(a, 'lab.html'), 'utf8'), css: fs.readFileSync(path.join(a, 'lab.css'), 'utf8'), js: fs.readFileSync(path.join(a, 'lab.js'), 'utf8') };
const c = crypto.createCipheriv('aes-256-gcm', keyFor(salt, ITER), iv);
const data = Buffer.concat([c.update(JSON.stringify(bundle), 'utf8'), c.final(), c.getAuthTag()]);
const seal = JSON.stringify({ v: 1, alg: 'PBKDF2-SHA256/AES-256-GCM', iter: ITER, salt: salt.toString('base64'), iv: iv.toString('base64'), data: data.toString('base64') });

const LOCK = `<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path fill="currentColor" d="M12 2a5 5 0 0 0-5 5v3H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8a2 2 0 0 0-2-2h-1V7a5 5 0 0 0-5-5zm-3 8V7a3 3 0 1 1 6 0v3H9zm3 4a2 2 0 0 1 1 3.7V19h-2v-1.3A2 2 0 0 1 12 14z"/></svg>`;
const page = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>Locked area – Obscure Trivia</title>
<meta name="theme-color" content="#121117">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='4' y='4' width='56' height='56' rx='14' fill='%23f2efe6'/%3E%3Cpath d='M32 14a10 10 0 0 0-10 10v5h-2a3 3 0 0 0-3 3v15a3 3 0 0 0 3 3h24a3 3 0 0 0 3-3V32a3 3 0 0 0-3-3h-2v-5a10 10 0 0 0-10-10zm-5 15v-5a5 5 0 0 1 10 0v5z' fill='%2315141a'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=Inter:wght@400;500;700&display=swap">
<style>
:root { --bg: #121117; --panel: #1c1b23; --line: #2e2c39; --ink: #f2efe6; --muted: #a7a3b5; --gold: #f2c14e; --bad: #f08a7c;
  --f-display: "Bricolage Grotesque", "Arial Black", system-ui, sans-serif; --f-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; background: radial-gradient(ellipse at 20% -10%, #2a2636 0%, transparent 55%), var(--bg); color: var(--ink); font-family: var(--f-body);
  font-size: 16px; line-height: 1.5; padding: max(22px, env(safe-area-inset-top, 0px)) max(16px, env(safe-area-inset-right, 0px)) 48px max(16px, env(safe-area-inset-left, 0px)); }
.wrap { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 22px; }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--ink); outline-offset: 3px; }
.top { display: flex; align-items: center; gap: 12px; }
.mark { width: 34px; height: 34px; border-radius: 9px; background: var(--ink); color: var(--bg); display: grid; place-items: center; font-family: var(--f-display); font-weight: 800;
  font-size: 1.3rem; transform: rotate(-6deg); text-decoration: none; }
.brand { font-family: var(--f-display); font-weight: 800; font-size: 1.35rem; letter-spacing: -0.01em; text-decoration: none; }
.top .btn { margin-left: auto; }
.eyebrow { font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.btn { border-radius: 10px; border: 1px solid var(--line); padding: 10px 16px; font: inherit; font-weight: 700; background: var(--panel); color: var(--ink); cursor: pointer; }
.btn:hover { border-color: var(--muted); }
.btn.gold { background: var(--ink); color: var(--bg); border-color: var(--ink); }
.btn:disabled { opacity: 0.6; cursor: default; }
.input { border-radius: 10px; border: 1px solid var(--line); background: var(--bg); color: var(--ink); padding: 10px 12px; font: inherit; min-width: 0; }
.gate { align-self: center; width: min(420px, 100%); margin-top: 6vh; background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 24px;
  display: flex; flex-direction: column; gap: 14px; }
.gate .lock { width: 52px; height: 52px; border-radius: 14px; display: grid; place-items: center; background: rgba(242, 193, 78, 0.14); color: var(--gold); }
.gate h2 { margin: 0; font-family: var(--f-display); font-weight: 800; font-size: 1.9rem; letter-spacing: -0.02em; }
.gate p { margin: 0; color: var(--muted); }
.pw { display: flex; gap: 8px; }
.pw .input { flex: 1; }
.check { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 0.92rem; }
.check input { width: 18px; height: 18px; accent-color: var(--gold); }
.err { color: var(--bad); min-height: 1.4em; margin: 0; font-size: 0.92rem; }
.back { color: var(--muted); font-size: 0.92rem; }
.lab { display: flex; flex-direction: column; gap: 18px; }
[hidden] { display: none !important; }
</style>
</head>
<body>
<div class="wrap">
  <header class="top"><a class="mark" href="../" aria-hidden="true" tabindex="-1">?</a><a class="brand" href="../">Obscure Trivia</a><button class="btn" id="relock" hidden>Lock</button></header>
  <main class="gate" id="gate">
    <span class="lock">${LOCK}</span>
    <span class="eyebrow">Locked area</span>
    <h2>Password needed</h2>
    <p>This part of the site is private. Type the password to open it.</p>
    <form class="stack" id="form" autocomplete="on" style="display:flex;flex-direction:column;gap:12px">
      <input type="text" name="username" value="Obscure Trivia locked area" autocomplete="username" hidden>
      <div class="pw"><input class="input" id="pw" type="password" autocomplete="current-password" aria-label="Password" placeholder="Password" required>
        <button class="btn" type="button" id="peek" aria-pressed="false">Show</button></div>
      <label class="check"><input type="checkbox" id="keep"> Keep this device unlocked</label>
      <button class="btn gold" type="submit" id="go">Unlock</button>
      <p class="err" id="err" role="alert"></p>
    </form>
    <a class="back" href="../">← All quizzes</a>
  </main>
  <main class="lab" id="lab" hidden></main>
</div>
<script id="sealed" type="application/json">${seal}</script>
<script>
(() => {
  const SEAL = JSON.parse(document.getElementById("sealed").textContent);
  const KEY = "ot-lab-key";
  const $ = id => document.getElementById(id);
  const bytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  const b64 = buf => btoa(String.fromCharCode(...new Uint8Array(buf)));
  const forget = () => { try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY); } catch (e) {} };
  const remember = (raw, keep) => { const v = JSON.stringify({ salt: SEAL.salt, k: raw }); try { (keep ? localStorage : sessionStorage).setItem(KEY, v); } catch (e) {} };
  async function derive(pw) {
    const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey({ name: "PBKDF2", salt: bytes(SEAL.salt), iterations: SEAL.iter, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, true, ["decrypt"]);
  }
  async function unseal(key) {
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: bytes(SEAL.iv) }, key, bytes(SEAL.data));
    return JSON.parse(new TextDecoder().decode(plain));
  }
  function show(bundle) {
    const st = document.createElement("style"); st.textContent = bundle.css; document.head.appendChild(st);
    $("lab").innerHTML = bundle.html; $("gate").hidden = true; $("lab").hidden = false; $("relock").hidden = false;
    new Function(bundle.js)();
  }
  $("relock").onclick = () => { forget(); location.reload(); };
  $("peek").onclick = () => { const p = $("pw"), on = p.type === "password"; p.type = on ? "text" : "password"; $("peek").textContent = on ? "Hide" : "Show"; $("peek").setAttribute("aria-pressed", String(on)); };
  if (!(window.crypto && crypto.subtle)) { $("err").textContent = "This browser can't open the locked area. Try an up-to-date Chrome, Safari, Firefox or Edge."; $("go").disabled = true; return; }
  $("form").onsubmit = async e => {
    e.preventDefault();
    const pw = $("pw").value.trim();
    if (!pw) return;
    $("go").disabled = true; $("go").textContent = "Unlocking…"; $("err").textContent = "";
    try {
      const key = await derive(pw), bundle = await unseal(key);
      remember(b64(await crypto.subtle.exportKey("raw", key)), $("keep").checked);
      show(bundle);
    } catch (err) {
      $("err").textContent = "That password isn't right. Check it and try again.";
      $("pw").select();
    }
    $("go").disabled = false; $("go").textContent = "Unlock";
  };
  // opened before in this tab (or on this device): no need to type it again
  (async () => {
    let saved = null;
    try { saved = JSON.parse(sessionStorage.getItem(KEY) || localStorage.getItem(KEY) || "null"); } catch (e) {}
    if (!saved || saved.salt !== SEAL.salt || typeof saved.k !== "string") { if (saved) forget(); $("pw").focus(); return; }
    try { show(await unseal(await crypto.subtle.importKey("raw", bytes(saved.k), "AES-GCM", false, ["decrypt"]))); }
    catch (e) { forget(); $("pw").focus(); }
  })();
})();
</script>
</body>
</html>
`;
fs.mkdirSync(path.dirname(b), { recursive: true });
fs.writeFileSync(b, page);
console.log('sealed', a, '->', b, `(${(page.length / 1024).toFixed(1)} KB)`);
