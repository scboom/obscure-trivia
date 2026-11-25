"""Build the Dead by Daylight question bank (exactly 1,000 questions).

Facts about killers, survivors, perks, maps, realms, chapters, add-ons and offerings come from the Dead by Daylight Wiki
(deadbydaylight.wiki.gg): its data tables (read as plain data by lua_tables.py), its Perks page and every character page.
Lore and game-fact questions were written from the wiki's pages, and each one carries the exact wiki text that backs it,
which is checked here again.
Usage: gen_dbd.py WORK_DIR OUT.json [--avail]
"""
import sys, json, random, re, collections, datetime, unicodedata

W, OUT = sys.argv[1:3]
DT = json.load(open(f"{W}/dt.json"))
LO = json.load(open(f"{W}/loadout.json"))
PERKPAGE = json.load(open(f"{W}/perks.json"))
PAGES = json.load(open(f"{W}/pages.json"))
rng = random.Random(20261125)
Q = collections.defaultdict(list)
SEEN = set()

GROUP = {}
for g, kinds in {
    "Killers": "ksurname ktitle krealname kname kpower kpowerof kweapon kspeed kslow kradius kdiff korigin kchapter kyear kfrom korder kcount",
    "Survivors": "ssurname srole srolename sorigin schapter syear sfrom sorder swith",
    "Perks": "powner pdesc pquote ppick pnotmine pgeneral pformer",
    "Lore": "lore",
    "Realms & Maps": "mrealm mlandmark mchapter rloc rmaps",
    "Chapters": "chkiller chsurv chyear chorder chfact",
    "Add-ons & Offerings": "akiller aitem orealm",
    "Game facts": "fact",
}.items():
    for k in kinds.split():
        GROUP[k] = g
TARGET = {"Killers": 205, "Survivors": 135, "Perks": 245, "Lore": 120, "Realms & Maps": 85, "Chapters": 65, "Add-ons & Offerings": 65, "Game facts": 80}
assert sum(TARGET.values()) == 1000, sum(TARGET.values())


def add(c, k, q, a, opts, x=None, ks=None, extra=None):
    a = str(a)
    opts = [o for o in dict.fromkeys(str(o) for o in opts) if o and o != a]
    if len(opts) < 3 or k in SEEN:
        return False
    SEEN.add(k)
    d = {"c": c, "k": k, "q": q, "a": a, "o": opts[:3]}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = list(dict.fromkeys(ks))
    if max(len(s) for s in [a] + d["o"]) > 26:
        d["r"] = 1
    if extra:
        d.update(extra)
    Q[c].append(d)
    return True


def pick(pool, n=3, avoid=()):
    pool = [p for p in dict.fromkeys(pool) if p not in avoid]
    return rng.sample(pool, min(n, len(pool)))


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


# ------------------------------------------------------------------ chapters (DLCs)
def clean_dlc(n):
    n = n.replace("®", "").replace("™", "").strip()
    return {"The HALLOWEEN Chapter": "The Halloween Chapter", "Resident Evil: PROJECT W": "Resident Evil: Project W"}.get(n, n)


def ddate(s):
    d, m, y = map(int, s.split("."))
    return datetime.date(y, m, d)


fmt = lambda d: f"{d.day} {d:%B} {d.year}"
DLC = {}
for x in DT["dlcs"]:
    if x["category"] == 1 and not x.get("skip"):
        DLC[x["id"]] = dict(x, title=clean_dlc(x["name"]), date=ddate(x["rDate"]))
BASE = datetime.date(2016, 6, 14)


def first_dlc(v):
    if v is None:
        return None
    return v[0] if isinstance(v, list) else v


# ------------------------------------------------------------------ killers and survivors
POWER = {v["killer"]: n for n, v in LO["p.powers"].items()}
K, S = {}, {}
for k in DT["killers"]:
    page = next(v for key, v in PAGES.items() if key.startswith(f"K{k['id']:02d}_"))
    dl = first_dlc(k.get("dlc"))
    K[k["id"]] = dict(k, title="The " + k["name"], power=POWER[k["id"]], dlc1=dl, date=DLC[dl]["date"] if dl else BASE, page=page)
for s in DT["survivors"]:
    page = next(v for key, v in PAGES.items() if key.startswith(f"S{s['id']:02d}_"))
    dl = first_dlc(s.get("dlc"))
    S[s["id"]] = dict(s, title=s.get("shortName") or s["name"], dlc1=dl, date=DLC[dl]["date"] if dl else BASE, page=page)
assert len(K) == 45 and len(S) == 55, (len(K), len(S))
KT = {k["title"]: k for k in K.values()}
ST = {s["title"]: s for s in S.values()}
for s in S.values():           # typos in the data table's survivor subtitles
    s["role"] = {"Brillant High School Student": "Brilliant High School Student", "Harded Archaeologist": "Hardened Archaeologist"}.get(s["role"].strip(), s["role"].strip())
kk = lambda k: f"k:{k['id']}"
sk = lambda s: f"s:{s['id']}"
chap = lambda c: c["title"] if c["dlc1"] else "the original game"
chap_of = lambda c: (f"{DLC[c['dlc1']]['title']} ({c['date'].year})" if c["dlc1"] else "the original 2016 release")


def ksum(k):
    bits = [f"{k['title']}" + (f" ({k['realName']})" if k.get("realName") else ""), f"power: {k['power']}"]
    bits.append(f"arrived with {DLC[k['dlc1']]['title']} on {fmt(k['date'])}" if k["dlc1"] else "in the game since launch, 14 June 2016")
    return ", ".join(bits) + "."


def ssum(s):
    return f"{s['title']}, the {s['role']}: " + (f"arrived with {DLC[s['dlc1']]['title']} on {fmt(s['date'])}." if s["dlc1"] else "one of the original four Survivors from 14 June 2016.")


