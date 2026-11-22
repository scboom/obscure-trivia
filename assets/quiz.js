
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
    const q = BANK[i], g = GROUP[q.c] || "Minion", ks = q.ks || [q.k];
    if (ks.some(k => keys.has(k)) || (groups[g] || 0) >= CAP[g]) continue;
    ks.forEach(k => keys.add(k)); groups[g] = (groups[g] || 0) + 1; picked.push(i);
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

// ------------------------------------------------------------ live party
// Two ways to reach a friend: the claude.ai room (when the page runs there), otherwise a
// free public MQTT relay. Each player shares { code, name, ans, done }. On the relay every
// player's latest state is kept for two days, so a friend who joins late, or reloads, still
// sees everyone's answers. Two relays are used at once in case one is down.
const MQTT_SRC = "https://unpkg.com/mqtt@5.10.1/dist/mqtt.min.js";
const BROKERS = ["wss://broker.emqx.io:8084/mqtt", "wss://broker.hivemq.com:8884/mqtt"];
let pals = new Map(), leftIds = new Set(), transport = null, gen = 0;

function myState() {
  const done = !!S.finishedAt;
  return { code: S.code, name: (S.nick || "Player").slice(0, 20), ans: encodeAnswers(S.answers), done, t: done ? elapsedSec() : 0, j: S.joinedAt || 0, sk: S.skipVote ? 1 : 0 };
}
const MULTI = m => m === "coop" || m === "party";
const PARTY_MAX = 6;
function capOf() { return S.meta && S.meta.cap ? S.meta.cap : PARTY_MAX; }
// everyone in the game, me included, in join order: earliest first
function orderedAll() {
  const list = others().map(p => ({ id: p.id, pid: p.id.slice(2), j: p.j || Infinity, name: p.name }));
  list.push({ id: "me", pid: S.pid || "", j: S.joinedAt || 0, name: S.nick || "You", me: true });
  return list.sort((a, b) => a.j - b.j || (a.pid < b.pid ? -1 : a.pid > b.pid ? 1 : 0));
}
// the other players who are actually in my game (not ones turned away as extra)
function gamePlayers() {
  const m = S.meta;
  if (m && m.started && Array.isArray(m.players)) return others().filter(p => m.players.includes(p.id.slice(2)));
  const allowed = new Set(orderedAll().slice(0, capOf()).map(x => x.id));
  return others().filter(p => allowed.has(p.id));
}
function colorOf(id) {
  const ids = orderedAll().filter(x => !x.me).map(x => x.id);
  const i = ids.indexOf(id);
  return "c" + ((i < 0 ? 0 : i) % 5 + 1);
}
function effectiveHost() {
  const all = orderedAll().slice(0, capOf());
  const fromMeta = S.meta && S.meta.host;
  // a party moved here by its host: that player is host, even before they arrive (for 20 seconds)
  const named = fromMeta || (S.expectHost && Date.now() < S.expectUntil ? S.expectHost : "");
  const h = all.find(x => (x.me ? S.pid : x.pid) === named && !(pals.get(x.id) || {}).left);
  if (h) return h;
  if (named && !fromMeta) return null;
  return all.find(x => x.me || !(pals.get(x.id) || {}).left) || all[0];
}
function hostPid() { const h = effectiveHost(); return h ? (h.me ? S.pid : h.pid) : ""; }
function iAmHost() { const h = effectiveHost(); return !!(h && h.me); }
function setMeta(m) {
  if (!m || typeof m !== "object" || !/^(coop|party)$/.test(m.mode)) return;
  const cap = Math.max(2, Math.min(PARTY_MAX, parseInt(m.cap, 10) || PARTY_MAX));
  S.meta = { mode: m.mode, cap, host: String(m.host || ""), started: Number(m.started) || 0,
    players: Array.isArray(m.players) ? m.players.filter(x => /^[a-z0-9]{12}$/.test(x)).slice(0, cap) : null };
  if (S.role === "guest" && S.mode !== m.mode) S.mode = m.mode;
  if (S.meta.started && S.screen === "ready") {
    if (S.meta.players && S.meta.players.includes(S.pid)) { S.screen = "quiz"; S.startedAt = Date.now(); render(); window.scrollTo({ top: 0 }); return; }
    turnAway("started"); return;
  }
  refreshPartnerBits();
}
function checkCapacity() {
  if (!S.synced || S.screen !== "ready" || (S.meta && S.meta.started)) return;
  const idx = orderedAll().findIndex(x => x.me);
  if (idx >= capOf()) turnAway("full");
}
function turnAway(reason) {
  S.fullReason = reason; S.fullCount = capOf();
  try { transport && transport.close(true); } catch (e) {}
  transport = null; gen++;
  S.screen = "full"; render();
}
function setPal(id, st) {
  if (!st || typeof st !== "object" || st.code !== S.code) return;
  const t = Number.isFinite(st.t) && st.t > 0 && st.t < 86400 ? Math.round(st.t) : 0;
  const j = Number.isFinite(st.j) && st.j > 0 ? st.j : 0;
  pals.set(id, { id, name: String(st.name || "Player").slice(0, 20), answers: decodeAnswers(st.ans), done: !!st.done, t, j, sk: st.sk === 1, left: leftIds.has(id) });
  refreshPartnerBits();
  checkCapacity();
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
      c.subscribe(base + "#", { qos: 1 }, () => setTimeout(() => { if (my === gen) { S.synced = true; checkCapacity(); refreshPartnerBits(); } }, 1500));
      c.publish(onTopic, "1", pubOpts);
      c.publish(stateTopic, JSON.stringify(myState()), pubOpts);
      if (S.role === "host" && !S.metaSent) {
        S.metaSent = true;
        S.meta = { mode: "party", cap: PARTY_MAX, host: pid, started: 0, players: null };
        c.publish(base + "meta", JSON.stringify(S.meta), pubOpts);
        saveSession();
      }
      setLive("on");
    });
    c.on("message", (topic, buf) => {
      if (my !== gen || !topic.startsWith(base)) return;
      const parts = topic.slice(base.length).split("/");
      const id = parts[0];
      if (id === "meta" && parts.length === 1 && buf.length && buf.length < 2000) {
        let m = null; try { m = JSON.parse(buf.toString()); } catch (e) { return; }
        setMeta(m); return;
      }
      if (id === "next" && parts.length === 1 && buf.length && buf.length < 500) {
        let m = null; try { m = JSON.parse(buf.toString()); } catch (e) { return; }
        onNext(m); return;
      }
      if (!/^[a-z0-9]{12}$/.test(id) || id === pid || buf.length > 2000) return;
      const text = buf.toString();
      if (!buf.length) { if (parts.length === 1 && pals.delete("m:" + id)) refreshPartnerBits(); return; }
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
    meta(m) { const s = JSON.stringify(m); clients.forEach(c => { if (c.connected) c.publish(base + "meta", s, pubOpts); }); },
    // the host moving the party on to a new game; resolves once a relay has it (or after 1.5 s)
    next(m) {
      const s = JSON.stringify(m), opts = { qos: 1, retain: true, ...(v5 ? { properties: { messageExpiryInterval: 3600 } } : {}) };
      return new Promise(res => {
        let done = false; const fin = () => { if (!done) { done = true; res(); } };
        setTimeout(fin, 1500);
        clients.forEach(c => { if (c.connected) c.publish(base + "next", s, opts, fin); });
      });
    },
    // leaving a lobby before the game starts frees the seat; leaving mid-game keeps your answers
    close(remove) {
      clients.forEach(c => {
        try {
          if (c.connected) {
            if (remove) { c.publish(stateTopic, "", { qos: 1, retain: true }); c.publish(onTopic, "", { qos: 1, retain: true }); }
            else c.publish(onTopic, "0", pubOpts);
          }
          c.end(false);
        } catch (e) {}
      });
    }
  };
}
async function connectLive() {
  if (!MULTI(S.mode) || !S.code) return;
  const my = ++gen, code = S.code;
  try { transport && transport.close(); } catch (e) {}
  transport = null; pals = new Map(); leftIds = new Set(); S.synced = false;
  setLive("connecting");
  let t = null;
  try { t = await viaMqtt(code, my); } catch (e) { t = null; }
  if (my !== gen) { try { t && t.close(); } catch (e) {} return; }
  if (!t) { setLive("off"); return; }
  transport = t;                                     // the relay sets "on" itself once it connects
}
function joinRoom() { connectLive(); }
function leaveRoom() {
  gen++;
  try { transport && transport.close(S.screen === "ready"); } catch (e) {}
  transport = null; pals = new Map(); leftIds = new Set(); roomState = "idle";
}
function pushPresence() { if (transport) transport.send(); }
window.addEventListener("pagehide", () => { try { transport && transport.close(S.screen === "ready"); } catch (e) {} });

