// Blackjack table, on the Spend coins page.
// Signed in to an account: the server shuffles, deals and pays (ot_bj_deal / ot_bj_act). This page only sends your moves and shows
// what the server sends back, which never includes the shoe or the dealer's face-down card, so nothing here can be used to cheat.
// Not signed in: the same rules run in the browser and bet the coins saved in this browser (which a browser can always edit,
// so they were never cheat-proof; account coins are). A hand in progress is saved, so a reload carries on with it.
// The table is drawn one card at a time: each new card flies out of the shoe and turns over, the dealer's hole card flips in
// place, and a split slides one card across to the new hand. BJSound (bj-sound.js) plays the table sounds.
(() => {
  const $ = s => document.querySelector(s);
  const C = window.OTCoins;
  const S = window.BJSound;
  const fmt = n => Math.round(n).toLocaleString();
  const SUIT_NAMES = ["spades", "hearts", "diamonds", "clubs"];
  const toCard = c => ({ r: c % 13 + 1, s: Math.floor(c / 13) });
  const toInt = c => (c.r - 1) + c.s * 13;
  const server = () => !!(C.enabled && C.user());
  const calm = () => window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  let view = { phase: "none", hands: [], dealer: [] };     // the table as last reported (same shape from the server and from the browser table)
  const disp = { round: null, hands: [], dealer: [] };       // the cards on the table right now (null = face down)
  let animating = false, stage = "", busy = false, err = "", note = "", mode = server();
  let bet = 10, shownCoins = null;
  // ---------------------------------------------------------------- the browser table: this browser's own coins
  const HAND = "ot-bj-hand";
  const local = { staked: 0, round: 0, g: BJ.create() };
  try {
    const saved = JSON.parse(localStorage.getItem(HAND) || "null");
    if (saved && saved.g && saved.g.hands) Object.assign(local, saved);
  } catch (e) {}
  const save = () => { try { localStorage.setItem(HAND, JSON.stringify(local)); } catch (e) {} };
  function localView() {
    const g = local.g, over = g.phase === "over";
    if (!g.hands || !g.hands.length) return { phase: "none", hands: [], dealer: [], coins: C.get() };
    const h = g.hands[g.active] || g.hands[0];
    return {
      phase: g.phase, round: local.round, coins: C.get(), active: g.active,
      hands: g.hands.map(x => ({ cards: x.cards.map(toInt), bet: x.bet, doubled: x.doubled, total: BJ.total(x.cards).t,
        result: over ? x.result : "", paid: over ? x.paid : 0 })),
      dealer: over ? g.dealer.map(toInt) : [toInt(g.dealer[0]), null],
      dealerTotal: BJ.total(over ? g.dealer : [g.dealer[0]]).t, dealerBJ: over && BJ.isBJ(g.dealer),
      insuranceCost: g.phase === "insurance" ? Math.floor(g.hands[0].bet / 2) : 0, insurancePaid: over ? g.insurancePaid || 0 : 0,
      staked: local.staked, returned: over ? g.hands.reduce((n, x) => n + x.paid, 0) + (g.insurancePaid || 0) : 0,
      couldDouble: BJ.canDouble(g), couldSplit: BJ.canSplit(g), betLeft: C.get() >= h.bet
    };
  }
  function localAct(action) {
    const g = local.g, h = g.hands && g.hands[g.active];
    const take = n => { if (n > C.get()) throw new Error("You don't have enough coins for that."); C.add(-n); local.staked += n; };
    if (action === "deal") {
      if (!(bet >= 1 && bet <= C.get())) throw new Error("You don't have enough coins for that bet.");
      local.g = BJ.create();
      local.staked = 0; take(bet); local.round++;
      local.g.shoe = BJ.newShoe();                             // a fresh shuffle every hand, like the server's table
      BJ.deal(local.g, bet); local.g.paidOut = false;
      if (local.g.phase === "insurance" && bet < 2) BJ.insure(local.g, false);
    } else if (action === "insure") { take(Math.floor(g.hands[0].bet / 2)); BJ.insure(g, true); }
    else if (action === "noinsure") BJ.insure(g, false);
    else if (action === "hit") BJ.hit(g);
    else if (action === "stand") BJ.stand(g);
    else if (action === "double") { take(h.bet); BJ.double(g); }
    else if (action === "split") { take(h.bet); BJ.split(g); }
    const G = local.g;
    while (G.phase === "dealer") BJ.dealerStep(G);
    if (G.phase === "over" && !G.paidOut) { G.paidOut = true; C.add(G.hands.reduce((n, x) => n + x.paid, 0) + (G.insurancePaid || 0)); }
    save();
    return localView();
  }

  // ---------------------------------------------------------------- moves
  const ACTION_SOUND = { deal: "chip", double: "chip", split: "chip", stand: "slide", insure: "chip", noinsure: "knock" };
  async function act(action) {
    if (busy || animating) return;
    S.wake();
    if (ACTION_SOUND[action]) S.play(ACTION_SOUND[action]);
    busy = true; err = ""; note = ""; render();
    try {
      const v = mode ? await C.call(action === "deal" ? "ot_bj_deal" : "ot_bj_act", action === "deal" ? { p_bet: bet } : { p_action: action }) : localAct(action);
      busy = false;
      show(v, action);
    } catch (e) {
      busy = false;
      err = (e && e.message) || "Something went wrong. Try again.";
      if (mode && e && (e.code === "bj_state" || e.code === "bj_busy")) { load(); return; }   // out of step with the server: ask where we are
    }
    render();
  }
  async function load() {
    mode = server();
    if (!mode) {
      const v = localView();
      show(v);
      if (v.phase === "play" || v.phase === "insurance") note = "Your last hand is still on the table.";
      render(); return;
    }
    busy = true; render();
    try {
      const v = await C.call("ot_bj_state");
      show(v);
      if (v.phase === "play" || v.phase === "insurance") note = "Your last hand is still on the table.";
    } catch (e) { err = (e && e.message) || "Couldn't reach the server."; }
    busy = false; render();
  }

  // ---------------------------------------------------------------- dealing it out, one card at a time
  // show() works out how the table gets from what's on it now (disp) to the new state, then plays those steps in order.
  function show(v, action) {
    view = v;
    const hands = (v.hands || []).map(h => h.cards), dealer = v.dealer || [];
    if (!action || !hands.length) {                          // a table loaded as it is: no animation
      disp.round = v.round; disp.hands = hands.map(c => c.slice()); disp.dealer = dealer.slice();
      return;
    }
    const steps = [];
    if (action === "deal" || disp.round !== v.round) {
      disp.round = v.round; disp.hands = [[]]; disp.dealer = [];
      steps.push(() => give(0), () => giveDealer(false), () => give(0), () => giveDealer(true));   // you, dealer, you, dealer face down
    }
    animating = true; stage = action === "deal" ? "deal" : "";
    run(steps);
  }
  // after the fixed steps, keep taking whatever step brings the table closer to the new state
  function nextStep() {
    const hands = view.hands.map(h => h.cards), dealer = view.dealer || [];
    if (hands.length > disp.hands.length) return split;
    for (let k = 0; k < hands.length; k++) {
      const have = disp.hands[k] || [], want = hands[k];
      let p = 0; while (p < have.length && p < want.length && have[p] === want[p]) p++;
      if (p < have.length) { disp.hands[k] = have.slice(0, p); return nextStep(); }
      if (have.length < want.length) return () => give(k);
    }
    if (disp.dealer[1] === null && dealer[1] !== null && dealer[1] !== undefined) return reveal;
    if (disp.dealer.length < dealer.length) return () => giveDealer(false);
    return null;
  }
  let timer = null;
  function run(steps) {
    clearTimeout(timer);
    const go = () => {
      const step = steps.length ? steps.shift() : nextStep();
      if (!step) {                                           // all dealt: let the last card land, then show the result
        timer = setTimeout(finish, calm() ? 60 : 380);
        return;
      }
      const wait = step();
      render(true);
      timer = setTimeout(go, calm() ? 90 : wait);
    };
    go();
  }
  function finish() {
    animating = false; stage = "";
    if (view.phase === "over") {
      const net = view.returned - view.staked, bj = view.hands.length === 1 && view.hands[0].result === "blackjack";
      S.play(net > 0 ? (bj ? "blackjack" : "win") : net < 0 ? "lose" : "push");
    }
    render();
  }
  function give(k) {
    const want = view.hands[k].cards;
    (disp.hands[k] = disp.hands[k] || []).push(want[disp.hands[k].length]);
    S.play("deal");
    return 260;
  }
  function giveDealer(down) {
    const want = view.dealer || [], i = disp.dealer.length;
    disp.dealer.push(down ? null : want[i]);
    if (i >= 2 || (i === 1 && !down)) stage = "dealer";
    S.play("deal");
    return i >= 2 ? 640 : 260;
  }
  function reveal() {
    disp.dealer[1] = view.dealer[1];
    stage = "dealer";
    S.play("flip");
    return 620;
  }
  function split() {
    const hands = view.hands.map(h => h.cards);
    hands.forEach((want, k) => {
      if (!disp.hands[k]) { disp.hands[k] = [want[0]]; moved.add(k); return; }
      const have = disp.hands[k];
      let p = 0; while (p < have.length && p < want.length && have[p] === want[p]) p++;
      disp.hands[k] = have.slice(0, p);
    });
    S.play("slide");
    return 380;
  }
  const moved = new Set();                                   // hands whose first card has just slid across from a split

  // ---------------------------------------------------------------- drawing the cards
  function faceHtml(c) {
    const k = toCard(c), r = BJ.RANKS[k.r], s = BJ.SUITS[k.s];
    return `<span class="pc-r">${r}<i>${s}</i></span><span class="pc-s">${s}</span><span class="pc-r pc-r2">${r}<i>${s}</i></span>`;
  }
  const label = c => c === null ? "Face-down card" : `${BJ.RANKS[toCard(c).r]} of ${SUIT_NAMES[toCard(c).s]}`;
  const isRed = c => c !== null && (toCard(c).s === 1 || toCard(c).s === 2);
  function makeCard(c) {
    const el = document.createElement("span");
    el.className = "pc" + (c === null ? " down" : "") + (isRed(c) ? " red" : "");
    el.dataset.c = c === null ? "x" : String(c);
    el.setAttribute("role", "img"); el.setAttribute("aria-label", label(c));
    el.innerHTML = `<span class="pc-in"><span class="pc-face">${c === null ? "" : faceHtml(c)}</span><span class="pc-back"></span></span>`;
    return el;
  }
  // a new card: it starts at the shoe (top right of the table) and flies to its place, turning over on the way
  function fly(el, faceUp) {
    if (calm()) return;
    const shoe = $("#bj-shoebox").getBoundingClientRect(), r = el.getBoundingClientRect();
    el.style.setProperty("--dx", `${shoe.left + shoe.width / 2 - (r.left + r.width / 2)}px`);
    el.style.setProperty("--dy", `${shoe.top + shoe.height / 2 - (r.top + r.height / 2)}px`);
    el.classList.add("fly");
    if (faceUp) el.classList.add("flipin");
    el.addEventListener("animationend", e => { if (e.target === el) el.classList.remove("fly", "flipin"); }, { once: false });
  }
  function turnOver(el, c) {
    el.querySelector(".pc-face").innerHTML = faceHtml(c);
    el.dataset.c = String(c); el.setAttribute("aria-label", label(c));
    el.classList.toggle("red", isRed(c));
    if (calm()) { el.classList.remove("down"); return; }
    void el.offsetWidth;
    el.classList.remove("down");
  }
  // bring a row of cards on the page in line with `cards`, animating only what changed
  function syncCards(box, cards, animate, slideFirst) {
    const kids = Array.from(box.children);
    cards.forEach((c, i) => {
      const k = kids[i], key = c === null ? "x" : String(c);
      if (k && k.dataset.c === key) return;
      if (k && k.dataset.c === "x" && c !== null) { turnOver(k, c); return; }
      const el = makeCard(c);
      if (k) box.replaceChild(el, k); else box.appendChild(el);
      if (animate) {
        if (i === 0 && slideFirst) { if (!calm()) el.classList.add("slidein"); }
        else fly(el, c !== null);
      }
    });
    kids.slice(cards.length).forEach(k => k.remove());
  }
  function totalText(cards) {
    const cs = cards.filter(c => c !== null && c !== undefined).map(toCard);
    if (!cs.length) return "";
    const t = BJ.total(cs);
    return cards.length === 2 && cs.length === 2 && t.t === 21 ? "Blackjack" : t.soft && t.t < 21 ? `${t.t - 10} or ${t.t}` : String(t.t);
  }
  const RESULT = { blackjack: ["Blackjack!", "win"], win: ["Win", "win"], push: ["Push", "push"], lose: ["Lose", "lose"], bust: ["Bust", "lose"] };
  function resultMessage(v) {
    const net = v.returned - v.staked, one = v.hands.length === 1 ? v.hands[0].result : "", d = v.dealerTotal;
    const n = x => `${fmt(x)} coin${x === 1 ? "" : "s"}`;
    const text = one === "blackjack" ? `Blackjack! You win ${n(net)}.`
      : v.dealerBJ ? (net > 0 ? `Dealer has blackjack, but insurance pays: you win ${n(net)}.` : net === 0 ? (v.insurancePaid ? "Dealer has blackjack, but your insurance covered it." : "Dealer has blackjack too. Push.") : `Dealer has blackjack. You lose ${n(-net)}.`)
      : v.hands.length > 1 ? (net > 0 ? `${d > 21 ? "Dealer busts! " : ""}You win ${n(net)} overall.` : net < 0 ? `${d > 21 ? "Dealer busts, but " : ""}You lose ${n(-net)} overall.` : "Some hands win, some lose: you break even.")
      : net > 0 ? `${d > 21 ? "Dealer busts! " : ""}You win ${n(net)}.`
      : net === 0 ? "Push. Your bet comes back."
      : one === "bust" ? `Bust. You lose ${n(-net)}.`
      : `${d > 21 ? "Dealer busts, but " : "Dealer wins. "}You lose ${n(-net)}.`;
    return [text, net > 0 ? "win" : net < 0 ? "lose" : "push"];
  }
  const coinsNow = () => mode ? (Number.isFinite(view.coins) ? view.coins : C.get()) : C.get();
  // the purse counts up (or down) to its new value
  let countTimer = null;
  function showCoins(n) {
    const el = $("#bj-coins");
    el.dataset.n = String(n);
    if (shownCoins === null || calm() || Math.abs(n - shownCoins) < 2) { shownCoins = n; el.textContent = fmt(n); return; }
    const from = shownCoins, t0 = performance.now(), dur = 650;
    shownCoins = n; cancelAnimationFrame(countTimer);
    el.classList.toggle("up", n > from);
    const tick = t => {
      const f = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - f, 3);
      el.textContent = fmt(from + (n - from) * e);
      if (f < 1) countTimer = requestAnimationFrame(tick); else el.classList.remove("up");
    };
    countTimer = requestAnimationFrame(tick);
  }
  function render(stepping) {
    const v = view;
    // while cards are still being dealt, the purse waits for the result
    if (!animating) showCoins(coinsNow());
    else if (shownCoins === null) showCoins(coinsNow());
    $("#bj-mode").innerHTML = mode
      ? `Betting your account's coins, <b>${String(C.user()).replace(/[<&]/g, "")}</b>. Every card is dealt by the server, so the game can't be cheated.`
      : C.enabled ? `Betting the coins saved in <b>this browser</b>. <a href="../account/">Make an account</a> to keep your coins safe on every device.`
      : `Betting the coins saved in <b>this browser</b>. Win them in any quiz: 1 coin for every right answer.`;
    syncCards($("#bj-dealer"), disp.dealer, stepping);
    $("#bj-dtotal").textContent = totalText(disp.dealer);
    const box = $("#bj-hands");
    if (!disp.hands.length) { box.innerHTML = `<div class="bj-empty muted">Your cards go here</div>`; }
    else {
      const empty = box.querySelector(".bj-empty"); if (empty) empty.remove();
      while (box.children.length < disp.hands.length) {
        const h = document.createElement("div"); h.className = "bj-hand";
        h.innerHTML = `<div class="cards"></div><div class="bj-meta"></div>`; box.appendChild(h);
      }
      while (box.children.length > disp.hands.length) box.lastElementChild.remove();
      disp.hands.forEach((cards, k) => {
        const el = box.children[k], h = v.hands[k] || { bet: 0 };
        const r = !animating && h.result && RESULT[h.result];
        const active = !animating && v.phase === "play" && k === v.active && v.hands.length > 1;
        el.className = `bj-hand${active ? " active" : ""}${r ? " " + r[1] : ""}`;
        syncCards(el.querySelector(".cards"), cards, stepping, moved.has(k));
        el.querySelector(".bj-meta").innerHTML = `<b>${totalText(cards)}</b><span class="muted">bet ${fmt(h.bet)}${h.doubled ? " (doubled)" : ""}</span>${r ? `<span class="bj-res ${r[1]}">${r[0]}</span>` : ""}`;
      });
    }
    moved.clear();
    let msg = "Choose your bet and press Deal.", tone = "";
    if (err) { msg = err; tone = "lose"; }
    else if (busy) msg = "…";
    else if (animating) msg = stage === "dealer" ? "Dealer's turn." : stage === "deal" ? "Dealing…" : null;
    else if (v.phase === "over") [msg, tone] = resultMessage(v);
    else if (v.phase === "insurance") msg = "Insurance?";
    else if (v.phase === "play") msg = note || (v.hands.length > 1 ? `Playing hand ${v.active + 1} of ${v.hands.length}.` : "Hit or stand?");
    if (msg !== null) { $("#bj-msg").className = "bj-msg " + tone; $("#bj-msg").textContent = msg; }   // null: a card is landing, keep the line as it is
    $("#bj-shoe").textContent = "Fresh 6-deck shuffle every hand";
    const snd = $("#bj-snd");
    snd.classList.toggle("off", !S.on); snd.setAttribute("aria-pressed", String(S.on));
    snd.setAttribute("aria-label", S.on ? "Sound on. Press to mute." : "Sound off. Press to turn it on."); snd.title = S.on ? "Mute" : "Sound on";
    controls();
  }

  // ---------------------------------------------------------------- buttons
  const clampBet = (n, coins) => Math.max(1, Math.min(coins, Math.floor(n)));
  function controls() {
    const el = $("#bj-controls"), v = view, coins = coinsNow(), unit = "coins";
    const hold = busy || animating;
    if (v.phase === "none" || v.phase === "over") {
      if (coins < 1) {
        el.dataset.ui = "broke";
        el.innerHTML = `<p class="muted" style="margin:0">You're out of coins. Win more in any quiz: 1 coin for every right answer.</p>
          <a class="btn gold bj-deal" href="../" style="text-decoration:none;text-align:center">Play a quiz</a>`;
        return;
      }
      if (!hold && bet > coins) bet = coins;
      const ui = "bet" + (mode ? "s" : "b");
      if (el.dataset.ui !== ui) {
        el.dataset.ui = ui;
        el.innerHTML = `
          <div class="bj-betrow">
            <label class="bj-betbox"><span class="muted small">Bet</span>
              <input class="bj-betin" id="bj-betin" type="number" inputmode="numeric" min="1" step="1" autocomplete="off" aria-describedby="bj-bethint">
              <span class="muted small" id="bj-unit"></span></label>
            <div class="bj-quick" role="group" aria-label="Change your bet">
              <button class="btn" data-q="half" title="Halve your bet">½</button><button class="btn" data-q="double" title="Double your bet">×2</button><button class="btn" data-q="all" title="Bet everything">All</button>
            </div>
          </div>
          <p class="muted small bj-hint" id="bj-bethint"></p>
          <button class="btn gold bj-deal" id="bj-deal"></button>`;
        const inp = $("#bj-betin");
        inp.value = String(bet);
        inp.oninput = () => { const n = Number(inp.value); if (inp.value !== "" && Number.isFinite(n)) bet = Math.floor(n); updateBet(); };
        inp.onblur = () => { bet = clampBet(Number(inp.value) || 1, coinsNow()); inp.value = String(bet); updateBet(); };
        inp.onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); inp.blur(); if (!$("#bj-deal").disabled) act("deal"); } };
        el.querySelectorAll("[data-q]").forEach(b => b.onclick = () => {
          const c = coinsNow(), k = b.dataset.q, was = bet;
          bet = k === "half" ? Math.max(1, Math.floor(clampBet(bet, c) / 2)) : k === "double" ? clampBet(clampBet(bet, c) * 2, c) : c;
          if (bet !== was) { S.wake(); S.play("chip"); }
          $("#bj-betin").value = String(bet); updateBet();
        });
        $("#bj-deal").onclick = () => act("deal");
      }
      const inp = $("#bj-betin");
      inp.max = String(coins);
      if (document.activeElement !== inp && inp.value !== String(bet)) inp.value = String(bet);
      $("#bj-unit").textContent = unit;
      updateBet(hold);
      return;
    }
    const canD = v.couldDouble && v.betLeft, canS = v.couldSplit && v.betLeft;
    const ui = v.phase === "insurance" ? "ins" : "play";
    if (v.phase === "insurance") {
      const ins = v.insuranceCost;
      el.dataset.ui = ui;
      el.innerHTML = `<p style="margin:0">The dealer shows an Ace. Insurance costs <b>${fmt(ins)}</b> and pays 2 to 1 if the dealer has blackjack.</p>
        <div class="row"><button class="btn gold" id="bj-ins-yes" ${coins < ins || hold ? "disabled" : ""}>Take insurance</button><button class="btn" id="bj-ins-no" ${hold ? "disabled" : ""}>No thanks</button></div>`;
      $("#bj-ins-yes").onclick = () => act("insure");
      $("#bj-ins-no").onclick = () => act("noinsure");
      return;
    }
    el.dataset.ui = ui;
    el.innerHTML = `<div class="row bj-acts">
      <button class="btn gold" id="bj-hit" ${hold ? "disabled" : ""}>Hit</button><button class="btn gold" id="bj-stand" ${hold ? "disabled" : ""}>Stand</button>
      <button class="btn" id="bj-double" ${canD && !hold ? "" : "disabled"} title="${v.couldDouble && !canD ? `Not enough ${unit}` : ""}">Double</button>
      <button class="btn" id="bj-split" ${canS && !hold ? "" : "disabled"} title="${v.couldSplit && !canS ? `Not enough ${unit}` : ""}">Split</button></div>`;
    $("#bj-hit").onclick = () => act("hit");
    $("#bj-stand").onclick = () => act("stand");
    $("#bj-double").onclick = () => { if (canD) act("double"); };
    $("#bj-split").onclick = () => { if (canS) act("split"); };
  }
  // the bet box: what's typed is checked as you type, and Deal shows the amount
  function updateBet(hold) {
    const inp = $("#bj-betin"); if (!inp) return;
    const coins = coinsNow(), unit = "coins", raw = inp.value.trim(), n = Number(raw);
    let hint = "", ok = true;
    if (raw === "" || !Number.isFinite(n) || n < 1) { ok = false; hint = "Type how many to bet: at least 1."; }
    else if (n !== Math.floor(n)) { ok = false; hint = "Whole numbers only."; }
    else if (n > coins) { ok = false; hint = `You only have ${fmt(coins)} ${unit}.`; }
    $("#bj-bethint").textContent = hint;
    $("#bj-bethint").classList.toggle("bad", !ok);
    const h = hold === undefined ? busy || animating : hold;
    const deal = $("#bj-deal");
    deal.disabled = !ok || h;
    deal.textContent = ok ? `Deal · bet ${fmt(n)}${n === coins ? " (all in)" : ""}` : "Deal";
    const c = clampBet(ok ? n : bet, coins);
    $("#bj-controls").querySelectorAll("[data-q]").forEach(b => {
      const k = b.dataset.q;
      b.disabled = h || (k === "half" ? c <= 1 : k === "double" ? c >= coins : c === coins && ok);
    });
    inp.disabled = h;
  }

  $("#bj-snd").onclick = () => { S.toggle(); render(); };
  // signed in or out in another tab: switch tables between hands
  C.on(() => {
    if (busy || animating) return;
    if (server() !== mode && (view.phase === "none" || view.phase === "over")) load(); else render();
  });
  load();
})();