# real names (some killers don't have one: creatures and mysteries)
REAL = {k["id"]: k["realName"].replace(" alias ", " (alias ").rstrip() + (")" if " alias " in k["realName"] else "") for k in K.values() if k.get("realName")}
REAL[14] = "Frank, Julie, Susie and Joey"
for i, r in REAL.items():
    k = K[i]
    same = [REAL[j] for j in REAL if j != i and K[j]["gender"] == k["gender"]] or list(REAL.values())
    if r != k["name"] and k["name"] not in r and i not in (20, 24):           # "Pyramid Head" / "Nemesis T-Type" are not names
        add("krealname", f"krealname:{i}", f"What is {k['title']}'s real name?", r, pick(same, 3, (r,)), ksum(k), [kk(k)])
        add("kname", f"kname:{i}", f"{r} is better known as which Killer?", k["title"], pick([K[j]["title"] for j in REAL if j != i], 3), ksum(k), [kk(k)])

# powers
for k in K.values():
    others = [K[j]["power"] for j in K if j != k["id"]]
    add("kpower", f"kpower:{k['id']}", f"What is {k['title']}'s power called?", k["power"], pick(others), ksum(k), [kk(k)])
    if k["power"].lower() not in (k["name"].lower(),):
        add("kpowerof", f"kpowerof:{k['id']}", f"Which Killer's power is called {k['power']}?", k["title"], pick([K[j]["title"] for j in K if j != k["id"]]), ksum(k), [kk(k)])

# weapons (the data table and the Wraith's page disagree on his, and the Ghoul's is missing)
for k in K.values():
    w = k["weapon"]
    if not isinstance(w, str) or k["id"] in (2,):
        continue
    add("kweapon", f"kweapon:{k['id']}", f"Which Killer's weapon is called {w if w.startswith('The ') else 'the ' + w}?", k["title"],
        pick([K[j]["title"] for j in K if j != k["id"]]), f"{k['title']}'s weapon is {w if w.startswith('The ') else 'the ' + w}. " + ksum(k), [kk(k)])

# movement speed (metres per second; 4.6 m/s is 115 %)
def mps(v):
    return f"{v:g} m/s ({round(v / 4.0 * 100):g}%)"


def base_speed(k):
    v = k["speed"]
    return v[0] if isinstance(v, list) else v


SPEEDS = sorted({base_speed(k) for k in K.values()})
for k in K.values():
    v = base_speed(k)
    opts = [mps(x) for x in [3.85, 4.0, 4.2, 4.4, 4.6, 4.8] if x != v]
    note = f" ({k['speed'][1]})" if isinstance(k["speed"], list) else ""
    if v != 4.6 or rng.random() < 0.3:
        how = {"Uncloaked": " while uncloaked", "Stalker Mode": " in Stalker Mode", "Charlotte": " as Charlotte"}.get(k["speed"][1], "") if note else ""
        add("kspeed", f"kspeed:{k['id']}", f"How fast does {k['title']} move{how}?", mps(v),
            pick([o for o in opts if o != mps(v)]), f"{k['title']} moves at {mps(v)}. Most Killers move at 4.6 m/s, 115% of a Survivor's 4 m/s run.", [kk(k)])
slow = [k for k in K.values() if base_speed(k) == 4.4]
fast = [k for k in K.values() if base_speed(k) == 4.6]
for k in slow:
    others = pick([f["title"] for f in fast], 3)
    add("kslow", f"kslow:{k['id']}", "Which of these Killers moves at 4.4 m/s (110%) instead of the usual 4.6 m/s?", k["title"], others,
        f"{k['title']} is one of the 110% Killers. " + ", ".join(others) + " move at 4.6 m/s.", [kk(k)] + [kk(KT[o]) for o in others])

# terror radius (one plain number only)
R = {k["id"]: k["radius"] for k in K.values() if isinstance(k["radius"], (int, float))}
for i, r in R.items():
    k = K[i]
    if r == 32:
        continue
    others = pick([K[j]["title"] for j in R if R[j] == 32], 3)
    add("kradius", f"kradius:{i}", f"Which of these Killers has a {r:g}-metre Terror Radius?", k["title"], others,
        f"{k['title']}'s Terror Radius is {r:g} metres. The usual one is 32 metres, as for " + ", ".join(others) + ".", [kk(k)] + [kk(KT[o]) for o in others])
    add("kradius", f"kradius-n:{i}", f"How big is {k['title']}'s Terror Radius?", f"{r:g} metres", [f"{x} metres" for x in (16, 24, 32, 40, 48) if x != r],
        f"{k['title']}'s Terror Radius is {r:g} metres; most Killers have 32.", [kk(k)])
add("kradius", "kradius:huntress", "How far away can Survivors hear the Huntress's lullaby?", "45 metres", ["20 metres", "32 metres", "64 metres"],
    "The Huntress hums her lullaby out to 45 metres, but her real Terror Radius is only 20 metres.", ["k:8"])

# difficulty
DIFF = {1: "Easy", 2: "Moderate", 3: "Hard", 4: "Very Hard"}
for k in K.values():
    if k.get("diff") in DIFF and (k["diff"] != 2 or rng.random() < 0.35):
        add("kdiff", f"kdiff:{k['id']}", f"What difficulty does the game give {k['title']}?", DIFF[k["diff"]], [v for v in DIFF.values() if v != DIFF[k["diff"]]],
            f"{k['title']} is rated {DIFF[k['diff']]}. " + ksum(k), [kk(k)])

# where they're from
ORIGIN_SHOW = {"Nigerian": "Nigeria", "Russian": "Russia", "Japanese": "Japan", "Canadian": "Canada", "Babylonian (Ancient Mesopotamia)": "Ancient Babylon",
               "Scottish": "Scotland", "French": "France", "South Korean": "South Korea", "English": "England", "Chilean": "Chile", "Hungarian": "Hungary",
               "Brazilian of Japanese descent": "Brazil", "Wallachian (Romania)": "Wallachia (Romania)", "Caribbean": "The Caribbean", "Thai": "Thailand",
               "Swedish": "Sweden", "Argentinian of Italian descent": "Argentina", "Chinese": "China", "Jamaican": "Jamaica", "Canadian of Norwegian descent": "Canada",
               "Lebanese American": "Lebanon / USA", "German": "Germany", "French, Malagasy": "France / Madagascar", "Italian": "Italy", "Brazilian": "Brazil",
               "Canadian of Indian descent": "Canada", "Latin American": "Latin America"}
