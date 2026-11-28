// Blackjack rules engine (no screen code). Casino rules:
//  6 decks, shuffled with a fair random source, reshuffled once fewer than 78 cards (a quarter of the shoe) are left.
//  Dealer peeks for blackjack with an Ace or a 10-value card showing, and stands on all 17s (soft 17 too).
//  Blackjack pays 3 to 2 (rounded down to whole coins), other wins pay 1 to 1, a tie (push) gives the bet back.
//  Double down on any first two cards, also after splitting. Split any two cards of the same value, up to 4 hands;
//  split Aces get one card each and can't be split again; 21 on a split hand is not a blackjack.
//  Insurance (half the bet) is offered when the dealer shows an Ace and pays 2 to 1.
const BJ = (() => {
  const DECKS = 6, CUT = 78, MAX_HANDS = 4;
  const SUITS = ["♠", "♥", "♦", "♣"], RANKS = ["", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];

  // a fair whole number from 0 to n-1, using the browser's cryptographic random numbers
  function cryptoInt(n) {
    const lim = Math.floor(0x100000000 / n) * n, buf = new Uint32Array(1);
    for (;;) { crypto.getRandomValues(buf); if (buf[0] < lim) return buf[0] % n; }
  }
  function newShoe(randInt = cryptoInt) {
    const shoe = [];
    for (let d = 0; d < DECKS; d++) for (let s = 0; s < 4; s++) for (let r = 1; r <= 13; r++) shoe.push({ r, s });
    for (let i = shoe.length - 1; i > 0; i--) { const j = randInt(i + 1); [shoe[i], shoe[j]] = [shoe[j], shoe[i]]; }
    return shoe;
  }
  const val = c => Math.min(c.r, 10);                                   // Ace counts 1 here; total() makes it 11 when it can
  function total(cards) {
    let t = 0, aces = 0;
    for (const c of cards) { t += val(c); if (c.r === 1) aces++; }
    const soft = aces > 0 && t + 10 <= 21;
    return { t: soft ? t + 10 : t, soft };
  }
  const isBJ = cards => cards.length === 2 && total(cards).t === 21;

  function create(randInt = cryptoInt) {
    return { shoe: newShoe(randInt), randInt, dealer: [], hands: [], active: 0, phase: "bet", insurance: 0, reshuffled: false, dealerBJ: false };
  }
  function draw(g) { return g.shoe.pop(); }
  const hand = g => g.hands[g.active];

  // start a round; the caller has already taken `bet` coins
  function deal(g, bet) {
    if (!(g.phase === "bet" || g.phase === "over") || !(bet >= 1)) throw new Error("can't deal now");
    g.reshuffled = false;
    if (g.shoe.length < CUT) { g.shoe = newShoe(g.randInt); g.reshuffled = true; }
    g.dealer = []; g.insurance = 0; g.dealerBJ = false; g.active = 0;
    const h = { cards: [], bet, doubled: false, fromSplit: false, splitAces: false, done: false, result: "", paid: 0 };
    g.hands = [h];
    h.cards.push(draw(g)); g.dealer.push(draw(g)); h.cards.push(draw(g)); g.dealer.push(draw(g));
    const up = g.dealer[0];
    if (up.r === 1) { g.phase = "insurance"; return g; }               // offer insurance first, then peek
    if (val(up) === 10 && isBJ(g.dealer)) return finish(g, true);      // dealer peeks: blackjack ends the round
    if (isBJ(h.cards)) return finish(g, false);
    g.phase = "play";
    return g;
  }
  // after an Ace shows: take insurance (the caller has taken half the bet, rounded down) or not
  function insure(g, take) {
    if (g.phase !== "insurance") throw new Error("no insurance now");
    g.insurance = take ? Math.floor(g.hands[0].bet / 2) : 0;
    if (isBJ(g.dealer)) return finish(g, true);
    if (isBJ(g.hands[0].cards)) return finish(g, false);
    g.phase = "play";
    return g;
  }
  const canDouble = g => g.phase === "play" && hand(g).cards.length === 2 && !hand(g).splitAces;
  const canSplit = g => g.phase === "play" && hand(g).cards.length === 2 && g.hands.length < MAX_HANDS && !hand(g).splitAces
    && val(hand(g).cards[0]) === val(hand(g).cards[1]);
  function next(g) {
    hand(g).done = true;
    while (g.active < g.hands.length && g.hands[g.active].done) g.active++;
    if (g.active < g.hands.length) {
      const h = hand(g);
      if (h.cards.length === 1) { h.cards.push(draw(g)); if (h.splitAces || total(h.cards).t === 21) return next(g); }   // second card for a split hand
      return g;
    }
    g.active = g.hands.length - 1;
    // the dealer only plays if some hand is still standing
    g.phase = g.hands.some(h => total(h.cards).t <= 21) ? "dealer" : "settle";
    if (g.phase === "settle") settle(g);
    return g;
  }
  function hit(g) {
    if (g.phase !== "play") throw new Error("can't hit now");
    const h = hand(g); h.cards.push(draw(g));
    if (total(h.cards).t >= 21) next(g);
    return g;
  }
  function stand(g) { if (g.phase !== "play") throw new Error("can't stand now"); return next(g); }
  // the caller has taken another `bet` coins for the hand
  function double(g) {
    if (!canDouble(g)) throw new Error("can't double now");
    const h = hand(g); h.bet *= 2; h.doubled = true; h.cards.push(draw(g));
    return next(g);
  }
  // the caller has taken another `bet` coins for the new hand
  function split(g) {
    if (!canSplit(g)) throw new Error("can't split now");
    const h = hand(g), aces = h.cards[0].r === 1;
    const h2 = { cards: [h.cards.pop()], bet: h.bet, doubled: false, fromSplit: true, splitAces: aces, done: false, result: "", paid: 0 };
    h.fromSplit = true; h.splitAces = aces;
    g.hands.splice(g.active + 1, 0, h2);
    h.cards.push(draw(g));
    if (aces || total(h.cards).t === 21) return next(g);
    return g;
  }
  // the dealer draws one card at a time (so the screen can show each one); false once the dealer stands
  function dealerStep(g) {
    if (g.phase !== "dealer") return false;
    if (total(g.dealer).t < 17) { g.dealer.push(draw(g)); return true; }
    settle(g); return false;
  }
  function finish(g, dealerBJ) { g.dealerBJ = dealerBJ; g.phase = "settle"; return settle(g); }
  // results and payouts: `paid` is what goes back to the player for each hand, bet included
  function settle(g) {
    const d = total(g.dealer).t, dBJ = isBJ(g.dealer);
    for (const h of g.hands) {
      const p = total(h.cards).t, pBJ = isBJ(h.cards) && !h.fromSplit;
      if (pBJ && dBJ) { h.result = "push"; h.paid = h.bet; }
      else if (pBJ) { h.result = "blackjack"; h.paid = h.bet + Math.floor(h.bet * 3 / 2); }
      else if (dBJ) { h.result = "lose"; h.paid = 0; }
      else if (p > 21) { h.result = "bust"; h.paid = 0; }
      else if (d > 21 || p > d) { h.result = "win"; h.paid = h.bet * 2; }
      else if (p === d) { h.result = "push"; h.paid = h.bet; }
      else { h.result = "lose"; h.paid = 0; }
    }
    g.insurancePaid = g.insurance && dBJ ? g.insurance * 3 : 0;
    g.phase = "over";
    return g;
  }
  const label = c => RANKS[c.r] + SUITS[c.s];
  return { DECKS, CUT, MAX_HANDS, SUITS, RANKS, create, newShoe, deal, insure, hit, stand, double, split, dealerStep, canDouble, canSplit,
    total, isBJ, val, label, cryptoInt };
})();
if (typeof module !== "undefined") module.exports = BJ;
