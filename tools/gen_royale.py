"""Build the Clash Royale question bank (exactly 1,000 questions).

Card facts (Elixir cost, rarity, type, unlock arena, release date, in-game description, stats, Evolutions, Heroes and
Champion abilities) come from the Clash Royale Wiki, read by cr_extract.py. Game mechanics and general facts are written
by hand and checked against the same wiki pages.
Usage: gen_royale.py CARDS.json OUT.json
"""
import sys, json, random, re, collections, datetime

SRC, OUT = sys.argv[1:3]
D = json.load(open(SRC))
rng = random.Random(20261123)
Q = collections.defaultdict(list)      # question type -> questions
SEEN = set()

GROUP = {
    "cost": "Elixir", "costmost": "Elixir", "costleast": "Elixir", "costone": "Elixir",
    "rarity": "Rarity", "champpick": "Rarity", "rarpick": "Rarity",
    "arena": "Arenas", "arenanum": "Arenas", "arenatro": "Arenas", "arenanext": "Arenas", "arenafact": "Arenas", "camp": "Arenas",
    "quote": "Card descriptions",
    "speed": "Stats", "target": "Stats", "count": "Stats", "range": "Stats", "hitspeed": "Stats", "hp": "Stats", "dmg": "Stats",
    "air": "Stats", "spellground": "Stats", "radius": "Stats", "life": "Stats", "deploy": "Stats", "type": "Stats", "spelltime": "Stats",
    "spellhit": "Stats",
    "mech": "Mechanics", "spawn": "Mechanics", "spawncount": "Mechanics", "jump": "Mechanics",
    "evoquote": "Evolutions", "evocycles": "Evolutions", "evohas": "Evolutions", "evoyear": "Evolutions", "evofirst": "Evolutions",
    "evodesc": "Evolutions", "evofact": "Evolutions",
    "heroab": "Heroes & Champions", "herodesc": "Heroes & Champions", "herohas": "Heroes & Champions", "heroquote": "Heroes & Champions",
    "herocost": "Heroes & Champions", "champab": "Heroes & Champions", "champdesc": "Heroes & Champions", "champcost": "Heroes & Champions",
    "herofact": "Heroes & Champions",
    "year": "History", "launch": "History", "first": "History", "newest": "History",
    "fact": "Game facts", "tower": "Game facts",
}
TARGET = {"Elixir": 125, "Rarity": 90, "Arenas": 135, "Card descriptions": 95, "Stats": 205, "Mechanics": 60, "Evolutions": 95,
          "Heroes & Champions": 75, "History": 85, "Game facts": 35}
assert sum(TARGET.values()) == 1000


def add(c, k, q, a, opts, x=None, ks=None, extra=None):
    opts = [o for o in dict.fromkeys(str(o) for o in opts) if o and o != str(a)]
    if len(opts) < 3 or k in SEEN:
        return False
    SEEN.add(k)
    d = {"c": c, "k": k, "q": q, "a": str(a), "o": opts[:3]}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = ks
    if extra:
        d.update(extra)
    Q[c].append(d)
    return True


# ------------------------------------------------------------------ cards
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September",
                                      "October", "November", "December"], 1)}


def date(s):
    s = s.replace(",", " ")
    m = re.match(r"\s*(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})", s) or None
    if m:
        return datetime.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
    m = re.match(r"\s*([A-Z][a-z]+)\s+(\d{1,2})\s+(\d{4})", s)
    if m:
        return datetime.date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
    return None


fmt = lambda d: f"{d.day} {d:%B} {d.year}"
ARENAS = D["arenas"]
ARENA_N = {a["name"]: a["n"] for a in ARENAS}
alabel = lambda name: "Training Camp" if ARENA_N[name] == 0 else f"{name} (Arena {ARENA_N[name]})"

C = {}
for n, c in D["cards"].items():
    t = dict(zip(*c["tables"][0])) if c["tables"] else {}
    cost = int(c["cost"]) if re.fullmatch(r"\d+", c["cost"]) else None
    C[n] = dict(c, t=t, cost=cost, date=date(c["released"]))
    assert C[n]["date"], (n, c["released"])
    assert c["arena"] in ARENA_N, (n, c["arena"])
CARDS = sorted(n for n, c in C.items() if c["type"] != "Tower Troop")
TOWERS = sorted(n for n, c in C.items() if c["type"] == "Tower Troop")
RAR = ["Common", "Rare", "Epic", "Legendary", "Champion"]
LAUNCH = datetime.date(2016, 1, 4)        # the soft launch; anything dated then has been in the game from the start
key = lambda *names: ["card:" + n for n in names]


def the(n, card=False):
    """'the Hog Rider', 'The Log', and 'the Archers card' for plural names."""
    if n.startswith("The "):
        return n
    return f"the {n} card" if card and n.endswith("s") else f"the {n}"


does = lambda n: "do" if n.endswith("s") and not n.startswith("The ") else "does"
poss = lambda n: (n if n.startswith("The ") else "the " + n) + ("'" if n.endswith("s") else "'s")
STAT_RE = {   # how each stat's changes are written in a card's History, e.g. "increased its lifetime to 25 seconds (from 30 seconds)"
    "hit": r"(?<!first )(?:attack time interval|attack speed|attack period|hit speed)[^.;(]*? to (\d+(?:\.\d+)?) seconds?",
    "range": r"(?<!sight )(?<!spawn )(?<!splash )(?<!deploy )(?<!dash )(?<!jump )\brange[^.;(]*? to (\d+(?:\.\d+)?) tiles",
    "life": r"lifetime[^.;(]*? to (\d+(?:\.\d+)?) seconds",
    "speed": r"movement speed[^.;(]*? to (Slow|Medium|Fast|Very Fast|\d+)",
    "dur": r"(?<!slow )(?<!stun )(?<!freeze )duration[^.;(]*? to (\d+(?:\.\d+)?) seconds",
}


def fresh(n, stat, value):
    """False when the card's History shows a later change that the stats table has not caught up with."""
    last = None
    for line in C[n]["history"]:
        if re.search(r"Evolution|Evolved|Hero |Merge Tactics|Clan Wars|Touchdown|Mega Deck", line):
            continue
        for m in re.finditer(STAT_RE[stat], line, re.I):
            last = m.group(1)
    if last is None:
        return True
    if stat == "speed":
        return last == value or last == {"Slow": "45", "Medium": "60", "Fast": "90", "Very Fast": "120"}.get(value)
    return abs(float(last) - float(value)) < 1e-6


def summary(n):
    c = C[n]
    bits = [f"{c['cost']} Elixir" if c["cost"] else None, f"{c['rarity']} {c['type'].lower()}",
            f"unlocked in {alabel(c['arena'])}", "in the game since launch" if c["date"] == LAUNCH else f"added on {fmt(c['date'])}"]
    return f"{n}: " + ", ".join(b for b in bits if b) + "."


def similar(n, pool, k=3, by=None):
    """Distractors that look like the answer: same type, then close in cost."""
    c = C[n]
    pool = [m for m in pool if m != n]
    by = by or (lambda m: (C[m]["type"] != c["type"], abs((C[m]["cost"] or 4) - (c["cost"] or 4)), rng.random()))
    return sorted(pool, key=by)[:k * 3]


def pick(lst, k=3):
    lst = list(dict.fromkeys(lst))
    return rng.sample(lst, min(k, len(lst)))


GENERIC = {"giant", "royal", "goblin", "goblins", "skeleton", "skeletons", "spirit", "spirits", "electro", "mega", "mini", "barbarian",
           "barbarians", "dragon", "dragons", "witch", "prince", "knight", "wizard", "tower", "barrel", "the", "ice", "fire", "hut", "golem"}