for k in K.values():
    o = k["origin"]
    if o in ORIGIN_SHOW and k["id"] not in (13, 18, 27, 39, 14):     # skip ones where two Killers share a country
        show = ORIGIN_SHOW[o]
        pool = [v for kk2, v in ORIGIN_SHOW.items() if v != show and v not in ("Lebanon / USA", "France / Madagascar", "Latin America")]
        add("korigin", f"korigin:{k['id']}", f"Where does {k['title']} come from?", show, pick(pool), f"{k['title']}: {o}. " + ksum(k), [kk(k)])
for s in S.values():
    o = s["origin"]
    if o in ORIGIN_SHOW and o not in ("Latin American",):
        show = ORIGIN_SHOW[o]
        sameshow = [x for x in S.values() if ORIGIN_SHOW.get(x["origin"]) == show]
        others = pick([x["title"] for x in S.values() if ORIGIN_SHOW.get(x["origin"]) not in (show, None) or x["origin"] == "American"], 3)
        if len(sameshow) == 1:
            add("sorigin", f"sorigin:{s['id']}", f"Which of these Survivors comes from {show}?", s["title"], others, f"{s['title']}: {o}. " + ssum(s), [sk(s)])

# chapters and release dates
for k in K.values():
    if not k["dlc1"]:
        continue
    pool = [DLC[x["dlc1"]]["title"] for x in K.values() if x["dlc1"] and x["id"] != k["id"]]
    add("kchapter", f"kchapter:{k['id']}", f"Which Chapter added {k['title']}?", DLC[k["dlc1"]]["title"], pick(pool), ksum(k), [kk(k), f"dlc:{k['dlc1']}"])
    y = k["date"].year
    add("kyear", f"kyear:{k['id']}", f"In which year did {k['title']} join the game?", y, [str(v) for v in pick([v for v in range(2016, 2027) if abs(v - y) <= 4 and v != y])],
        ksum(k), [kk(k)])
for s in S.values():
    if not s["dlc1"]:
        continue
    pool = [DLC[x["dlc1"]]["title"] for x in S.values() if x["dlc1"] and x["dlc1"] != s["dlc1"]]
    add("schapter", f"schapter:{s['id']}", f"Which Chapter added {s['title']}?", DLC[s["dlc1"]]["title"], pick(pool), ssum(s), [sk(s), f"dlc:{s['dlc1']}"])
    y = s["date"].year
    add("syear", f"syear:{s['id']}", f"In which year did {s['title']} join the game?", y, [str(v) for v in pick([v for v in range(2016, 2027) if abs(v - y) <= 4 and v != y])],
        ssum(s), [sk(s)])
# who came together
for s in S.values():
    if not s["dlc1"]:
        continue
    ks_ = [k for k in K.values() if k["dlc1"] == s["dlc1"]]
    if len(ks_) == 1:
        k = ks_[0]
        add("swith", f"swith:{s['id']}", f"Which Killer arrived in the same Chapter as {s['title']}?", k["title"],
            pick([x["title"] for x in K.values() if x["dlc1"] != s["dlc1"]]), f"Both came with {DLC[s['dlc1']]['title']} ({s['date'].year}).", [sk(s), kk(k)])
        mates = [x["title"] for x in S.values() if x["dlc1"] == s["dlc1"]]
        add("swith", f"swith-k:{s['id']}", f"Which Survivor arrived in the same Chapter as {k['title']}?", s["title"],
            pick([x["title"] for x in S.values() if x["dlc1"] != s["dlc1"]]), f"{' and '.join(mates)} came with {k['title']} in {DLC[s['dlc1']]['title']} ({s['date'].year}).", [sk(s), kk(k)])
add("swith", "swith:base", "Which of these Killers was in the game from day one, alongside Dwight, Meg, Claudette and Jake?", "The Hillbilly",
    ["The Nurse", "The Shape", "The Hag"], "The original 2016 game had three Killers: the Trapper, the Wraith and the Hillbilly. The Nurse came two months later.", ["k:3"])
add("swith", "swith:base2", "Which of these Survivors was NOT one of the original four?", "Nea Karlsson", ["Dwight Fairfield", "Meg Thomas", "Jake Park"],
    "The original four were Dwight, Meg, Claudette and Jake. Nea came with the Nurse in August 2016.", ["s:5"])

# order of release
def order_q(kind, pool, key, label):
    pool = [p for p in pool]
    for n in range(40):
        four = rng.sample(pool, 4)
        dates = [p["date"] for p in four]
        if len(set(dates)) < 4 or min(abs((a - b).days) for a in dates for b in dates if a != b) < 60:
            continue
        first = min(four, key=lambda p: p["date"])
        others = [p["title"] for p in four if p is not first]
        if add(kind, f"{kind}:" + "|".join(sorted(p["title"] for p in four)), f"Which of these {label} came out first?", first["title"], others,
               " · ".join(f"{p['title']}: {p['date']:%B %Y}" for p in sorted(four, key=lambda p: p["date"])) + ".", [key(p) for p in four] + [f"kind:{kind}"]):
            return


for _ in range(14):
    order_q("korder", list(K.values()), kk, "Killers")
for _ in range(10):
    order_q("sorder", list(S.values()), sk, "Survivors")

# the franchise a licensed character comes from (checked against each page's "originates from" line)
FROM = {5: "Halloween", 9: "The Texas Chain Saw Massacre", 10: "A Nightmare on Elm Street", 11: "Saw", 17: "Stranger Things", 20: "Silent Hill",
        24: "Resident Evil", 25: "Hellraiser", 27: "Ring (Ringu)", 29: "Resident Evil", 33: "Alien", 34: "Child's Play", 36: "Dungeons & Dragons",
        37: "Castlevania", 39: "Tokyo Ghoul", 40: "Five Nights at Freddy's", 42: "Stranger Things", 43: "Friday the 13th", 45: "Terrifier"}
