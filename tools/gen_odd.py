"""Build the Odd One Out bank (exactly 1,000 rounds).

Every domain is a table of things and their attributes. A round takes three things that share a value of a rule attribute
and one that doesn't. Before a round is kept, every attribute we know about (plus the first letter and the number of words
in each name) is checked: if any of them would single out a DIFFERENT one of the four, the round is thrown away, so the
odd one out is the only defensible answer.

Tables: the site's own checked data (Clash Royale cards, Dead by Daylight characters, Minecraft mobs and biomes, Hearthstone
Battlegrounds minions, car brands, Premier League and World Cup winners), Wikidata countries, the Animals quiz's animal
table (classes checked against Wikipedia), numbers worked out here, and general-knowledge tables in odd/work/tables.json.
Usage: gen_odd.py SCRATCH_DIR OUT.json [--avail|--show DOMAIN|--loose]
"""
import sys, json, random, re, collections, os

D, OUT = sys.argv[1:3]
rng = random.Random(20261126)
DOMAINS = []


def domain(name, kind, items, attrs, rules, tag=None, per_rule=None, weight=1.0):
    for it in items:
        for a in attrs:
            assert a in it and it[a] is not None, (name, it.get("name"), a)
            assert str(it[a]) in attrs[a]["values"], (name, it["name"], a, it[a])
    DOMAINS.append({"domain": name, "kind": kind, "items": items, "attrs": attrs, "rules": rules, "tag": tag, "weight": weight})


def vals(**kw):
    """value -> [singular phrase (after 'is'), plural phrase (after 'are all')]"""
    return {k: list(v) for k, v in kw.items()}


# ------------------------------------------------------------------ Clash Royale cards
CR = json.load(open(f"{D}/cr/cards.json"))
cr_items = []
for n, c in CR["cards"].items():
    if not re.fullmatch(r"\d+", c.get("cost", "")) or c["type"] not in ("Troop", "Spell", "Building"):
        continue
    cr_items.append({"name": n, "type": c["type"].lower(), "rarity": c["rarity"].lower(), "cost": str(int(c["cost"]))})
domain("Games", "card", cr_items, {
    "type": {"label": "card type", "values": vals(troop=["a troop", "troops"], spell=["a spell", "spells"], building=["a building", "buildings"])},
    "rarity": {"label": "rarity", "values": {r: [f"{'an' if r[0] in 'aeiou' else 'a'} {r.title()} card", f"{r.title()} cards"] for r in {i["rarity"] for i in cr_items}}},
    "cost": {"label": "Elixir cost", "values": {c: [f"a {c}-Elixir card", f"{c}-Elixir cards"] for c in {i["cost"] for i in cr_items}}},
}, ["type", "rarity", "cost"], tag="Clash Royale")

# ------------------------------------------------------------------ Dead by Daylight
DT = json.load(open(f"{D}/dbd/work/dt.json"))
LIC = {x["id"] for x in DT["dlcs"] if x.get("licensed")}
first = lambda v: v[0] if isinstance(v, list) else v
people = []
for k in DT["killers"]:
    if k.get("realName") and " alias " not in k["realName"] and "," not in k["realName"] and "&" not in k["realName"]:
        people.append({"name": k["realName"].replace(" The ", " the "), "role": "killer", "licensed": "yes" if first(k.get("dlc")) in LIC else "no"})
for s in DT["survivors"]:
    nm = s.get("shortName") or s["name"]
    if "&" in nm:
        continue
    people.append({"name": nm, "role": "survivor", "licensed": "yes" if first(s.get("dlc")) in LIC else "no"})
domain("Games", "character", people, {
    "role": {"label": "side", "values": vals(killer=["a Killer", "Killers"], survivor=["a Survivor", "Survivors"])},
    "licensed": {"label": "licensed", "values": vals(yes=["from another franchise", "from other franchises"], no=["an original Dead by Daylight character", "original Dead by Daylight characters"])},
}, ["role"], tag="Dead by Daylight")
kill = [{"name": "The " + k["name"], "licensed": "yes" if first(k.get("dlc")) in LIC else "no",
         "speed": "4.4" if (k["speed"][0] if isinstance(k["speed"], list) else k["speed"]) == 4.4 else "other"} for k in DT["killers"]]
