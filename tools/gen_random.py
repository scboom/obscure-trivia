"""Build the Random Games question bank (1,000 questions): an even mix of seven games.

Clash of Clans, Clash Royale, Hay Day, Phasmophobia and Bee Swarm Simulator questions come from each game's fan wiki
(stats tables and infoboxes), plus hand-written questions. Hearthstone Battlegrounds and Minecraft questions are taken from
this site's own checked banks for those quizzes.
Usage: gen_random.py RG_DIR SRC_DIR OUT.json
"""
import sys, json, random, re, collections

RG, SRC, OUT = sys.argv[1:4]
rng = random.Random(20261127)
Q = collections.defaultdict(list)
SEEN = set()
PER_GAME = {"coc": 143, "cr": 143, "hd": 143, "ph": 143, "bss": 142, "hs": 143, "mc": 143}


def add(c, k, q, a, opts, x=None, ks=None, extra=None):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) < 3:
        return False
    opts = opts[:3]
    if k in SEEN:
        return False
    SEEN.add(k)
    d = {"c": c, "k": k, "q": q, "a": a, "o": opts}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = ks
    if extra:
        d.update(extra)
    Q[c].append(d)
    return True


def near_num(n, pool=None, steps=(-2, -1, 1, 2, 3)):
    if pool:
        c = sorted({p for p in pool if p != n}, key=lambda v: (abs(v - n), rng.random()))
        return [str(v) for v in c[:3]]
    ok = [s for s in steps if n + s > 0]
    ok += [s for s in (3, 4, 5, 6) if s not in ok and n + s > 0][:max(0, 3 - len(ok))]
    return [str(n + s) for s in rng.sample(ok, 3)]


def clean_quote(qt, *names):
    """In-game descriptions, unless they give the answer away or lost words when links were stripped."""
    if not qt or len(qt) < 25 or qt[0].islower() or re.search(r"\s[,.!?]|\b(?:after|and|the|for|against|of) (?:s|and|,)\b|\s{2}|''|\[", qt):
        return None
    words = {w.lower() for n in names for w in re.findall(r"[A-Za-z]{4,}", n)}
    if any(w in qt.lower() for w in words):
        return None
    return qt


# ================================================================== Phasmophobia (Phasmophobia Wiki ghost pages)
PH = json.load(open(f"{RG}/phasmo.json"))
EVID = ["EMF Level 5", "Spirit Box", "Ultraviolet (fingerprints)", "Ghost Orbs", "Ghost Writing", "Freezing Temperatures", "D.O.T.S. Projector"]
ghosts = {n: g for n, g in PH.items() if len(g["evidence"]) == 3}
names = sorted(ghosts)
combo = collections.Counter(frozenset(g["evidence"]) for g in ghosts.values())
for n, g in ghosts.items():
    ev, missing = g["evidence"], [e for e in EVID if e not in g["evidence"]]
    for e in ev:
        add("ph", f"ph:has:{n}:{e}", f"Which of these is one of the {n}'s three pieces of evidence?", e, rng.sample(missing, 3),
            f"The {n} leaves {', '.join(ev[:2])} and {ev[2]}.", ks=["ph:" + n])
    add("ph", f"ph:not:{n}", f"Which piece of evidence does the {n} NOT leave?", rng.choice(missing), ev,
        f"The {n} leaves {', '.join(ev[:2])} and {ev[2]}.", ks=["ph:" + n])
    if combo[frozenset(ev)] == 1:
        close = sorted((m for m in names if m != n), key=lambda m: (-len(set(ghosts[m]["evidence"]) & set(ev)), rng.random()))
        add("ph", f"ph:combo:{n}", f"Which ghost leaves {ev[0]}, {ev[1]} and {ev[2]}?", n, close[:3], ks=["ph:" + n])
    for kind, lst in (("strength", g["strength"]), ("weakness", g["weakness"])):
        t = re.split(r"\|weakness|\}\}", lst[0])[0].strip() if lst else ""
        if t and len(t) > 15 and not any(w.lower() in t.lower() for w in n.split()):
            add("ph", f"ph:{kind}:{n}", f'Which ghost has this {kind}: "{t.rstrip(".")}"?', n, rng.sample([m for m in names if m != n], 3), ks=["ph:" + n])
    qt = clean_quote(g.get("quote", ""), n)
    if qt:
        add("ph", f"ph:quote:{n}", f'Which ghost does the journal describe like this: "{qt}"', n, rng.sample([m for m in names if m != n], 3), ks=["ph:" + n],
            extra={"r": 1})
