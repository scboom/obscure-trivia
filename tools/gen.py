import sys, json, re, random, collections
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, clean_text

cards, byd, byid = load(sys.argv[1])
OUT = sys.argv[2]
rng = random.Random(20261120)

RACE = {14: "Murloc", 15: "Demon", 17: "Mech", 18: "Elemental", 20: "Beast", 23: "Pirate",
        24: "Dragon", 43: "Quilboar", 92: "Naga", 11: "Undead", 126: "Aberration"}
SUBSET = {"BEAST": "Beast", "DEMON": "Demon", "DRAGON": "Dragon", "ELEMENTALS": "Elemental", "MECH": "Mech",
          "MURLOC": "Murloc", "NAGA": "Naga", "PIRATE": "Pirate", "QUILLBOAR": "Quilboar", "UNDEAD": "Undead",
          "ABERRATION": "Aberration"}
ALL_TYPES = sorted(set(RACE.values()))

def plain(t):
    return re.sub(r"<[^>]+>", "", t or "")

def mask(text, name, repl):
    if not text or not name: return text
    return re.sub(re.escape(name) + r"s?\b", repl, text)

STOP = {"tavern", "golden", "minion", "minions", "battlegrounds", "the", "of", "and"}
def giveaway(name, text):
    """True when a distinctive word from the name appears in the answer text."""
    words = [w.lower() for w in re.findall(r"[A-Za-z']{5,}", name) if w.lower() not in STOP]
    low = plain(text).lower()
    return any(w in low for w in words)

def text_of(c, self_name, repl):
    t = clean_text(c)
    if not t: return None
    if self_name and self_name in plain(t) and repl == "this minion": return None
    t = mask(t, self_name, repl)
    if not t or len(plain(t)) > 230: return None
    return t

# ---------------------------------------------------------------- entities
pool = [c for c in cards if c["tags"].get("IS_BACON_POOL_MINION") == 1 and not c["tags"].get("PREMIUM")]
pool_names = {c["CARDNAME"] for c in pool}

def minion_types(c):
    r = c["tags"].get("CARDRACE")
    subs = sorted(SUBSET[k[13:]] for k in c["tags"] if k.startswith("BACON_SUBSET_") and k[13:] in SUBSET and c["tags"][k])
    if r is None:
        return ["No type"] if not subs else None
    if r not in RACE: return None
    if subs == [RACE[r]]: return [RACE[r]]
    if len(subs) == 2 and RACE[r] in subs: return subs
    return None

retired = []
seen = set()
for c in cards:
    t = c["tags"]
    if (t.get("CARDTYPE") == 4 and t.get("TECH_LEVEL") and t.get("BACON_TRIPLE_UPGRADE_MINION_ID")
            and not t.get("IS_BACON_POOL_MINION") and not t.get("PREMIUM")
            and c["CARDNAME"] not in pool_names and c["id"].startswith(("BG", "TB_BaconShop", "BGS"))
            and "_Buddy" not in c["id"] and "Giant" not in c["id"] and not c["CARDNAME"].startswith("Timewarped")
            and not re.search(r"t\d*$", c["id"].split("_")[-1]) and c["CARDNAME"] not in seen):
        seen.add(c["CARDNAME"])
        retired.append(c)

heroes = [c for c in cards if c["tags"].get("BACON_HERO_CAN_BE_DRAFTED") == 1 and c.get("CARDNAME")]

trinkets = []
tn = collections.Counter()
for c in cards:
    if c["tags"].get("CARDTYPE") == 44 and c["tags"].get("BACON_TRINKET") == 1 and c.get("CARDNAME"):
        kind = {11: "Lesser", 12: "Greater"}.get(c["tags"].get("SPELL_SCHOOL"))
        if kind:
            trinkets.append((c, kind)); tn[c["CARDNAME"]] += 1