domain("Games", "Killer", kill, {
    "licensed": {"label": "licensed", "values": vals(yes=["from another franchise (licensed)", "from other franchises (licensed)"], no=["an original Dead by Daylight Killer", "original Dead by Daylight Killers"])},
    "speed": {"label": "speed", "values": vals(**{"4.4": ["a 110% speed Killer", "110% speed Killers"], "other": ["not a 110% Killer", "not 110% Killers"]})},
}, ["licensed"], tag="Dead by Daylight")

# ------------------------------------------------------------------ Minecraft (Bedrock data)
MC = json.load(open(f"{D}/mc/mcdata.json"))
mobs = []
CATS = {"Passive mobs": "passive", "Hostile mobs": "hostile"}
# neutral mobs (they only attack when provoked) are left out, so "passive" and "hostile" are never in doubt
NEUTRAL = {"Wolf", "Bee", "Llama", "Trader Llama", "Panda", "Polar Bear", "Dolphin", "Goat", "Iron Golem", "Snow Golem", "Enderman", "Piglin",
           "Zombified Piglin", "Zombie Pigman", "Spider", "Cave Spider", "Pufferfish", "Fox", "Ocelot"}
for e in MC["ents"]:
    if e.get("c") in CATS and e["t"] in ("animal", "hostile", "mob", "passive", "ambient", "water_creature") and e["d"] not in NEUTRAL:
        mobs.append({"name": e["d"], "cat": CATS[e["c"]]})
domain("Games", "mob", mobs, {"cat": {"label": "behaviour", "values": vals(passive=["a passive mob", "passive mobs"], hostile=["a hostile mob", "hostile mobs"])}},
       ["cat"], tag="Minecraft")
bio = [{"name": b["n"].replace("_", " ").title().replace(" Of ", " of ").replace(" The ", " the "), "dim": b["dim"]} for b in MC["biomes"]]
if False: domain("Games", "biome", bio, {"dim": {"label": "dimension", "values": vals(overworld=["an Overworld biome", "Overworld biomes"], nether=["a Nether biome", "Nether biomes"], the_end=["an End biome", "End biomes"], end=["an End biome", "End biomes"])}},
       ["dim"], tag="Minecraft", weight=0.6)

# ------------------------------------------------------------------ car brands (the Cars quiz's checked table)
src = open(f"{D}/scripts/gen_cars.py").read()
BR = eval(src[src.index("BRANDS = {") + len("BRANDS = "):src.index("\n}\n", src.index("BRANDS = {")) + 2])
cars = [{"name": b, "country": c, "owner": o or "independent"} for b, (c, t, o) in BR.items() if c]
CN = {"USA": "American", "UK": "British", "Japan": "Japanese", "Germany": "German", "Italy": "Italian", "France": "French", "South Korea": "South Korean",
      "Sweden": "Swedish", "Czech Republic": "Czech", "Spain": "Spanish", "Romania": "Romanian", "Croatia": "Croatian", "Russia": "Russian",
      "India": "Indian", "Malaysia": "Malaysian", "Australia": "Australian", "China": "Chinese"}
domain("Cars", "car brand", cars, {
    "country": {"label": "country", "values": {c: [f"a{'n' if CN[c][0] in 'AEIOU' else ''} {CN[c]} brand", f"{CN[c]} brands"] for c in {x["country"] for x in cars}}},
    "owner": {"label": "owner", "values": {o: ([f"owned by {o}", f"owned by {o}"] if o != "independent" else ["(independent)", "(independent)"]) for o in {x["owner"] for x in cars}}},
}, ["country", "owner"])

# ------------------------------------------------------------------ football: Premier League and World Cup winners (data up to 2025-26 and 2026)
PL = json.load(open(f"{D}/football/pl.json"))
champs, clubs = set(), collections.Counter()
for s, v in PL.items():
    if s == max(PL):                                  # the season being played now
        continue
    champs.add(v["table"][0][0])
    for row in v["table"]:
        clubs[row[0]] += 1
pl = [{"name": c, "won": "yes" if c in champs else "no"} for c, n in clubs.items() if n >= 12]
domain("Sport", "club", pl, {"won": {"label": "Premier League title", "values": vals(yes=["a Premier League champion", "Premier League champions"], no=["a club that has never won the Premier League", "clubs that have never won the Premier League"])}},
       ["won"], tag="Premier League")