SFROM = {6: "Halloween", 8: "Left 4 Dead", 11: "A Nightmare on Elm Street", 12: "Saw", 17: "Evil Dead", 18: "Stranger Things", 19: "Stranger Things",
         22: "Silent Hill", 26: "Resident Evil", 27: "Resident Evil", 30: "Ring (Ringu)", 32: "Resident Evil", 33: "Resident Evil", 39: "Alien",
         40: "Alan Wake", 43: "Tomb Raider", 44: "Castlevania", 47: "The Walking Dead", 48: "The Walking Dead", 50: "Stranger Things", 51: "Stranger Things",
         55: "Terrifier"}
FRANCHISES = sorted(set(FROM.values()) | set(SFROM.values()) | {"Scream", "The Exorcist", "It", "Hannibal", "The Evil Within", "Dead Space"})
CHECK = {"Ring (Ringu)": "Ring", "Child's Play": "Chucky", "Evil Dead": "Evil Dead", "The Texas Chain Saw Massacre": "Texas Chain"}
for i, f in FROM.items():
    k = K[i]
    intro = k["page"]["sections"]["intro"]
    assert CHECK.get(f, f).lower() in intro.lower(), (k["title"], f, intro[:300])
    add("kfrom", f"kfrom:{i}", f"Which franchise does {k['title']} come from?", f, pick([x for x in FRANCHISES if x != f]), ksum(k), [kk(k)])
for i, f in SFROM.items():
    s = S[i]
    intro = s["page"]["sections"]["intro"]
    assert CHECK.get(f, f).lower() in intro.lower() or i == 30, (s["title"], f, intro[:300])
    add("sfrom", f"sfrom:{i}", f"Which franchise does {s['title']} come from?", f, pick([x for x in FRANCHISES if x != f]), ssum(s), [sk(s)])

# survivor subtitles
for s in S.values():
    if s["id"] in (17,):        # the table's "Alone Wolf" for Ash looks wrong; leave it out
        continue
    r = s["role"]
    if any(w.lower() in r.lower() for w in s["title"].split()):
        continue
    others = [x["role"] for x in S.values() if x["id"] != s["id"] and x["id"] != 17]
    add("srole", f"srole:{s['id']}", f"Which Survivor is known as the {r}?", s["title"], pick([x["title"] for x in S.values() if x["id"] != s["id"]]), ssum(s), [sk(s)])
    add("srolename", f"srolename:{s['id']}", f"What is {s['title']}'s title in the game?", r, pick(others), ssum(s), [sk(s)])

add("kcount", "kcount:killers", "How many Killers are in Dead by Daylight as of November 2026?", "45", ["38", "41", "49"],
    "The Terrifier, Art the Clown, became the 45th Killer on 24 November 2026.", None)
add("kcount", "kcount:survivors", "How many Survivors are in Dead by Daylight as of November 2026?", "55", ["44", "50", "60"],
    "Sienna Shaw from Terrifier became the 55th Survivor on 24 November 2026.", None)


# ------------------------------------------------------------------ surnames with look-alike spellings, and the names fans know Killers by
NAMES = json.load(open(f"{W}/names.json"))
REAL_TITLES = {k["title"] for k in K.values()}
for key, first, last, fakes in NAMES["surname"]:
    c = (K if key[0] == "K" else S)[int(key[1:])]
    full = c.get("realName") if key[0] == "K" else c["name"]
    assert re.search(rf"\b{re.escape(first)}\b.*\b{re.escape(last)}\b", full), (key, full)
    assert last not in fakes and len(set(fakes)) == 3, key
    if key[0] == "K":
        add("ksurname", f"ksurname:{key}", f"{c['title']}'s real name is {first} ___. What is the surname?", last, fakes,
            f"{c['title']} is {full}.", [kk(c), f"surname:{last}"])
    else:
        add("ssurname", f"ssurname:{key}", f"What is {first}'s surname?", last, fakes, f"{c['name']}, the {c['role']}.", [sk(c), f"surname:{last}"])
for i, known, fakes in NAMES["title"]:
    k = K[i]
    text = " ".join(k["page"]["sections"].values())
    assert known.split()[0] in text or known == k.get("realName"), (i, known)
    assert not set(fakes) & REAL_TITLES, (i, set(fakes) & REAL_TITLES)
    add("ktitle", f"ktitle:{i}", f"What is {known} called in Dead by Daylight?", k["title"], fakes,
        ksum(k), [kk(k)])

# ------------------------------------------------------------------ perks
PK = LO["p.perks"]
PERK = {}
for p in PERKPAGE:
    t = PK[p["name"]]
    if t.get("unused"):
        continue
    owner = None
    if t.get("character"):
        owner = K[t["character"]] if t["charType"] == "K" else S[t["character"]]
    PERK[p["name"]] = dict(p, side=t["charType"], owner=owner, former=t.get("formerName"), fowner=t.get("formerCharacter"))
assert len(PERK) == 336, len(PERK)
side_word = {"K": "Killer", "S": "Survivor"}
PREFIXES = ("Hex: ", "Boon: ", "Scourge Hook: ", "Invocation: ", "Teamwork: ")
prefix = lambda n: next((x for x in PREFIXES if n.startswith(x)), "")
owner_t = lambda p: p["owner"]["title"] if p["owner"] else f"every {side_word[p['side']]} (a general perk)"
pkey = lambda p: [f"perk:{p['name']}"] + ([kk(p["owner"]) if p["side"] == "K" else sk(p["owner"])] if p["owner"] else [])


def psum(p):
    return f"{p['name']} is {('a ' + side_word[p['side']] + ' perk from ' + p['owner']['title']) if p['owner'] else 'a general ' + side_word[p['side']] + ' perk'}."