def mask(qt, n):
    """Hide the card's own name in its description (other card names that contain it stay as they are)."""
    if not qt or len(qt) < 30 or re.search(r"\[|\{|''", qt):
        return None
    keep = {}
    for other in sorted(C, key=len, reverse=True):
        if other != n and re.search(r"\b" + re.escape(other) + r"(?![A-Za-z])", qt):
            tok = f"\x00{len(keep)}\x00"
            keep[tok] = other
            qt = qt.replace(other, tok)
    variants = {n, n.replace(".", ""), n.rstrip("s"), n.replace("P.E.K.K.A.", "P.E.K.K.A")}
    for v in sorted(variants, key=len, reverse=True):
        qt = re.sub(r"(?i)\b(?:evolved |evo |hero )?" + re.escape(v) + r"\w*(?:'s|’s)?",
                    lambda m: "___" + ("'s" if m.group(0).endswith(("'s", "’s")) else ""), qt)
    for tok, other in keep.items():
        qt = qt.replace(tok, other)
    return None if qt.count("___") > 3 else qt


def stems(n):
    return [w.rstrip("s") if len(w) > 3 else w for w in re.findall(r"[A-Za-z][A-Za-z.]{2,}", n) if w not in ("The",)]


def desc_opts(n, text, pool):
    """Distractors for a 'which card is described' question. If a word of the answer's name is still in the text,
    every distractor has to share it too (or the question is dropped)."""
    tells = [w for w in stems(n) if re.search(r"(?i)\b" + re.escape(w), text)]
    if not tells:
        return pick(similar(n, pool))
    both = [m for m in C if m != n and all(re.search(r"(?i)\b" + re.escape(w), m) for w in tells)]
    return pick(both) if len(both) >= 3 else None


# ================================================================== Elixir
for n in CARDS:
    c = C[n]
    if c["cost"] is None or n == "Spirit Empress":
        continue
    v = c["cost"]
    opts = [str(x) for x in sorted({1, 2, 3, 4, 5, 6, 7, 8, 9} - {v}, key=lambda x: (abs(x - v), rng.random()))[:3]]
    add("cost", f"cost:{n}", f"How much Elixir does {the(n, True)} cost?", v, opts, summary(n), key(n))
costed = [n for n in CARDS if C[n]["cost"] and n != "Spirit Empress"]
for kind, word, fn in (("costmost", "the most", max), ("costleast", "the least", min)):
    tries = 0
    while len(Q[kind]) < 16 and tries < 4000:
        tries += 1
        four = rng.sample(costed, 4)
        costs = [C[m]["cost"] for m in four]
        if len(set(costs)) < 4:
            continue
        top = fn(four, key=lambda m: C[m]["cost"])
        add(kind, f"{kind}:" + "|".join(sorted(four)), f"Which of these cards costs {word} Elixir?", top, [m for m in four if m != top],
            " · ".join(f"{m}: {C[m]['cost']}" for m in sorted(four, key=lambda m: -C[m]["cost"])) + ".", key(*four))
ones = [n for n in costed if C[n]["cost"] == 1]
for n in ones:
    add("costone", f"costone:{n}", "Which of these cards costs just 1 Elixir?", n, pick([m for m in costed if C[m]["cost"] == 2], 3),
        f"The 1-Elixir cards are {', '.join(ones[:-1])} and {ones[-1]}.", key(n))

# ================================================================== Rarity
for n in CARDS + TOWERS:
    c = C[n]
    if c["rarity"] == "Champion":
        continue
    opts = [r for r in RAR if r != c["rarity"] and (r != "Champion" or c["type"] == "Troop")]
    if len(opts) > 3:
        opts = rng.sample(opts, 3)
    what = "tower troop" if c["type"] == "Tower Troop" else "card"
    add("rarity", f"rarity:{n}", f"What rarity is {the(n)} {what}?" if not n.startswith("The ") else f"What rarity is {n}?", c["rarity"], opts,
        summary(n), key(n))
champs = [n for n in CARDS if C[n]["rarity"] == "Champion"]
legs = [n for n in CARDS if C[n]["rarity"] == "Legendary" and C[n]["type"] == "Troop"]
for n in champs:
    add("champpick", f"champpick:{n}", "Which of these cards is a Champion?", n, pick(legs), f"{n} is a Champion; the others are Legendary.", key(n))
for r in ("Common", "Rare", "Epic", "Legendary"):
    pool = [n for n in CARDS if C[n]["rarity"] == r and C[n]["type"] == "Troop"]
    other = [n for n in CARDS if C[n]["rarity"] not in (r, "Champion") and C[n]["type"] == "Troop"]
    for n in rng.sample(pool, 4):
        wrong = pick([m for m in other if abs((C[m]["cost"] or 4) - (C[n]["cost"] or 4)) <= 1])
        add("rarpick", f"rarpick:{r}:{n}", f"Which of these troops is {'an' if r[0] in 'AEIOU' else 'a'} {r} card?", n, wrong,
            " · ".join(f"{m}: {C[m]['rarity']}" for m in [n] + wrong) + ".", key(n, *wrong))

# ================================================================== Arenas
for n in CARDS + TOWERS:
    c = C[n]
    a = ARENA_N[c["arena"]]
    near = sorted((x for x in ARENAS if x["n"] != a and x["n"] <= 18), key=lambda x: (abs(x["n"] - a), rng.random()))[:5]
    add("arena", f"arena:{n}", f"In which arena do you unlock {the(n, True)}?", alabel(c["arena"]), [alabel(x["name"]) for x in rng.sample(near, 3)],
        summary(n), key(n))
real = [x for x in ARENAS if x["n"] >= 1]
for x in real:
    nums = sorted((y["n"] for y in real if y["n"] != x["n"]), key=lambda v: (abs(v - x["n"]), rng.random()))[:3]
    add("arenanum", f"arenanum:{x['name']}", f"Which arena number is {x['name']}?", f"Arena {x['n']}", [f"Arena {v}" for v in nums],
        f"{x['name']} is Arena {x['n']}, from {x['lo']:,} to {x['hi']:,} trophies.", ["arena:" + x["name"]])
    los = sorted((y["lo"] for y in real if y["lo"] != x["lo"]), key=lambda v: (abs(v - x["lo"]), rng.random()))[:3]
    add("arenatro", f"arenatro:{x['name']}", f"How many trophies do you need to reach {x['name']}?", f"{x['lo']:,}", [f"{v:,}" for v in los],
        f"{x['name']} (Arena {x['n']}) runs from {x['lo']:,} to {x['hi']:,} trophies.", ["arena:" + x["name"]])
    nxt = [y for y in real if y["n"] == x["n"] + 1]
    if nxt:
        y = nxt[0]
        wrong = [z["name"] for z in sorted(real, key=lambda z: (abs(z["n"] - x["n"]), rng.random())) if z["n"] not in (x["n"], y["n"])][:3]
        add("arenanext", f"arenanext:{x['name']}", f"On Trophy Road, which arena comes right after {x['name']}?", y["name"], wrong,
            f"{x['name']} is Arena {x['n']} and {y['name']} is Arena {y['n']}.", ["arena:" + x["name"], "arena:" + y["name"]])
camp = [n for n in ARENAS[0]["cards"] if n in C]
for n in camp:
    add("camp", f"camp:{n}", "Which of these cards do you get in the Training Camp, before Trophy Road?", n,
        pick([m for m in CARDS if ARENA_N[C[m]["arena"]] >= 4 and C[m]["type"] == C[n]["type"]]),
        f"The Training Camp gives you {', '.join(camp[:-1])} and {camp[-1]}.", key(n))