PH_FACTS = [
    ("Which studio makes Phasmophobia?", "Kinetic Games", ["Supercell", "Bloober Team", "Frictional Games"]),
    ("In which year did Phasmophobia come out in early access?", "2020", ["2018", "2019", "2021"]),
    ("How many players can hunt together in one contract?", "4", ["2", "3", "6"]),
    ("How many pieces of evidence does a ghost normally leave?", "3", ["2", "4", "5"]),
    ("Which piece of equipment shows Ghost Orbs?", "A video camera (night vision)", ["The EMF Reader", "The Thermometer", "The UV Light"]),
    ("Which piece of equipment shows fingerprints?", "The UV Light", ["The Video Camera", "The Spirit Box", "The Parabolic Microphone"]),
    ("Which piece of equipment do you use to check for Freezing Temperatures?", "The Thermometer", ["The EMF Reader", "The UV Light", "The Sound Recorder"]),
    ("What do you put down to catch the ghost writing?", "A Ghost Writing Book", ["A Crucifix", "Salt", "A Photo Camera"]),
    ("Which item stops a ghost from starting a hunt close to it?", "A Crucifix", ["Salt", "A Candle", "A Sound Sensor"]),
    ("What do you burn to stop a hunt or keep the ghost away for a while?", "Incense", ["A Candle", "A Firelight", "Salt"]),
    ("What do you put on the floor to spot a ghost's footsteps?", "Salt", ["Sugar", "Flour", "Sand"]),
    ("Which ghost never steps in salt?", "Wraith", ["Spirit", "Phantom", "Banshee"]),
    ("Which of these is NOT a cursed possession?", "The Spirit Box", ["The Ouija Board", "The Music Box", "The Monkey Paw"]),
    ("Which of these is a cursed possession?", "Tarot Cards", ["The Parabolic Microphone", "The Head Gear", "The Motion Sensor"]),
    ("Below what average sanity can most ghosts start hunting?", "50%", ["25%", "70%", "90%"]),
    ("Which ghost can start hunting at a higher sanity (70%) than most?", "Demon", ["Shade", "Spirit", "Wraith"]),
    ("Which map is a lighthouse?", "Point Hope", ["Grafton Farmhouse", "Camp Woodwind", "Edgefield Road"]),
    ("Which of these Phasmophobia maps is a school?", "Brownstone High School", ["Sunny Meadows", "Bleasdale Farmhouse", "Maple Lodge Campsite"]),
    ("What is the big asylum map called?", "Sunny Meadows Mental Institution", ["Brownstone High School", "Prison", "Willow Street House"]),
    ("Where do you keep track of evidence and pick the ghost type?", "The journal", ["The van radio", "The whiteboard", "The truck computer"]),
]

# ================================================================== Clash Royale (Clash Royale Wiki card infoboxes)
CR = json.load(open(f"{RG}/royale.json"))
cards = {n: c for n, c in CR.items() if c["rarity"] in ("Common", "Rare", "Epic", "Legendary", "Champion") and c["type"] in ("Troop", "Spell", "Building")
         and c["arena"] and c["arena"] != "Special Event" and re.search(r"\d{4}$", c["released"])}   # normal cards only, not event-only ones
