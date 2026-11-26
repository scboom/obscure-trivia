"""Build the Timeline bank (exactly 1,000 rounds).

Events: dated events from English Wikipedia, each with the exact text that gives its date (checked again here), plus dated
facts this site already holds (Dead by Daylight Chapters, Clash Royale cards, World Cup and Premier League winners).
Rounds: which came first, which came last, put four in order (the four are listed A to D), and which year / decade.
Events are only compared when their dates are clearly apart, so a round never hangs on a guess about the same year.
Usage: gen_timeline.py SCRATCH_DIR OUT.json [--avail|--show KIND|--loose]
"""
import sys, json, random, re, collections, os, unicodedata, datetime, itertools

D, OUT = sys.argv[1:3]
rng = random.Random(20261126)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


class Ev:
    def __init__(self, cat, label, y, m=None, d=None, tag=None, level=2, src="", short=None, noun=None):
        self.cat, self.label, self.y, self.m, self.d, self.tag, self.level, self.src = cat, label, y, m, d, tag, level, src
        self.short, self.noun = short or label, noun

    @property
    def key(self):                      # sortable
        return (self.y, self.m or 6, self.d or 15)

    def days(self):
        return self.y * 365.25 + ((self.m or 6) - 1) * 30.44 + (self.d or 15)

    def when(self):
        y = f"{-self.y} BC" if self.y < 0 else str(self.y)
        if self.d:
            return f"{self.d} {MONTHS[self.m - 1]} {y}"
        if self.m:
            return f"{MONTHS[self.m - 1]} {y}"
        return y


EV = []
norm = lambda s: re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def evidence_ok(text, ev):
    f = lambda s: norm(s).replace("’", "'").replace("“", '"').replace("”", '"').replace("–", "-").lower()
    return f(ev) in f(text)


# ------------------------------------------------------------------ Wikipedia events
EF = f"{D}/timeline/work/events.json"
if os.path.exists(EF):
    bad = 0
    for e in json.load(open(EF)):
        f = f"{D}/timeline/facts/{re.sub(r'[^A-Za-z0-9_.()-]', '', e['page'].replace(' ', '_'))}.txt"
        cands = [f] + [os.path.join(f"{D}/timeline/facts", x) for x in os.listdir(f"{D}/timeline/facts") if x.lower().startswith(e["page"].replace(" ", "_").lower()[:24])]
        if not any(os.path.exists(c) and evidence_ok(open(c).read(), e["evidence"]) for c in cands):
            bad += 1; continue
        m = re.fullmatch(r"(-?\d{1,4})(?:-(\d\d))?(?:-(\d\d))?", e["date"])
        if not m:
            bad += 1; continue
        y, mo, da = int(m.group(1)), m.group(2) and int(m.group(2)), m.group(3) and int(m.group(3))
        if e["precision"] == "year":
            mo = da = None
        elif e["precision"] == "month":
            da = None
        EV.append(Ev(e["cat"], e["event"], y, mo, da, level=e.get("level", 2), src="wikipedia"))
    print(f"wikipedia events: {len(EV)} kept, {bad} failed the evidence check")

# ------------------------------------------------------------------ the site's own dated data
DT = json.load(open(f"{D}/dbd/work/dt.json"))
DLC = {x["id"]: x for x in DT["dlcs"]}
first = lambda v: v[0] if isinstance(v, list) else v
for k in DT["killers"]:
    dl = first(k.get("dlc"))
    if dl and dl in DLC:
        d, mo, y = map(int, DLC[dl]["rDate"].split("."))
        EV.append(Ev("Video games", f"The {k['name']} joins Dead by Daylight", y, mo, d, tag="Dead by Daylight", level=3, src="dbd", short=f"The {k['name']}", noun="Killers"))
CR = json.load(open(f"{D}/cr/cards.json"))
for n, c in CR["cards"].items():
    m = re.match(r"(\d{1,2}) ([A-Z][a-z]+) (\d{4})", c.get("released", ""))
    if m and m.group(2) in MONTHS:
        EV.append(Ev("Video games", f"The {n} card arrives in Clash Royale", int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)), tag="Clash Royale", level=3, src="cr", short=n, noun="cards"))
for team, y in [("Uruguay", 1930), ("Italy", 1934), ("West Germany", 1954), ("Brazil", 1958), ("England", 1966), ("Argentina", 1978), ("France", 1998), ("Spain", 2010)]:
    EV.append(Ev("Sport", f"{team} win{'s' if team != 'England' else ''} their first World Cup".replace("wins their", "win their"), y, tag="World Cup", level=2, src="football"))
fin = [m for m in json.load(open(f"{D}/football/wc/2026.json"))["matches"] if m.get("round") == "Final"][0]
PL = json.load(open(f"{D}/football/pl.json"))
seen_ch = set()
for s in sorted(PL):
    if s == max(PL):
        continue
    ch = PL[s]["table"][0][0]
    if ch not in seen_ch:
        seen_ch.add(ch)
        if ch not in ("Manchester United",):
            EV.append(Ev("Sport", f"{ch} win their first Premier League title", int(s[:4]) + 1, 5, tag="Premier League", level=2, src="football"))