AN = lambda i: alabel([a["name"] for a in ARENAS if a["n"] == i][0])
ARENA_FACTS = [
    ("Which arena unlocks Epic cards?", AN(6), [AN(3), AN(8), AN(11)], "Epic cards unlock in P.E.K.K.A.'s Playhouse (Arena 6)."),
    ("Which arena unlocks Legendary cards?", AN(11), [AN(8), AN(13), AN(16)], "Legendary cards unlock in Electro Valley (Arena 11)."),
    ("Which arena unlocks Champion cards?", AN(16), [AN(11), AN(14), AN(18)], "Champions unlock in Executioner's Kitchen (Arena 16)."),
    ("In which arena do you unlock Card Evolution?", AN(3), [AN(1), AN(6), AN(10)], "Card Evolution and the first Evolution slot unlock in Barbarian Bowl (Arena 3)."),
    ("In which arena do you unlock Clan Wars?", AN(3), [AN(1), AN(5), AN(8)], "Clan Wars unlock in Barbarian Bowl (Arena 3)."),
    ("Which arena lets you pick a second tower troop, besides the Tower Princess?", AN(8), [AN(5), AN(11), AN(13)],
     "A second tower troop unlocks in Frozen Peak (Arena 8), which also gives you the Cannoneer."),
    ("Which is the last arena where you unlock new cards?", AN(18), [AN(16), AN(19), AN(24)],
     "Silent Sanctuary (Arena 18) is the last arena with new cards; every arena after it unlocks none."),
    ("What is the last normal arena on Trophy Road, where Ranked unlocks?", AN(32), [AN(24), AN(28), AN(30)],
     "Spirit Square (Arena 32), from 13,500 trophies, is the final normal arena and unlocks Ranked."),
    ("How many trophies does Trophy Road span, from the first arena to the end of the last?", "14,000", ["7,500", "10,000", "20,000"],
     "32 arenas span 14,000 trophies."),
    ("How many arenas are there on Trophy Road?", "32", ["20", "24", "28"], "There are 32 arenas, plus the Training Camp tutorial."),
    ("Which of these arena names is spelled in capital letters with an exclamation mark?", "PANCAKES!", ["Valkalla", "Clash Fest", "Boot Camp"],
     "PANCAKES! is Arena 22."),
    ("Which arena is Arena 1, the first one after the Training Camp?", "Goblin Stadium", ["Bone Pit", "Barbarian Bowl", "Spell Valley"],
     "Goblin Stadium is Arena 1, from 0 to 300 trophies."),
    ("Which arena was called Legendary Arena before it was renamed in March 2017?", "Hog Mountain", ["Jungle Arena", "Frozen Peak", "Royal Arena"],
     "The March 2017 update renamed the old Legendary Arena to Hog Mountain and added a new Legendary Arena higher up."),
    ("Which arena unlocks the most cards?", AN(15), [AN(8), AN(13), AN(5)], "Miner's Mine (Arena 15) unlocks 10 cards, more than any other."),
]
TOPIC = {"How many trophies does Trophy Road span": "t:road", "How many arenas are there": "t:road", "What is the last normal arena": "t:road",
         "Which arena unlocks Champion cards": "t:champ2021", "Which rarity was added in October 2021": "t:champ2021",
         "Which three Champions arrived together": "t:champ2021", "Which update added the very first Card Evolutions": "t:evo2023",
         "Which of these was one of the first four Card Evolutions": "t:evo2023", "Which tower troop does everyone start with": "t:tower",
         "Which tower troop has the most hitpoints": "t:tower", "When did the Tower Troop Update": "t:tower", "How much Elixir do you start": "t:elixir",
         "What is the most Elixir you can hold": "t:elixir", "How many tiles wide": "t:size", "How many tiles long": "t:size",
         "How long is a battle before": "t:time", "When does Double Elixir start": "t:time", "What comes after Double Elixir": "t:time",
         "In normal time, how long does it take": "t:elixir2", "How much slower is Elixir in 2v2": "t:elixir2",
         "Which card costs 9 Elixir": "t:nine", "In which year did Clash Royale come out": "t:launch", "Which company makes": "t:sc",
         "In which country is Supercell": "t:sc", "Which Champion was added in March 2022": "t:champ2021"}


def topic(q):
    return [v for k, v in TOPIC.items() if q.startswith(k)]


for q, a, o, x in ARENA_FACTS:
    m = re.match(r"(.+) \(Arena \d+\)$", a)
    add("arenafact", "arenafact:" + q, q, a, o, x, (["arena:" + m.group(1)] if m else ["arena:" + a] if a in ARENA_N else []) + topic(q) or None)

# ================================================================== Card descriptions (in-game text)
for n in CARDS + TOWERS:
    c = C[n]
    qt = mask(c["quote"], n)
    if not qt:
        continue
    pool = [m for m in CARDS + TOWERS if C[m]["type"] == c["type"]]
    opts = desc_opts(n, qt, pool)
    if opts:
        add("quote", f"quote:{n}", f"Which card's in-game description is this?\n{qt}", n, opts, summary(n), key(n))

# ================================================================== Stats
SPEEDS = ["Slow", "Medium", "Fast", "Very Fast"]
single = lambda c: len(c["tables"]) == 1 or c["type"] == "Building" and n not in ("Barbarian Hut", "Goblin Hut", "Tombstone", "Goblin Drill", "Goblin Cage")
for n in CARDS:
    c, t = C[n], C[n]["t"]
    if c["type"] == "Troop" and t.get("Speed") and t.get("Count") in ("x1", "1x", "1", None) or n in ("Barbarians", "Minion Horde", "Skeleton Army", "Royal Hogs", "Bats", "Goblins"):
        if t.get("Speed"):
            sp = t["Speed"].split(" (")[0]
            if sp in SPEEDS and fresh(n, "speed", sp):
                add("speed", f"speed:{n}", f"How fast {does(n)} {the(n)} move?", sp, [s for s in SPEEDS if s != sp],
                    f"{n}: {t['Speed']} movement speed. The speeds are Slow (45), Medium (60), Fast (90) and Very Fast (120).", key(n))
TG = {"Ground": "Ground troops and buildings", "Air & Ground": "Air and ground", "Buildings": "Buildings only", "Building": "Buildings only"}
for n in CARDS + TOWERS:
    c, t = C[n], C[n]["t"]
    if c["type"] in ("Troop", "Building", "Tower Troop") and t.get("Target") in TG and len(c["tables"]) == 1 or n in ("Goblin Hut",):
        tg = TG.get(t.get("Target"))
        if n == "Goblin Hut" or not tg:
            continue
        add("target", f"target:{n}", f"What {does(n)} {the(n)} attack?", tg, [v for v in dict.fromkeys(list(TG.values()) + ["Air troops only"]) if v != tg],
            f"{n} targets: {t['Target']}.", key(n))
COUNTS = {"Archers": ("Archers", 2), "Barbarians": ("Barbarians", 5), "Bats": ("Bats", 5), "Elite Barbarians": ("Elite Barbarians", 2),
          "Goblins": ("Goblins", 4), "Guards": ("Guards", 3), "Minion Horde": ("Minions", 6), "Minions": ("Minions", 3),
          "Royal Hogs": ("hogs", 4), "Royal Recruits": ("Royal Recruits", 6), "Skeleton Army": ("Skeletons", 15),
          "Skeleton Dragons": ("Skeleton Dragons", 2), "Skeletons": ("Skeletons", 3), "Spear Goblins": ("Spear Goblins", 3),
          "Wall Breakers": ("Wall Breakers", 2), "Zappies": ("Zappies", 3)}
for n, (unit, v) in COUNTS.items():
    assert C[n]["t"].get("Count") == f"x{v}", (n, C[n]["t"].get("Count"))
    opts = [str(x) for x in sorted({1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20} - {v}, key=lambda x: (abs(x - v), rng.random()))[:3]]
    add("count", f"count:{n}", f"How many {unit} does one {n} card put on the arena?", v, opts, f"{n}: {v} {unit} for {C[n]['cost']} Elixir.", key(n))
num = lambda s: float(s) if re.fullmatch(r"\d+(?:\.\d+)?", s or "") else None
ranged = {n: num(C[n]["t"].get("Range")) for n in CARDS + TOWERS if num(C[n]["t"].get("Range")) and C[n]["type"] != "Spell" and len(C[n]["tables"]) <= 2}
rvals = sorted(set(ranged.values()))
tiles = lambda v: f"{v:g} tiles"
for n, v in ranged.items():
    if not fresh(n, "range", v):
        print("stale range", n, v)
        continue
    opts = sorted((r for r in rvals if r != v), key=lambda r: (abs(r - v), rng.random()))[:3]
    add("range", f"range:{n}", f"What is {poss(n)} attack range?", tiles(v), [tiles(r) for r in opts], f"{n}: {tiles(v)} range.", key(n))