// ------------------------------------------------------------ recent quizzes (saved in this browser only)
const RECENT_KEY = QUIZ.recentKey, RECENT_MAX = 5;
function ordinal(n) { const s = ["th", "st", "nd", "rd"], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); }
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
  const pals = (S.final || []).map(p => ({ n: p.name, ans: encodeAnswers(p.answers), s: scoreOf(p.answers), t: p.t || 0 }));
  const e = { code: S.code, mode: S.mode, at: S.finishedAt, t: elapsedSec(), bv: bankVersion(),
    me: { n: S.meName || S.nick || "You", ans: encodeAnswers(S.answers), s: myScore() }, pals };
  const list = loadRecent().filter(x => !(x.code === e.code && x.at === e.at));
  list.unshift(e);
  store(RECENT_KEY, JSON.stringify(list.slice(0, RECENT_MAX)));
  saveSession();
  postScore();
}
function openRecent(i) {
  const e = loadRecent()[i];
  if (!e) return;
  stopReveal(); leaveRoom();
  S = fresh({ screen: "results", mode: e.mode, code: e.code, qs: buildQuiz(e.code), answers: decodeAnswers(e.me.ans),
    final: (e.pals || []).map((p, i) => ({ id: "h" + i, name: String(p.n).slice(0, 20), answers: decodeAnswers(p.ans), done: true, t: p.t || 0, c: "c" + (i % 5 + 1) })),
    startedAt: e.at - (e.t || 0) * 1000, finishedAt: e.at, saved: true, past: true, meName: String(e.me.n || "You").slice(0, 20) });
  render(); window.scrollTo({ top: 0 });
}
function recentView() {
  const list = loadRecent(), bv = bankVersion();
  const when = ms => { try { return new Date(ms).toLocaleString(undefined, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }); } catch (x) { return ""; } };
  const items = list.map((e, i) => {
    const others = e.pals || [];
    const names = others.map(p => esc(p.n));
    const title = others.length ? `Party with ${names.length > 3 ? names.slice(0, 3).join(", ") + " &amp; " + (names.length - 3) + " more" : names.join(" &amp; ")}`
      : MULTI(e.mode) ? "Party (nobody joined)" : "Solo";
    let outcome = "";
    if (others.length) {
      const place = 1 + others.filter(p => p.s > e.me.s).length;
      const tied = others.some(p => p.s === e.me.s);
      outcome = place === 1 ? (tied ? "Tied for 1st" : "You won") : `You came ${ordinal(place)} of ${others.length + 1}`;
    }
    const scores = [`<span class="rc-score"><span class="you-t">${esc(e.me.n)}</span> <b>${e.me.s}</b><small>/${LEN}</small></span>`]
      .concat(others.map((p, i) => `<span class="rc-score"><span class="pal-name c${i % 5 + 1}">${esc(p.n)}</span> <b>${p.s}</b><small>/${LEN}</small></span>`)).join("");
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


// ------------------------------------------------------------ top scores this week
// Each finished game posts every player's score to the relay; every visitor sees the 3 best from the last 7 days
// (the same person can hold all three). Ties go to the faster time, then the more recent game.
const FEED_BASE = QUIZ.topic + "feed/";
const WEEK = 7 * 864e5;
const FEED = { entries: new Map(), clients: [], state: "idle", queue: [], open: false };
function feedValid(e) {
  if (!e || typeof e !== "object" || e.v !== 1) return null;
  const s = Number(e.s), p = Number(e.p), at = Number(e.at), t = Number(e.t);
  if (!Number.isInteger(s) || s < 0 || s > LEN || !Number.isInteger(p) || p < 1 || p > PARTY_MAX) return null;
  if (!Number.isFinite(at) || at > Date.now() + 864e5 || at < Date.now() - WEEK) return null;
  return { n: String(e.n || "Someone").slice(0, 20), s, p, at, t: Number.isFinite(t) ? Math.max(0, Math.min(LIMIT_MS / 1000, Math.round(t))) : 0, m: e.m === "party" ? "party" : "solo" };
}
function feedRank(a, b) { return b.s - a.s || (a.t || 1e9) - (b.t || 1e9) || b.at - a.at; }
function feedTop() { const cut = Date.now() - WEEK; return [...FEED.entries.values()].filter(e => e.at >= cut).sort(feedRank).slice(0, 3); }
function feedConnect() {
  if (FEED.state !== "idle") return;
  FEED.state = "connecting";
  loadMqtt().then(mqtt => {
    const cfg = window.TT_MQTT || {};
    const v5 = cfg.protocolVersion !== 4;
    FEED.v5 = v5;
    FEED.clients = (cfg.brokers || BROKERS).map(url => {
      const c = mqtt.connect(url, { protocolVersion: v5 ? 5 : 4, clientId: "ttf_" + Math.random().toString(36).slice(2, 12),
        clean: true, connectTimeout: 10000, reconnectPeriod: 10000, keepalive: 60 });
      c.on("connect", () => {
        FEED.state = "on";
        c.subscribe(FEED_BASE + "+", { qos: 1 }, () => setTimeout(feedPrune, 2500));
        FEED.queue.splice(0).forEach(([id, msg]) => feedPublish(id, msg));
        renderFeed();
      });
      c.on("message", (topic, buf) => {
        const id = topic.slice(FEED_BASE.length);
        if (!/^[a-z0-9]{10}$/.test(id) || buf.length > 600) return;
        if (!buf.length) { FEED.entries.delete(id); renderFeed(); return; }
        let raw = null; try { raw = JSON.parse(buf.toString()); } catch (x) { return; }
        const e = feedValid(raw);
        if (e) { FEED.entries.set(id, e); renderFeed(); }
        else if (raw && Number(raw.at) < Date.now() - WEEK) c.publish(topic, "", { qos: 1, retain: true });   // over a week old: clear it
      });
      c.on("error", () => {});
      return c;
    });
    setTimeout(() => { if (FEED.state !== "on") { FEED.state = "off"; renderFeed(); } }, 15000);
  }).catch(() => { FEED.state = "off"; renderFeed(); });
}
function feedPublish(id, msg) {
  const live = FEED.clients.filter(c => c.connected);
  if (!live.length) { FEED.queue.push([id, msg]); return; }
  const opts = { qos: 1, retain: true, ...(FEED.v5 ? { properties: { messageExpiryInterval: 7 * 86400 } } : {}) };
  live.forEach(c => c.publish(FEED_BASE + id, msg, opts));
}
function feedPrune() {   // keep the relay tidy: drop scores over a week old and scores that can never be top 3 again
  const cut = Date.now() - WEEK, all = [...FEED.entries.entries()];
  // a score is beaten for good once 3 better scores exist that will last at least as long (posted no earlier)
  const beaten = ([id, e]) => all.filter(([j, f]) => j !== id && f.at >= e.at && feedRank(f, e) < 0).length >= 3;
  const keep = all.filter(x => x[1].at >= cut && !beaten(x)).sort((a, b) => feedRank(a[1], b[1])).slice(0, 40).map(x => x[0]);
  all.filter(([id]) => !keep.includes(id)).forEach(([id]) => {
    FEED.entries.delete(id);
    FEED.clients.forEach(c => { if (c.connected) c.publish(FEED_BASE + id, "", { qos: 1, retain: true }); });
  });
}
function postScore() {
  if (S.posted || S.past || !S.finishedAt) return;
  const pals = S.final || [];
  if (MULTI(S.mode) && pals.length && !iAmHost()) { S.posted = true; return; }   // one post per party, from the host
  const all = [{ n: S.nick || (MULTI(S.mode) ? "Player" : "Someone"), s: myScore(), t: elapsedSec() }]
    .concat(pals.map(p => ({ n: p.name, s: scoreOf(p.answers), t: p.t || 0 })));
  all.sort((a, b) => b.s - a.s || (a.t || 1e9) - (b.t || 1e9));
  const at = Date.now(), m = MULTI(S.mode) ? "party" : "solo", p = Math.min(PARTY_MAX, all.length);
  S.posted = true;
  all.slice(0, PARTY_MAX).forEach(pl => {   // every player's score counts, one relay entry each
    const id = Array.from(crypto.getRandomValues(new Uint32Array(2)), x => x.toString(36).padStart(7, "0").slice(-5)).join("");
    const e = { v: 1, n: String(pl.n).slice(0, 20), s: pl.s, t: pl.t, m, p, at };
    FEED.entries.set(id, feedValid(e));
    feedPublish(id, JSON.stringify(e));
  });
  if (FEED.state === "on") feedPrune();
  renderFeed();
}
function ago(ms) {
  const m = Math.max(0, Math.round((Date.now() - ms) / 60000));
  return m < 1 ? "just now" : m < 60 ? m + " min ago" : m < 1440 ? Math.round(m / 60) + " h ago" : Math.round(m / 1440) + " d ago";
}
const TROPHY = `<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M7 3h10v2h3v3a4 4 0 0 1-4 4h-.3A5 5 0 0 1 13 14.9V17h3v3H8v-3h3v-2.1A5 5 0 0 1 8.3 12H8a4 4 0 0 1-4-4V5h3V3zm0 4H6v1a2 2 0 0 0 1 1.7V7zm10 0v2.7A2 2 0 0 0 18 8V7h-1z"/></svg>`;
function feedTab() {
  if (S.screen !== "home" && S.screen !== "results") return "";
  const list = feedTop();
  const body = list.length ? `<ol class="feed-list">${list.map((e, i) => `<li><span class="feed-rank">${i + 1}</span><b>${esc(e.n)}</b> scored <b class="feed-score">${e.s}/${LEN}</b>
      <span class="muted">${e.m === "party" ? `party of ${e.p}` : "solo"}${e.t ? ` · ${fmtTime(e.t)}` : ""} · ${ago(e.at)}</span></li>`).join("")}</ol>`
    : `<p class="small muted" style="margin:0">${FEED.state === "off" ? "Couldn't load scores right now." : FEED.state === "on" ? "No scores this week yet. Finish a quiz to set one!" : "Loading…"}</p>`;
  return `<aside class="feed${FEED.open ? " open" : ""}" id="feed">
    ${FEED.open ? `<div class="feed-panel" id="feed-panel"><div class="feed-head"><span class="eyebrow">Top scores this week</span><button class="feed-x" id="feed-close" aria-label="Close">×</button></div>${body}</div>` : ""}
    <button class="feed-btn" id="feed-btn" aria-expanded="${FEED.open}" aria-controls="feed-panel">${TROPHY}<span>Top scores</span></button>
  </aside>`;
}
function renderFeed() {
  const el = $("#feed");
  if (el) { el.outerHTML = feedTab(); bindFeed(); }
}
function bindFeed() {
  const b = $("#feed-btn"); if (b) b.onclick = () => { FEED.open = !FEED.open; renderFeed(); };
  const x = $("#feed-close"); if (x) x.onclick = () => { FEED.open = false; renderFeed(); };
}

// ------------------------------------------------------------ actions
function fresh(extra) {
  return Object.assign({ screen: "home", mode: "solo", role: "host", code: "", nick: S.nick, qs: [], answers: [], cur: 0, compare: null,
    startedAt: 0, finishedAt: 0, final: null, step: 0, saved: false, past: false, meName: "",
    pid: "", joinedAt: 0, meta: null, metaSent: false, synced: false, fullReason: "", timedOut: false, skipVote: false, posted: false,
    expectHost: "", expectUntil: 0, pickQuiz: false }, extra || {});
}
function elapsedSec() { return S.startedAt && S.finishedAt ? Math.max(1, Math.min(LIMIT_MS / 1000, Math.round((S.finishedAt - S.startedAt) / 1000))) : 0; }

// ------------------------------------------------------------ 10-minute limit
const LIMIT_MS = (window.TT_LIMIT_S || 600) * 1000;
function timeLeft() { return S.startedAt ? Math.max(0, S.startedAt + LIMIT_MS - Date.now()) : LIMIT_MS; }
// the countdown: big digits at the top middle of the screen, a bar that drains, amber under 2 minutes, red under 1
function clockHtml() {
  const left = timeLeft();
  return `<div class="clockbox${clockState(left)}" id="clockbox" role="timer" aria-label="Time left">
    <span class="clock-label">Time left</span><span class="clock" id="clock">${fmtTime(Math.ceil(left / 1000))}</span>
    <span class="clock-bar" aria-hidden="true"><span id="clockfill" style="transform:scaleX(${(left / LIMIT_MS).toFixed(4)})"></span></span></div>`;
}
function clockState(left) { return (left < 60000 ? " low" : left < 120000 ? " warn" : "") + (window.scrollY > 30 ? " compact" : ""); }
// scrolled down: the timer shrinks to a slim pill so it covers less of the question
window.addEventListener("scroll", () => { const b = $("#clockbox"); if (b) b.className = "clockbox" + clockState(timeLeft()); }, { passive: true });
function tick() {
  if (S.screen !== "quiz" || !S.startedAt) return;
  const left = timeLeft(), el = $("#clock"), box = $("#clockbox"), fill = $("#clockfill");
  if (el) el.textContent = fmtTime(Math.ceil(left / 1000));
  if (box) box.className = "clockbox" + clockState(left);
  if (fill) fill.style.transform = `scaleX(${(left / LIMIT_MS).toFixed(4)})`;
  if (left <= 0) { S.timedOut = true; finishQuiz(); }
}
setInterval(tick, 250);
function needName() {
  if (S.nick) return false;
  const el = $("#nickerr"); if (el) el.textContent = "Type your name first so the other players know who you are.";
  const n = $("#nick"); n && n.focus();
  return true;
}
function startGame(mode, code, role) {
  stopReveal();
  if (MULTI(S.mode)) leaveRoom();
  S = fresh({ screen: mode === "solo" ? "quiz" : "ready", mode, role: role || "host", code, qs: buildQuiz(code), answers: Array(LEN).fill(null),
    startedAt: mode === "solo" ? Date.now() : 0, pid: MULTI(mode) ? playerId(code) : "", joinedAt: Date.now() });
  render(); window.scrollTo({ top: 0 });
  if (MULTI(mode)) joinRoom(); else leaveRoom();
}
function startParty() {
  if (!iAmHost() || !transport) return;
  const ids = orderedAll().slice(0, capOf()).filter(x => x.me || !(pals.get(x.id) || {}).left).map(x => x.me ? S.pid : x.pid);
  if (ids.length < 2) return;
  S.meta = Object.assign({}, S.meta || { mode: "party", cap: PARTY_MAX, host: S.pid }, { started: Date.now(), players: ids });
  transport.meta(S.meta);
  S.screen = "quiz"; S.startedAt = Date.now(); render(); window.scrollTo({ top: 0 });
}
function answer(k) {
  if (S.answers[S.cur] !== null) return;
  S.answers[S.cur] = k; pushPresence(); render();
  const nb = $("#next"); nb && nb.focus({ preventScroll: true });
}
function next() {
  if (S.answers[S.cur] === null) return;
  if (S.cur < LEN - 1) { S.cur++; render(); window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  finishQuiz();
}
function finishQuiz() {
  if (S.screen !== "quiz") return;
  S.finishedAt = Math.min(Date.now(), S.startedAt ? S.startedAt + LIMIT_MS : Date.now());
  if (MULTI(S.mode) && roomState !== "off") { S.screen = "waiting"; pushPresence(); render(); checkAllDone(); }
  else { S.screen = "results"; pushPresence(); render(); saveRecent(); }
  window.scrollTo({ top: 0 });
}
function checkAllDone() {
  if (S.screen !== "waiting") return;
  const ps = gamePlayers();
  const playing = ps.filter(p => !p.done && !p.left);
  if (ps.some(p => p.done) && !playing.length) startReveal();
}
function finishWithoutWaiting() { startReveal(); }

// the reveal: "Quiz completed!" 5 s, "Let's have a look at the answers" 2 s, then 5 s per question
let revealTimer = 0;
const STEP_MS = k => (k === 0 ? 5000 : k === 1 ? 2000 : 5000) * (window.TT_SPEED || 1);
function startReveal() {
  S.final = gamePlayers().filter(p => p.done || p.answers.some(a => a !== null))
    .map(p => ({ id: p.id, name: p.name, answers: p.answers.slice(), t: p.t, done: p.done, c: colorOf(p.id) }));
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
// in a party everyone still in the game has to vote before the reveal is skipped
function skipTally() {
  const ids = (S.final || []).map(p => p.id).filter(id => { const p = pals.get(id); return !(p && p.left); });
  const votes = (S.skipVote ? 1 : 0) + ids.filter(id => (pals.get(id) || {}).sk).length;
  return { votes, needed: 1 + ids.length };
}
function skipLabel() {
  if (!MULTI(S.mode) || !(S.final && S.final.length) || roomState !== "on") return "Skip to results";
  const { votes, needed } = skipTally();
  return `Skip to results ${votes}/${needed}`;   // greyed out once you've voted
}
function checkSkip() {
  if (S.screen !== "reveal" || !S.skipVote) return;
  const { votes, needed } = skipTally();
  if (votes >= needed) endReveal();
}
function onSkip() {
  if (!MULTI(S.mode) || !(S.final && S.final.length) || roomState !== "on") { endReveal(); return; }
  S.skipVote = true; pushPresence();
  const el = $("#skip"); if (el) { el.textContent = skipLabel(); el.disabled = true; }
  checkSkip();
}
// ------------------------------------------------------------ keep the party going: play again / change quiz
function quizUrl(letter) {
  const c = (QUIZ.catalog || []).find(x => x.letter === letter);
  return c ? c.url : (QUIZ.others || {})[letter];
}
function expectHost(pid) {
  if (!/^[a-z0-9]{12}$/.test(pid || "")) return;
  S.expectHost = pid; S.expectUntil = Date.now() + 20000;
  setTimeout(refreshPartnerBits, 20500);
}
async function nextGame(letter) {
  if (!iAmHost() || !transport || S.moving) return;
  const target = letter || QUIZ.letter;
  if (target !== QUIZ.letter && !quizUrl(target)) return;
  S.moving = true; render();
  const r = new Uint32Array(4); crypto.getRandomValues(r);
  const code = target + Array.from(r, x => ALPH[x % ALPH.length]).join("");
  const me = playerId(code);                       // the same id the new lobby will use for me
  await transport.next({ code, host: me, from: S.pid, t: Date.now() });
  if (target === QUIZ.letter) { startGame("party", code, "host"); window.scrollTo({ top: 0 }); }
  else location.href = quizUrl(target) + "?host=" + code;
}
function onNext(m) {
  if (!m || typeof m !== "object" || !validCode(String(m.code || "")) || m.code === S.code) return;
  if (!MULTI(S.mode) || !(S.screen === "results" || S.screen === "reveal") || S.past) return;
  if (m.from === S.pid || m.from !== hostPid() || !(Date.now() - Number(m.t) < 3600000)) return;
  if (S.screen === "reveal") { stopReveal(); saveRecent(); }
  const code = m.code;
  if (code[0] === QUIZ.letter) {
    startGame("party", code, "guest");
    expectHost(m.host); render(); window.scrollTo({ top: 0 });
  } else {
    const url = quizUrl(code[0]);
    if (url) location.href = url + "?join=" + code + (/^[a-z0-9]{12}$/.test(m.host || "") ? "&h=" + m.host : "");
  }
}
function nextGameHtml() {
  const live = MULTI(S.mode) && !S.past && transport && roomState === "on";
  if (!live) return `<div id="nextgame" hidden></div>`;
  if (S.moving) return `<section class="board stack center" id="nextgame"><span class="eyebrow">Next game</span><p class="muted" style="margin:0">Moving everyone to the new lobby…</p></section>`;
  const here = 1 + (S.final || []).filter(p => { const q = pals.get(p.id); return q && !q.left; }).length;
  if (iAmHost()) {
    const quizzes = (QUIZ.catalog || []).filter(c => c.letter !== QUIZ.letter);
    return `<section class="board stack" id="nextgame">
      <span class="eyebrow">Next game · ${here} ${here === 1 ? "player" : "players"} still here</span>
      <h3 style="font-size:1.3rem">Keep the party going</h3>
      <p class="small muted" style="margin:0">Everyone still on this screen moves with you into a new lobby. Press Start once they're all in.</p>
      <div class="row"><button class="btn gold" id="again-party">Play again</button>
        <button class="btn" id="change-quiz" aria-expanded="${S.pickQuiz ? "true" : "false"}">Change quiz</button></div>
      ${S.pickQuiz ? `<div class="quizpick" role="group" aria-label="Choose a quiz">${quizzes.map(c => `<button class="btn" data-quiz="${esc(c.letter)}">${esc(c.name)}</button>`).join("")}</div>` : ""}
    </section>`;
  }
  const h = effectiveHost();
  return `<section class="board stack" id="nextgame">
    <span class="eyebrow">Next game</span>
    <p class="muted" style="margin:0">Waiting for <b class="${h ? "pal-name " + colorOf(h.id) : ""}">${esc(h ? h.name : "the host")}</b> to start another game. Stay on this screen and you'll be moved there automatically.</p>
  </section>`;
}
function bindNext() {
  const a = $("#again-party"); if (a) a.onclick = () => nextGame();
  const c = $("#change-quiz"); if (c) c.onclick = () => { S.pickQuiz = !S.pickQuiz; refreshNext(); };
  document.querySelectorAll("[data-quiz]").forEach(b => b.onclick = () => nextGame(b.dataset.quiz));
}
function refreshNext() { const el = $("#nextgame"); if (el) { el.outerHTML = nextGameHtml(); bindNext(); } }
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
  return `<header class="top${S.screen === "quiz" ? " quiz-top" : ""}">
    <button class="brand" id="go-home" aria-label="${esc(QUIZ.short)} quiz home"><span class="coin" aria-hidden="true">${QUIZ.icon}</span><h1>${esc(QUIZ.short)}</h1></button>
    ${S.screen === "quiz" ? `${clockHtml()}<div class="score" aria-label="Score"><span class="coin" aria-hidden="true"></span><span>${myScore()} / ${LEN}</span></div>`
      : showScore ? `<div class="score" aria-label="Score"><span class="coin" aria-hidden="true"></span><span>${myScore()} / ${LEN}</span></div>`
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
    <label for="nick">Your name (shown to other players)</label>
    <input class="input" id="nick" maxlength="20" placeholder="${esc(QUIZ.namePh || "e.g. Sam")}" value="${esc(S.nick)}" autocomplete="nickname">
    <p class="err" id="nickerr" role="alert"></p>
  </div>
  <div class="modes">
    <section class="board mode">
      <span class="eyebrow">Solo</span>
      <h3>Play alone</h3>
      <p>Twenty random questions. Your last 5 games are saved under <b>Recent quizzes</b>.</p>
      <div class="spacer"></div>
      <button class="btn gold block" id="solo">Start 20 questions</button>
    </section>
    <section class="board mode">
      <span class="eyebrow">Party · 2 to ${PARTY_MAX} players</span>
      <h3>Play with friends</h3>
      <p>Get a 5-letter code and share it. Everyone answers the same 20 questions, then you watch the answers revealed together and see who wins.</p>
      <button class="btn gold block" id="create">Create a party</button>
      <div class="divider">or join one</div>
      <form class="row" id="joinform" autocomplete="off">
        <input class="input codein" id="joincode" maxlength="5" placeholder="CODE" aria-label="Party code">
        <button class="btn" type="submit">Join</button>
      </form>
      <p class="err" id="joinerr" role="alert"></p>
    </section>
  </div>
  <p class="foot">${esc(QUIZ.foot)}</p>`;
}
const CROWN = `<svg class="crown" viewBox="0 0 24 18" aria-label="Host" role="img"><path d="M2 16h20l1.5-12-6.5 5L12 1 7 9 .5 4z" fill="currentColor"/></svg>`;
function palStatus(p) {
  const n = p.answers.filter(a => a !== null).length;
  return p.done ? "Finished" : p.left ? "Left the quiz" : `On question ${Math.min(n + 1, LEN)} of ${LEN}`;
}
function hostId() { const h = effectiveHost(); return h ? h.id : null; }
// one row per player: colour dot, name (you marked), crown for the host, and an optional status
function playerRows(withStatus) {
  const hid = hostId();
  const inGame = S.meta && S.meta.started && S.meta.players ? new Set(S.meta.players) : null;
  const rows = orderedAll().slice(0, capOf()).filter(x => !inGame || inGame.has(x.me ? S.pid : x.pid));
  return rows.map(x => {
    const p = pals.get(x.id);
    const left = p && p.left && !p.done;
    const status = !withStatus ? (left ? "Left" : "") : x.me ? (S.finishedAt ? "Finished" : S.screen === "quiz" ? `On question ${S.cur + 1} of ${LEN}` : "") : palStatus(p);
    return `<li class="player${left ? " gone" : ""}">
      <span class="dot ${x.me ? "you" : colorOf(x.id)}" aria-hidden="true"></span>
      <span class="pname ${x.me ? "you-t" : "pal-name " + colorOf(x.id)}">${esc(x.me ? (S.nick || "You") : x.name)}${x.me ? ' <span class="muted">(you)</span>' : ""}</span>
      ${x.id === hid ? CROWN : ""}
      ${status ? `<span class="pal-prog">${status}</span>` : ""}
    </li>`;
  }).join("");
}
function partnerStrip() {
  if (!MULTI(S.mode)) return "";
  let body;
  if (roomState === "off") {
    body = `<p class="small muted" style="margin:0">Couldn't reach the party server, so you won't see the other players' progress. Everyone still gets the same questions.</p>`;
  } else if (roomState === "connecting" || roomState === "idle") {
    body = `<div class="pal-row"><span class="dot wait" aria-hidden="true"></span><span class="muted">Connecting…</span></div>`;
  } else {
    body = `<ul class="players">${playerRows(true)}</ul>`;
  }
  return `<section class="board partners" id="partners" aria-live="polite">
    <div class="head"><span class="eyebrow">Party · code <span class="codechip">${esc(S.code)}</span></span>
    <button class="btn copy" data-copy="${esc(S.code)}">Copy code</button></div>
    ${body}
  </section>`;
}
function readyView() {
  const n = orderedAll().slice(0, capOf()).length;
  const host = effectiveHost();
  const me = iAmHost();
  let list, action;
  if (roomState === "off") {
    list = `<p class="muted" style="margin:0">Couldn't reach the party server. Check your internet connection and try again.</p>`;
    action = `<button class="btn gold" id="retry">Try again</button>`;
  } else if (roomState !== "on" || !S.synced) {
    list = `<div class="pal-row"><span class="dot wait" aria-hidden="true"></span><span class="muted">Connecting to the lobby…</span></div>`;
    action = "";
  } else {
    list = `<ul class="players lobby">${playerRows(false)}</ul>`;
    action = me
      ? (n >= 2 ? `<button class="btn gold" id="begin">Start the quiz</button><p class="small muted" style="margin:0">Everyone starts at the same moment. Nobody can join once it's started.</p>`
               : `<button class="btn gold" id="begin" disabled>Start the quiz</button><p class="small muted" style="margin:0">You need at least 2 players to start.</p>`)
      : `<p class="muted" style="margin:0">Waiting for <b class="${host && host.me ? "you-t" : "pal-name " + (host ? colorOf(host.id) : "")}">${esc(host ? host.name : "the host")}</b> to start the quiz…</p>`;
  }
  return `${header()}
  <section class="board stack center">
    <span class="eyebrow">Quiz lobby · party code</span>
    <div class="code-big" aria-label="Party code ${esc(S.code.split("").join(" "))}">${esc(S.code)}</div>
    <div class="row" style="justify-content:center"><button class="btn copy" data-copy="${esc(S.code)}">Copy code</button></div>
    <p class="muted" style="margin:0 auto;max-width:46ch">Share this code. Friends choose <b>Join</b> on the ${esc(QUIZ.short)} page and type it in. Up to ${PARTY_MAX} players.</p>
  </section>
  <section class="board stack">
    <div class="head-row"><h3 class="lobby-title">Current list of players</h3><span class="muted small">${roomState === "on" && S.synced ? `${n} of ${PARTY_MAX}` : ""}</span></div>
    ${list}
    <div class="stack" style="gap:8px">${action}</div>
  </section>`;
}
function fullView() {
  const started = S.fullReason === "started";
  return `${header()}
  <section class="board stack center">
    <span class="eyebrow">Party code ${esc(S.code)}</span>
    <h2 class="bigmsg">${started ? "This quiz is already ongoing" : "This quiz lobby is full"}</h2>
    <p class="muted" style="margin:0 auto;max-width:44ch">${started ? "The host has already started this quiz, so nobody else can join. Ask them for a new code when it's finished."
      : `A party can have up to ${PARTY_MAX} players, and this one already has ${PARTY_MAX}.`}</p>
    <div class="row" style="justify-content:center"><button class="btn gold" id="go-home2">Back to home</button></div>
  </section>`;
}
// head-to-head questions: two cards, each with a hidden value that shows once answered
const isDuel = item => !!qOf(item).v;
const optsClass = item => "opts" + (isDuel(item) ? " duel" : "");
const valOf = (item, k) => { const q = qOf(item); return q.v ? q.v[item.opts[k]] || "" : ""; };
const whyHtml = item => qOf(item).x ? `<p class="why">${rich(qOf(item).x)}</p>` : "";
function duelHtml(item, picks, reveal) {
  const q = qOf(item);
  const cards = item.opts.map((o, k) => {
    const chosen = picks.filter(p => p.a === k);
    let cls = k ? "side-b" : "side-a";
    if (reveal) cls += k === item.correct ? " right" : chosen.length ? " wrong" : " faded";
    const marks = chosen.map(p => `<span class="tag ${p.cls}">${esc(p.label)}</span>`).join("");
    const sub = q.d && q.d[o] ? `<span class="sub">${esc(q.d[o])}</span>` : "";
    const val = reveal ? `<span class="val">${esc(q.v[o] || "")}</span>` : `<span class="val hide" aria-hidden="true">?</span>`;
    return `<button class="opt card ${cls}" data-opt="${k}" ${reveal ? "disabled" : ""}>
      <span class="key">${LET[k]}</span>${reveal && k === item.correct ? `<span class="win" aria-label="Right answer">✓</span>` : ""}
      <span class="lbl">${rich(o)}</span>${sub}${val}
      ${marks ? `<span class="marks">${marks}</span>` : ""}</button>`;
  });
  return cards[0] + `<span class="vs" aria-hidden="true">VS</span>` + cards[1];
}
function optionsHtml(item, picks, reveal) {
  // picks: [{label, cls, a}] for each player; reveal: show correct answer
  const q = qOf(item), bigLabels = !q.r;
  if (q.v) return duelHtml(item, picks, reveal);
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
    ${q.i ? `<img class="qimg" src="${esc(q.i)}" alt="Picture for this question" decoding="async">` : ""}
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
    <div class="${optsClass(item)}" role="group" aria-label="Answers">${optionsHtml(item, done ? [{ label: "You", cls: "you", a: mine }] : [], done)}</div>
    ${done ? `${whyHtml(item)}<div class="feedback">
        <span class="verdict ${mine === item.correct ? "ok" : "no"}">${mine === item.correct ? "Correct!" : "Not quite."}</span>
        <button class="btn gold" id="next">${S.cur < LEN - 1 ? "Next question" : "Finish"}</button>
      </div>` : `<p class="small muted tip" style="margin:0">Tip: press ${item.opts.length === 2 ? "1 or 2" : "1 to 4"} to answer, Enter for the next question.</p>`}
  </section>
  ${partnerStrip()}`;
}
function waitingView() {
  const ps = gamePlayers();
  const playing = ps.filter(p => !p.done && !p.left);
  const nobody = !ps.length;
  const leftEarly = ps.some(p => p.left && !p.done);
  const nm = playing.map(p => `<b class="pal-name ${colorOf(p.id)}">${esc(p.name)}</b>`);
  const names = nm.length > 1 ? nm.slice(0, -1).join(", ") + " and " + nm[nm.length - 1] : nm.join("");
  return `${header()}
  <section class="board stack center waiting">
    <span class="eyebrow">Game ${esc(S.code)}</span>
    <h2 class="bigmsg">${S.timedOut ? "Time's up!" : "You're done!"}</h2>
    <p class="muted" style="margin:0 auto;max-width:44ch">${nobody ? "Nobody else is in this quiz. You can see your results now."
      : playing.length ? `Waiting for ${names} to finish. The answers are revealed as soon as everyone's done.`
      : leftEarly ? "Someone left before finishing." : "Getting the reveal ready…"}</p>
    <div class="hourglass" aria-hidden="true"><span></span></div>
    ${nobody || leftEarly ? `<div class="row" style="justify-content:center"><button class="btn gold" id="nowait">Show my results now</button></div>` : ""}
  </section>
  ${partnerStrip()}`;
}
function revealView() {
  const players = [{ label: S.meName || S.nick || "You", cls: "you", answers: S.answers }].concat((S.final || []).map(p => ({ label: p.name, cls: "pal " + (p.c || "c1"), answers: p.answers })));
  const ms = STEP_MS(S.step);
  const timer = `<div class="timer" aria-hidden="true"><span style="animation-duration:${ms}ms"></span></div>`;
  const skip = `<button class="btn skip" id="skip" ${S.skipVote ? "disabled" : ""}>${esc(skipLabel())}</button>`;
  if (S.step === 0) {
    return `${header()}<section class="board stack center reveal">
      <span class="eyebrow">Party ${esc(S.code)} · ${players.length} players</span>
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
    return `<span class="who-line"><b class="${p.cls === "you" ? "you-t" : "pal-name " + p.cls.split(" ")[1]}">${esc(p.label)}</b> ${a === null || a === undefined ? `<span class="muted">didn't answer</span>` : a === item.correct ? `<span class="ok-t">✓ right</span>` : `<span class="no-t">✗ picked ${LET[a]}</span>`}</span>`;
  }).join("");
  return `${header()}
  <div class="pips" aria-label="Reveal: question ${k + 1} of ${LEN}">${S.qs.map((_, i) => `<span class="pip ${i < k ? "done" : i === k ? "now" : ""}"></span>`).join("")}</div>
  <section class="board stack reveal">
    ${qHead(item, k)}
    <div class="${optsClass(item)}">${optionsHtml(item, picks, true)}</div>
    ${whyHtml(item)}
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
  const scores = [{ name: S.meName || S.nick || "You", s: me, t: elapsedSec(), cls: "you", me: true }]
    .concat(pals.map(p => ({ name: p.name, s: scoreOf(p.answers), t: p.t || 0, cls: "pal " + (p.c || "c1") })));
  scores.sort((a, b) => b.s - a.s || (a.t || 1e9) - (b.t || 1e9));
  // places: same score shares a place, faster time breaks ties
  let tiles;
  if (pals.length) {
    let place = 0, prev = null;
    tiles = scores.map((x, i) => {
      if (!prev || x.s !== prev.s || x.t !== prev.t) place = i + 1;
      prev = x;
      return `<li class="rank${place === 1 ? " first" : ""}"><span class="place">${ordinal(place)}</span>
        <span class="pname ${x.me ? "you-t" : "pal-name " + x.cls.split(" ")[1]}">${esc(x.name)}${x.me ? ' <span class="muted">(you)</span>' : ""}</span>
        <span class="rscore">${x.s}<small>/${LEN}</small></span><span class="rtime">${x.t ? fmtTime(x.t) : ""}</span></li>`;
    });
  } else {
    tiles = [`<div class="tile you"><span class="eyebrow">${esc(scores[0].name)}</span><span class="n">${me}<small> / ${LEN}</small></span></div>`];
  }
  const review = S.qs.map((it, k) => {
    const q = qOf(it);
    const [qline, ...rest] = q.q.split("\n");
    const line = (who, cls, a) => a === null || a === undefined ? `<div class="ans"><span class="who ${cls}">${esc(who)}</span><span class="v muted">No answer</span></div>`
      : `<div class="ans"><span class="who ${cls}">${esc(who)}</span><span class="v ${a === it.correct ? "ok-t" : "no-t"}">${a === it.correct ? "✓" : "✗"} ${rich(it.opts[a])}</span>${q.v ? `<span class="v muted small">${esc(valOf(it, a))}</span>` : ""}</div>`;
    return `<div class="rv"><div class="q"><span class="num">${k + 1}.</span>${esc(qline)}${rest.length ? ` <span class="muted small">“${rich(rest.join(" "))}”</span>` : ""}${q.i ? ` <img class="rvimg" src="${esc(q.i)}" alt="" loading="lazy">` : ""}</div>
      ${line(S.meName || S.nick || "You", "you", S.answers[k])}
      ${pals.map(p => line(p.name, "pal " + (p.c || "c1"), p.answers[k])).join("")}
      ${S.answers[k] !== it.correct ? `<div class="ans"><span class="who key">Answer</span><span class="v">${rich(q.a)}</span>${q.v ? `<span class="v muted small">${esc(q.v[q.a] || "")}</span>` : ""}</div>` : ""}
      ${q.x ? `<div class="ans small muted">${rich(q.x)}</div>` : ""}</div>`;
  }).join("");
  const showCompare = !(S.final && S.final.length) && !S.past;
  return `${header()}
  <section class="board stack">
    <span class="eyebrow">${S.past ? "Past game" : "Results"} · code <span class="codechip">${esc(S.code)}</span> · ${fmtTime(elapsedSec())}</span>
    <h2 style="font-size:1.9rem">${verdict}</h2>
    ${S.timedOut ? `<p class="small muted" style="margin:0">Time ran out. Unanswered questions count as wrong.</p>` : ""}
    ${pals.length ? `<ol class="ranking">${tiles.join("")}</ol><p class="small muted" style="margin:0">Same score? The faster time ranks higher.</p>` : `<div class="tally">${tiles.join("")}</div>`}
    <div class="facts">${Object.entries(byGroup).map(([g, [a, b]]) => `<span class="chip">${esc(g)} ${a}/${b}</span>`).join("")}</div>
    <div class="row">
      ${S.past ? `<button class="btn gold" id="recent-btn">Back to recent quizzes</button>`
        : MULTI(S.mode) && transport && roomState === "on" ? "" : `<button class="btn gold" id="again">${MULTI(S.mode) ? "Start a new party" : "Play 20 more"}</button>`}
      <button class="btn" id="go-home2">Home</button>
    </div>
  </section>
  ${nextGameHtml()}
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
  const v = { home: homeView, recent: recentView, ready: readyView, quiz: quizView, waiting: waitingView, reveal: revealView, full: fullView }[S.screen] || resultsView;
  app.innerHTML = v() + feedTab();
  bind();
  bindFeed();
  saveSession();
}
function refreshPartnerBits() {
  if (S.screen === "reveal") { const el = $("#skip"); if (el) el.textContent = skipLabel(); checkSkip(); return; }
  if (S.screen === "results") { refreshNext(); return; }
  if (S.screen === "home" || S.screen === "recent" || S.screen === "full") return;
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
  on("create", () => { if (!needName()) startGame("party", newCode(), "host"); });
  const jf = $("#joinform");
  if (jf) jf.onsubmit = e => {
    e.preventDefault();
    if (needName()) return;
    const c = normCode($("#joincode").value);
    if (!validCode(c)) { $("#joinerr").textContent = `Codes are 5 letters or numbers, like ${QUIZ.letter}7QX2. Check it and try again.`; return; }
    const other = otherQuizFor(c);
    if (other) { location.href = other + "?join=" + c; return; }
    startGame("party", c, "guest");
  };
  on("begin", startParty);
  on("retry", joinRoom);
  document.querySelectorAll("[data-opt]:not([disabled])").forEach(b => b.onclick = () => answer(+b.dataset.opt));
  on("next", next);
  on("nowait", finishWithoutWaiting);
  on("skip", onSkip);
  on("again", () => startGame(MULTI(S.mode) ? "party" : "solo", newCode(), "host"));
  bindNext();
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
  if (S.screen === "full") return false;
  render();
  if (MULTI(S.mode) && S.screen !== "results") joinRoom();
  if (S.screen === "results") saveRecent();
  return true;
}
function start(saved) {
  S.nick = store("tt-nick") || "";
  fetch(QUIZ.bank).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(bank => {
    BANK = bank;
    let session = null;
    try { session = JSON.parse(sessionStorage.getItem(QUIZ.sessionKey) || "null"); } catch (e) {}
    let join = null, hostCode = null, h = "";
    try {
      const sp = new URLSearchParams(location.search);
      join = normCode(sp.get("join") || ""); hostCode = normCode(sp.get("host") || ""); h = sp.get("h") || "";
    } catch (e) {}
    if (hostCode && validCode(hostCode) && hostCode[0] === QUIZ.letter && S.nick) {
      try { history.replaceState(null, "", location.pathname); } catch (e) {}
      feedConnect(); startGame("party", hostCode, "host"); return;
    }
    if (join && validCode(join) && !otherQuizFor(join)) {
      try { history.replaceState(null, "", location.pathname); } catch (e) {}
      feedConnect();
      if (S.nick) { startGame("party", join, "guest"); expectHost(h); render(); return; }
      render();
      const jc = $("#joincode"); if (jc) jc.value = join;
      const n = $("#nick"); n && n.focus();
      const e = $("#nickerr"); if (e) e.textContent = "Type your name, then press Join to play game " + join + ".";
      return;
    }
    if (!restore(saved && saved.S) && !restore(session)) render();
    feedConnect();
  }).catch(() => {
    $("#app").innerHTML = `<div class="loading">The question bank didn't load. Reload the page to try again.</div>`;
  });
}
window.claude?.hot?.snapshot?.(() => ({ S: { ...S, qs: undefined } }));
window.claude?.hot?.ready ? window.claude.hot.ready(start) : start(window.claude?.hot?.data ?? {});
})();