cnames = sorted(cards)
RAR = ["Common", "Rare", "Epic", "Legendary", "Champion"]
famous_cr = [n for n in cnames if cards[n]["released"].endswith("2016")] + [n for n in cnames if not cards[n]["released"].endswith("2016")]
for n in famous_cr:
    c = cards[n]
    add("cr", f"cr:cost:{n}", f"How much Elixir does the {n} card cost?", str(c["cost"]), near_num(c["cost"], steps=(-2, -1, 1, 2)),
        ks=["cr:" + n])
    add("cr", f"cr:rar:{n}", f"What rarity is the {n} card?", c["rarity"], [r for r in RAR if r != c["rarity"]][:4], ks=["cr:" + n])
    if c["arena"] and c["arena"] not in ("Special Event",):
        arenas = list(dict.fromkeys(x["arena"] for x in cards.values() if x["arena"] and x["arena"] != c["arena"] and x["arena"] != "Special Event"))
        add("cr", f"cr:arena:{n}", f"In which arena is the {n} card unlocked?", c["arena"], rng.sample(arenas, 3), ks=["cr:" + n])
    qt = clean_quote(c["quote"], n)
    if qt:
        add("cr", f"cr:quote:{n}", f'Which card has this description: "{qt}"', n, rng.sample([m for m in cnames if cards[m]["type"] == c["type"] and m != n], 3),
            ks=["cr:" + n], extra={"r": 1})
for t in ("Spell", "Building"):
    pool = [n for n in cnames if cards[n]["type"] == t]
    other = [n for n in cnames if cards[n]["type"] == "Troop"]
    for n in rng.sample(pool, min(10, len(pool))):
        add("cr", f"cr:type:{n}", f"Which of these cards is a {t.lower()}?", n, rng.sample(other, 3), ks=["cr:" + n])
for n in [n for n in cnames if cards[n]["rarity"] == "Champion"]:
    add("cr", f"cr:champ:{n}", "Which of these cards is a Champion?", n, rng.sample([m for m in cnames if cards[m]["rarity"] == "Legendary"], 3), ks=["cr:" + n])
tries = 0
while sum(1 for q in Q["cr"] if q["k"].startswith("cr:most")) < 15 and tries < 5000:
    tries += 1
    four = rng.sample(famous_cr[:70], 4)
    costs = [cards[n]["cost"] for n in four]
    if len(set(costs)) == 4:
        top = max(four, key=lambda n: cards[n]["cost"])
        add("cr", "cr:most:" + "|".join(sorted(four)), "Which of these cards costs the most Elixir?", top, [n for n in four if n != top],
            " · ".join(f"{n}: {cards[n]['cost']}" for n in sorted(four, key=lambda n: -cards[n]["cost"])) + ".")
CR_FACTS = [
    ("Which company makes Clash Royale?", "Supercell", ["King", "Rovio", "Riot Games"]),
    ("In which year did Clash Royale come out worldwide?", "2016", ["2012", "2014", "2018"]),
    ("How many cards are in a Clash Royale battle deck?", "8", ["6", "10", "12"]),
    ("What is the most Elixir you can hold at once?", "10", ["8", "12", "20"]),
    ("How many towers does each player start a battle with?", "3", ["1", "2", "4"]),
    ("What are the two smaller towers called?", "Princess Towers", ["Knight Towers", "Archer Towers", "Guard Towers"]),
    ("How many crowns do you get for destroying the King's Tower?", "3", ["1", "2", "5"]),
    ("How long is a normal battle before overtime?", "3 minutes", ["2 minutes", "4 minutes", "5 minutes"]),
    ("Which card copies the last card you played, for one more Elixir?", "Mirror", ["Clone", "Rage", "Tornado"]),
    ("Which card costs 9 Elixir, the most of any card?", "Three Musketeers", ["Golem", "Mega Knight", "Electro Giant"]),
    ("Which rarity was added last, in 2021?", "Champion", ["Legendary", "Epic", "Mythic"]),
    ("What do you collect from chests to upgrade cards?", "Cards and Gold", ["Gems only", "Elixir", "Crowns only"]),
    ("Which game does Clash Royale share its characters with?", "Clash of Clans", ["Brawl Stars", "Hay Day", "Boom Beach"]),
]

# ================================================================== Clash of Clans (Clash of Clans Wiki stats tables)
CO = json.load(open(f"{RG}/coc.json"))
cl = lambda v: re.sub(r"^.*\|\s*", "", v).strip()


def stats(n):
    u = CO.get(n)
    if not u:
        return {}
    return {k.split("|")[-1].strip(): cl(v) for k, v in u["stats"].items() if "!!" not in k}