hits = {}
for n in CARDS + TOWERS:
    hs = C[n]["t"].get("Hit Speed", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?) sec", hs)
    if m and len(C[n]["tables"]) <= 2 and n not in ("X-Bow", "Mighty Miner", "Inferno Tower", "Inferno Dragon"):
        if fresh(n, "hit", m.group(1)):
            hits[n] = float(m.group(1))
        else:
            print("stale hit speed", n, m.group(1))
hvals = sorted(set(hits.values()))
secs = lambda v: f"{v:g} seconds" if v != 1 else "1 second"
for n, v in hits.items():
    opts = sorted((h for h in hvals if h != v), key=lambda h: (abs(h - v), rng.random()))[:3]
    add("hitspeed", f"hitspeed:{n}", f"How often {does(n)} {the(n)} attack (the hit speed)?", f"Every {secs(v)}", [f"Every {secs(h)}" for h in opts],
        f"{n}: one attack every {secs(v)}.", key(n))
HP = {n: int(C[n]["vars"]["hp_11"]) for n in CARDS + TOWERS if "hp_11" in C[n]["vars"] and C[n]["type"] in ("Troop", "Building")
      and not any(k.endswith("hp_11") and k != "hp_11" for k in C[n]["vars"]) and len(C[n]["tables"]) <= 2 and n not in ("Rascals", "Goblin Gang")}
HP["Golem"] = int(C["Golem"]["vars"]["golem_hp_11"])
DMG = {n: int(C[n]["vars"]["dmg_11"]) for n in HP if "dmg_11" in C[n]["vars"] and C[n]["vars"]["dmg_11"].isdigit()}
for kind, table, word in (("hp", HP, "has the most hitpoints"), ("dmg", DMG, "hits the hardest, with the most damage per hit")):
    tries = 0
    while len(Q[kind]) < (40 if kind == "hp" else 25) and tries < 20000:
        tries += 1
        four = rng.sample(sorted(table), 4)
        vals = sorted((table[m] for m in four), reverse=True)
        if vals[0] < vals[1] * 1.25 or any(C[m]["type"] != C[four[0]]["type"] for m in four):
            continue
        top = max(four, key=lambda m: table[m])
        add(kind, f"{kind}:" + "|".join(sorted(four)), f"At the same card level, which of these {word}?", top, [m for m in four if m != top],
            "At level 11: " + " · ".join(f"{m} {table[m]:,}" for m in sorted(four, key=lambda m: -table[m])) + ".", key(*four))
fliers = [n for n in CARDS if C[n]["type"] == "Troop" and "Air" == C[n]["t"].get("Transport")]
walkers = [n for n in CARDS if C[n]["type"] == "Troop" and C[n]["t"].get("Transport") == "Ground" and C[n]["rarity"] != "Champion"]
for n in fliers:
    add("air", f"air:{n}", "Which of these is a flying troop?", n, pick(walkers), f"{n} flies, so only air-targeting cards can hit it.", key(n))
spells = [n for n in CARDS if C[n]["type"] == "Spell"]
ground_sp = [n for n in spells if C[n]["t"].get("Target") == "Ground"]
air_sp = [n for n in spells if C[n]["t"].get("Target") == "Air & Ground"]
for n in ground_sp:
    for i in range(2):
        add("spellground", f"spellground:{n}:{i}", "Which of these spells can NOT hit air troops?", n, pick(air_sp),
            f"{n} only hits ground units. Spells that cannot hit air: {', '.join(ground_sp)}.", key(n))
RAD = {n: num(C[n]["t"].get("Radius")) for n in spells if num(C[n]["t"].get("Radius"))}
tries = 0
while len(Q["radius"]) < 10 and tries < 5000:
    tries += 1
    four = rng.sample(sorted(RAD), 4)
    vals = sorted((RAD[m] for m in four), reverse=True)
    if vals[0] == vals[1]:
        continue
    top = max(four, key=lambda m: RAD[m])
    add("radius", "radius:" + "|".join(sorted(four)), "Which of these spells covers the biggest area?", top, [m for m in four if m != top],
        "Radius: " + " · ".join(f"{m} {RAD[m]:g} tiles" for m in sorted(four, key=lambda m: -RAD[m])) + ".", key(*four))
LIFE = {"Cannon": "30 seconds", "Bomb Tower": "30 seconds", "Inferno Tower": "30 seconds", "Mortar": "30 seconds", "X-Bow": "30 seconds",
        "Tesla": "25 seconds", "Goblin Hut": "30 seconds", "Barbarian Hut": "30 seconds", "Tombstone": "30 seconds",
        "Goblin Cage": "20 seconds", "Goblin Drill": "10 seconds", "Elixir Collector": "1 minute 50 seconds"}
for n, v in LIFE.items():
    raw = C[n]["t"]["Lifetime"]
    assert raw.replace("sec", "seconds").replace("min", "minute") == v, (n, raw)
    if not fresh(n, "life", {"1 minute 50 seconds": "110"}.get(v, v.split()[0])):
        print("stale lifetime", n, v)
        continue
    add("life", f"life:{n}", f"How long does a {n} last before it falls apart on its own?", v,
        [o for o in ["10 seconds", "20 seconds", "25 seconds", "30 seconds", "40 seconds", "1 minute", "1 minute 50 seconds"] if o != v][:6:2],
        f"{n}: lasts {v}.", key(n))
for n in ("Golem", "X-Bow", "Mortar"):
    v = C[n]["t"]["Deploy Time"]
    assert v in ("3 sec", "3.5 sec"), (n, v)
    add("deploy", f"deploy:{n}", f"How long does the {n} take to deploy, when most cards take 1 second?", v.replace("sec", "seconds"),
        ["0.5 seconds", "2 seconds", "5 seconds", "3 seconds", "3.5 seconds"], f"{n}: {v.replace('sec', 'seconds')} deploy time.", key(n))
buildings = [n for n in CARDS if C[n]["type"] == "Building"]
troops = [n for n in CARDS if C[n]["type"] == "Troop"]
for n in buildings:
    add("type", f"type:b:{n}", "Which of these cards is a building?", n, pick(troops), f"{n} is a building card.", key(n))
for n in rng.sample(spells, 12):
    add("type", f"type:s:{n}", "Which of these cards is a spell?", n, pick(troops + buildings), f"{n} is a spell card.", key(n))
SPELLTIME = [("Freeze", "Freeze Duration", "How long does Freeze freeze enemies for?"), ("Earthquake", "Duration", "How long does an Earthquake last?"),
             ("Graveyard", "Duration", "How long does a Graveyard keep spawning Skeletons?"), ("Goblin Curse", "Duration", "How long does the Goblin Curse last?"),
             ("Rage", "Duration", "How long does the Rage spell last?"), ("Zap", "Stun Duration", "How long does Zap stun enemies for?")]
for n, col, q in SPELLTIME:
    v = num(C[n]["t"][col].replace(" sec", ""))
    if col == "Duration" and not fresh(n, "dur", v):
        print("stale duration", n, v)
        continue
    pool = [0.5, 1, 2, 3, 4, 4.5, 5, 6, 8, 9, 10, 12]
    opts = sorted((p for p in pool if p != v), key=lambda p: (abs(p - v), rng.random()))[:3]
    add("spelltime", f"spelltime:{n}", q, secs(v), [secs(o) for o in opts], f"{n}: {secs(v)}.", key(n))
SP_DMG = {n: int(C[n]["vars"]["dmg_11"]) for n in spells if C[n]["vars"].get("dmg_11", "").isdigit() and "dmg_hits" not in C[n]["vars"]
          and n not in ("Goblin Barrel", "Graveyard", "Barbarian Barrel", "Royal Delivery", "Goblin Curse", "Rage")}