# ------------------------------------------------------------------ rounds
def gap_ok(a, b):
    """dates far enough apart to compare fairly"""
    lo = min(a.y, b.y)
    need_years = 1 if lo >= 1990 else 2 if lo >= 1900 else 10 if lo >= 1500 else 40 if lo >= 0 else 150
    if a.src in ("dbd", "cr") and b.src in ("dbd", "cr") and a.d and b.d:
        return abs(a.days() - b.days()) >= 75
    if a.d and b.d and abs(a.y - b.y) <= 1 and lo >= 1990:
        return abs(a.days() - b.days()) >= 200
    return abs(a.y - b.y) >= need_years


def spread(four):
    s = sorted(four, key=lambda e: e.key)
    return all(gap_ok(s[i], s[i + 1]) for i in range(3))


R = collections.defaultdict(list)
SEEN = set()
CATS = sorted({e.cat for e in EV})


def listing(four):
    return " · ".join(f"{e.label}: {e.when()}" for e in sorted(four, key=lambda e: e.key))


def add_round(kind, group, q):
    if q["k"] in SEEN:
        return False
    SEEN.add(q["k"]); q["c"] = kind; q["g"] = group
    R[group].append(q)
    return True


def window(y):
    """how far apart events may be in a 'close' round, depending on the era"""
    return 35 if y >= 1900 else 120 if y >= 1500 else 500 if y >= 0 else 1500


def pick_four(pool, tries=80):
    close = rng.random() < 0.75                      # most rounds compare events from around the same time
    for _ in range(tries):
        if close:
            a = rng.choice(pool)
            near = [e for e in pool if e is not a and abs(e.y - a.y) <= window(a.y)]
            if len(near) < 3:
                continue
            four = [a] + rng.sample(near, 3)
        else:
            four = rng.sample(pool, 4)
        if spread(four) and len({e.label for e in four}) == 4:
            return four
    return None


def make(group, pool, n_first, n_last, n_order, noun=None):
    lab = (lambda e: e.short) if noun else (lambda e: e.label)
    for kind, n in (("first", n_first), ("last", n_last), ("order", n_order)):
        made = 0
        for _ in range(n * 12):
            if made >= n:
                break
            four = pick_four(pool)
            if not four:
                break
            s = sorted(four, key=lambda e: e.key)
            key = kind + ":" + "|".join(sorted(e.label for e in four))
            tag = s[0].tag if noun else None
            listing_ = " · ".join(f"{lab(e)}: {e.when()}" for e in s)
            if kind in ("first", "last"):
                ans = s[0] if kind == "first" else s[-1]
                qt = (f"Which of these {noun} came out first?" if kind == "first" else f"Which of these {noun} came out most recently?") if noun else \
                     ("Which of these happened first?" if kind == "first" else "Which of these happened most recently?")
                q = {"k": key, "q": qt, "a": lab(ans), "o": [lab(e) for e in four if e is not ans], "x": listing_, "ks": ["ev:" + e.label for e in four]}
                if not noun:
                    q["r"] = 1
            else:
                letters = "ABCD"
                shown = four[:]
                rng.shuffle(shown)
                L = {id(e): letters[i] for i, e in enumerate(shown)}
                right = [L[id(e)] for e in s]
                wrongs = set()
                for i in range(3):
                    w = right[:]; w[i], w[i + 1] = w[i + 1], w[i]; wrongs.add(tuple(w))
                w = right[:]; w[0], w[3] = w[3], w[0]; wrongs.add(tuple(w))
                w = right[::-1]; wrongs.add(tuple(w))
                wrongs = [list(x) for x in wrongs if list(x) != right]
                rng.shuffle(wrongs)
                fmt = lambda seq: " → ".join(seq)
                qt = f"Put these {noun} in order of release, earliest first." if noun else "Put these in order, from earliest to latest."
                q = {"k": key, "q": qt, "l": [lab(e) for e in shown], "a": fmt(right), "o": [fmt(w) for w in wrongs[:3]], "x": listing_,
                     "ks": ["ev:" + e.label for e in four]}
            if tag:
                q["t"] = tag
            if add_round(kind, group, q):
                made += 1


def decade(y):
    return f"{y // 10 * 10}s"