ELIXIR_T = "Barbarian|Archer|Giant|Goblin|Wall Breaker|Balloon|Wizard|Healer|Dragon|Baby Dragon|Miner|Yeti|Dragon Rider|Root Rider|Thrower|Meteor Golem".split("|")
DARK_T = "Minion|Hog Rider|Valkyrie|Golem|Witch|Bowler|Headhunter|Apprentice Warden|Druid|Furnace".split("|")
SPELLS = "Healing Spell|Rage Spell|Jump Spell|Freeze Spell|Clone Spell|Invisibility Spell|Recall Spell|Totem Spell|Poison Spell|Skeleton Spell|Overgrowth Spell|Ice Block Spell".split("|")
DARK_S = {"Poison Spell", "Skeleton Spell", "Overgrowth Spell", "Ice Block Spell"}
SIEGES = "Wall Wrecker|Battle Blimp|Stone Slammer|Siege Barracks|Log Launcher|Flame Flinger|Battle Drill".split("|")
PETS = "L.A.S.S.I|Electro Owl|Mighty Yak|Unicorn|Frosty|Diggy|Poison Lizard|Phoenix|Spirit Fox|Angry Jelly|Sneezy|Greedy Raven".split("|")
troops = {n: stats(n) for n in ELIXIR_T + DARK_T if stats(n).get("Housing Space", "").isdigit()}
housing = {n: int(s["Housing Space"]) for n, s in troops.items()}
for n in troops:
    hs = housing[n]
    add("coc", f"coc:house:{n}", f"How much housing space does one {n} take in your army?", str(hs), near_num(hs, pool=list(housing.values())), ks=["coc:" + n])
spells = {n: stats(n) for n in SPELLS if stats(n).get("Housing Space", "").isdigit()}
for n, s in spells.items():
    hs = int(s["Housing Space"])
    add("coc", f"coc:spellhouse:{n}", f"How much spell space does the {n} take?", str(hs), [str(v) for v in (1, 2, 3, 4) if v != hs], ks=["coc:" + n])
for n in [n for n in DARK_T if n in troops]:
    add("coc", f"coc:dark:{n}", "Which of these is a Dark Elixir troop?", n, rng.sample([m for m in ELIXIR_T if m in troops], 3), ks=["coc:" + n])
for n in [n for n in ELIXIR_T if n in troops][:10]:
    add("coc", f"coc:elixir:{n}", "Which of these is trained with normal (pink) Elixir, not Dark Elixir?", n, rng.sample([m for m in DARK_T if m in troops], 3), ks=["coc:" + n])
for n in DARK_S & set(spells):
    add("coc", f"coc:darkspell:{n}", "Which of these is a Dark Spell?", n, rng.sample([m for m in spells if m not in DARK_S], 3), ks=["coc:" + n])
lvl = {}
for n in ELIXIR_T:
    s = troops.get(n, {})
    v = next((v for k, v in s.items() if k == "Barracks Level Required"), "")
    if v.isdigit():
        lvl[n] = int(v)
tries = 0
while sum(1 for q in Q["coc"] if q["k"].startswith("coc:first")) < 12 and tries < 3000:
    tries += 1
    four = rng.sample(list(lvl), 4)
    first = min(four, key=lambda n: lvl[n])
    add("coc", "coc:first:" + "|".join(sorted(four)), "Which of these troops is unlocked first in the Barracks?", first, [n for n in four if n != first],
        " · ".join(f"{n}: Barracks level {lvl[n]}" for n in sorted(four, key=lambda n: lvl[n])) + ".")
tries = 0
while sum(1 for q in Q["coc"] if q["k"].startswith("coc:most")) < 12 and tries < 3000:
    tries += 1
    four = rng.sample(list(housing), 4)
    if len({housing[n] for n in four}) == 4:
        top = max(four, key=lambda n: housing[n])
        add("coc", "coc:most:" + "|".join(sorted(four)), "Which of these troops takes up the most housing space?", top, [n for n in four if n != top],
            " · ".join(f"{n}: {housing[n]}" for n in sorted(four, key=lambda n: -housing[n])) + ".")