# every World Cup winner up to 2022, then the 2026 final read from the data
WINNERS = {"Uruguay", "Italy", "Germany", "West Germany", "Brazil", "England", "Argentina", "France", "Spain"}
teams = collections.Counter()
for f in sorted(os.listdir(f"{D}/football/wc")):
    ms = json.load(open(f"{D}/football/wc/{f}"))["matches"]
    for m in ms:
        teams[m["team1"]] += 1; teams[m["team2"]] += 1
fin = [m for m in json.load(open(f"{D}/football/wc/2026.json"))["matches"] if m.get("round") == "Final"][0]
g = fin["score"].get("p") or fin["score"].get("et") or fin["score"]["ft"]
WINNERS.add(fin["team1"] if g[0] > g[1] else fin["team2"])
wcw = WINNERS
WC_NAMES = {"West Germany": "Germany", "Soviet Union": "Russia"}
tm = collections.Counter()
for t, n in teams.items():
    tm[WC_NAMES.get(t, t)] += n
wcwin = {WC_NAMES.get(t, t) for t in wcw}
wc = [{"name": t, "won": "yes" if t in wcwin else "no"} for t, n in tm.items() if n >= 25 and t not in ("Czechoslovakia", "Yugoslavia", "Russia")]
domain("Sport", "national team", wc, {"won": {"label": "World Cup", "values": vals(yes=["a World Cup winner", "World Cup winners"], no=["a team that has never won the World Cup", "teams that have never won the World Cup"])}},
       ["won"], tag="World Cup")

# ------------------------------------------------------------------ countries (Wikidata)
cc = collections.defaultdict(lambda: {"cont": set(), "n": 0, "landlocked": False, "island": False})
for r in json.load(open(f"{D}/animals/wd/countries.json")):
    x = cc[r["cLabel"]]
    if r.get("contLabel"):
        x["cont"].add(r["contLabel"])
    x["n"] = max(x["n"], int(r["n"])); x["landlocked"] |= r["landlocked"] == "true"; x["island"] |= r["island"] == "true"
COUNTRY_FIX = {"People's Republic of China": "China", "Kingdom of the Netherlands": "Netherlands", "Kingdom of Denmark": "Denmark", "State of Palestine": None}
countries = []
for name, x in cc.items():
    name2 = COUNTRY_FIX.get(name, name)
    if not name2 or len(x["cont"]) != 1 or x["n"] < 300:
        continue
    cont = next(iter(x["cont"]))
    cont = {"Insular Oceania": "Oceania", "Australian continent": "Oceania", "Australia": "Oceania"}.get(cont, cont)
    countries.append({"name": name2, "cont": cont, "landlocked": "yes" if x["landlocked"] else "no", "island": "yes" if x["island"] else "no"})
conts = {c["cont"] for c in countries}
domain("Geography", "country", countries, {
    "cont": {"label": "continent", "values": {c: [f"in {c}", f"in {c}"] for c in conts}},
    "landlocked": {"label": "landlocked", "values": vals(yes=["landlocked, with no coastline", "landlocked"], no=["on the coast", "on the coast"])},
    "island": {"label": "island country", "values": vals(yes=["an island country", "island countries"], no=["not an island country", "not island countries"])},
}, ["cont", "landlocked", "island"])

# ------------------------------------------------------------------ animals (the Animals quiz's table, classes checked against Wikipedia)
AF = f"{D}/animals/work/animals.json"
if os.path.exists(AF):
    SHORT_FLIGHTS = {"Chicken", "Turkey", "Peacock"}           # they can fly, but only a little: too arguable either way
    an = [{"name": a["name"], "class": a["class"], "diet": a["diet"], "flies": "short" if a["name"] in SHORT_FLIGHTS else a["flies"], "lives": a["lives"]}
          for a in json.load(open(AF))]
    CLS = {"mammal": "a mammal", "bird": "a bird", "reptile": "a reptile", "amphibian": "an amphibian", "fish": "a fish", "insect": "an insect",
           "arachnid": "an arachnid", "crustacean": "a crustacean", "mollusc": "a mollusc"}
    PL_ = {"fish": "fish"}
    domain("Animals", "animal", an, {
        "class": {"label": "class", "values": {k: [v, PL_.get(k, k + "s")] for k, v in CLS.items()}},
        "diet": {"label": "diet", "values": vals(herbivore=["a herbivore", "herbivores"], carnivore=["a carnivore", "carnivores"], omnivore=["an omnivore", "omnivores"], unclear=["(diet varies)", "(diet varies)"])},
        "flies": {"label": "flight", "values": vals(yes=["able to fly", "able to fly"], no=["unable to fly", "unable to fly"], short=["(only short flights)", "(only short flights)"])},
        "lives": {"label": "home", "values": vals(land=["a land animal", "land animals"], water=["a water animal", "water animals"], both=["at home on land and in water", "at home on land and in water"])},
    }, ["class", "flies", "diet"], weight=1.4)