def mask(text, p):
    out = text
    names = [p["name"], p["name"][len(prefix(p["name"])):]]
    if p["former"]:
        names += [p["former"], p["former"][len(prefix(p["former"])):]]
    for n in sorted(set(names), key=len, reverse=True):
        out = re.sub(re.escape(n), "this perk", out, flags=re.I)
    out = re.sub(r"this perk('s)?", lambda m: "this perk" + (m.group(1) or ""), out)
    return out


def short_desc(p):
    t = p["desc"]
    t = re.sub(r'^"[^"]{3,200}"\s*', "", t)                       # the flavour line at the top
    t = re.sub(r"\s+", " ", t)
    sents = re.split(r"(?<=[.!?:])\s+(?=[A-Z0-9+-])", t)
    out, best = "", ""
    for s_ in sents:
        if len(out) + len(s_) > 270:
            break
        out = (out + " " + s_).strip()
        if out.endswith((".", "!", "?")):
            best = out
    return mask(best, p) if len(best) >= 90 else ""


UNIQUE = {s: [p for p in PERK.values() if p["side"] == s and p["owner"]] for s in "KS"}
for p in PERK.values():
    if not p["owner"]:
        continue
    pool = [o["title"] for o in (K.values() if p["side"] == "K" else S.values()) if o["id"] != p["owner"]["id"]]
    add("powner", f"powner:{p['name']}", f"Which {side_word[p['side']]} brings the perk {p['name']}?", p["owner"]["title"], pick(pool), psum(p), pkey(p))

for p in PERK.values():
    d = short_desc(p)
    if not d:
        continue
    pre = prefix(p["name"])
    same = [x["name"] for x in PERK.values() if x["side"] == p["side"] and x["name"] != p["name"] and prefix(x["name"]) == pre]
    if len(same) < 3:
        same += [x["name"] for x in PERK.values() if x["side"] == p["side"] and x["name"] != p["name"]]
    add("pdesc", f"pdesc:{p['name']}", f"Which {side_word[p['side']]} perk is this? “{d}”", p["name"], pick(same), psum(p), pkey(p), {"r": 1})

for p in PERK.values():
    qt = p["quote"]
    if not qt or len(qt) > 190 or len(qt) < 25 or re.search(r"shit|fuck|bitch|asshole|bastard", qt, re.I):
        continue
    if any(n.lower() in qt.lower() for n in [p["name"], p["name"][len(prefix(p["name"])):]] + ([p["former"]] if p["former"] else [])):
        continue
    if p["owner"] and p["owner"]["title"].split()[0].lower() in qt.lower():
        continue
    same = [x["name"] for x in PERK.values() if x["side"] == p["side"] and x["name"] != p["name"]]
    who = f" ({p['author']})" if p["author"] else ""
    add("pquote", f"pquote:{p['name']}", f"Which perk has this quote? “{qt}”", p["name"], pick(same), f"The quote{who} is on {p['name']}. " + psum(p), pkey(p), {"r": 1})

# one of these is theirs
OWN = collections.defaultdict(list)
for p in PERK.values():
    if p["owner"]:
        OWN[(p["side"], p["owner"]["id"])].append(p)
for (side, i), ps in OWN.items():
    o = (K if side == "K" else S)[i]
    for p in ps[:2]:
        others = pick([x["name"] for x in UNIQUE[side] if x["owner"]["id"] != i], 3)
        add("ppick", f"ppick:{side}{i}:{p['name']}", f"Which of these perks belongs to {o['title']}?", p["name"], others,
            f"{o['title']}'s perks: " + ", ".join(x["name"] for x in ps) + ".", [kk(o) if side == "K" else sk(o), f"perk:{p['name']}"])
    if len(ps) == 3:
        stranger = rng.choice([x for x in UNIQUE[side] if x["owner"]["id"] != i])
        add("pnotmine", f"pnotmine:{side}{i}", f"Which of these perks is NOT one of {o['title']}'s?", stranger["name"], [x["name"] for x in ps],
            f"{stranger['name']} belongs to {stranger['owner']['title']}. {o['title']}'s perks are " + ", ".join(x["name"] for x in ps) + ".",
            [kk(o) if side == "K" else sk(o), f"perk:{stranger['name']}"])

GENERAL = {s: [p for p in PERK.values() if p["side"] == s and not p["owner"]] for s in "KS"}
TWINNED = {x["former"] for x in PERK.values() if x["former"]}          # unique perks that also exist under a general name
for side in "KS":
    for p in GENERAL[side]:
        if p["former"]:
            continue
        others = pick([x["name"] for x in UNIQUE[side] if x["name"] not in TWINNED], 3)
        add("pgeneral", f"pgeneral:{p['name']}", f"Which of these is a general {side_word[side]} perk that every {side_word[side]} can use?", p["name"], others,
            f"{p['name']} is a general perk. " + "; ".join(f"{PERK[o]['name']} belongs to {PERK[o]['owner']['title']}" for o in others) + ".",
            [f"perk:{p['name']}", f"kind:pgeneral{side}"])
for p in PERK.values():
    if p["former"] and p["fowner"]:
        fo = (K if p["side"] == "K" else S)[p["fowner"]]
        sib = [x["name"] for x in PERK.values() if x["former"] and x["name"] != p["name"]] + [x["name"] for x in GENERAL[p["side"]] if not x["former"]]
        add("pformer", f"pformer:{p['name']}", f"{fo['title']}'s perk {p['former']} lives on as which general perk?", p["name"], pick(sib),
            f"Since {fo['title']}'s Chapter left the store, players who don't own it get {p['former']} as the general perk {p['name']}.",
            [f"perk:{p['name']}", kk(fo) if p["side"] == "K" else sk(fo)])

# ------------------------------------------------------------------ realms and maps
REALM = {r["id"]: r for r in DT["realms"]}
rname = lambda r: r["name"]
MAP_DLC = {}
DLC_BY_PATCH = {x["release"]: x["id"] for x in DLC.values()}
for m in DT["maps"]:
    rel = m.get("release") or (m.get("variations") or [{}])[0].get("release")
    if rel in DLC_BY_PATCH:
        MAP_DLC[m["id"]] = DLC_BY_PATCH[rel]