petlvl = {n: int(v) for n in PETS for k, v in stats(n).items() if k == "Pet House Level Required" and v.isdigit()}
tries = 0
while sum(1 for q in Q["coc"] if q["k"].startswith("coc:petfirst")) < 8 and tries < 3000:
    tries += 1
    four = rng.sample(list(petlvl), 4)
    first = min(four, key=lambda n: petlvl[n])
    add("coc", "coc:petfirst:" + "|".join(sorted(four)), "Which of these pets is unlocked first in the Pet House?", first, [n for n in four if n != first],
        " · ".join(f"{n}: Pet House level {petlvl[n]}" for n in sorted(four, key=lambda n: petlvl[n])) + ".")
TARGET = {"Giant": "Defenses", "Goblin": "Resources", "Wall Breaker": "Walls", "Balloon": "Defenses", "Hog Rider": "Defenses", "Golem": "Defenses",
          "Headhunter": "Heroes", "Dragon Rider": "Defenses", "Root Rider": "Defenses"}
for n, t in TARGET.items():
    if n in troops and t.lower()[:5] in troops[n].get("Preferred Target", "").lower():
        add("coc", f"coc:target:{n}", f"What does the {n} go for first?", t, [x for x in ("Defenses", "Resources", "Walls", "Heroes", "Anything nearby") if x != t][:3],
            ks=["coc:" + n])
HEROES = {"Barbarian King": 7, "Archer Queen": 8, "Minion Prince": 9, "Grand Warden": 11, "Royal Champion": 13, "Dragon Duke": 15}   # Town Hall, from each hero's table
for h, th in HEROES.items():
    add("coc", f"coc:hero:{h}", f"At which Town Hall level is the {h} unlocked?", str(th), near_num(th, pool=list(HEROES.values()) + [10, 12, 14]), ks=["coc:" + h])
    add("coc", f"coc:herowho:{th}", f"Which hero is unlocked at Town Hall {th}?", h, [x for x in HEROES if x != h], ks=["coc:" + h])
for n in SIEGES:
    if n in CO:
        add("coc", f"coc:siege:{n}", "Which of these is a Siege Machine?", n, rng.sample([m for m in troops] + list(spells), 3), ks=["coc:" + n])
for n in PETS:
    if n in CO:
        add("coc", f"coc:pet:{n}", "Which of these is a hero pet?", n, rng.sample(SIEGES + list(troops), 3), ks=["coc:" + n])
for n in list(troops) + list(spells) + SIEGES:
    qt = clean_quote(CO.get(n, {}).get("quote", ""), n, n.replace(" Spell", ""))
    if qt:
        pool = list(spells) if n in spells else SIEGES if n in SIEGES else list(troops)
        add("coc", f"coc:quote:{n}", f'Which one has this in-game description: "{qt}"', n, rng.sample([m for m in pool if m != n], 3), ks=["coc:" + n], extra={"r": 1})
COC_FACTS = [
    ("Which company makes Clash of Clans?", "Supercell", ["King", "Rovio", "Zynga"]),
    ("In which year did Clash of Clans come out?", "2012", ["2010", "2014", "2016"]),
    ("What is Clash of Clans' premium currency called?", "Gems", ["Diamonds", "Crystals", "Crowns"]),
    ("Which three resources do you spend on troops and buildings?", "Gold, Elixir and Dark Elixir", ["Gold, Gems and Oil", "Wood, Stone and Gold", "Elixir, Coins and Crystals"]),
    ("What is the most stars you can win in one attack?", "3", ["1", "5", "10"]),
    ("How much destruction earns you one star?", "50%", ["25%", "75%", "100%"]),
    ("Destroying which building always earns you a star?", "The Town Hall", ["The Clan Castle", "An Air Defense", "The Laboratory"]),
    ("What does the Clan Castle hold?", "Reinforcement troops from your clanmates", ["Extra gems", "Your heroes", "Spare walls"]),
    ("What is the second village, reached by boat, called?", "The Builder Base", ["The Clan Capital", "The Goblin Map", "The Night Island"]),
    ("Which clan-wide village did Clan Capital add in 2022?", "A shared Clan Capital that the whole clan builds", ["A second Builder Base", "A goblin campaign", "A pet shop"]),
    ("Which building do you upgrade to research stronger troops?", "The Laboratory", ["The Barracks", "The Spell Factory", "The Clan Castle"]),
    ("Which spell copies the troops inside it for a short time?", "Clone Spell", ["Rage Spell", "Recall Spell", "Totem Spell"]),
    ("Which spell lets your troops jump over walls?", "Jump Spell", ["Haste Spell", "Freeze Spell", "Rage Spell"]),
    ("Which spell stops defenses (and troops) from moving or attacking for a few seconds?", "Freeze Spell", ["Poison Spell", "Healing Spell", "Overgrowth Spell"]),
    ("Which troop prefers to attack resource buildings and does double damage to them?", "Goblin", ["Barbarian", "Archer", "Miner"]),
]