spells = [c for c in cards if c["tags"].get("IS_BACON_POOL_SPELL") == 1 and c.get("CARDNAME")]
anomalies, an_seen = [], set()
for c in cards:
    if c["tags"].get("CARDTYPE") == 43 and c.get("CARDNAME") and c["CARDNAME"] not in an_seen:
        an_seen.add(c["CARDNAME"]); anomalies.append(c)
rewards, qr_seen = [], collections.Counter(c["CARDNAME"] for c in cards if c["tags"].get("CARDTYPE") == 40)
rewards = [c for c in cards if c["tags"].get("CARDTYPE") == 40 and qr_seen[c["CARDNAME"]] == 1]

# ---------------------------------------------------------------- helpers
Q = collections.defaultdict(list)

BADNAME = re.compile(r"[\[\]{}<>]")
def add(cat, key, q, a, opts, tag=None, rich=False):
    if not rich and (BADNAME.search(a) or any(BADNAME.search(o) for o in opts)): return
    if BADNAME.search(q.split("\n")[0]): return
    opts = [o for o in opts if o != a]
    if len(set(opts)) < len(opts): return
    if len(opts) not in (1, 3): return
    rec = {"c": cat, "k": key, "q": q, "a": a, "o": opts}
    if tag: rec["t"] = tag
    if rich: rec["r"] = 1
    Q[cat].append(rec)

def num_opts(v, lo, hi, spread=3):
    hi = max(hi, v + spread)
    cand = [x for x in range(max(lo, v - spread), min(hi, v + spread) + 1) if x != v]
    rng.shuffle(cand)
    return cand[:3]

def stat_opts(a, h):
    cand = {(a + 1, h), (a, h + 1), (a - 1, h), (a, h - 1), (a + 1, h + 1), (a - 1, h + 1), (a + 1, h - 1),
            (h, a), (a + 2, h), (a, h + 2), (a + 2, h + 2)}
    cand = [x for x in cand if x != (a, h) and x[0] >= 0 and x[1] >= 1]
    rng.shuffle(cand)
    return ["%d/%d" % x for x in cand[:3]]

def pick_texts(correct, pool_texts, n=3):
    """Pick n distractor texts that differ from the correct one."""
    cp = plain(correct).lower()
    cand = [t for t in dict.fromkeys(pool_texts) if plain(t).lower() != cp]
    rng.shuffle(cand)
    return cand[:n] if len(cand) >= n else None

def pick_names(correct, names, n=3):
    cand = [x for x in dict.fromkeys(names) if x != correct]
    rng.shuffle(cand)
    return cand[:n] if len(cand) >= n else None

# ---------------------------------------------------------------- minions
mtext = {c["dbf"]: text_of(c, c["CARDNAME"], "this minion") for c in pool + retired}
by_tier = collections.defaultdict(list)
for c in pool: by_tier[c["tags"]["TECH_LEVEL"]].append(c)