tries = 0
while len(Q["spellhit"]) < 10 and tries < 5000:
    tries += 1
    four = rng.sample(sorted(SP_DMG), 4)
    vals = sorted((SP_DMG[m] for m in four), reverse=True)
    if vals[0] < vals[1] * 1.2:
        continue
    top = max(four, key=lambda m: SP_DMG[m])
    add("spellhit", "spellhit:" + "|".join(sorted(four)), "Which of these spells deals the most damage to a troop in one hit?", top,
        [m for m in four if m != top], "At level 11: " + " · ".join(f"{m} {SP_DMG[m]:,}" for m in sorted(four, key=lambda m: -SP_DMG[m])) + ".", key(*four))

# ================================================================== Mechanics (hand-written, checked against each card's wiki page)
SPAWN = [   # card, what it makes, how
    ("Witch", "Skeletons", "The Witch summons a group of Skeletons around her every few seconds."),
    ("Night Witch", "Bats", "The Night Witch summons Bats every 5 seconds, and drops one more Bat when defeated."),
    ("Tombstone", "Skeletons", "The Tombstone spawns Skeletons while it stands, and four more when it is destroyed."),
    ("Goblin Hut", "Spear Goblins", "The Goblin Hut sends out a Spear Goblin when an enemy is in range."),
    ("Barbarian Hut", "Barbarians", "The Barbarian Hut summons Barbarians every 15 seconds."),
    ("Furnace", "Fire Spirits", "The Furnace summons a Fire Spirit every 7 seconds."),
    ("Graveyard", "Skeletons", "The Graveyard raises a Skeleton every half second for 9 seconds."),
    ("Lava Hound", "Lava Pups", "When defeated, the Lava Hound bursts into six Lava Pups."),
    ("Golem", "Golemites", "When defeated, the Golem explodes and splits into two Golemites."),
    ("Elixir Golem", "Elixir Golemites", "The Elixir Golem splits into two Elixir Golemites, which each split into two Elixir Blobs."),
    ("Battle Ram", "Barbarians", "When the Battle Ram breaks, the two Barbarians carrying it keep fighting."),
    ("Skeleton Barrel", "Skeletons", "The Skeleton Barrel drops seven Skeletons when it reaches a building or is shot down."),
    ("Goblin Barrel", "Goblins", "The Goblin Barrel lands three Goblins wherever you throw it."),
    ("Goblin Drill", "Goblins", "The Goblin Drill pops up anywhere and spawns a Goblin every 3 seconds."),
    ("Goblin Cage", "A Goblin Brawler", "When the Goblin Cage is destroyed, the Goblin Brawler inside breaks out."),
    ("Phoenix", "An egg", "A defeated Phoenix leaves an egg that hatches into a new Phoenix if not destroyed in time."),
    ("Royal Delivery", "A Royal Recruit", "Royal Delivery drops a box that deals damage and leaves a Royal Recruit behind."),
    ("Mother Witch", "Cursed Hogs", "Troops cursed by the Mother Witch turn into Cursed Hogs if they die while cursed."),
    ("Goblin Curse", "Goblins", "Enemy troops that die inside the Goblin Curse turn into Goblins on your side."),
    ("Suspicious Bush", "Bush Goblins", "When the Suspicious Bush reaches a building or is defeated, two Bush Goblins jump out."),
    ("Lumberjack", "A Rage spell", "When the Lumberjack is defeated, he drops a Rage spell."),
    ("Giant Skeleton", "A huge bomb", "The Giant Skeleton drops a bomb when he dies, which explodes after 3 seconds."),
    ("Balloon", "A bomb", "The Balloon drops a bomb when it is destroyed."),
    ("Goblin Giant", "Spear Goblins", "The Goblin Giant carries two Spear Goblins on his back, who keep fighting when he falls."),
]
made = sorted({s[1] for s in SPAWN} | {"Minions", "Royal Ghosts", "Ice Spirits"})
CLASH = [{"Golemites", "Elixir Golemites"}, {"A bomb", "A huge bomb"}, {"Goblins", "Spear Goblins", "Bush Goblins"}]
for n, thing, x in SPAWN:
    assert n in C
    ok = [m for m in made if m != thing and not any({m, thing} <= grp for grp in CLASH)]
    add("spawn", f"spawn:{n}", f"What does the {n} spawn or leave behind?", thing, pick(ok), x, key(n))
SPAWNCOUNT = [("How many Lava Pups burst out of a defeated Lava Hound?", 6, "Lava Hound", "Six Lava Pups."),
              ("How many Golemites does a Golem split into?", 2, "Golem", "Two Golemites, which explode too."),
              ("How many Goblins come out of a Goblin Barrel?", 3, "Goblin Barrel", "Three Goblins."),
              ("How many Skeletons drop out of a Skeleton Barrel?", 7, "Skeleton Barrel", "Seven Skeletons."),
              ("How many Barbarians are under a Battle Ram?", 2, "Battle Ram", "Two Barbarians carry it."),
              ("How many Bush Goblins jump out of a Suspicious Bush?", 2, "Suspicious Bush", "Two Bush Goblins."),
              ("How many Spear Goblins ride on the Goblin Giant's back?", 2, "Goblin Giant", "Two Spear Goblins."),
              ("How many Elixir Blobs does each Elixir Golemite split into?", 2, "Elixir Golem", "Each Elixir Golemite splits into two Elixir Blobs."),
              ("How many Skeletons does a Tombstone release when it is destroyed?", 4, "Tombstone", "Four Skeletons."),
              ("How many daggers can the Dagger Duchess throw before she has to reload?", 8, "Dagger Duchess", "Up to 8 daggers, then she reloads one at a time.")]
for q, v, n, x in SPAWNCOUNT:
    opts = [str(o) for o in sorted({1, 2, 3, 4, 5, 6, 7, 8, 10} - {v}, key=lambda o: (abs(o - v), rng.random()))[:3]]
    add("spawncount", "spawncount:" + q, q, v, opts, x, key(n))
JUMPERS = ["Hog Rider", "Prince", "Dark Prince", "Ram Rider"]
nojump = ["Giant", "Knight", "Valkyrie", "Mini P.E.K.K.A.", "Battle Ram", "Royal Giant", "Barbarians", "Elite Barbarians", "Bandit", "P.E.K.K.A."]
for n in JUMPERS:
    add("jump", f"jump:{n}", "Which of these troops can jump over the river?", n, pick(nojump), f"{n} can jump the river; so can the "
        + ", ".join(m for m in JUMPERS if m != n) + ".", key(n))