# ================================================================== Hay Day (Hay Day Wiki goods list and building pages)
HG = json.load(open(f"{RG}/hd_goods.json"))
HB = json.load(open(f"{RG}/hayday.json"))
machines = {n: b for n, b in HB.items() if b["kind"] == "Machine" and b["level"].isdigit() and b["time"] and b["price"]}   # not seasonal event machines


def secs(t):
    units = {"s": 1, "min": 60, "h": 3600, "d": 86400}
    return sum(int(v) * units[u] for v, u in re.findall(r"(\d+)\s*(s|min|h|d)\b", t))
crops = {n: g for n, g in HG.items() if g["source"] == "Field" and g["level"] and g["time"]}
animal_goods = {n: g for n, g in HG.items() if g["source"] in ("Chicken", "Cow", "Pig", "Sheep", "Goat")}
made = {n: g for n, g in HG.items() if g["source"] in machines and g["level"] and int(g["level"]) <= 60}
mlist = sorted(machines)
for n, g in sorted(made.items(), key=lambda kv: int(kv[1]["level"])):
    add("hd", f"hd:made:{n}", f"Which machine makes {n}?", g["source"], rng.sample([m for m in mlist if m != g["source"] and int(machines[m]["level"]) <= 60], 3), ks=["hd:" + n])
    ingredients = [i for i, _ in g["needs"]]
    if ingredients:
        others = [x for x in HG if x not in ingredients and x != n and HG[x]["level"] and int(HG[x]["level"]) <= 40]
        add("hd", f"hd:needs:{n}", f"Which of these do you need to make {n}?", rng.choice(ingredients), rng.sample(others, 3),
            f"{n} needs " + ", ".join(f"{q}× {i}" for i, q in g["needs"]) + ".", ks=["hd:" + n])
for n, g in crops.items():
    lv = int(g["level"])
    add("hd", f"hd:croplvl:{n}", f"At which experience level do you unlock {n}?", str(lv), near_num(lv, steps=(-4, -2, 2, 3, 5)), ks=["hd:" + n])
    times = sorted(dict.fromkeys(c["time"] for c in crops.values() if c["time"] != g["time"] and secs(c["time"])), key=lambda t: abs(secs(t) - secs(g["time"])))
    add("hd", f"hd:croptime:{n}", f"How long does {n} take to grow in a field?", g["time"], rng.sample(times[:5], 3), ks=["hd:" + n])
for n, g in animal_goods.items():
    add("hd", f"hd:animal:{n}", f"Which animal gives you {n.lower() if n not in ('Goat milk',) else n}?", g["source"],
        [a for a in ("Chicken", "Cow", "Pig", "Sheep", "Goat") if a != g["source"]][:3], ks=["hd:" + n])
for n, b in machines.items():
    lv = int(b["level"])
    if lv <= 60:
        add("hd", f"hd:mlvl:{n}", f"At which experience level is the {n} unlocked?", str(lv), near_num(lv, steps=(-5, -3, 3, 5, 8)), ks=["hd:" + n])