for c in pool:
    t, n = c["tags"], c["CARDNAME"]
    tier, atk, hp = t["TECH_LEVEL"], t.get("ATK", 0), t.get("HEALTH", 1)
    key = "m:" + n
    duo = "Duos only" if t.get("IS_BACON_DUOS_EXCLUSIVE") else None
    others = [x for x in range(1, 8) if x != tier]
    others.sort(key=lambda x: (abs(x - tier) + rng.random() * 2.5))
    add("tier", key, rng.choice(["What Tavern Tier is %s?", "%s: which Tavern Tier is it in?",
                                 "Which Tavern Tier do you find %s on?"]) % n,
        "Tier %d" % tier, ["Tier %d" % x for x in others[:3]], duo)
    add("stats", key, rng.choice(["What are the base stats of %s?", "What are %s's base stats?",
                                  "%s: what are its base Attack and Health?"]) % n,
        "%d/%d" % (atk, hp), stat_opts(atk, hp), duo)
    ty = minion_types(c)
    if ty:
        ans = " + ".join(ty)
        if len(ty) == 2:
            pairs = set()
            while len(pairs) < 3:
                p = tuple(sorted(rng.sample(ALL_TYPES, 2)))
                if list(p) != ty: pairs.add(" + ".join(p))
            add("type", key, "%s has two minion types. Which two?" % n, ans, list(pairs), duo)
        else:
            pool_t = [x for x in ALL_TYPES + ["No type"] if x != ans]
            rng.shuffle(pool_t)
            add("type", key, rng.choice(["What minion type is %s?", "Which minion type does %s have?"]) % n,
                ans, pool_t[:3], duo)
    tx = mtext[c["dbf"]]
    if tx and not giveaway(n, tx):
        same = [mtext[o["dbf"]] for o in by_tier[tier] + by_tier.get(tier + 1, []) + by_tier.get(tier - 1, [])
                if o["dbf"] != c["dbf"] and mtext[o["dbf"]]]
        ds = pick_texts(tx, same)
        if ds:
            add("effect", key, "What does %s do?" % n, tx, ds, "Tier %d" % tier, rich=True)
        names = [o["CARDNAME"] for o in by_tier[tier] + by_tier.get(tier + 1, []) if o["dbf"] != c["dbf"]
                 and (mtext[o["dbf"]] or "") != tx]
        ds = pick_names(n, names)
        if ds and sum(1 for o in pool if mtext[o["dbf"]] == tx) == 1:
            add("whois", key, "Which Tier %d minion has this text?\n%s" % (tier, tx), n, ds, rich=True)
    g = byd.get(t.get("BACON_TRIPLE_UPGRADE_MINION_ID"))
    if g and g["tags"].get("PREMIUM") and g["tags"].get("ATK") is not None:
        ga, gh = g["tags"].get("ATK", 0), g["tags"].get("HEALTH", 1)
        add("golden", key, "What are the stats of a Golden %s?" % n, "%d/%d" % (ga, gh), stat_opts(ga, gh), duo)

for c in retired:
    t, n = c["tags"], c["CARDNAME"]
    key = "m:" + n
    atk, hp = t.get("ATK", 0), t.get("HEALTH", 1)
    add("oldstats", key, "%s has rotated out of the Tavern. What were its base stats?" % n, "%d/%d" % (atk, hp),
        stat_opts(atk, hp), "Rotated out")
    tx = mtext[c["dbf"]]
    if tx and not giveaway(n, tx):
        ds = pick_texts(tx, [mtext[o["dbf"]] for o in retired if o["dbf"] != c["dbf"] and mtext[o["dbf"]]])
        if ds:
            add("oldeffect", key, "What did %s do?" % n, tx, ds, "Rotated out", rich=True)

duos = [c for c in pool if c["tags"].get("IS_BACON_DUOS_EXCLUSIVE")]
solo = [c["CARDNAME"] for c in pool if not c["tags"].get("IS_BACON_DUOS_EXCLUSIVE")]
for c in duos:
    add("duos", "m:" + c["CARDNAME"], "Which of these minions only shows up in Duos?", c["CARDNAME"],
        rng.sample(solo, 3))

# ---------------------------------------------------------------- heroes
hp_of, bud_of = {}, {}
for h in heroes:
    hp = byd.get(h["tags"].get("HERO_POWER"))
    if hp and hp.get("CARDNAME"): hp_of[h["CARDNAME"]] = hp
    b = byd.get(h["tags"].get("BACON_COMPANION_ID"))
    if b and b.get("CARDNAME"): bud_of[h["CARDNAME"]] = b
hero_names = [h["CARDNAME"] for h in heroes]
hp_names = collections.Counter(hp["CARDNAME"] for hp in hp_of.values())
bud_names = collections.Counter(b["CARDNAME"] for b in bud_of.values())
hptext = {n: text_of(hp, n, "your hero") for n, hp in hp_of.items()}

