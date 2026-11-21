
(() => {
"use strict";
const ALPH = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
const LEN = 20;
const LET = ["A", "B", "C", "D"];
const QUIZ = window.QUIZ;
const GROUP = QUIZ.groups;
const CAP = QUIZ.caps;

let BANK = null;
let S = { screen: "home", mode: "solo", code: "", nick: "", qs: [], answers: [], cur: 0, compare: null };
let roomState = "idle";

// ------------------------------------------------------------ helpers
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const rich = s => esc(s).replace(/&lt;(\/?)(b|i)&gt;/g, "<$1$2>");
function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

function xmur3(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
  return () => { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); return (h ^= h >>> 16) >>> 0; };
}
function mulberry32(a) {
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function shuffle(arr, rand) {
  for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; }
  return arr;
}
function newCode() {
  const r = new Uint32Array(4); crypto.getRandomValues(r);
  return QUIZ.letter + Array.from(r, x => ALPH[x % ALPH.length]).join("");
}
// a code that starts with another quiz's letter belongs to that quiz
function otherQuizFor(code) { const o = (QUIZ.others || {})[code[0]]; return o && code[0] !== QUIZ.letter ? o : null; }
function normCode(s) { return String(s || "").toUpperCase().replace(/[^A-Z0-9]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1"); }
function validCode(c) { return c.length === 5 && [...c].every(ch => ALPH.includes(ch)); }

function buildQuiz(code) {
  const rand = mulberry32(xmur3(QUIZ.seed + code)());
  const order = shuffle([...BANK.keys()], rand);
  const picked = [], keys = new Set(), groups = {};
  for (const i of order) {
    const q = BANK[i], g = GROUP[q.c] || "Minion";
    if (keys.has(q.k) || (groups[g] || 0) >= CAP[g]) continue;
    keys.add(q.k); groups[g] = (groups[g] || 0) + 1; picked.push(i);
    if (picked.length === LEN) break;
  }
  return picked.map(i => {
    const q = BANK[i];
    const opts = q.c === "trinketkind" ? ["Lesser Trinket", "Greater Trinket"] : shuffle([q.a, ...q.o], rand);
    return { i, opts, correct: opts.indexOf(q.a) };
  });
}
const qOf = item => BANK[item.i];
const myScore = () => S.answers.reduce((n, a, k) => n + (a === S.qs[k].correct ? 1 : 0), 0);
const answeredCount = () => S.answers.filter(a => a !== null && a !== undefined).length;
function encodeAnswers(arr) { return S.qs.map((_, k) => (arr[k] === null || arr[k] === undefined) ? "-" : LET[arr[k]]).join(""); }
function decodeAnswers(str) { return [...String(str || "")].slice(0, LEN).map(ch => { const n = LET.indexOf(ch); return n < 0 ? null : n; }); }
function scoreOf(arr) { return arr.reduce((n, a, k) => n + (S.qs[k] && a === S.qs[k].correct ? 1 : 0), 0); }

// ------------------------------------------------------------ live co-op
// Two ways to reach a friend: the claude.ai room (when the page runs there), otherwise a
// free public MQTT relay. Each player shares { code, name, ans, done }. On the relay every
// player's latest state is kept for two days, so a friend who joins late, or reloads, still
// sees everyone's answers. Two relays are used at once in case one is down.
const MQTT_SRC = "https://unpkg.com/mqtt@5.10.1/dist/mqtt.min.js";
const BROKERS = ["wss://broker.emqx.io:8084/mqtt", "wss://broker.hivemq.com:8884/mqtt"];
let pals = new Map(), leftIds = new Set(), transport = null, gen = 0;

function myState() {
  const done = !!S.finishedAt;
  return { code: S.code, name: (S.nick || "Player").slice(0, 20), ans: encodeAnswers(S.answers), done, t: done ? elapsedSec() : 0 };
}
function setPal(id, st) {
  if (!st || typeof st !== "object" || st.code !== S.code) return;
  const t = Number.isFinite(st.t) && st.t > 0 && st.t < 86400 ? Math.round(st.t) : 0;
  pals.set(id, { id, name: String(st.name || "Your friend").slice(0, 20), answers: decodeAnswers(st.ans), done: !!st.done, t, left: leftIds.has(id) });
  refreshPartnerBits();
}
function markLeft(id) { leftIds.add(id); const p = pals.get(id); if (p && !p.left) { p.left = true; refreshPartnerBits(); } }
function markBack(id) { leftIds.delete(id); const p = pals.get(id); if (p && p.left) { p.left = false; refreshPartnerBits(); } }
function others() { return [...pals.values()]; }
function partnerList() {
  const live = others();
  if (S.compare && !live.some(p => p.name === S.compare.name)) live.push(S.compare);
  return live;
}
function setLive(state) { if (roomState !== state) { roomState = state; refreshPartnerBits(); } }
function withTimeout(p, ms) { return Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]); }

async function viaRoom(code, my) {
  let lobby = null;
  try { lobby = await window.claude?.use?.("room"); } catch (e) { lobby = null; }
  if (!lobby) return null;
  const r = await lobby.join("q-" + code.toLowerCase());
  const unsub = r.onPeers(ch => {
    if (my !== gen) return;
    const here = new Set();
    ch.peers.forEach(p => { if (p.sameTab || !p.presence || !p.presence.code) return; here.add("r:" + p.peer); setPal("r:" + p.peer, p.presence); });
    for (const id of pals.keys()) if (id.startsWith("r:") && !here.has(id)) markLeft(id);
  }, () => { if (my === gen) setLive("off"); });
  return {
    send() { r.presence(myState()).catch(() => {}); },
    close() { try { unsub(); } catch (e) {} try { r.leave(); } catch (e) {} }
  };
}

function loadMqtt() {
  if (window.mqtt) return Promise.resolve(window.mqtt);
  return new Promise((res, rej) => {
    const s = document.createElement("script");
    s.src = MQTT_SRC; s.async = true;
    s.onload = () => window.mqtt ? res(window.mqtt) : rej(new Error("no mqtt"));
    s.onerror = () => rej(new Error("load failed"));
    document.head.appendChild(s);
  });
}
function playerId(code) {
  // one id per browser tab and game, kept across reloads so a refresh doesn't create a second "you"
  const key = "tt-pid-" + code;
  let id = null;
  try { id = sessionStorage.getItem(key); } catch (e) {}
  if (!id || !/^[a-z0-9]{12}$/.test(id)) {
    const r = new Uint32Array(3); crypto.getRandomValues(r);
    id = Array.from(r, x => x.toString(36).padStart(7, "0").slice(-4)).join("");
    try { sessionStorage.setItem(key, id); } catch (e) {}
  }
  return id;
}
async function viaMqtt(code, my) {
  const mqtt = await withTimeout(loadMqtt(), 12000);
  const cfg = window.TT_MQTT || {};
  const v5 = cfg.protocolVersion !== 4;
  const pid = playerId(code);
  const base = QUIZ.topic + code + "/";
  const stateTopic = base + pid, onTopic = base + pid + "/on";
  const keep = v5 ? { properties: { messageExpiryInterval: 172800 } } : {};   // relay forgets it after 2 days
  const pubOpts = { qos: 1, retain: true, ...keep };
  const clients = (cfg.brokers || BROKERS).map(url => {
    const c = mqtt.connect(url, {
      protocolVersion: v5 ? 5 : 4,
      clientId: "tt_" + pid + "_" + Math.random().toString(36).slice(2, 8),
      clean: true, connectTimeout: 10000, reconnectPeriod: 5000, keepalive: 30,
      will: { topic: onTopic, payload: "0", qos: 1, retain: true, ...keep }
    });
    c.on("connect", () => {
      if (my !== gen) return;
      c.subscribe(base + "#", { qos: 1 });
      c.publish(onTopic, "1", pubOpts);
      c.publish(stateTopic, JSON.stringify(myState()), pubOpts);
      setLive("on");
    });
    c.on("message", (topic, buf) => {
      if (my !== gen || !topic.startsWith(base)) return;
      const parts = topic.slice(base.length).split("/");
      const id = parts[0];
      if (!/^[a-z0-9]{12}$/.test(id) || id === pid || buf.length > 2000) return;
      const text = buf.toString();
      if (parts.length === 1) {
        let st = null; try { st = JSON.parse(text); } catch (e) { return; }
        setPal("m:" + id, st);
      } else if (parts.length === 2 && parts[1] === "on") {
        text === "1" ? markBack("m:" + id) : markLeft("m:" + id);
      }
    });
    c.on("error", () => {});
    return c;
  });
  setTimeout(() => { if (my === gen && !clients.some(c => c.connected)) setLive("off"); }, 15000);
  return {
    send() { const s = JSON.stringify(myState()); clients.forEach(c => { if (c.connected) c.publish(stateTopic, s, pubOpts); }); },
    close() { clients.forEach(c => { try { if (c.connected) c.publish(onTopic, "0", pubOpts); c.end(false); } catch (e) {} }); }
  };
}
async function connectLive() {
  if (S.mode !== "coop" || !S.code) return;
  const my = ++gen, code = S.code;
  try { transport && transport.close(); } catch (e) {}
  transport = null; pals = new Map(); leftIds = new Set();
  setLive("connecting");
  let t = null, viaClaude = false;
  try { t = await viaRoom(code, my); viaClaude = !!t; } catch (e) { t = null; }
  if (!t) { try { t = await viaMqtt(code, my); } catch (e) { t = null; } }
  if (my !== gen) { try { t && t.close(); } catch (e) {} return; }
  if (!t) { setLive("off"); return; }
  transport = t;
  if (viaClaude) { setLive("on"); t.send(); }       // the relay sets "on" itself once it connects
}
function joinRoom() { connectLive(); }
function leaveRoom() {
  gen++;
  try { transport && transport.close(); } catch (e) {}
  transport = null; pals = new Map(); leftIds = new Set(); roomState = "idle";
}
function pushPresence() { if (transport) transport.send(); }
window.addEventListener("pagehide", () => { try { transport && transport.close(); } catch (e) {} });

// ------------------------------------------------------------ recent quizzes (saved in this browser only)
const RECENT_KEY = QUIZ.recentKey, RECENT_MAX = 5;
function fmtTime(sec) { sec = Math.max(0, Math.round(sec || 0)); return Math.floor(sec / 60) + ":" + String(sec % 60).padStart(2, "0"); }
function bankVersion() {
  let h = 0; const str = BANK.length + BANK.slice(0, 20).map(q => q.q).join("|");
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) | 0;
  return String(h);
}
function loadRecent() {
  try {
    const a = JSON.parse(store(RECENT_KEY) || "[]");
    return Array.isArray(a) ? a.filter(e => e && validCode(String(e.code)) && e.me && typeof e.me.ans === "string").slice(0, RECENT_MAX) : [];
  } catch (e) { return []; }
}
function saveRecent() {
  if (S.saved || !S.finishedAt || S.past) return;
  S.saved = true;
  const pals = (S.final || []).map(p => ({ n: p.name, ans: encodeAnswers(p.answers), s: scoreOf(p.answers) }));
  const e = { code: S.code, mode: S.mode, at: S.finishedAt, t: elapsedSec(), bv: bankVersion(),
    me: { n: S.meName || S.nick || "You", ans: encodeAnswers(S.answers), s: myScore() }, pals };
  const list = loadRecent().filter(x => !(x.code === e.code && x.at === e.at));
  list.unshift(e);
  store(RECENT_KEY, JSON.stringify(list.slice(0, RECENT_MAX)));
  saveSession();
}
function openRecent(i) {
  const e = loadRecent()[i];
  if (!e) return;
  stopReveal(); leaveRoom();
  S = fresh({ screen: "results", mode: e.mode, code: e.code, qs: buildQuiz(e.code), answers: decodeAnswers(e.me.ans),
    final: (e.pals || []).map(p => ({ name: String(p.n).slice(0, 20), answers: decodeAnswers(p.ans), done: true })),
    startedAt: e.at - (e.t || 0) * 1000, finishedAt: e.at, saved: true, past: true, meName: String(e.me.n || "You").slice(0, 20) });
  render(); window.scrollTo({ top: 0 });
}
function recentView() {
  const list = loadRecent(), bv = bankVersion();
  const when = ms => { try { return new Date(ms).toLocaleString(undefined, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }); } catch (x) { return ""; } };
  const items = list.map((e, i) => {
    const others = e.pals || [];
    const title = others.length ? `Co-op with ${others.map(p => esc(p.n)).join(" &amp; ")}` : e.mode === "coop" ? "Co-op (nobody joined)" : "Solo";
    let outcome = "";
    if (others.length) {
      const all = [e.me, ...others], best = Math.max(...all.map(p => p.s));
      outcome = all.filter(p => p.s === best).length > 1 ? "Tie" : e.me.s === best ? "You won" : `${esc(others.find(p => p.s === best).n)} won`;
    }
    const scores = [`<span class="rc-score"><span class="you-t">${esc(e.me.n)}</span> <b>${e.me.s}</b><small>/${LEN}</small></span>`]
      .concat(others.map(p => `<span class="rc-score"><span class="pal-name">${esc(p.n)}</span> <b>${p.s}</b><small>/${LEN}</small></span>`)).join("");
    return `<li class="rc">
      <div class="rc-top"><span class="rc-title">${title}</span><span class="small muted">${esc(when(e.at))}</span></div>
      <div class="rc-scores">${scores}${outcome ? `<span class="chip${outcome === "You won" ? "" : " mana"}">${outcome}</span>` : ""}</div>
      <div class="rc-foot"><span class="small muted">Game <span class="codechip">${esc(e.code)}</span> · ${fmtTime(e.t)}</span>
        ${e.bv === bv ? `<button class="btn copy" data-recent="${i}">See answers</button>` : ""}</div>
    </li>`;
  }).join("");
  return `${header()}
  <section class="board stack">
    <span class="eyebrow">Recent quizzes</span>
    <h2 style="font-size:1.6rem">Your last ${RECENT_MAX} games</h2>
    ${list.length ? `<ol class="recent">${items}</ol>` : `<p class="muted" style="margin:0">No quizzes yet. Your last ${RECENT_MAX} games show up here once you finish one.</p>`}
    <p class="small muted" style="margin:0">Saved on this device and browser only.</p>
    <div class="row"><button class="btn gold" id="go-home2">Back to home</button></div>
  </section>`;
}