HD_FACTS = [
    ("Which company makes Hay Day?", "Supercell", ["Zynga", "King", "Playrix"]),
    ("In which year did Hay Day come out?", "2012", ["2009", "2015", "2017"]),
    ("Where are your crops stored?", "The Silo", ["The Barn", "The Truck", "The Roadside Shop"]),
    ("Where are your products (not crops) stored?", "The Barn", ["The Silo", "The Mailbox", "The Town Hall"]),
    ("What is Hay Day's premium currency?", "Diamonds", ["Gems", "Gold Bars", "Coins"]),
    ("Where do you sell goods to other players?", "The Roadside Shop", ["The Barn", "The Silo", "The Feed Mill"]),
    ("Which three items do you need to upgrade the Barn?", "Bolts, planks and duct tape", ["Nails, screws and wood panels", "Land deeds, mallets and marker stakes", "Axes, saws and dynamite"]),
    ("Which three items do you need to upgrade the Silo?", "Nails, screws and wood panels", ["Bolts, planks and duct tape", "Land deeds, mallets and marker stakes", "Shovels, pickaxes and TNT"]),
    ("Which three items do you need to clear land to expand your farm?", "Land deeds, mallets and marker stakes", ["Bolts, planks and duct tape", "Nails, screws and wood panels", "Axes, saws and shovels"]),
    ("What do you fill to send goods away by road for coins and experience?", "Truck orders", ["Boat crates", "The Roadside Shop", "The Mailbox"]),
    ("What is the very first crop you can grow?", "Wheat", ["Corn", "Carrots", "Soybeans"]),
    ("What does a chicken eat?", "Chicken feed", ["Wheat", "Corn", "Cow feed"]),
]

# ================================================================== Bee Swarm Simulator (Bee Swarm Simulator Wiki bee and field pages)
BS = json.load(open(f"{RG}/bss.json"))
bees = BS["bees"]
bnames = sorted(bees)
BRAR = ["Common", "Rare", "Epic", "Legendary", "Mythic", "Event"]
COLOR = {"Colorless": "Colorless (white)", "Red": "Red", "Blue": "Blue"}
for n, b in bees.items():
    add("bss", f"bss:rar:{n}", f"What rarity is the {n}?", b["rarity"], [r for r in BRAR if r != b["rarity"]][:5] and rng.sample([r for r in BRAR if r != b["rarity"]], 3), ks=["bss:" + n])
    col = COLOR.get(b["color"])
    if col:
        add("bss", f"bss:col:{n}", f"What colour is the {n}?", col, [c for c in ("Red", "Blue", "Colorless (white)", "Yellow") if c != col], ks=["bss:" + n])
    if b["treat"] in ("Sunflower Seed", "Strawberry", "Blueberry", "Pineapple"):
        add("bss", f"bss:treat:{n}", f"What is the {n}'s favourite treat?", b["treat"], [t for t in ("Sunflower Seed", "Strawberry", "Blueberry", "Pineapple") if t != b["treat"]],
            ks=["bss:" + n])
    qt = clean_quote(b["desc"], n.replace(" Bee", ""))
    if qt:
        add("bss", f"bss:desc:{n}", f'Which bee has this description: "{qt}"', n, rng.sample([m for m in bnames if m != n], 3), ks=["bss:" + n], extra={"r": 1})
MAIN_FIELDS = "Sunflower Field|Dandelion Field|Mushroom Field|Blue Flower Field|Clover Field|Spider Field|Strawberry Field|Bamboo Field|Pineapple Patch|Stump Field|Cactus Field|Pumpkin Patch|Pine Tree Forest|Rose Field|Mountain Top Field|Coconut Field|Pepper Patch".split("|")
fields = {n: BS["fields"][n] for n in MAIN_FIELDS if n in BS["fields"]}
for n, f in fields.items():
    need = "No bees needed (starter field)" if f["bees"] in ("None", "0", "") else f"{f['bees']} bees"
    opts = [o for o in ("No bees needed (starter field)", "5 bees", "10 bees", "15 bees", "25 bees", "35 bees") if o != need]
    add("bss", f"bss:fieldbees:{n}", f"How many bees do you need to reach the {n}?", need, rng.sample(opts, 3), ks=["bss:" + n])
    if f["color"] in ("Red", "Blue", "White"):
        add("bss", f"bss:fieldcol:{n}", f"What colour are most flowers in the {n}?", f["color"], [c for c in ("Red", "Blue", "White", "A mix of colours") if c != f["color"]],
            ks=["bss:" + n])