for m in DT["maps"]:
    r = REALM[m["realm"]]
    add("mrealm", f"mrealm:{m['id']}", f"Which Realm is the map {m['name']} in?", rname(r), pick([rname(x) for x in REALM.values() if x["id"] != r["id"]]),
        f"{m['name']} is one of the maps of {rname(r)} ({r['location']}).", [f"map:{m['id']}", f"realm:{r['id']}"])
    lm = m.get("landmark")
    if lm and " or " not in lm and lm not in ("Main Hall",) and sum(1 for x in DT["maps"] if x.get("landmark") == lm) == 1:
        add("mlandmark", f"mlandmark:{m['id']}", f"Which map's main landmark is the {lm}?", m["name"],
            pick([x["name"] for x in DT["maps"] if x["id"] != m["id"] and x.get("landmark")]), f"The {lm} is the main building of {m['name']} in {rname(r)}.", [f"map:{m['id']}"])
for mid, did in MAP_DLC.items():
    m = next(x for x in DT["maps"] if x["id"] == mid)
    ks_ = [k for k in K.values() if k["dlc1"] == did]
    if len(ks_) == 1:
        k = ks_[0]
        add("mchapter", f"mchapter:{mid}", f"Which Killer's Chapter added the map {m['name']}?", k["title"],
            pick([x["title"] for x in K.values() if x["id"] != k["id"]]), f"{m['name']} came with {DLC[did]['title']} ({DLC[did]['date'].year}), {k['title']}'s Chapter.",
            [f"map:{mid}", kk(k)])
LOC = {}
for r in REALM.values():
    loc = r.get("location") or ""
    if loc and loc != "United States":
        LOC[r["id"]] = loc
for i, loc in LOC.items():
    r = REALM[i]
    if sum(1 for v in LOC.values() if v == loc) > 1:
        continue
    add("rloc", f"rloc:{i}", f"Where is the Realm {rname(r)} set?", loc, pick([v for j, v in LOC.items() if j != i and v != loc]),
        f"{rname(r)}: {loc}.", [f"realm:{i}"])
NMAPS = collections.Counter(m["realm"] for m in DT["maps"])
for i, n in NMAPS.items():
    r = REALM[i]
    if n >= 3:
        add("rmaps", f"rmaps:{i}", f"How many maps does the Realm {rname(r)} have?", n, [str(v) for v in pick([v for v in range(1, 8) if v != n and abs(v - n) <= 3])],
            f"{rname(r)}: " + ", ".join(m["name"] for m in DT["maps"] if m["realm"] == i) + ".", [f"realm:{i}", "kind:rmaps"])

# ------------------------------------------------------------------ chapters
KCH = [k for k in K.values() if k["dlc1"]]
for did, c in DLC.items():
    ks_ = [k for k in K.values() if k["dlc1"] == did]
    ss_ = [s for s in S.values() if s["dlc1"] == did]
    if len(ks_) == 1 and not any(w in c["title"].lower() for w in ks_[0]["name"].lower().split()):
        k = ks_[0]
        add("chkiller", f"chkiller:{did}", f"Which Killer came with the Chapter {c['title']}?", k["title"], pick([x["title"] for x in K.values() if x["id"] != k["id"]]),
            f"{c['title']} ({fmt(c['date'])}): {k['title']}" + (" and " + " and ".join(s["title"] for s in ss_) if ss_ else "") + ".", [f"dlc:{did}", kk(k)])
    if len(ss_) == 1 and not any(w.lower() in c["title"].lower() for w in ss_[0]["title"].split()):
        s = ss_[0]
        add("chsurv", f"chsurv:{did}", f"Which Survivor came with the Chapter {c['title']}?", s["title"], pick([x["title"] for x in S.values() if x["id"] != s["id"]]),
            f"{c['title']} ({fmt(c['date'])}) brought " + " and ".join([k["title"] for k in ks_] + [s["title"]]) + ".", [f"dlc:{did}", sk(s)])
    y = c["date"].year
    if ks_ or ss_:
        add("chyear", f"chyear:{did}", f"In which year did the Chapter {c['title']} come out?", y, [str(v) for v in pick([v for v in range(2016, 2027) if abs(v - y) <= 4 and v != y])],
            f"{c['title']} came out on {fmt(c['date'])}.", [f"dlc:{did}"])
CHS = [dict(title=c["title"], date=c["date"], id=did) for did, c in DLC.items() if any(k["dlc1"] == did for k in K.values()) or any(s["dlc1"] == did for s in S.values())]
for _ in range(14):
    order_q("chorder", CHS, lambda c: f"dlc:{c['id']}", "Chapters")

# ------------------------------------------------------------------ add-ons and offerings
ADD = {}
for n, v in LO["p.addons"].items():          # shown names; a name two add-ons share (Pocket Watch, Jump Rope...) is left out
    ADD.setdefault(v.get("displayName") or n, []).append(v)
ADD = {n: vs[0] for n, vs in ADD.items() if len(vs) == 1}
for n, v in ADD.items():
    if not v.get("killer") or v.get("unused") or v.get("unusedVisible") or v.get("retired"):
        continue
    k = K.get(v["killer"])
    if not k:
        continue
    words = {w.lower().strip("'s") for w in [k["name"]] + (k.get("realName") or "").split() + k["power"].split() if len(w) > 3}
    if any(w in n.lower() for w in words):
        continue
    if rng.random() > 0.22:
        continue
    add("akiller", f"akiller:{n}", f"Which Killer uses the add-on {n}?", k["title"], pick([x["title"] for x in K.values() if x["id"] != k["id"]]),
        f"{n} is an add-on for {k['title']}'s power, {k['power']}.", [f"addon:{n}", kk(k)])
ITEMCAT = {1: "Key", 2: "Firecracker", 3: "Flashlight", 5: "Map", 6: "Med-Kit", 7: "Toolbox"}
for n, v in ADD.items():
    c = v.get("itemsCategory")
    if c not in ITEMCAT or v.get("unused") or v.get("unusedVisible") or v.get("retired"):
        continue
    add("aitem", f"aitem:{n}", f"Which Survivor item takes the add-on {n}?", ITEMCAT[c], [x for x in ("Key", "Flashlight", "Map", "Med-Kit", "Toolbox") if x != ITEMCAT[c]],
        f"{n} is a {ITEMCAT[c]} add-on.", [f"addon:{n}", "kind:aitem"])