# ------------------------------------------------------------------ numbers, worked out here
def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


nums = []
for n in range(2, 101):
    it = {"name": str(n), "parity": "even" if n % 2 == 0 else "odd", "prime": "yes" if is_prime(n) else "no",
          "square": "yes" if int(n ** 0.5) ** 2 == n else "no", "cube": "yes" if round(n ** (1 / 3)) ** 3 == n else "no",
          "digits": "1" if n < 10 else "2" if n < 100 else "3", "last": str(n % 10), "big": "yes" if n > 50 else "no"}
    for m in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        it[f"m{m}"] = "yes" if n % m == 0 else "no"
    nums.append(it)
numattrs = {
    "parity": {"label": "odd or even", "values": vals(even=["even", "even"], odd=["odd", "odd"])},
    "prime": {"label": "prime", "values": vals(yes=["a prime number", "prime numbers"], no=["not a prime number", "not prime"])},
    "square": {"label": "square", "values": vals(yes=["a square number", "square numbers"], no=["not a square number", "not square numbers"])},
    "cube": {"label": "cube", "values": vals(yes=["a cube number", "cube numbers"], no=["not a cube number", "not cube numbers"])},
    "digits": {"label": "digits", "values": {d: [f"{d}-digit", f"{d}-digit numbers"] for d in "123"}},
    "last": {"label": "last digit", "values": {str(d): [f"ending in {d}", f"ending in {d}"] for d in range(10)}},
    "big": {"label": "over 50", "values": vals(yes=["over 50", "over 50"], no=["50 or under", "50 or under"])},
}
for m in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
    numattrs[f"m{m}"] = {"label": f"multiple of {m}", "values": vals(yes=[f"a multiple of {m}", f"multiples of {m}"], no=[f"not a multiple of {m}", f"not multiples of {m}"])}
domain("Numbers", "number", nums, numattrs, ["prime", "square", "m3", "m4", "m5", "m6", "m7", "m9", "m11", "cube"], weight=1.2)

# ------------------------------------------------------------------ general knowledge tables
TF = f"{D}/odd/work/tables.json"
if os.path.exists(TF):
    for t in json.load(open(TF)):
        if t["kind"] == "car brand":          # cars come from the Cars quiz's own checked table above
            continue
        items = [dict(i, **{a: str(i[a]) for a in t["attrs"]}) for i in t["items"]]
        attrs = {a: {"label": v["label"], "values": {str(k): p for k, p in v["values"].items()}} for a, v in t["attrs"].items()}
        rules = [r for r in t["rules"] if not (t["domain"] == "History" and r == "where")]   # "where it happened" is too arguable
        try:
            domain(t["domain"], t["kind"], items, attrs, rules)
        except AssertionError as e:
            print("skipped table", t["domain"], t["kind"], e)


# ================================================================== rounds
def isolated(items, key):
    """the one item whose value differs from the other three (which agree), or None"""
    v = [key(i) for i in items]
    c = collections.Counter(v)
    if len(c) == 2 and sorted(c.values()) == [1, 3]:
        lone = next(x for x, n in c.items() if n == 1)
        return items[v.index(lone)]
    return None


def words(n):
    return str(len(n.split()))


unknown = lambda dom, a, i: dom["attrs"][a]["values"][str(i[a])][0].startswith("(")


def ok_round(dom, four, odd, rule):
    if unknown(dom, rule, odd):
        return False
    for a in dom["attrs"]:
        if any(unknown(dom, a, i) for i in four if i is not odd):
            return False
        iso = isolated(four, lambda i: i[a])
        if iso is not None and iso is not odd:
            return False
    for key in (lambda i: i["name"][0].upper(), lambda i: words(i["name"]), lambda i: i["name"].split()[0] if " " in i["name"] else i["name"],
                lambda i: i["name"].split()[-1]):
        iso = isolated(four, key)
        if iso is not None and iso is not odd:
            return False
    return True