for h in heroes:
    n, t = h["CARDNAME"], h["tags"]
    key = "h:" + n
    arm, duo_arm = t.get("ARMOR"), t.get("E3206")
    if arm is not None and t.get("HEALTH") == 30:
        add("armor", key, rng.choice(["How much Armor does %s start with in Solo?",
                                      "In Solo Battlegrounds, how much Armor does %s start with?"]) % n,
            str(arm), [str(x) for x in num_opts(arm, 0, 25)])
    if duo_arm is not None and t.get("HEALTH") == 30:
        add("duoarmor", key, rng.choice(["How much Armor does %s have in Duos?",
                                         "In Duos, how much Armor does %s start with?"]) % n,
            str(duo_arm), [str(x) for x in num_opts(duo_arm, 0, 25)], "Duos")
    if t.get("HEALTH") and t["HEALTH"] != 30:
        add("health", key, "How much Health does %s start with?" % n, str(t["HEALTH"]),
            ["30", "40", "50", "60", "45", "35", "20"][:4])
    hp = hp_of.get(n)
    if hp:
        hn = hp["CARDNAME"]
        if hp_names[hn] == 1 and hn != n:
            ds = pick_names(hn, [x for x in hp_names if hp_names[x] == 1])
            if ds: add("hpname", key, "What is %s's Hero Power called?" % n, hn, ds)
            ds = pick_names(n, hero_names)
            if ds and not giveaway(n, hn): add("hpwho", key, "Which hero has the Hero Power “%s”?" % hn, n, ds)
        tx = hptext.get(n)
        if tx:
            ds = pick_texts(tx, [v for k, v in hptext.items() if k != n and v])
            if ds: add("hpeffect", key, "What does %s's Hero Power, %s, do?" % (n, hn), tx, ds, rich=True)
        cost = hp["tags"].get("COST")
        if cost:
            add("hpcost", key, "How much Gold does %s's Hero Power (%s) cost?" % (n, hn), str(cost),
                [str(x) for x in num_opts(cost, 0, 5, 3)])
    b = bud_of.get(n)
    if b and bud_names[b["CARDNAME"]] == 1:
        bn = b["CARDNAME"]
        ds = pick_names(bn, [x for x in bud_names if bud_names[x] == 1])
        if ds: add("buddy", key, "Who is %s's Buddy?" % n, bn, ds)
        ds = pick_names(n, hero_names)
        if ds: add("buddywho", key, "%s is which hero's Buddy?" % bn, n, ds)

# ---------------------------------------------------------------- quest rewards
qtext = {c["dbf"]: text_of(c, None, None) for c in rewards}
for c in rewards:
    n, tx = c["CARDNAME"], qtext[c["dbf"]]
    if not tx or giveaway(n, tx): continue
    others = [qtext[o["dbf"]] for o in rewards if o["dbf"] != c["dbf"] and qtext[o["dbf"]]]
    ds = pick_texts(tx, others)
    if ds: add("quest", "q:" + n, rng.choice(["What does the quest reward %s do?",
                                              "You finish your quest and get %s. What does it do?"]) % n,
               tx, ds, "Quest reward", rich=True)
    ds = pick_names(n, [o["CARDNAME"] for o in rewards if qtext[o["dbf"]] != tx])
    if ds and sum(1 for o in rewards if qtext[o["dbf"]] == tx) == 1:
        add("questwho", "q:" + n, "Which quest reward has this text?\n%s" % tx, n, ds, "Quest reward", rich=True)

# ---------------------------------------------------------------- trinkets
ttext = {c["dbf"]: text_of(c, None, None) for c, _ in trinkets}
for c, kind in trinkets:
    n, tx = c["CARDNAME"], ttext[c["dbf"]]
    key = "t:" + n + kind
    label = "%s Trinket" % kind
    if tx and not giveaway(n, tx):
        ds = pick_texts(tx, [ttext[o["dbf"]] for o, k in trinkets if k == kind and o["dbf"] != c["dbf"] and ttext[o["dbf"]]])
        if ds: add("trinket", key, "What does the %s %s do?" % (label, n), tx, ds, label, rich=True)
    cost = c["tags"].get("COST")
    if cost:
        add("trinketcost", key, "How much Gold does the %s %s cost?" % (label, n), str(cost),
            [str(x) for x in num_opts(cost, 0, 10, 3)], label)
    if tn[n] == 1:
        add("trinketkind", key, "Is %s a Lesser or a Greater Trinket?" % n, "%s Trinket" % kind,
            ["%s Trinket" % ("Greater" if kind == "Lesser" else "Lesser")])