OFF = LO["p.offerings"]
REALM_BY_NAME = {r["name"]: r for r in REALM.values()}
for n, v in OFF.items():
    if not v.get("realm") or v.get("retired") or v.get("deprecated") or v.get("notAvailable"):
        continue
    r = REALM_BY_NAME[v["realm"]]
    where = f"the map {v['map']} in {r['name']}" if v.get("map") else r["name"]
    q = f"Burning the offering {n} sends the Trial to which {'map' if v.get('map') else 'Realm'}?"
    if v.get("map"):
        add("orealm", f"orealm:{n}", q, v["map"], pick([m["name"] for m in DT["maps"] if m["name"] != v["map"]]), f"{n} sends the Trial to {where}.", [f"offering:{n}"])
    else:
        add("orealm", f"orealm:{n}", q, r["name"], pick([x["name"] for x in REALM.values() if x["id"] != r["id"]]), f"{n} sends the Trial to {where}.", [f"offering:{n}", f"realm:{r['id']}"])

# ------------------------------------------------------------------ written questions: lore and game facts, each with the wiki text behind it
def section_text(who, sec):
    for key, v in PAGES.items():
        if key == who:
            return v["sections"].get(sec, "")
    return ""


def evidence_ok(text, ev):
    t = norm(text).replace("’", "'").replace("“", '"').replace("”", '"').lower()
    e = norm(ev).replace("’", "'").replace("“", '"').replace("”", '"').lower()
    return e in t


def written(path, kind, check):
    try:
        items = json.load(open(path))
    except FileNotFoundError:
        print("missing", path)
        return
    bad = 0
    for it in items:
        if not check(it):
            bad += 1
            continue
        ks = []
        if kind == "lore" and it["who"][:1] in "KS" and it["who"] != "world":
            ks.append(("k:" if it["who"][0] == "K" else "s:") + str(int(it["who"][1:3])))
        add(kind, f"{kind}:{it['q']}", it["q"], it["a"], it["o"], it.get("x"), ks + [f"{kind}:{it['q']}"])
    print(f"{path}: {len(items) - bad} kept, {bad} failed the evidence check")


def lore_check(it):
    if it["who"] == "world":                    # the Entity, the Observer, the Realms...: pages saved in dbd/world
        base = f"{W}/../world/{it['section'].replace(' ', '_')}"
        texts = [open(p).read() for p in (base + ".txt", base + ".plain.txt") if __import__("os").path.exists(p)]
        return any(evidence_ok(t, it["evidence"]) for t in texts)
    return evidence_ok(section_text(it["who"], it.get("section", "Lore")), it["evidence"])


def fact_check(it):
    f = f"{W}/../facts/{re.sub(r'_+', '_', it['page'].replace(' ', '_').replace('/', '_').replace('&', ''))}.txt"
    try:
        return evidence_ok(open(f).read(), it["evidence"])
    except FileNotFoundError:
        return False