QUESTIONS = ["Which is the odd one out?", "Which one doesn't belong?", "Three of these have something in common. Which one doesn't?"]
R = collections.defaultdict(list)
SEEN = set()


def join3(names):
    return f"{names[0]}, {names[1]} and {names[2]}"


for di, dom in enumerate(DOMAINS):
    items = dom["items"]
    for rule in dom["rules"]:
        by = collections.defaultdict(list)
        for it in items:
            by[it[rule]].append(it)
        groups = [v for v, lst in by.items() if len(lst) >= 3 and not dom["attrs"][rule]["values"][v][0].startswith("(")]
        tries = 0
        made = 0
        cap_ = int(90 * dom["weight"])
        while tries < 3000 and made < cap_:
            tries += 1
            if not groups:
                break
            v = rng.choice(groups)
            others = [it for it in items if it[rule] != v and not dom["attrs"][rule]["values"][it[rule]][0].startswith("(")]
            if not others:
                break
            three = rng.sample(by[v], 3)
            odd = rng.choice(others)
            four = three + [odd]
            key = "|".join(sorted(i["name"] for i in four))
            neg = v in ("no", "other", "independent", "none", "neither") or re.match(r"(not |neither |without |no )", dom["attrs"][rule]["values"][v][1])
            if neg and (rng.random() < 0.75 or (dom["domain"] == "Numbers" and rule not in ("prime", "square", "cube"))):
                continue
            if key in SEEN or not ok_round(dom, four, odd, rule):
                continue
            SEEN.add(key)
            ph = dom["attrs"][rule]["values"]
            x = (f"{odd['name']} is the only one that is {ph[odd[rule]][0]}." if neg else
                 f"{join3([i['name'] for i in three])} are all {ph[v][1]}. {odd['name']} is {ph[odd[rule]][0]}.")
            q = {"c": f"{di}:{rule}", "k": "odd:" + key, "q": rng.choice(QUESTIONS), "a": odd["name"], "o": [i["name"] for i in three], "x": x,
                 "ks": ["odd:" + i["name"] for i in four]}
            q["x"] = re.sub(r"\bare all born\b", "were all born", re.sub(r"\bis born\b", "was born", q["x"]))
            if dom["tag"]:
                q["t"] = dom["tag"]
            if max(len(i["name"]) for i in four) > 22:
                q["r"] = 1
            R[dom["domain"]].append(q)
            made += 1

if "--show" in sys.argv:
    want = sys.argv[sys.argv.index("--show") + 1]
    for q in rng.sample(R[want], min(14, len(R[want]))):
        print(f"[{q.get('t', '')}] {q['o'] + [q['a']]} -> {q['a']}\n      {q['x']}")
    sys.exit()
if "--avail" in sys.argv:
    for d, lst in sorted(R.items(), key=lambda kv: -len(kv[1])):
        print(f"{d:18} {len(lst)}  " + ", ".join(f"{c}:{n}" for c, n in collections.Counter(q['c'] for q in lst).most_common()))
    sys.exit()

TARGET = json.loads(os.environ.get("ODD_TARGET", "{}")) or None
assert TARGET, "set ODD_TARGET to a JSON object of domain -> rounds"
out = []
for d, want in TARGET.items():
    lst = R[d]
    by_c = collections.defaultdict(list)
    for q in lst:
        by_c[q["c"]].append(q)
    for v in by_c.values():
        rng.shuffle(v)
    got, took = [], collections.Counter()
    while len(got) < want and any(by_c.values()):
        c = min((c for c in by_c if by_c[c]), key=lambda c: (took[c], rng.random()))
        got.append(by_c[c].pop()); took[c] += 1
    print(f"{d:18} {len(got)}/{want}")
    assert len(got) == want or "--loose" in sys.argv, d
    out += got
slug = lambda d: re.sub(r"[^a-z]+", "", d.lower())[:12]
groups = {}
for d in TARGET:
    groups[slug(d)] = d
for q in out:
    d = DOMAINS[int(q["c"].split(":")[0])]["domain"]
    q["c"] = slug(d)
    assert q["a"] not in q["o"] and len(set(q["o"])) == 3
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
json.dump(groups, open(os.path.join(os.path.dirname(OUT) or ".", "odd_groups.json"), "w"), ensure_ascii=False)
print(len(out), "rounds")