BSS_FACTS = [
    ("On which platform is Bee Swarm Simulator played?", "Roblox", ["Minecraft", "Fortnite Creative", "Steam only"]),
    ("Who created Bee Swarm Simulator?", "Onett", ["Builderman", "Dued1", "Gamer Robot"]),
    ("In which year did Bee Swarm Simulator come out?", "2018", ["2014", "2016", "2021"]),
    ("What do your bees turn pollen into at the hive?", "Honey", ["Nectar", "Jelly", "Wax"]),
    ("Which bear gives you your first quests?", "Black Bear", ["Polar Bear", "Science Bear", "Panda Bear"]),
    ("What does Royal Jelly do to a bee?", "Changes it into a random bee", ["Doubles its honey", "Makes it gifted for sure", "Levels it up by 5"]),
    ("Which bee leads the Red bees?", "Riley Bee", ["Bucko Bee", "Rage Bee", "Demon Bee"]),
    ("Which bee leads the Blue bees?", "Bucko Bee", ["Riley Bee", "Frosty Bee", "Cool Bee"]),
    ("What is the most bees you can have in your hive?", "50", ["25", "40", "100"]),
    ("Which bee rarity is the rarest you can hatch from normal eggs and jelly?", "Mythic", ["Legendary", "Epic", "Event"]),
    ("Which field do new players start next to, along with Dandelion and Mushroom?", "Sunflower Field", ["Coconut Field", "Pepper Patch", "Rose Field"]),
]
for c, facts in (("ph", PH_FACTS), ("cr", CR_FACTS), ("coc", COC_FACTS), ("hd", HD_FACTS), ("bss", BSS_FACTS)):
    for q, a, o in facts:
        add(c, "fact:" + q, q, a, o)

# ================================================================== Hearthstone Battlegrounds and Minecraft: a varied pick from this site's banks
for c, src, skip in (("hs", "hs_questions.json", {"oldstats", "oldeffect", "duoarmor", "health"}), ("mc", "mc_questions.json", {"recipe"})):
    bank = json.load(open(f"{SRC}/{src}"))
    by = collections.defaultdict(list)
    for q in bank:
        if q["c"] not in skip:
            by[q["c"]].append(q)
    for v in by.values():
        rng.shuffle(v)
    while len(Q[c]) < PER_GAME[c] + 10 and any(by.values()):
        for cat in sorted(by):   # round-robin across question types, so no type dominates
            if by[cat] and len(Q[c]) < PER_GAME[c] + 10:
                q = by[cat].pop()
                extra = {k: q[k] for k in ("t", "r", "x") if k in q}
                add(c, f"{c}:{q['c']}:{q['k']}", q["q"], q["a"], q["o"], ks=[f"{c}:{k}" for k in (q.get("ks") or [q["k"]])], extra=extra)
    if c == "mc":   # recipe questions need the Minecraft page's recipe pictures, so they're left out here
        pass

# ================================================================== balance: the same number from every game
print({c: len(v) for c, v in Q.items()}, file=sys.stderr)
bank = []
for c, n in PER_GAME.items():
    v = Q[c]
    facts = [q for q in v if q["k"].startswith("fact:")]
    rest = [q for q in v if not q["k"].startswith("fact:")]
    by = collections.defaultdict(list)
    for q in rest:
        by[q["k"].split(":")[1]].append(q)
    take, keep = list(facts), n - len(facts)
    while keep > 0 and any(by.values()):
        for t in sorted(by):
            if by[t] and keep > 0:
                take.append(by[t].pop(0)); keep -= 1
    if len(take) < n:
        raise SystemExit(f"{c}: only {len(take)} questions")
    bank += take
if len(bank) != 1000:
    raise SystemExit(f"bank has {len(bank)} questions")
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank), collections.Counter(q["c"] for q in bank), file=sys.stderr)