MECH = [
    ("Which card can be deployed anywhere on the arena, even next to an enemy tower?", "Miner", ["Hog Rider", "Bandit", "Knight"],
     "The Miner digs underground and can be placed anywhere."),
    ("Which troop stays invisible until it attacks?", "Royal Ghost", ["Bandit", "Prince", "Valkyrie"],
     "The Royal Ghost turns visible only when he attacks, and fades again after 1.8 seconds out of a fight."),
    ("Which troop's damage ramps up the longer it stays on one target?", "Inferno Dragon", ["Baby Dragon", "Electro Dragon", "Skeleton Dragons"],
     "The Inferno Dragon's beam gets stronger the longer it locks on, like the Inferno Tower."),
    ("Which building's beam gets stronger the longer it locks on to one target?", "Inferno Tower", ["Tesla", "Bomb Tower", "Cannon"],
     "The Inferno Tower's damage ramps up over time on a single target."),
    ("Which troop fires 10 pellets like a shotgun, hitting harder up close?", "Hunter", ["Musketeer", "Princess", "Firecracker"],
     "The Hunter's 10 pellets spread out, so he does the most damage at close range."),
    ("Whose axe flies out and comes back like a boomerang, hitting enemies both ways?", "Executioner", ["Valkyrie", "Lumberjack", "Bowler"],
     "The Executioner's axe pierces through enemies on the way out and back."),
    ("Which troop's arrows fly through every enemy in a straight line?", "Magic Archer", ["Archers", "Princess", "Dart Goblin"],
     "The Magic Archer's arrow travels to its full range, piercing everything it passes."),
    ("Which troop uses a hook to drag enemies towards him, or pull himself to buildings?", "Fisherman", ["Lumberjack", "Bandit", "Executioner"],
     "The Fisherman's hook pulls troops in, or pulls him to a building."),
    ("Which troop dashes at enemies and cannot be hurt while dashing?", "Bandit", ["Prince", "Battle Ram", "Royal Ghost"],
     "The Bandit is immune to damage during her dash."),
    ("Which card has a rider who throws snares that slow troops by 70%?", "Ram Rider", ["Battle Ram", "Hog Rider", "Royal Hogs"],
     "The Ram Rider's rider snares troops while the ram charges buildings."),
    ("Which troop zaps and stuns any enemy that hits it from close range?", "Electro Giant", ["Giant", "Electro Wizard", "Sparky"],
     "Enemies hitting the Electro Giant from within 3 tiles get zapped and stunned."),
    ("Which troop slowly charges up one huge blast, but has its charge reset by Zap?", "Sparky", ["Electro Wizard", "Executioner", "Bowler"],
     "Sparky charges up over time, and any stun resets her."),
    ("Destroying which card gives your opponent Elixir?", "Elixir Golem", ["Golem", "Elixir Collector", "Ice Golem"],
     "Each part of the Elixir Golem gives the opponent Elixir when destroyed: 1 for the Golem and 0.5 for each smaller part."),
    ("How often does the Elixir Collector make 1 Elixir?", "Every 15 seconds", ["Every 5 seconds", "Every 10 seconds", "Every 30 seconds"],
     "It makes 1 Elixir every 15 seconds, and 1 more when destroyed."),
    ("Which spell makes fragile copies of your troops?", "Clone", ["Mirror", "Rage", "Tornado"], "Clone duplicates every friendly troop in its area, with 1 hitpoint each."),
    ("Which card copies the last card you played, for 1 more Elixir?", "Mirror", ["Clone", "Rage", "Royal Delivery"], "Mirror replays your last card at +1 Elixir."),
    ("Which troop blocks attacks from melee troops and strikes back for double damage?", "Ronin", ["Knight", "Monk", "Golden Knight"],
     "The Ronin, added in July 2026, blocks melee attacks and hits back for double damage every 3.5 seconds."),
    ("Which troop turns into a fast, building-charging bomber once it drops below half health?", "Goblin Demolisher", ["Goblin Giant", "Wall Breakers", "Goblin Machine"],
     "Below 50% hitpoints the Goblin Demolisher charges at the nearest building."),
    ("Which card costs 6 Elixir as a flying form, or 3 as a ground form, depending on your Elixir?", "Spirit Empress", ["Phoenix", "Mother Witch", "Little Prince"],
     "With 6 or more Elixir you get the flying form; with less you get the 3-Elixir ground form."),
    ("Which spell deals more damage the fewer troops are inside it?", "Void", ["Poison", "Goblin Curse", "Vines"],
     "The Void splits its damage between troops in its area, so a lone target takes the most."),
    ("Which spell traps the three highest-hitpoint troops in its area?", "Vines", ["Freeze", "Tornado", "Void"],
     "Vines grab the three troops with the most hitpoints and hold them in place."),
    ("Which giant buffs up to two of your other troops so that every 3rd attack hits harder?", "Rune Giant", ["Goblin Giant", "Electro Giant", "Royal Giant"],
     "The Rune Giant throws enchantments on up to two allied troops."),
    ("Which troop carries a rocket launcher with a blind spot close to it?", "Goblin Machine", ["Goblin Giant", "Goblin Demolisher", "Cannon Cart"],
     "The Goblin Machine's rocket launcher can't hit enemies inside its blind spot."),
    ("Which tower troop throws pancakes that level up one of your troops?", "Royal Chef", ["Tower Princess", "Cannoneer", "Dagger Duchess"],
     "About every 23 seconds the Royal Chef throws a pancake that gives a troop +1 level."),
    ("Which troop pushes enemies back with every 3rd hit of its combo, even ones that normally can't be knocked back?", "Monk",
     ["Golden Knight", "Valkyrie", "Knight"], "The Monk's 3-hit combo ends with a big knockback strike."),
    ("When do Champion cards come back into your hand?", "Only after they are defeated", ["After every 4 cards you play", "After 30 seconds", "Never in the same battle"],
     "A Champion stays out of your cycle while on the arena and only returns once defeated."),
]
for q, a, o, x in MECH:
    if a:
        add("mech", "mech:" + q, q, a, o, x, key(a) if a in C else None)

# ================================================================== Evolutions
EVO = {n: c["evo"] for n, c in C.items() if "evo" in c}
EL = D["evolist"]
evodate = {n: date(e["released"]) for n, e in EVO.items() if date(e["released"])}
for n, e in EVO.items():
    qt = mask(e["quote"], n)
    opts = qt and desc_opts(n, qt, list(EVO))
    if opts:
        add("evoquote", f"evoquote:{n}", f"Which card's Evolution has this in-game description?\n{qt}", n, opts,
            f"Evolved {n}" + (f", added on {fmt(evodate[n])}." if n in evodate else "."), key(n))
    cyc = EL.get(n, {}).get("n")
    if cyc in ("1", "2") and (not e["cycles"] or e["cycles"] == cyc):
        nxt = "every other time" if cyc == "1" else "every third time"
        add("evocycles", f"evocycles:{n}", f"How many cycles does {'the ' if not n.startswith('The ') else ''}{n} Evolution need?", f"{cyc} cycle" + ("s" if cyc != "1" else ""),
            [o for o in ("1 cycle", "2 cycles", "3 cycles", "4 cycles") if not o.startswith(cyc)],
            f"Evolved {n} needs {cyc} cycle{'s' if cyc != '1' else ''}, so it comes up {nxt} you play the card.", key(n))
    if n in evodate:
        y = evodate[n].year
        add("evoyear", f"evoyear:{n}", f"In which year did {the(n, True)} get its Evolution?", y, [v for v in (2022, 2023, 2024, 2025, 2026, 2027) if v != y][:5][::1],
            f"Evolved {n} came out on {fmt(evodate[n])}.", key(n))
noevo = [n for n in CARDS if n not in EVO and C[n]["date"].year <= 2022 and C[n]["rarity"] != "Champion"]
for n in sorted(EVO, key=lambda m: rng.random())[:30]:
    add("evohas", f"evohas:{n}", "Which of these cards has an Evolution?", n, pick(similar(n, noevo)), f"{n} has an Evolution.", key(n))
tries = 0
evd = sorted(evodate)
while len(Q["evofirst"]) < 14 and tries < 5000:
    tries += 1
    four = rng.sample(evd, 4)
    ds = sorted(evodate[m] for m in four)
    if any((b - a).days < 120 for a, b in zip(ds, ds[1:])):
        continue
    first = min(four, key=lambda m: evodate[m])
    add("evofirst", "evofirst:" + "|".join(sorted(four)), "Which of these Evolutions came out first?", first, [m for m in four if m != first],
        " · ".join(f"{m} {evodate[m]:%B %Y}" for m in sorted(four, key=lambda m: evodate[m])) + ".", key(*four))
FIRST4 = [n for n in EVO if evodate.get(n) == datetime.date(2023, 6, 19)]
assert sorted(FIRST4) == ["Barbarians", "Firecracker", "Royal Giant", "Skeletons"], FIRST4
later = [n for n in EVO if n in evodate and evodate[n].year >= 2024]
for n in FIRST4:
    add("evofact", f"evofact:first:{n}", "Which of these was one of the first four Card Evolutions, in June 2023?", n, pick(later),
        "The first four Evolutions, on 19 June 2023, were Barbarians, Royal Giant, Firecracker and Skeletons.", key(n) + ["t:evo2023"])
