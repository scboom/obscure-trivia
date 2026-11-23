// Obscure Trivia coins and accounts: one coin count for the whole site.
// Not signed in: coins live in this browser. Signed in: they live in the account on the server, so they're never lost,
// and every change is queued here first (with an id, so a retry can't count twice) and sent as soon as the server answers.
(() => {
  const CONFIG = /*ACCOUNTS*/{"url": "", "key": ""}/*END*/;
  const LOCAL = "ot-coins", ACCT = "ot-acct", QUEUE = "ot-acct-queue";
  const ls = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { v === null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) {} }
  };
  const json = (k, d) => { try { const v = JSON.parse(ls.get(k) || "null"); return v === null ? d : v; } catch (e) { return d; } };
  const enabled = !!(CONFIG.url && CONFIG.key);
  let acct = enabled ? json(ACCT, null) : null;          // { token, user, coins }
  if (acct && !(acct.token && acct.user)) acct = null;
  const listeners = new Set();
  const emit = () => listeners.forEach(f => { try { f(); } catch (e) {} });

  const local = () => Math.max(0, parseInt(ls.get(LOCAL), 10) || 0);
  const queue = () => { const q = json(QUEUE, []); return Array.isArray(q) ? q.filter(x => x && typeof x.id === "string" && Number.isFinite(x.d)) : []; };
  const saveAcct = () => ls.set(ACCT, acct ? JSON.stringify(acct) : null);
  function get() { return acct ? Math.max(0, (acct.coins || 0) + queue().reduce((n, x) => n + x.d, 0)) : local(); }
  const opId = () => { const r = new Uint32Array(3); crypto.getRandomValues(r); return Array.from(r, x => x.toString(36)).join(""); };

  // ------------------------------------------------------------ the server (Supabase: only the functions in accounts.sql can be called)
  class Fail extends Error { constructor(code, msg) { super(msg || code); this.code = code; } }
  const MESSAGES = {
    taken: "That username is already taken. Try another one.",
    bad_username: "Usernames are 3 to 20 letters, numbers or underscores.",
    bad_password: "Passwords need 8 to 72 characters.",
    wrong: "That username and password don't match.",
    locked: "Too many wrong passwords. Wait 15 minutes, then try again.",
    session: "You've been signed out. Sign in again to use your account.",
    offline: "Couldn't reach the server. Check your internet connection and try again."
  };
  async function rpc(fn, args) {
    if (!enabled) throw new Fail("offline", "Accounts aren't switched on yet.");
    const headers = { "Content-Type": "application/json", apikey: CONFIG.key };
    if (CONFIG.key.startsWith("eyJ")) headers.Authorization = "Bearer " + CONFIG.key;   // older Supabase keys are JWTs and go here too
    let r;
    try { r = await fetch(CONFIG.url.replace(/\/$/, "") + "/rest/v1/rpc/" + fn, { method: "POST", headers, body: JSON.stringify(args), cache: "no-store" }); }
    catch (e) { throw new Fail("offline", MESSAGES.offline); }
    let body = null; try { body = await r.json(); } catch (e) {}
    if (r.ok && !(body && body.error)) return body;
    if (r.ok) { const c = String(body.error).replace(/^ot:/, ""); throw new Fail(c, MESSAGES[c] || "Something went wrong. Try again in a moment."); }
    const m = String((body && (body.message || body.hint)) || "").match(/ot:(\w+)/);
    const code = m ? m[1] : r.status >= 500 || r.status === 0 ? "offline" : "error";
    throw new Fail(code, MESSAGES[code] || "Something went wrong. Try again in a moment.");
  }
  // the account's token stopped working: keep any coins that hadn't been sent yet, in this browser
  function dropSession() {
    const left = queue().reduce((n, x) => n + x.d, 0);
    acct = null; saveAcct(); ls.set(QUEUE, null);
    if (left > 0) ls.set(LOCAL, String(local() + left));
    emit();
  }
  let flushing = null, retry = 0;
  function flush() {
    if (!acct) return Promise.resolve();
    if (flushing) return flushing;
    // cleared only after this promise is stored, so a run with nothing to send can't leave a stale "still sending"
    flushing = (async () => {
      try {
        for (let op = queue()[0]; op && acct; op = queue()[0]) {
          const res = await rpc("ot_coins", { p_token: acct.token, p_delta: op.d, p_op: op.id });
          acct.coins = res.coins; saveAcct();
          ls.set(QUEUE, JSON.stringify(queue().filter(x => x.id !== op.id)));
          emit();
        }
      } catch (e) {
        if (e.code === "session") dropSession();
        else { clearTimeout(retry); retry = setTimeout(() => { retry = 0; flush(); }, 15000); }   // offline: try again in a bit
      }
    })().finally(() => { flushing = null; if (acct && queue().length && !retry) flush(); });
    return flushing;
  }
  function add(d) {
    d = Math.trunc(Number(d) || 0);
    if (!d) return get();
    if (acct) { ls.set(QUEUE, JSON.stringify(queue().concat({ id: opId(), d }))); emit(); flush(); }
    else { ls.set(LOCAL, String(Math.max(0, local() + d))); emit(); }
    return get();
  }
  async function refresh() {
    if (!acct) return;
    try { const res = await rpc("ot_me", { p_token: acct.token }); acct.coins = res.coins; acct.user = res.username; saveAcct(); emit(); flush(); }
    catch (e) { if (e.code === "session") dropSession(); }
  }
  // signing in or up moves this browser's coins into the account, so nothing is left behind
  function start(res) {
    acct = { token: res.token, user: res.username, coins: res.coins };
    saveAcct(); ls.set(QUEUE, null); emit();
  }
  async function signUp(username, password) {
    const moved = local();
    const res = await rpc("ot_signup", { p_username: String(username).trim(), p_password: String(password), p_coins: moved });
    ls.set(LOCAL, "0"); start(res);
    return { moved };
  }
  async function signIn(username, password) {
    const res = await rpc("ot_login", { p_username: String(username).trim(), p_password: String(password) });
    const moved = local();
    start(res);
    if (moved > 0) { ls.set(LOCAL, "0"); add(moved); await flush(); }
    return { moved };
  }
  async function signOut() {
    if (!acct) return;
    await flush();
    if (queue().length) throw new Fail("offline", "Some coins haven't reached your account yet. Get online, then sign out.");
    const token = acct.token;
    acct = null; saveAcct(); emit();
    rpc("ot_logout", { p_token: token }).catch(() => {});
  }
  window.addEventListener("storage", e => {
    if (e.key === ACCT) { acct = enabled ? json(ACCT, null) : null; }
    if (e.key === LOCAL || e.key === ACCT || e.key === QUEUE || e.key === null) emit();
  });
  window.addEventListener("online", flush);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") refresh(); });
  if (acct) refresh();

  window.OTCoins = {
    enabled, get, add, refresh, signUp, signIn, signOut,
    user: () => (acct ? acct.user : null),
    pending: () => (acct ? queue().length : 0),
    on: f => listeners.add(f), off: f => listeners.delete(f)
  };
})();