written(f"{W}/lore_q.json", "lore", lore_check)
written(f"{W}/facts_q.json", "fact", fact_check)
CHFACTS = [
    ("Which Chapter left the game in January 2026, taking The Shape and Laurie Strode off the store?", "The Halloween Chapter",
     ["The SAW Chapter", "Stranger Things", "Hellraiser"], "Players who already owned them keep Michael Myers and Laurie Strode.", ["K05", "retired on 19th of January 2026"]),
    ("Which Chapter was taken out of the game from November 2021 until November 2023?", "Stranger Things", ["Hellraiser", "The Halloween Chapter", "Ghost Face"],
     "The first Stranger Things Chapter came back on 6 November 2023, and a second one followed in January 2026.", ["S18", "between 17 November 2021 and 6 November 2023"]),
    ("Which Killer's Chapter was pulled from the stores in March 2025?", "The Cenobite", ["The Shape", "The Good Guy", "The Nightmare"],
     "Hellraiser left the stores in March 2025, but owners can still play Pinhead.", ["K25", "delisted from platform stores on 4 March 2025"]),
    ("Which Killer was due to leave the store on 24 November 2026, the day The Terrifier arrived?", "The Good Guy", ["The Nightmare", "The Pig", "The Ghost Face"],
     "The Chucky Chapter and all its outfits were set to be delisted that day; owners keep him.", ["K34", "delisted from all platform stores and the in-game store on 24 November 2026"]),
    ("Which Killer must you unlock by playing the Killer Tutorial?", "The Wraith", ["The Trapper", "The Hillbilly", "The Nurse"],
     "Finish the Killer Tutorial and the Wraith is yours.", ["K02", "completing the Killer Tutorial"]),
    ("Which Survivor do you unlock by playing the Survivor Tutorial?", "David King", ["Dwight Fairfield", "Meg Thomas", "Jake Park"],
     "David King came with A Lullaby for the Dark in 2017, and now he is the Survivor Tutorial's reward.", ["S10", "completing the Survivor Tutorial"]),
    ("Which Survivor's Chapter was only on PC at first?", "Bill Overbeck", ["Ash Williams", "Quentin Smith", "David Tapp"],
     "Left Behind, with Bill from Left 4 Dead, came out in March 2017 as a PC-exclusive Half-Chapter.", ["S08", "originally PC-exclusive"]),
    ("Which Chapter pack bundles The Hag, The Doctor, The Clown and The Spirit?", "Maddening Darkness Pack", ["Old Wounds Pack", "Macabre Tales Pack", "Endless Hunt Pack"],
     "Old Chapters were retired on 8 January 2024 and sold as packs instead.", ["K06", "Maddening Darkness Pack"]),
    ("Which Chapter pack bundles The Legion, The Plague, The Oni and The Deathslinger?", "Old Wounds Pack", ["Maddening Darkness Pack", "Macabre Tales Pack", "Endless Hunt Pack"],
     "They are also still sold one by one in the in-game store.", ["K14", "Old Wounds Pack"]),
    ("Which Chapter pack bundles The Blight, The Twins and The Trickster?", "Macabre Tales Pack", ["Maddening Darkness Pack", "Old Wounds Pack", "Endless Hunt Pack"],
     "Their Survivors Felix, Élodie and Yun-jin are in it too.", ["K21", "Macabre Tales Pack"]),
    ("Which Chapter pack bundles The Artist, The Dredge, The Knight and The Skull Merchant?", "Endless Hunt Pack", ["Maddening Darkness Pack", "Old Wounds Pack", "Macabre Tales Pack"],
     "Their Chapters were retired on 14 May 2024.", ["K26", "Endless Hunt Pack"]),
    ("Ghost Face's iconic mask is licensed from which company?", "Fun World", ["Universal", "Spirit Halloween", "Blumhouse"],
     "BHVR's Ghost Face, Danny Johnson, is its own take on the character, wearing the licensed mask.", ["K16", "licensed by Fun World"]),
    ("Which Survivor is a child in his film, so BHVR made a grown-up version for the game?", "Yoichi Asakawa", ["Quentin Smith", "Steve Harrington", "Leon Scott Kennedy"],
     "Yoichi comes from the 1998 film Ring, where he is a little boy.", ["S30", "aged-up adult"]),
    ("Which of these was the first licensed Chapter?", "The Halloween Chapter", ["The SAW Chapter", "A Nightmare on Elm Street", "LEATHERFACE"],
     "The Halloween Chapter brought Michael Myers and Laurie Strode on 25 October 2016.", None),
    ("Which of these Chapters was free for everyone?", "A Lullaby for the Dark", ["Spark of Madness", "Curtain Call", "Of Flesh and Mud"],
     "A Lullaby for the Dark gave everyone the Huntress and David King in July 2017.", ["K08", "free Chapter DLC"]),
    ("Which Survivor came with the 2019 Half-Chapter Ash vs Evil Dead?", "Ash Williams", ["Bill Overbeck", "Quentin Smith", "Steve Harrington"],
     "It added a Survivor but no Killer.", None),
    ("The Walking Dead Half-Chapter brought which two Survivors?", "Rick and Michonne Grimes", ["Rick Grimes and Daryl Dixon", "Michonne and Negan", "Glenn and Maggie"],
     "It came out on 29 July 2025, with no Killer.", ["S47", "one of two Survivors of The Walking Dead"]),
]
for q, a, o, x, ev in CHFACTS:
    if ev:
        who, frag = ev
        txt = next(v for key, v in PAGES.items() if key.startswith(who))["sections"]["intro"]
        assert evidence_ok(txt, frag), (q, frag)
    add("chfact", f"chfact:{q}", q, a, o, x)

# ================================================================== balance each group to its target, sharing it between question types by weight
WEIGHT = {"ksurname": 4, "ktitle": 4, "ssurname": 4, "krealname": 2, "kname": 2, "kpower": 3, "kpowerof": 2.5, "kweapon": 2, "kspeed": 1, "kslow": 1, "kradius": 1, "kdiff": 1.2, "korigin": 1,
          "kchapter": 2, "kyear": 1.2, "kfrom": 1.5, "korder": 1, "kcount": 0.2,
          "srole": 2.5, "srolename": 1.5, "sorigin": 1, "schapter": 2, "syear": 1, "sfrom": 1.5, "sorder": 1, "swith": 2,
          "powner": 5, "pdesc": 3, "pquote": 2.5, "ppick": 2, "pnotmine": 1, "pgeneral": 0.8, "pformer": 0.4,
          "mrealm": 3, "mlandmark": 1.5, "mchapter": 1.5, "rloc": 1, "rmaps": 0.5,
          "chkiller": 2, "chsurv": 2, "chyear": 1.5, "chorder": 1, "chfact": 1, "akiller": 3, "aitem": 1, "orealm": 1.5, "lore": 1, "fact": 1}
if "--show" in sys.argv:
    for k in Q:
        for q in rng.sample(Q[k], min(2, len(Q[k]))):
            print(f"[{k}] {q['q']}\n      A: {q['a']}  |  {' / '.join(q['o'])}\n      x: {q.get('x', '')}")
    sys.exit()
if "--avail" in sys.argv:
    for g in TARGET:
        print(f"{g:20} " + ", ".join(f"{k} {len(Q[k])}" for k in Q if GROUP[k] == g), "=", sum(len(Q[k]) for k in Q if GROUP[k] == g), "/", TARGET[g])
    sys.exit()
out = []
for g, want in TARGET.items():
    kinds = [k for k in Q if GROUP[k] == g]
    pools = {k: rng.sample(Q[k], len(Q[k])) for k in kinds}
    took = collections.Counter()
    got = []
    while len(got) < want and any(pools.values()):
        k = min((k for k in kinds if pools[k]), key=lambda k: (took[k] / WEIGHT.get(k, 1), rng.random()))
        got.append(pools[k].pop())
        took[k] += 1
    print(f"{g:20} {len(got):4}/{want}  " + ", ".join(f"{k} {took[k]}/{len(Q[k])}" for k in kinds))
    assert len(got) == want or "--loose" in sys.argv, g
    out += got
ONE_PER_GAME = {"kslow", "kradius", "kspeed", "korder", "sorder", "chorder", "kcount", "pgeneral", "pformer", "rmaps", "aitem", "kdiff", "kyear", "syear", "chyear",
                "sorigin", "korigin", "pnotmine"}
for q in out:
    if q["c"] in ONE_PER_GAME:
        q["ks"] = (q.get("ks") or [q["k"]]) + ["kind:" + q["c"]]
missing = [k for k in Q if k not in GROUP]
assert not missing, missing
for q in out:
    assert len(q["o"]) == 3 and q["a"] not in q["o"] and len(set(q["o"])) == 3, q
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
print(len(out), "questions")