EVO_FACTS = [
    ("How many Evolution Shards does it take to unlock a card's Evolution?", "6", ["3", "10", "20"],
     "Every Evolution takes 6 Evolution Shards (or Wild Shards)."),
    ("What does the number of 'cycles' for an Evolution mean?", "How many times you play the card before it evolves", ["How many Elixir it costs extra", "How many levels it gains", "How many seconds it lasts"],
     "With 2 cycles, every third time you play the card it comes out evolved."),
    ("Which shards can be used on any card's Evolution?", "Wild Shards", ["Hero Shards", "Star Shards", "Crown Shards"],
     "Wild Shards work for any card with an Evolution."),
    ("Which of these Evolutions gets 50% more hitpoints than the normal card?", "Bats", ["Knight", "Barbarians", "Skeletons"],
     "Evolved Bats get +50% hitpoints and heal past their maximum."),
    ("Which Evolution gets 1 extra tile of range?", "Archers", ["Musketeer", "Princess", "Dart Goblin"], "Evolved Archers get +1 tile range."),
    ("Which Evolution brings a Skeleton General along with the army?", "Skeleton Army", ["Skeletons", "Graveyard", "Skeleton Barrel"],
     "Evolved Skeleton Army comes with a Skeleton General."),
    ("Which Evolution throws a net that stuns the closest troop, and grounds flying ones?", "Hunter", ["Fisherman", "Princess", "Executioner"],
     "Evolved Hunter's net traps a troop, pulling fliers to the ground."),
]
for q, a, o, x in EVO_FACTS:
    add("evofact", "evofact:" + q, q, a, o, x, key(a) if a in C else None, extra={"r": 1} if max(len(s) for s in [a] + o) > 24 else None)
# ================================================================== Heroes and Champions
HL = D["herolist"]
heroes = sorted(set(HL) | {n for n in C if "hero" in C[n]})
abil = {n: HL[n]["ability"] for n in HL}
for n in HL:
    a = abil[n]
    add("heroab", f"heroab:{n}", f"Which card's Hero version has the ability \"{a}\"?", n, pick(similar(n, heroes)),
        f"Hero {n}'s ability is {a}: {HL[n]['desc']}", key(n))
    d = mask(HL[n]["desc"], n)
    opts = d and desc_opts(n, d, heroes)
    if opts:
        add("herodesc", f"herodesc:{n}", f"Which Hero has this ability?\n{d}", n, opts, f"Hero {n}: {a}.", key(n))
    sub = C[n].get("hero", {})
    if sub.get("abilityCost") and sub["abilityCost"] == HL[n]["n"]:
        v = int(HL[n]["n"])
        add("herocost", f"herocost:{n}", f"How much Elixir does Hero {n}'s ability cost?", v, [o for o in (1, 2, 3, 4, 5) if o != v][:4],
            f"Hero {n}: {C[n]['cost']} Elixir to play, plus {v} for {a}.", key(n))
nohero = [n for n in CARDS if n not in heroes and C[n]["rarity"] != "Champion" and C[n]["date"].year <= 2022]
for n in heroes:
    add("herohas", f"herohas:{n}", "Which of these cards has a Hero version?", n, pick(similar(n, nohero)), f"{n} has a Hero version.", key(n))
    qt = mask(C[n].get("hero", {}).get("quote", ""), n)
    opts = qt and desc_opts(n, qt, heroes)
    if opts:
        add("heroquote", f"heroquote:{n}", f"Which Hero has this in-game description?\n{qt}", n, opts, f"Hero {n}.", key(n))
first_heroes = sorted(n for n in heroes if date(C[n].get("hero", {}).get("released", "")) == datetime.date(2025, 12, 1))
assert first_heroes == ["Giant", "Knight", "Mini P.E.K.K.A.", "Musketeer"], first_heroes
add("herofact", "herofact:first", "Which four cards got the very first Hero versions, in December 2025?", "Knight, Giant, Mini P.E.K.K.A. and Musketeer",
    ["Knight, Archers, Giant and Wizard", "Valkyrie, Wizard, Bowler and Balloon", "Goblins, Mega Minion, Ice Golem and Wizard"],
    "Heroes arrived on 1 December 2025 with the Knight, Giant, Mini P.E.K.K.A. and Musketeer.", extra={"r": 1})
champab = {n: C[n]["ability"] for n in champs if C[n]["ability"]}
for n, ab in champab.items():
    add("champab", f"champab:{n}", f"What is the {n}'s ability called?", ab["name"], pick([v["name"] for m, v in champab.items() if m != n]),
        f"{n}: {ab['name']}. {ab['desc']}", key(n))
    d = mask(ab["desc"], n)
    opts = d and desc_opts(n, d, [m for m in champab])
    if opts:
        add("champdesc", f"champdesc:{n}", f"Which Champion's ability does this?\n{d}", n, opts, f"{n}: {ab['name']}.", key(n))
    v = int(C[n]["abilityCost"])
    add("champcost", f"champcost:{n}", f"How much Elixir does the {n}'s ability cost?", v, [o for o in (1, 2, 3, 4) if o != v],
        f"{n}: {C[n]['cost']} Elixir to play, and {v} for {ab['name']}.", key(n))
HERO_FACTS = [
    ("Which Champion was added in March 2022, after the first three?", "Mighty Miner", ["Monk", "Little Prince", "Goblinstein"],
     "The Mighty Miner came out on 30 March 2022, five months after the Archer Queen, Golden Knight and Skeleton King."),
    ("Which three Champions arrived together when Champions were added in October 2021?", "Archer Queen, Golden Knight and Skeleton King",
     ["Archer Queen, Monk and Mighty Miner", "Golden Knight, Little Prince and Monk", "Skeleton King, Goblinstein and Boss Bandit"],
     "Champions launched on 27 October 2021 with the Archer Queen, Golden Knight and Skeleton King."),
    ("What is the name of the Little Prince's bodyguard?", "Guardienne", ["Guinevere", "Gertrude", "Galahad"], "Guardienne charges in with the Royal Rescue ability."),
]
for q, a, o, x in HERO_FACTS:
    add("herofact", "herofact:" + q, q, a, o, x, (key(a) if a in C else []) + topic(q) or None, extra={"r": 1} if max(len(s) for s in [a] + o) > 24 else None)

# ================================================================== History
dated = [n for n in CARDS if C[n]["date"] > datetime.date(2016, 3, 2)]
for n in dated:
    y = C[n]["date"].year
    opts = sorted((v for v in range(2016, 2027) if v != y), key=lambda v: (abs(v - y), rng.random()))[:3]
    add("year", f"year:{n}", f"In which year was {the(n, True)} added to Clash Royale?", y, opts, summary(n), key(n))
og = [n for n in CARDS if C[n]["date"] == LAUNCH]
late = [n for n in CARDS if C[n]["date"].year >= 2017]
for n in rng.sample(og, 18):
    add("launch", f"launch:{n}", "Which of these cards has been in Clash Royale since the very beginning?", n, pick(similar(n, late)),
        f"{n} was one of the launch cards; the others came later.", key(n))
for kind, fn, word in (("first", min, "came out first"), ("newest", max, "is the newest")):
    tries = 0
    while len(Q[kind]) < 18 and tries < 5000:
        tries += 1
        four = rng.sample(CARDS, 4)
        ds = sorted(C[m]["date"] for m in four)
        if any((b - a).days < 300 for a, b in zip(ds, ds[1:])):
            continue
        top = fn(four, key=lambda m: C[m]["date"])
        add(kind, f"{kind}:" + "|".join(sorted(four)), f"Which of these cards {word}?", top, [m for m in four if m != top],
            " · ".join(f"{m} {C[m]['date']:%B %Y}" if C[m]["date"] != LAUNCH else f"{m} at launch" for m in sorted(four, key=lambda m: C[m]["date"])) + ".",
            key(*four))