# ---------------------------------------------------------------- tavern spells
stext = {c["dbf"]: text_of(c, None, None) for c in spells}
for c in spells:
    n, t, tx = c["CARDNAME"], c["tags"], stext[c["dbf"]]
    key = "s:" + n
    if t.get("COST") is not None:
        add("spellcost", key, "How much Gold does the Tavern spell %s cost?" % n, str(t["COST"]),
            [str(x) for x in num_opts(t["COST"], 0, 8, 3)], "Tavern spell")
    if t.get("TECH_LEVEL"):
        tier = t["TECH_LEVEL"]
        others = sorted([x for x in range(1, 8) if x != tier], key=lambda x: abs(x - tier) + rng.random() * 2.5)
        add("spelltier", key, "What Tavern Tier is the spell %s?" % n, "Tier %d" % tier,
            ["Tier %d" % x for x in others[:3]], "Tavern spell")
    if tx and not giveaway(n, tx):
        ds = pick_texts(tx, [stext[o["dbf"]] for o in spells if o["dbf"] != c["dbf"] and stext[o["dbf"]]])
        if ds: add("spell", key, "What does the Tavern spell %s do?" % n, tx, ds, "Tavern spell", rich=True)

# ---------------------------------------------------------------- anomalies
atext = {c["dbf"]: text_of(c, None, None) for c in anomalies}
for c in anomalies:
    n, tx = c["CARDNAME"], atext[c["dbf"]]
    if not tx or giveaway(n, tx): continue
    ds = pick_texts(tx, [atext[o["dbf"]] for o in anomalies if o["dbf"] != c["dbf"] and atext[o["dbf"]]])
    if ds: add("anomaly", "a:" + n, rng.choice(["What does the anomaly %s do?",
                                                "The lobby rolls the anomaly %s. What does it do?"]) % n,
               tx, ds, "Anomaly", rich=True)
    ds = pick_names(n, [o["CARDNAME"] for o in anomalies if atext[o["dbf"]] != tx])
    if ds and sum(1 for o in anomalies if atext[o["dbf"]] == tx) == 1:
        add("anomalywho", "a:" + n, "Which anomaly has this text?\n%s" % tx, n, ds, "Anomaly", rich=True)

# ---------------------------------------------------------------- quotas
QUOTA = {"tier": 109, "stats": 105, "type": 70, "effect": 70, "whois": 45, "golden": 25,
         "oldstats": 40, "oldeffect": 25, "duos": 12,
         "armor": 55, "duoarmor": 50, "health": 5, "hpname": 40, "hpwho": 35, "hpeffect": 40, "hpcost": 20,
         "buddy": 35, "buddywho": 20,
         "quest": 35, "questwho": 15,
         "trinket": 35, "trinketcost": 18, "trinketkind": 10,
         "spellcost": 15, "spelltier": 15, "spell": 20,
         "anomaly": 30, "anomalywho": 10}
avail = {k: len(v) for k, v in Q.items()}
print("available:", avail, "total", sum(avail.values()))
final = []
for cat, n in QUOTA.items():
    items = Q.get(cat, [])
    # keep the user's own examples in the bank
    must = [x for x in items if any(s in x["q"] for s in ("Picky Eater", "Partner in Crime", "Nozdormu"))]
    rest = [x for x in items if x not in must]
    rng.shuffle(rest)
    final += (must + rest)[:max(n, len(must))]
print("final", len(final), collections.Counter(x["c"] for x in final))
with open(OUT, "w") as f:
    f.write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in final) + "\n]\n")