// ------------------------------------------------------------ actions
function fresh(extra) {
  return Object.assign({ screen: "home", mode: "solo", role: "host", code: "", nick: S.nick, qs: [], answers: [], cur: 0, compare: null,
    startedAt: 0, finishedAt: 0, final: null, step: 0, saved: false, past: false, meName: "" }, extra || {});
}
function elapsedSec() { return S.startedAt && S.finishedAt ? Math.max(1, Math.round((S.finishedAt - S.startedAt) / 1000)) : 0; }
function needName() {
  if (S.nick) return false;
  const el = $("#nickerr"); if (el) el.textContent = "Type your name first so your friend knows who you are.";
  const n = $("#nick"); n && n.focus();
  return true;
}
function startGame(mode, code, role) {
  stopReveal();
  S = fresh({ screen: mode === "solo" ? "quiz" : "ready", mode, role: role || "host", code, qs: buildQuiz(code), answers: Array(LEN).fill(null),
    startedAt: mode === "solo" ? Date.now() : 0 });
  render();
  if (mode === "coop") joinRoom(); else leaveRoom();
}
function answer(k) {
  if (S.answers[S.cur] !== null) return;
  S.answers[S.cur] = k; pushPresence(); render();
  const nb = $("#next"); nb && nb.focus({ preventScroll: true });
}
function next() {
  if (S.answers[S.cur] === null) return;
  if (S.cur < LEN - 1) { S.cur++; render(); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  S.finishedAt = Date.now();
  if (S.mode === "coop" && roomState !== "off") { S.screen = "waiting"; pushPresence(); render(); checkAllDone(); }
  else { S.screen = "results"; pushPresence(); render(); saveRecent(); }
  window.scrollTo({ top: 0 });
}
function checkAllDone() {
  if (S.screen !== "waiting") return;
  const ps = others();
  const playing = ps.filter(p => !p.done && !p.left);
  if (ps.some(p => p.done) && !playing.length) startReveal();
}
function finishWithoutWaiting() { startReveal(); }

// the reveal: "Quiz completed!" 5 s, "Let's have a look at the answers" 2 s, then 5 s per question
let revealTimer = 0;
const STEP_MS = k => (k === 0 ? 5000 : k === 1 ? 2000 : 5000) * (window.TT_SPEED || 1);
function startReveal() {
  S.final = others().filter(p => p.done || p.answers.some(a => a !== null))
    .map(p => ({ id: p.id, name: p.name, answers: p.answers.slice(), t: p.t, done: p.done }));
  if (!S.final.length) { S.final = null; S.screen = "results"; render(); saveRecent(); return; }
  S.screen = "reveal"; S.step = 0; render(); window.scrollTo({ top: 0 });
  scheduleStep();
}
function scheduleStep() {
  clearTimeout(revealTimer);
  revealTimer = setTimeout(() => {
    if (S.screen !== "reveal") return;
    if (S.step >= LEN + 1) { endReveal(); return; }
    S.step++; render(); scheduleStep();
  }, STEP_MS(S.step));
}
function stopReveal() { clearTimeout(revealTimer); revealTimer = 0; }
function endReveal() { stopReveal(); S.screen = "results"; render(); window.scrollTo({ top: 0 }); saveRecent(); }

function home() { stopReveal(); leaveRoom(); S = fresh(); clearSession(); render(); }
function showRecent() { stopReveal(); leaveRoom(); S = fresh({ screen: "recent" }); clearSession(); render(); window.scrollTo({ top: 0 }); }
function copyText(text, btn) {
  const done = ok => { if (btn) { const t = btn.textContent; btn.textContent = ok ? "Copied" : "Select it and copy"; setTimeout(() => btn.textContent = t, 1600); } };
  try { navigator.clipboard.writeText(text).then(() => done(true), () => done(false)); } catch (e) { done(false); }
}
function saveSession() {
  if (S.screen === "home" || S.screen === "recent") return;
  try { sessionStorage.setItem(QUIZ.sessionKey, JSON.stringify({ ...S, qs: undefined })); } catch (e) {}
}
function clearSession() { try { sessionStorage.removeItem(QUIZ.sessionKey); } catch (e) {} }

// ------------------------------------------------------------ rendering
function header() {
  const showScore = S.screen === "quiz" || S.screen === "results";
  return `<header class="top">
    <button class="brand" id="go-home" aria-label="${esc(QUIZ.short)} quiz home"><span class="coin" aria-hidden="true">${QUIZ.icon}</span><h1>${esc(QUIZ.short)}</h1></button>
    ${showScore ? `<div class="score" aria-label="Score"><span class="coin" aria-hidden="true"></span><span>${myScore()} / ${LEN}</span></div>`
      : S.screen === "home" ? `<div class="row top-links"><a class="btn copy" href="${QUIZ.hub}">All quizzes</a><button class="btn copy" id="recent-btn">Recent quizzes</button></div>` : ""}
  </header>`;
}
function homeView() {
  const counts = {};
  BANK.forEach(q => { const g = GROUP[q.c]; counts[g] = (counts[g] || 0) + 1; });
  return `${header()}
  <section class="hero">
    <span class="eyebrow">${esc(QUIZ.eyebrow)}</span>
    <h2>${esc(QUIZ.headline)}</h2>
    <p>Twenty random questions from a bank of ${BANK.length.toLocaleString()}: ${esc(QUIZ.topics)}.</p>
    <div class="facts">${Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([g, n]) => `<span class="chip">${n} ${esc(g)}</span>`).join("")}</div>
  </section>
  <div class="field" style="max-width:320px">
    <label for="nick">Your name (shown to your friend)</label>
    <input class="input" id="nick" maxlength="20" placeholder="e.g. Pogo Fan" value="${esc(S.nick)}" autocomplete="nickname">
    <p class="err" id="nickerr" role="alert"></p>
  </div>
  <div class="modes">
    <section class="board mode">
      <span class="eyebrow">Solo</span>
      <h3>Play alone</h3>
      <p>Twenty fresh questions from the bank. Your last 5 games are saved under <b>Recent quizzes</b>.</p>
      <div class="spacer"></div>
      <button class="btn gold block" id="solo">Start 20 questions</button>
    </section>
    <section class="board mode">
      <span class="eyebrow">Co-op</span>
      <h3>Play with a friend</h3>
      <p>Get a 5-letter code and send it to a friend. You both answer the same 20 questions, then watch the answers revealed together.</p>
      <button class="btn gold block" id="create">Create a game</button>
      <div class="divider">or join one</div>
      <form class="row" id="joinform" autocomplete="off">
        <input class="input codein" id="joincode" maxlength="5" placeholder="CODE" aria-label="Invite code">
        <button class="btn" type="submit">Join</button>
      </form>
      <p class="err" id="joinerr" role="alert"></p>
    </section>
  </div>
  <p class="foot">${esc(QUIZ.foot)}</p>`;
}
function palStatus(p) {
  const n = p.answers.filter(a => a !== null).length;
  return p.done ? "Finished" : p.left ? "Left the game" : `On question ${Math.min(n + 1, LEN)} of ${LEN}`;
}
function partnerStrip() {
  if (S.mode !== "coop") return "";
  const list = others();
  let body;
  const guest = S.role === "guest";
  if (roomState === "off" && !list.length) {
    body = `<p class="small muted" style="margin:0">Couldn't reach the live server, so you won't see your friend's progress. You still get the same questions. Swap result codes at the end to compare.</p>`;
  } else if (!list.length) {
    const msg = roomState === "connecting" ? "Connecting…"
      : guest ? `Connected to game ${esc(S.code)}. Nobody else is here yet. Check that your friend clicked <b>Create a game</b> and sent you this exact code.`
      : "Waiting for your friend to join with the code";
    body = `<div class="pal-row"><span class="dot wait" aria-hidden="true"></span><span class="muted">${msg}</span></div>`;
  } else {
    body = list.map(p => `<div class="pal-row"><span class="dot${p.left && !p.done ? " wait" : ""}" aria-hidden="true"></span><span class="pal-name">${esc(p.name)}</span>
        <span class="pal-prog">${palStatus(p)}</span></div>`).join("");
  }
  return `<section class="board partners" id="partners" aria-live="polite">
    <div class="head"><span class="eyebrow">Co-op · code <span class="codechip">${esc(S.code)}</span></span>
    <button class="btn copy" data-copy="${esc(S.code)}">Copy code</button></div>
    ${body}
  </section>`;
}
function readyView() {
  const after = "You'll see which question each other is on, and all the answers are revealed together at the end.";
  if (S.role === "guest") {
    const pals = others();
    const who = pals.length ? pals.map(p => `<b class="pal-name">${esc(p.name)}</b>`).join(" and ") : "";
    return `${header()}
  <section class="board stack center">
    <span class="eyebrow">You joined game</span>
    <div class="code-big" aria-label="Game code ${esc(S.code.split("").join(" "))}">${esc(S.code)}</div>
    <p class="muted" style="margin:0 auto;max-width:46ch">${who ? `You're playing with ${who}. ` : ""}You'll both get the same 20 questions in the same order. ${after}</p>
    <div class="row" style="justify-content:center">
      <button class="btn gold" id="begin">Start the quiz</button>
    </div>
  </section>
  ${partnerStrip()}`;
  }
  return `${header()}
  <section class="board stack center">
    <span class="eyebrow">Your invite code</span>
    <div class="code-big" aria-label="Invite code ${esc(S.code.split("").join(" "))}">${esc(S.code)}</div>
    <p class="muted" style="margin:0 auto;max-width:46ch">Send this code to your friend. They choose <b>Join</b> on the home screen and type it in. You'll both get the same 20 questions in the same order.</p>
    <div class="row" style="justify-content:center">
      <button class="btn" data-copy="${esc(S.code)}">Copy code</button>
      <button class="btn gold" id="begin">Start the quiz</button>
    </div>
    <p class="small muted" style="margin:0 auto;max-width:46ch">You can start before your friend joins. ${after}</p>
  </section>
  ${partnerStrip()}`;
}
function optionsHtml(item, picks, reveal) {
  // picks: [{label, cls, a}] for each player; reveal: show correct answer
  const q = qOf(item), bigLabels = !q.r;
  return item.opts.map((o, k) => {
    const chosen = picks.filter(p => p.a === k);
    let cls = "";
    if (reveal) cls = k === item.correct ? "right" : chosen.length ? "wrong" : "faded";
    const marks = chosen.map(p => `<span class="tag ${p.cls}">${esc(p.label)}</span>`).join("");
    return `<button class="opt ${cls}" data-opt="${k}" ${reveal ? "disabled" : ""}>
      <span class="key">${LET[k]}</span><span class="lbl ${bigLabels ? "big" : ""}">${rich(o)}</span>
      ${marks ? `<span class="marks">${marks}</span>` : ""}</button>`;
  }).join("");
}
function qHead(item, k) {
  const q = qOf(item), g = GROUP[q.c];
  const [qline, ...rest] = q.q.split("\n");
  const card = rest.join(" ");
  return `<div class="qmeta"><span class="eyebrow">Question ${k + 1} of ${LEN}</span>
      <span class="facts" style="margin:0"><span class="chip">${esc(g)}</span>${q.t && q.t !== g ? `<span class="chip mana">${esc(q.t)}</span>` : ""}</span></div>
    <h2 class="qtext">${esc(qline)}</h2>
    ${card ? `<div class="cardtext">${rich(card)}</div>` : ""}`;
}
function quizView() {
  const item = S.qs[S.cur], mine = S.answers[S.cur], done = mine !== null;
  const pips = S.qs.map((it, k) => {
    const a = S.answers[k];
    const cls = k === S.cur && !done ? "now" : a === null ? "" : a === it.correct ? "ok" : "no";
    return `<span class="pip ${cls}"></span>`;
  }).join("");
  return `${header()}
  <div class="pips" aria-label="Progress: question ${S.cur + 1} of ${LEN}">${pips}</div>
  <section class="board stack">
    ${qHead(item, S.cur)}
    <div class="opts" role="group" aria-label="Answers">${optionsHtml(item, done ? [{ label: "You", cls: "you", a: mine }] : [], done)}</div>
    ${done ? `<div class="feedback">
        <span class="verdict ${mine === item.correct ? "ok" : "no"}">${mine === item.correct ? "Correct!" : "Not quite."}</span>
        <button class="btn gold" id="next">${S.cur < LEN - 1 ? "Next question" : "Finish"}</button>
      </div>` : `<p class="small muted" style="margin:0">Tip: press 1 to 4 to answer, Enter for the next question.</p>`}
  </section>
  ${partnerStrip()}`;
}
function waitingView() {
  const ps = others();
  const playing = ps.filter(p => !p.done && !p.left);
  const nobody = !ps.length;
  const leftEarly = ps.some(p => p.left && !p.done);
  const names = playing.map(p => `<b class="pal-name">${esc(p.name)}</b>`).join(" and ");
  return `${header()}
  <section class="board stack center waiting">
    <span class="eyebrow">Game ${esc(S.code)}</span>
    <h2 class="bigmsg">You're done!</h2>
    <p class="muted" style="margin:0 auto;max-width:44ch">${nobody ? "Nobody else has joined this game yet. Send them the code, or see your results now."
      : playing.length ? `Waiting for ${names} to finish. The answers are revealed as soon as everyone's done.`
      : leftEarly ? "Your friend left before finishing." : "Getting the reveal ready…"}</p>
    <div class="hourglass" aria-hidden="true"><span></span></div>
    ${nobody || leftEarly ? `<div class="row" style="justify-content:center"><button class="btn gold" id="nowait">Show my results now</button></div>` : ""}
  </section>
  ${partnerStrip()}`;
}
function revealView() {
  const players = [{ label: S.meName || S.nick || "You", cls: "you", answers: S.answers }].concat((S.final || []).map(p => ({ label: p.name, cls: "pal", answers: p.answers })));
  const ms = STEP_MS(S.step);
  const timer = `<div class="timer" aria-hidden="true"><span style="animation-duration:${ms}ms"></span></div>`;
  const skip = `<button class="btn skip" id="skip">Skip to scores</button>`;
  if (S.step === 0) {
    return `${header()}<section class="board stack center reveal">
      <span class="eyebrow">Game ${esc(S.code)} · ${players.map(p => esc(p.label)).join(" &amp; ")}</span>
      <h2 class="bigmsg pop">Quiz completed!</h2>${timer}${skip}</section>`;
  }
  if (S.step === 1) {
    return `${header()}<section class="board stack center reveal">
      <h2 class="bigmsg pop">Let's have a look at the answers</h2>${timer}${skip}</section>`;
  }
  const k = S.step - 2, item = S.qs[k];
  const picks = players.map(p => ({ label: p.label, cls: p.cls, a: p.answers[k] }));
  const lines = players.map(p => {
    const a = p.answers[k];
    return `<span class="who-line"><b class="${p.cls === "you" ? "you-t" : "pal-name"}">${esc(p.label)}</b> ${a === null || a === undefined ? `<span class="muted">didn't answer</span>` : a === item.correct ? `<span class="ok-t">✓ right</span>` : `<span class="no-t">✗ picked ${LET[a]}</span>`}</span>`;
  }).join("");
  return `${header()}
  <div class="pips" aria-label="Reveal: question ${k + 1} of ${LEN}">${S.qs.map((_, i) => `<span class="pip ${i < k ? "done" : i === k ? "now" : ""}"></span>`).join("")}</div>
  <section class="board stack reveal">
    ${qHead(item, k)}
    <div class="opts">${optionsHtml(item, picks, true)}</div>
    <div class="who-lines">${lines}</div>
    ${timer}
    <div class="row" style="justify-content:flex-end">${skip}</div>
  </section>`;
}
function resultsView() {
  const me = myScore();
  const pals = S.final && S.final.length ? S.final : (S.compare ? [S.compare] : []);
  const myCode = S.code + "-" + encodeAnswers(S.answers);
  const byGroup = {};
  S.qs.forEach((it, k) => { const g = GROUP[qOf(it).c]; byGroup[g] = byGroup[g] || [0, 0]; byGroup[g][1]++; if (S.answers[k] === it.correct) byGroup[g][0]++; });
  const verdict = (QUIZ.verdicts.find(([min]) => me >= min) || QUIZ.verdicts[QUIZ.verdicts.length - 1])[1];
  const scores = [{ name: S.meName || S.nick || "You", s: me, cls: "you" }].concat(pals.map(p => ({ name: p.name, s: scoreOf(p.answers), cls: "pal" })));
  const best = Math.max(...scores.map(x => x.s));
  const tiles = scores.map(x => `<div class="tile ${x.cls}"><span class="eyebrow">${esc(x.name)}${pals.length && x.s === best && scores.filter(y => y.s === best).length === 1 ? " · winner" : ""}</span><span class="n">${x.s}<small> / ${LEN}</small></span></div>`);
  if (pals.length) tiles.push(`<div class="tile"><span class="eyebrow">Team total</span><span class="n">${scores.reduce((a, x) => a + x.s, 0)}<small> / ${LEN * scores.length}</small></span></div>`);
  const review = S.qs.map((it, k) => {
    const q = qOf(it);
    const [qline, ...rest] = q.q.split("\n");
    const line = (who, cls, a) => a === null || a === undefined ? `<div class="ans"><span class="who ${cls}">${esc(who)}</span><span class="v muted">No answer</span></div>`
      : `<div class="ans"><span class="who ${cls}">${esc(who)}</span><span class="v ${a === it.correct ? "ok-t" : "no-t"}">${a === it.correct ? "✓" : "✗"} ${rich(it.opts[a])}</span></div>`;
    return `<div class="rv"><div class="q"><span class="num">${k + 1}.</span>${esc(qline)}${rest.length ? ` <span class="muted small">“${rich(rest.join(" "))}”</span>` : ""}</div>
      ${line(S.meName || S.nick || "You", "you", S.answers[k])}
      ${pals.map(p => line(p.name, "pal", p.answers[k])).join("")}
      ${S.answers[k] !== it.correct ? `<div class="ans"><span class="who key">Answer</span><span class="v">${rich(q.a)}</span></div>` : ""}</div>`;
  }).join("");
  const showCompare = !(S.final && S.final.length) && !S.past;
  return `${header()}
  <section class="board stack">
    <span class="eyebrow">${S.past ? "Past game" : "Results"} · code <span class="codechip">${esc(S.code)}</span> · ${fmtTime(elapsedSec())}</span>
    <h2 style="font-size:1.9rem">${verdict}</h2>
    <div class="tally">${tiles.join("")}</div>
    <div class="facts">${Object.entries(byGroup).map(([g, [a, b]]) => `<span class="chip">${esc(g)} ${a}/${b}</span>`).join("")}</div>
    <div class="row">
      ${S.past ? `<button class="btn gold" id="recent-btn">Back to recent quizzes</button>` : `<button class="btn gold" id="again">${S.mode === "coop" ? "New co-op game" : "Play 20 more"}</button>`}
      <button class="btn" id="go-home2">Home</button>
    </div>
  </section>
  ${showCompare ? `<section class="board stack">
    <span class="eyebrow">Compare with result codes</span>
    <p class="small muted" style="margin:0">Your result code holds your game code and your 20 picks. Send it to a friend who played the same code, or paste theirs below.</p>
    <div class="row"><div class="resultcode" style="flex:1 1 220px">${esc(myCode)}</div><button class="btn" data-copy="${esc(myCode)}">Copy</button></div>
    <form class="row" id="cmpform" autocomplete="off">
      <input class="input" id="cmpname" maxlength="20" placeholder="Friend's name" aria-label="Friend's name" style="flex:1 1 120px">
      <input class="input" id="cmpcode" placeholder="Paste their result code" aria-label="Friend's result code" style="flex:2 1 200px">
      <button class="btn" type="submit">Compare</button>
    </form>
    <p class="err" id="cmperr" role="alert"></p>
  </section>` : ""}
  <details class="stack review-wrap"><summary>See every question again</summary>
    <div class="review">${review}</div>
  </details>`;
}

function render() {
  const app = $("#app");
  if (!BANK) return;
  const v = { home: homeView, recent: recentView, ready: readyView, quiz: quizView, waiting: waitingView, reveal: revealView }[S.screen] || resultsView;
  app.innerHTML = v();
  bind();
  saveSession();
}
function refreshPartnerBits() {
  if (S.screen === "home" || S.screen === "recent" || S.screen === "reveal" || S.screen === "results") return;
  if (S.screen === "waiting") { render(); checkAllDone(); return; }
  if (S.screen === "ready") { render(); return; }
  const el = $("#partners");
  if (el) { el.outerHTML = partnerStrip(); bindCopy(); }
}
function bindCopy() { document.querySelectorAll("[data-copy]").forEach(b => b.onclick = () => copyText(b.dataset.copy, b)); }
function bind() {
  bindCopy();
  const on = (id, fn) => { const el = document.getElementById(id); if (el) el.onclick = fn; };
  on("go-home", home); on("go-home2", home);
  const nick = $("#nick");
  if (nick) nick.oninput = () => { S.nick = nick.value.trim().slice(0, 20); store("tt-nick", S.nick); const e = $("#nickerr"); if (e && S.nick) e.textContent = ""; };
  on("solo", () => startGame("solo", newCode()));
  on("recent-btn", showRecent);
  document.querySelectorAll("[data-recent]").forEach(b => b.onclick = () => openRecent(+b.dataset.recent));
  on("create", () => { if (!needName()) startGame("coop", newCode(), "host"); });
  const jf = $("#joinform");
  if (jf) jf.onsubmit = e => {
    e.preventDefault();
    if (needName()) return;
    const c = normCode($("#joincode").value);
    if (!validCode(c)) { $("#joinerr").textContent = `Codes are 5 letters or numbers, like ${QUIZ.letter}7QX2. Check it and try again.`; return; }
    const other = otherQuizFor(c);
    if (other) { location.href = other + "?join=" + c; return; }
    startGame("coop", c, "guest");
  };
  on("begin", () => { S.screen = "quiz"; S.startedAt = Date.now(); render(); });
  document.querySelectorAll("[data-opt]:not([disabled])").forEach(b => b.onclick = () => answer(+b.dataset.opt));
  on("next", next);
  on("nowait", finishWithoutWaiting);
  on("skip", endReveal);
  on("again", () => startGame(S.mode, newCode(), "host"));
  const cf = $("#cmpform");
  if (cf) cf.onsubmit = e => {
    e.preventDefault();
    const raw = $("#cmpcode").value.trim().toUpperCase();
    const m = raw.match(/^([A-Z0-9]{5})-([ABCD-]{20})$/);
    if (!m) { $("#cmperr").textContent = "That doesn't look like a result code. It should look like K7QX2- followed by 20 letters."; return; }
    if (normCode(m[1]) !== S.code) { $("#cmperr").textContent = `That result is for game ${m[1]}, but you played ${S.code}. You need the same code to compare.`; return; }
    S.compare = { name: ($("#cmpname").value.trim() || "Friend").slice(0, 20), answers: decodeAnswers(m[2]), done: true };
    render();
  };
}
document.addEventListener("keydown", e => {
  if (S.screen !== "quiz" || e.target.tagName === "INPUT") return;
  const k = "1234".indexOf(e.key) >= 0 ? "1234".indexOf(e.key) : "abcd".indexOf(e.key.toLowerCase());
  if (k >= 0 && k < S.qs[S.cur].opts.length && e.key.length === 1) { answer(k); e.preventDefault(); }
  else if (e.key === "Enter" && S.answers[S.cur] !== null && !(e.target.id === "next")) { next(); e.preventDefault(); }
});

// ------------------------------------------------------------ boot
function restore(saved) {
  if (!saved || !saved.code || !validCode(saved.code) || saved.screen === "home") return false;
  S = fresh(saved); S.nick = store("tt-nick") || saved.nick || "";
  S.qs = buildQuiz(S.code);
  if (!Array.isArray(S.answers) || S.answers.length !== LEN) S.answers = Array(LEN).fill(null);
  if (S.screen === "reveal") S.screen = "results";
  render();
  if (S.mode === "coop" && S.screen !== "results") joinRoom();
  if (S.screen === "results") saveRecent();
  return true;
}
function start(saved) {
  S.nick = store("tt-nick") || "";
  fetch(QUIZ.bank).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(bank => {
    BANK = bank;
    let session = null;
    try { session = JSON.parse(sessionStorage.getItem(QUIZ.sessionKey) || "null"); } catch (e) {}
    let join = null;
    try { join = normCode(new URLSearchParams(location.search).get("join") || ""); } catch (e) {}
    if (join && validCode(join) && !otherQuizFor(join)) {
      try { history.replaceState(null, "", location.pathname); } catch (e) {}
      if (S.nick) { startGame("coop", join, "guest"); return; }
      render();
      const jc = $("#joincode"); if (jc) jc.value = join;
      const n = $("#nick"); n && n.focus();
      const e = $("#nickerr"); if (e) e.textContent = "Type your name, then press Join to play game " + join + ".";
      return;
    }
    if (!restore(saved && saved.S) && !restore(session)) render();
  }).catch(() => {
    $("#app").innerHTML = `<div class="loading">The question bank didn't load. Reload the page to try again.</div>`;
  });
}
window.claude?.hot?.snapshot?.(() => ({ S: { ...S, qs: undefined } }));
window.claude?.hot?.ready ? window.claude.hot.ready(start) : start(window.claude?.hot?.data ?? {});
})();