# ================================================================== Game facts
FACTS = [
    ("Which company makes Clash Royale?", "Supercell", ["Rovio", "King", "Riot Games"], "Supercell also makes Clash of Clans, Brawl Stars and Hay Day."),
    ("In which country is Supercell based?", "Finland", ["Sweden", "Denmark", "Norway"], "Supercell is based in Helsinki, Finland."),
    ("In which year did Clash Royale come out worldwide?", "2016", ["2014", "2015", "2017"],
     "It launched worldwide on 2 March 2016, after a soft launch in some countries that January."),
    ("Which game do Clash Royale's troops come from?", "Clash of Clans", ["Brawl Stars", "Boom Beach", "Hay Day"],
     "Clash Royale is a spin-off of Clash of Clans, with many of the same characters."),
    ("How much Elixir do you start a battle with?", "5", ["3", "7", "10"], "You start with 5 Elixir and can hold up to 10."),
    ("What is the most Elixir you can hold at once?", "10", ["8", "12", "15"], "Elixir stops filling at 10."),
    ("In normal time, how long does it take to make 1 Elixir?", "2.8 seconds", ["1.4 seconds", "2 seconds", "4 seconds"],
     "1 Elixir every 2.8 seconds, every 1.4 seconds in Double Elixir."),
    ("How long is a battle before it goes to overtime?", "3 minutes", ["2 minutes", "4 minutes", "5 minutes"], "Regular time is 3 minutes."),
    ("When does Double Elixir start in a normal battle?", "With 1 minute left", ["Straight away", "With 2 minutes left", "Only in overtime"],
     "Double Elixir kicks in once 2 of the 3 minutes have passed."),
    ("What comes after Double Elixir if overtime keeps going?", "Triple Elixir", ["Quadruple Elixir", "Sudden Death", "Infinite Elixir"],
     "Once 4 minutes have passed, Elixir is tripled for the rest of the battle."),
    ("How much slower is Elixir in 2v2 battles?", "30% slower", ["10% slower", "50% slower", "It's the same speed"],
     "2v2 Elixir comes 30% slower, because there are two players' worth of cards on each side."),
    ("How many cards are in a battle deck?", "8", ["6", "10", "12"], "A deck has 8 cards."),
    ("How many cards can you choose from in your hand during a battle?", "4", ["3", "5", "6"], "You hold 4 cards, with the next one shown beside them."),
    ("How many crowns do you get for destroying the King's Tower?", "3", ["1", "2", "4"], "Taking down the King's Tower gives all 3 crowns and wins the battle."),
    ("What are the two smaller towers on each side called?", "Princess Towers", ["Knight Towers", "Archer Towers", "Crown Guards"],
     "Two Princess Towers guard the King's Tower."),
    ("What is the big tower in the middle called?", "King's Tower", ["Royal Tower", "Crown Keep", "Castle Tower"], "The King's Tower sits in the middle."),
    ("If a battle is still tied when overtime ends, what decides it?", "Towers drain until the weakest one falls", ["A coin toss", "Whoever has more Elixir",
     "Whoever played fewer cards"], "In the tiebreaker, every tower loses health until the one with the lowest health is destroyed."),
    ("Which tower troop does everyone start with?", "Tower Princess", ["Cannoneer", "Dagger Duchess", "Royal Chef"], "The Tower Princess is unlocked in the Training Camp."),
    ("Which tower troop has the most hitpoints?", "Tower Princess", ["Cannoneer", "Dagger Duchess", "Royal Chef"],
     "The Tower Princess has the highest hitpoints of the tower troops."),
    ("How many tiles wide is the arena?", "18", ["14", "22", "26"], "The arena is 18 tiles wide and 32 tiles long."),
    ("How many tiles long is the arena?", "32", ["24", "28", "40"], "The arena is 32 tiles long and 18 tiles wide."),
    ("How many bridges cross the river?", "2", ["1", "3", "4"], "One bridge in each lane."),
    ("What is Clash Royale's season pass called?", "Pass Royale", ["Royal Pass", "Crown Pass", "Battle Pass"], "Pass Royale started in July 2019."),
    ("Which mode is an auto-battler where you buy and merge troops on a board?", "Merge Tactics", ["Touchdown", "Mega Draft", "Triple Draft"],
     "Merge Tactics unlocks in Goblin Stadium (Arena 1)."),
    ("In which mode do you score by getting a troop into the enemy's end zone?", "Touchdown", ["Merge Tactics", "Heist", "Draft"],
     "Touchdown has no towers: a troop that reaches the end zone scores a crown."),
    ("How many members can a clan have?", "50", ["30", "40", "100"], "A clan holds up to 50 players."),
    ("Which card costs 9 Elixir, the most of any card?", "Three Musketeers", ["Golem", "Mega Knight", "Electro Giant"], "Golem is next at 8."),
    ("Which rarity was added in October 2021?", "Champion", ["Legendary", "Mythic", "Hero"], "Champions arrived in the Champions Update on 27 October 2021."),
    ("Which of these cards was added the latest?", "Minion Giant", ["Ronin", "Spirit Empress", "Vines"],
     "Minion Giant came out on 5 September 2026, after the Ronin (July 2026), Spirit Empress (July 2025) and Vines (September 2025)."),
    ("In November 2025, the highest card level went up to what?", "16", ["14", "15", "20"], "The Level 16 Update came out on 24 November 2025."),
    ("Which update added the very first Card Evolutions?", "The Card Evolution Update, June 2023", ["The Champions Update, October 2021",
     "The Tower Troop Update, December 2023", "The Level 16 Update, November 2025"], "The Card Evolution Update came out on 19 June 2023."),
    ("When did the Tower Troop Update let you swap the Tower Princess for other tower troops?", "December 2023", ["June 2023", "October 2021", "March 2016"],
     "The Tower Troop Update came out on 13 December 2023, and the Cannoneer arrived on 1 January 2024."),
]
for q, a, o, x in FACTS:
    add("fact", "fact:" + q, q, a, o, x, (key(a) if a in C else []) + topic(q) or None, extra={"r": 1} if max(len(s) for s in [a] + o) > 24 else None)
for n in TOWERS:
    c = C[n]
    add("tower", f"tower:{n}", f"In which arena do you unlock the {n} tower troop?", alabel(c["arena"]),
        [alabel(C[m]["arena"]) for m in TOWERS if C[m]["arena"] != c["arena"]] + [alabel("Jungle Arena")], summary(n), key(n))

# ================================================================== balance: each group to its target, sharing it between question types by weight
WEIGHT = {"cost": 4, "costmost": 1, "costleast": 1, "costone": 0.4, "rarity": 4, "champpick": 0.6, "rarpick": 1,
          "arena": 4, "arenanum": 1, "arenatro": 1, "arenanext": 0.8, "camp": 0.5, "arenafact": 1,
          "speed": 3, "target": 3, "count": 1.5, "range": 1.5, "hitspeed": 0.8, "hp": 2, "dmg": 1, "air": 1, "spellground": 0.6, "radius": 0.6,
          "life": 0.8, "deploy": 0.3, "type": 1, "spelltime": 0.6, "spellhit": 0.6,
          "year": 4, "launch": 1, "first": 1, "newest": 1, "evoquote": 3, "evocycles": 1.5, "evohas": 1.5, "evoyear": 2, "evofirst": 1,
          "evofact": 1, "fact": 4, "tower": 0.5}
if "--avail" in sys.argv:
    for g in TARGET:
        print(f"{g:20} " + ", ".join(f"{k} {len(Q[k])}" for k in Q if GROUP[k] == g), "=", sum(len(Q[k]) for k in Q if GROUP[k] == g))
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
    assert len(got) == want, g
    out += got
ONE_PER_GAME = {"costmost", "costleast", "costone", "champpick", "rarpick", "camp", "hp", "dmg", "air", "spellground", "radius", "type", "spellhit",
                "launch", "first", "newest", "evohas", "evofirst", "herohas", "jump", "deploy", "life", "spelltime", "evocycles", "herocost",
                "champcost", "arenatro", "arenanum", "arenanext", "hitspeed", "range", "count", "spawncount", "evoyear"}
for q in out:
    if q["c"] in ONE_PER_GAME:
        q["ks"] = (q.get("ks") or [q["k"]]) + ["kind:" + q["c"]]
missing = [k for k in Q if k not in GROUP]
assert not missing, missing
for q in out:
    assert len(q["o"]) == 3 and q["a"] not in q["o"], q
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
print(len(out), "questions")