def make_years(group, pool, n):
    made = 0
    for e in rng.sample(pool, len(pool)):
        if made >= n:
            break
        if e.y >= 1900 and e.level <= 2 and e.src == "wikipedia":
            offs = rng.sample([-9, -7, -6, -5, -4, -3, 3, 4, 5, 6, 7, 9], 3)
            opts = [str(e.y + o) for o in offs if e.y + o <= 2026]
            if len(opts) < 3:
                continue
            q = {"k": "year:" + e.label, "q": f"In which year did this happen?\n{e.label}", "a": str(e.y), "o": opts,
                 "x": f"{e.label}: {e.when()}.", "ks": ["ev:" + e.label]}
        elif 1500 <= e.y < 1900 and e.src == "wikipedia":
            d0 = e.y // 10 * 10
            opts = [decade(d0 + o) for o in rng.sample([-40, -30, -20, -10, 10, 20, 30, 40], 3) if d0 + o <= 2020]
            q = {"k": "decade:" + e.label, "q": f"In which decade did this happen?\n{e.label}", "a": decade(e.y), "o": opts,
                 "x": f"{e.label}: {e.when()}.", "ks": ["ev:" + e.label]}
        else:
            continue
        if len(q["o"]) == 3 and add_round("year", group, q):
            made += 1


by_cat = collections.defaultdict(list)
for e in EV:
    by_cat[e.cat].append(e)
SINGLE = {"Dead by Daylight", "Clash Royale"}             # one game's own releases: asked among themselves only
for cat, pool in by_cat.items():
    general = [e for e in pool if e.tag not in SINGLE]
    if len(general) >= 8:
        make(cat, general, 40, 25, 30)
        make_years(cat, general, 30)
    for tag in sorted({e.tag for e in pool if e.tag in SINGLE}):
        tp = [e for e in pool if e.tag == tag]
        if len(tp) >= 8:
            make(cat, tp, 22, 12, 14, noun=tp[0].noun)
# mixed rounds: events from different categories within a few decades of each other, for surprising comparisons
wiki = [e for e in EV if e.src == "wikipedia"]
if len(wiki) > 40:
    for _ in range(4000):
        if len(R["Anything goes"]) >= 220:
            break
        a = rng.choice(wiki)
        near = [e for e in wiki if e.cat != a.cat and abs(e.y - a.y) <= max(30, abs(2026 - a.y) // 3)]
        if len(near) < 6:
            continue
        four = None
        for _ in range(30):
            cand = [a] + rng.sample(near, 3)
            if len({e.cat for e in cand}) >= 3 and spread(cand):
                four = cand; break
        if not four:
            continue
        s = sorted(four, key=lambda e: e.key)
        kind = rng.choice(["first", "first", "last", "order"])
        key = kind + ":" + "|".join(sorted(e.label for e in four))
        if kind == "order":
            continue
        ans = s[0] if kind == "first" else s[-1]
        add_round(kind, "Anything goes", {"k": key, "q": "Which of these happened first?" if kind == "first" else "Which of these happened most recently?",
                                         "a": ans.label, "o": [e.label for e in four if e is not ans], "x": listing(four), "ks": ["ev:" + e.label for e in four], "r": 1})

if "--show" in sys.argv:
    want = sys.argv[sys.argv.index("--show") + 1]
    for g, lst in R.items():
        for q in [q for q in lst if q["c"] == want][:4]:
            print(f"[{g}{' / ' + q['t'] if q.get('t') else ''}] {q['q']} {q.get('l', '')}\n      A: {q['a']} | {' / '.join(q['o'])}\n      x: {q['x']}")
    sys.exit()
if "--avail" in sys.argv:
    for g, lst in sorted(R.items(), key=lambda kv: -len(kv[1])):
        print(f"{g:20} {len(lst)}  " + ", ".join(f"{c}:{n}" for c, n in collections.Counter(q['c'] for q in lst).most_common()))
    print(len(EV), "events")
    sys.exit()
TARGET = json.loads(os.environ.get("TL_TARGET", "{}"))
assert TARGET, "set TL_TARGET"
out = []
for g, want in TARGET.items():
    by_c = collections.defaultdict(list)
    for q in R[g]:
        by_c[q["c"]].append(q)
    for v in by_c.values():
        rng.shuffle(v)
    W_ = {"first": 3, "last": 2, "order": 2.5, "year": 2}
    took, got = collections.Counter(), []
    while len(got) < want and any(by_c.values()):
        c = min((c for c in by_c if by_c[c]), key=lambda c: (took[c] / W_.get(c, 1), rng.random()))
        got.append(by_c[c].pop()); took[c] += 1
    print(f"{g:20} {len(got)}/{want}  " + ", ".join(f"{c} {n}" for c, n in took.items()))
    assert len(got) == want or "--loose" in sys.argv, g
    out += got
slug = lambda d: re.sub(r"[^a-z]+", "", d.lower())[:12]
groups = {}
for q in out:
    q["c"] = slug(q.pop("g")); groups[q["c"]] = next(g for g in TARGET if slug(g) == q["c"])
    assert q["a"] not in q["o"] and len(set(q["o"])) == 3, q
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
json.dump(groups, open(os.path.join(os.path.dirname(OUT) or ".", "timeline_groups.json"), "w"), ensure_ascii=False)
print(len(out), "rounds")
