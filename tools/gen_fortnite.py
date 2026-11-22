"""Build the OG Fortnite question bank (1,000 questions): Chapter 1 only, from the Pre-Season to Season X.

Nothing from Chapter 2 or later, in the questions, the wrong answers or the explanations; the build fails if anything slips in.
Outfit and emote seasons come from the Fortnite-API cosmetics database (fortnite-api.com). Seasons, named locations
(season by season, on the Chapter 1 island) and live events come from the Fortnite Wiki (fortnite.fandom.com).
Hand-written questions cover the big moments of each season, items, Battle Pass outfits, records and history,
each checked against the wiki. Only the main Battle Royale island counts for map questions.
Usage: gen_fortnite.py cosmetics.json data.json OUT.json
"""
import sys, json, random, re, collections

COS, DATA, OUT = sys.argv[1:4]
rng = random.Random(20261126)
Q = collections.defaultdict(list)
SEEN = set()


def add(c, k, q, a, opts, x=None, ks=None):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) != 3:
        raise SystemExit(f"bad options for {q!r}: {a!r} {opts}")
    if k in SEEN:
        return False
    SEEN.add(k)
    d = {"c": c, "k": k, "q": q, "a": a, "o": opts}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = ks
    Q[c].append(d)
    return True


data = json.load(open(DATA))


# ------------------------------------------------------------------ seasons: Chapter 1 Pre-Season ... Chapter 1 Season X (shown as "Season 4" etc.)
def wiki_label(page):
    m = re.match(r"Chapter 1: (.+)", page)
    return "Chapter 1 " + (m.group(1) if m else page)


SEASONS = [dict(s, name=wiki_label(s["page"])) for s in data["seasons"] if s["chapter"] == 1]
ORDER = [s["name"] for s in SEASONS]
POS = {n: i for i, n in enumerate(ORDER)}
assert ORDER[0] == "Chapter 1 Pre-Season" and ORDER[-1] == "Chapter 1 Season X", ORDER
REAL = ORDER[1:]   # Season 1 to Season X


def near_seasons(label, n=3, pool=None, spread=4):
    pool = pool or ORDER
    i = pool.index(label)
    cand = [pool[j] for j in range(max(0, i - spread), min(len(pool), i + spread + 1)) if j != i]
    rng.shuffle(cand)
    cand.sort(key=lambda s: abs(pool.index(s) - i))
    out = cand[:n]
    if len(out) < n:
        out += rng.sample([s for s in pool if s != label and s not in out], n - len(out))
    return out


def fair_seasons(label, pool=None):
    """One neighbouring season and two a little further away: still hard, but answerable if you know the era."""
    pool = pool or ORDER
    i = pool.index(label)
    near = [pool[j] for j in (i - 1, i + 1) if 0 <= j < len(pool)]
    far = [pool[j] for j in range(max(0, i - 5), min(len(pool), i + 6)) if abs(j - i) >= 2]
    out = rng.sample(near, 1) + rng.sample(far, min(2, len(far)))
    if len(out) < 3:
        out += rng.sample([s for s in pool if s != label and s not in out], 3 - len(out))
    return out


# ------------------------------------------------------------------ outfits and emotes from Chapter 1
cos = json.load(open(COS))["data"]
first = {}
for c in cos:
    intro = c.get("introduction")
    if not intro or c["type"]["value"] not in ("outfit", "emote") or str(intro.get("chapter")) != "1":
        continue
    if not c.get("name") or re.search(r"_|NPC|^TBD$|^null$", c["name"]):   # placeholders from the game files
        continue
    lab = f"Chapter 1 Season {intro.get('season')}"
    if lab not in POS:
        continue
    key = (c["type"]["value"], c["name"])
    if key not in first or POS[lab] < POS[first[key]["season"]]:
        first[key] = {"name": c["name"], "type": c["type"]["value"], "season": lab, "series": (c.get("series") or {}).get("value"),
                      "rarity": (c.get("rarity") or {}).get("value"), "id": c["id"]}
FAMOUS = """Renegade Raider|Aerial Assault Trooper|Ghoul Trooper|Skull Trooper|Black Knight|Blue Squire|Royale Knight|Sparkle Specialist|Red Knight|Cuddle Team Leader|Rabbit Raider|Love Ranger|Brite Bomber|Dark Bomber|The Reaper|Raven|Rex|Tricera Ops|Raptor|Mission Specialist|Rust Lord|Moonwalker|Havoc|Omega|Carbide|Zoey|Teknique|Valor|Battlehawk|Drift|Ragnarok|Huntress|Calamity|Dire|Fable|Nitehare|Skull Ranger|Spooky Team Leader|Zenith|The Ice King|Lynx|Sgt. Winter|Onesie|Powder|Trog|Merry Marauder|Nog Ops|Crackshot|Yuletide Ranger|Codename E.L.F.|Blackheart|Hybrid|Peely|Luxe|Rox|Vendetta|Sentinel|Bunker Jonesy|Catalyst|X-Lord|Ultima Knight|Eternal Voyager|Fishstick|Tomatohead|Beef Boss|Dark Voyager|Elite Agent|Sun Strider|Funk Ops|Disco Diva|Abstrakt|Burnout|Lucky Rider|Leviathan|Wukong|Whiplash|Wildcat|Galaxy|Wonder|Glow|Scorpion|Marshmello|John Wick|Major Lazer|Highland Warrior|Midnight Ops|Jonesy|Ramirez|Spitfire|Headhunter|Banshee|Wild Card|Moisty Merman|Toxic Trooper|Prisoner|Chomp Sr.|Kitbash|Lace|Zadie|Grill Sergeant|Hothouse""".split("|")
SERIES_OK = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series", "Gaming Legends Series"}
outfits = {n: o for (t, n), o in first.items() if t == "outfit"}
pool = list({outfits[n]["name"]: outfits[n] for n in FAMOUS if n in outfits}.values())
famous_names = {o["name"] for o in pool}
series_pool = [o for o in outfits.values() if o["series"] in SERIES_OK and o["name"] not in famous_names]
RANK = {"legendary": 0, "epic": 1, "rare": 2, "uncommon": 3}
rest = [o for o in outfits.values() if o["name"] not in famous_names and o["series"] not in SERIES_OK]
rng.shuffle(series_pool); rng.shuffle(rest)
rest.sort(key=lambda o: RANK.get(o["rarity"], 4))   # the better-known Legendary and Epic outfits first
OUTFITS = pool + series_pool + rest                    # the bank is trimmed from the end, so the most obscure go first
print("outfits", len(pool), "famous +", len(series_pool), "collab +", len(rest), "others", file=sys.stderr)

OUTFIT_NOTE = {
    "John Wick": "The official John Wick outfit came with the crossover for the third John Wick film, in May 2019. Players had already nicknamed The Reaper (Season 3) \"John Wick\".",
    "The Reaper": "Players nicknamed it \"John Wick\". The official John Wick outfit didn't arrive until Season 9.",
}
for o in OUTFITS:
    the = "" if o["name"].startswith("The ") else "the "
    add("outseason", "outseason:" + o["name"], f"In which season was {the}{o['name']} outfit added to Fortnite?", o["season"], fair_seasons(o["season"]),
        OUTFIT_NOTE.get(o["name"]), ks=["outfit:" + o["name"]] + (["outfit:John Wick"] if o["name"] == "The Reaper" else []))
tries = 0
while len(Q["outfirst"]) < 80 and tries < 80000:
    tries += 1
    os_ = sorted(rng.sample(pool, 4), key=lambda o: POS[o["season"]])
    ps = [POS[o["season"]] for o in os_]
    if any(b - a < 2 for a, b in zip(ps, ps[1:])) or ps[-1] - ps[0] > 9:
        continue
    add("outfirst", "outfirst:" + "|".join(sorted(o["name"] for o in os_)), "Which of these outfits came out first?", os_[0]["name"], [o["name"] for o in os_[1:]],
        " · ".join(f"{o['name']}: {o['season']}" for o in os_) + ".", ks=["outfit:" + o["name"] for o in os_])
SERIES_NAME = {"Icon Series": "the Icon Series (real-life stars)", "MARVEL SERIES": "the Marvel Series", "DC SERIES": "the DC Series",
               "Star Wars Series": "the Star Wars Series", "Gaming Legends Series": "the Gaming Legends Series"}
nonseries = [o for o in pool if not o["series"]]
for ser, nice in SERIES_NAME.items():
    members = [o for o in pool + series_pool if o["series"] == ser]
    rng.shuffle(members)
    for o in members[:20]:
        add("outseries", f"outseries:{o['name']}", f"Which of these outfits is part of {nice}?", o["name"], [w["name"] for w in rng.sample(nonseries, 3)],
            ks=["outfit:" + o["name"]])
EMOTES = """Floss|Take The L|Orange Justice|Best Mates|Electro Shuffle|Fresh|Hype|Scenario|Laugh It Up|Ride the Pony|Dab|Groove Jam|Rambunctious|Breakin'|Pure Salt|Smooth Moves|Infinite Dab|Rollie|Tidy|Boogie Down|Distraction|Billy Bounce|The Robot|Pump Up the Jam|Lil' Treat|Zany|Squat Kick|Wiggle|Flapper|Disco Fever|Jubilation|True Heart|Freestylin'|Pop Lock|Hootenanny|Rawr|Living Large|Crackdown|Fancy Feet|Intensity|Bendy|Mime Time|Reanimated|Lazy Shuffle|Phone It In|Make it Rain|Confused|Llama Conga|Gun Show|The Worm|Hula|Star Power|Shimmer|Jaywalking|Tai Chi|Slitherin'|Glowsticks|Dance Therapy|Hand Signals|Salute|Clean Groove|Mic Drop|Kiss the Cup|Poki|Hot Marat|Bring It Around|Where Is Matt?|Electro Swing|Treat Yourself|Fist Pump|Snap|Facepalm|Calculated|Chicken|Kung-Fu Salute|Jazz Hands|The Floss|Tsunami""".split("|")
emotes = {n: o for (t, n), o in first.items() if t == "emote"}
for n in EMOTES:
    if n in emotes:
        o = emotes[n]
        add("emote", "emote:" + n, f'In which season was the "{n}" emote added?', o["season"], fair_seasons(o["season"]), ks=["emote:" + n])

# ------------------------------------------------------------------ Battle Pass outfits (each checked on its Fortnite Wiki page)
TOP = [("Chapter 1 Season 3", "The Reaper"), ("Chapter 1 Season 4", "Omega"), ("Chapter 1 Season 5", "Ragnarok"), ("Chapter 1 Season 6", "Dire"),
       ("Chapter 1 Season 7", "The Ice King"), ("Chapter 1 Season 8", "Luxe"), ("Chapter 1 Season 9", "Vendetta"), ("Chapter 1 Season X", "Ultima Knight")]
INSTANT = {"Chapter 1 Season 2": ["Blue Squire"], "Chapter 1 Season 3": ["Mission Specialist"], "Chapter 1 Season 5": ["Drift", "Huntress"],
           "Chapter 1 Season 6": ["Calamity"], "Chapter 1 Season 7": ["Zenith", "Lynx"], "Chapter 1 Season 8": ["Blackheart", "Hybrid"],
           "Chapter 1 Season 9": ["Rox", "Sentinel"], "Chapter 1 Season X": ["Catalyst", "X-Lord"]}
tops = [o for _, o in TOP] + ["Black Knight"]
for season, o in TOP:
    add("outbp", f"bptop:{season}", f"Which outfit was the Tier 100 reward of the {season} Battle Pass?", o, rng.sample([t for t in tops if t != o], 3),
        ks=["outfit:" + o, "bp:" + season])
    add("outbp", f"bptopwhich:{o}", f"{o} was the Tier 100 reward of which season's Battle Pass?", season,
        fair_seasons(season, pool=ORDER[ORDER.index("Chapter 1 Season 2"):]), ks=["outfit:" + o, "bp:" + season])
add("outbp", "bptop:s2", "Which outfit was the final reward (Tier 70) of the Season 2 Battle Pass, the first Battle Pass ever?", "Black Knight",
    ["The Reaper", "Blue Squire", "Omega"], ks=["outfit:Black Knight", "bp:Chapter 1 Season 2"])
add("outbp", "bptiers:s2", "How many tiers did the very first Battle Pass (Season 2) have?", "70", ["50", "100", "90"],
    "Black Knight was the Tier 70 reward. From Season 3 the Battle Pass had 100 tiers.", ks=["bp:Chapter 1 Season 2"])
instants = [o for v in INSTANT.values() for o in v]
for season, os_ in INSTANT.items():
    for o in os_:
        add("outbp", f"bpinstant:{o}", f"Which outfit did you unlock straight away by buying the {season} Battle Pass?", o,
            rng.sample([x for x in instants if x not in os_], 3), " and ".join(os_) + (" were" if len(os_) > 1 else " was") + " unlocked as soon as you bought it.",
            ks=["outfit:" + o, "bp:" + season])
add("outbp", "bppeely", "At which tier of the Season 8 Battle Pass was Peely unlocked?", "47", ["1", "23", "100"], ks=["outfit:Peely"])

# ------------------------------------------------------------------ seasons
named = [s for s in SEASONS if s["subtitle"]]
subs = [s["subtitle"] for s in named]
for s in named:
    opts = rng.sample([t for t in subs if t != s["subtitle"]], 3)
    add("seasonname", "seasonname:" + s["name"], f"What was {s['name']} called?", s["subtitle"], opts, f"It started on {s['start']}.", ks=["season:" + s["name"]])
    add("seasonname", "seasonwhich:" + s["name"], f'Which season was called "{s["subtitle"]}"?', s["name"], fair_seasons(s["name"], pool=[t["name"] for t in named]),
        ks=["season:" + s["name"]])
themes = collections.Counter(s["theme"] for s in SEASONS)
for s in SEASONS:
    if s["theme"] in ("None", "") or themes[s["theme"]] > 1 or s["theme"] == s["subtitle"]:
        continue
    add("seasontheme", "seasontheme:" + s["name"], f'Which season\'s theme was "{s["theme"]}"?', s["name"], fair_seasons(s["name"]), ks=["season:" + s["name"]])


def month_year(d):
    m = re.match(r"([A-Za-z]+) \d+\w* (\d{4})", d)
    return f"{m.group(1)} {m.group(2)}" if m else None


starts = {s["name"]: month_year(s["start"]) for s in SEASONS if month_year(s["start"])}
for s in SEASONS:
    my = starts.get(s["name"])
    if not my or "Pre-Season" in s["name"]:
        continue
    others = [starts[n] for n in near_seasons(s["name"], n=6) if starts.get(n) and starts[n] != my]
    if len(set(others)) < 3:
        continue
    add("seasonstart", "seasonstart:" + s["name"], f"When did {s['name']} begin?", my, list(dict.fromkeys(others))[:3], f"It began on {s['start']}.", ks=["season:" + s["name"]])


# ------------------------------------------------------------------ the map: named locations on the Chapter 1 island, season by season
def note(t):
    """Wiki notes as tidy sentences, leaving out anything after Chapter 1 ended (Update v11.00 started Chapter 2)."""
    parts = [p.strip().rstrip(".") for p in t.split(" / ") if p.strip()]
    parts = [p for p in parts if not (m := re.search(r"Update v(\d+)", p)) or int(m.group(1)) <= 10]
    return ". ".join(parts) + "." if parts else None


NORMAL = lambda col: bool(re.match(r"Chapter 1: Season", col))
info = data["islands"]["Athena"]
cols = [c for c in info["seasons"] if NORMAL(c)]
lab = lambda col: "Chapter 1 " + col.split(": ")[1]
isl_pool = [lab(c) for c in cols]
locs = []
for l in info["locations"]:
    pres = [c for c in l["present"] if NORMAL(c)]
    if pres:
        locs.append({"name": l["name"], "pres": pres, "note": l["note"]})
for l in locs:
    name, pres = l["name"], l["pres"]
    if pres[0] != cols[0]:
        add("locadded", f"locadded:{name}", f"In which season was {name} added to the map?", lab(pres[0]), near_seasons(lab(pres[0]), pool=isl_pool),
            note(l["note"].split(" / ")[0]) if l["note"] else None, ks=["loc:" + name])
    if pres[-1] != cols[-1]:
        add("loclast", f"loclast:{name}", f"What was the last season {name} was on the map?", lab(pres[-1]), near_seasons(lab(pres[-1]), pool=isl_pool), ks=["loc:" + name])
    n = len(pres)
    if n > 1 and name != "Pleasant Park":   # Pleasant Park is asked by hand (your example)
        opts = sorted({max(1, n + d) for d in (-3, -2, -1, 1, 2, 3)} - {n}, key=lambda v: (abs(v - n), rng.random()))[:3]
        add("loccount", f"loccount:{name}", f"How many seasons was {name} on the map in Chapter 1?", str(n), [str(v) for v in opts],
            "Counting Season 1 to Season X (not the Pre-Season)." + (" It was on the map in every one of them." if n == len(cols) else ""), ks=["loc:" + name])
    m = re.search(r"Replaced by ([^.]+?) in Update v(\d+)", l["note"])
    if m and len(m.group(1)) < 30 and int(m.group(2)) <= 10:
        repl = m.group(1).strip()
        back = {x["name"]: x["note"] for x in locs}.get(repl, "")
        if repl in l["note"].split("Replaced by")[0] or re.search(r"Replaced by " + re.escape(name) + r" in Update", back):
            continue
        add("locreplaced", f"locreplaced:{name}", f"Which location replaced {name} on the map?", repl, rng.sample([x["name"] for x in locs if x["name"] not in (name, repl)], 3),
            note(l["note"]), ks=["loc:" + name, "loc:" + repl])
for col in cols:   # which places were (or weren't) there in a given season
    here = [l["name"] for l in locs if col in l["pres"]]
    gone = [l["name"] for l in locs if col not in l["pres"]]
    rng.shuffle(here); rng.shuffle(gone)
    for n in here[:6]:
        if len(gone) >= 3:
            add("locseason", f"locin:{col}:{n}", f"Which of these named locations was on the map in {lab(col)}?", n, rng.sample(gone, 3), ks=["loc:" + n])
    for n in gone[:6]:
        add("locseason", f"locout:{col}:{n}", f"Which of these named locations was NOT on the map in {lab(col)}?", n, rng.sample(here, 3), ks=["loc:" + n])

# ------------------------------------------------------------------ live events
def ev_name(n):
    n = re.sub(r"^.*\|", "", n).strip()
    n = re.sub(r" Event$", "", n)
    n = {"Butterfly": "The Butterfly"}.get(n, n)
    return n.title() if n.isupper() else n


evs = [dict(e, name=ev_name(e["name"])) for e in data["events"] if e["chapter"] == 1 and e["name"]]
evs = [e for e in evs if not re.search(r"Aftermath|Rift$|Phase|Part \d", e["name"])]
for e in evs:
    label = "Chapter 1 " + e["season"]
    if label not in POS:
        continue
    add("event", "event:" + e["name"], f'In which season did the live event "{e["name"]}" take place?', label, fair_seasons(label),
        f"{e['summary']} ({e['date'].split(' / ')[0]})" if e["summary"] else None, ks=["event:" + e["name"]])

# ------------------------------------------------------------------ the big moments of each season (checked against the wiki)
BIG = {
    "Chapter 1 Season 2": ["Tilted Towers first appeared", "The first Battle Pass arrived"],
    "Chapter 1 Season 4": ["A meteor crashed into Dusty Depot", "A rocket launched and tore a rift in the sky", "Hop Rocks and Jetpacks arrived"],
    "Chapter 1 Season 5": ["Rifts appeared and a desert and a Viking village came through them", "A purple cube (Kevin) rolled across the island", "All Terrain Karts arrived"],
    "Chapter 1 Season 6": ["Pets arrived as back blings", "The Butterfly event happened at the floating island"],
    "Chapter 1 Season 7": ["Snow covered part of the island and Polar Peak appeared", "Planes (the X-4 Stormwing) arrived", "Fortnite Creative launched", "Marshmello played the first big in-game concert"],
    "Chapter 1 Season 8": ["A volcano appeared and later destroyed Tilted Towers", "Players voted to bring back the Drum Gun"],
    "Chapter 1 Season 9": ["Tilted Towers was rebuilt as Neo Tilted", "A giant robot fought a monster", "The Fortnite World Cup was held in New York"],
    "Chapter 1 Season X": ["B.R.U.T.E. mechs arrived", "The island was sucked into a black hole"],
}
ASKED = {"Tilted Towers first appeared", "The first Battle Pass arrived", "Hop Rocks and Jetpacks arrived", "All Terrain Karts arrived", "Pets arrived as back blings",
         "Planes (the X-4 Stormwing) arrived", "Fortnite Creative launched", "B.R.U.T.E. mechs arrived"}   # already asked by season elsewhere
for season, evs_ in BIG.items():
    others = [e for s2, v in BIG.items() if s2 != season for e in v]
    for ev in evs_:
        if ev not in ASKED:
            add("bigmoment", f"big:{ev}", f'In which season did this happen: "{ev}"?', season, fair_seasons(season, pool=REAL), ks=["big:" + ev])
        add("bigmoment", f"bigin:{ev}", f"Which of these happened in {season}?", ev, rng.sample(others, 3), ks=["big:" + ev])

# ------------------------------------------------------------------ hand-written, checked against the wiki
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
FACTS = [
    # your examples
    F("item", "When Supply Drops were first added, how much health did they have?", "2,000", ["500", "1,000", "1,250"], "They were in the game from the Pre-Season. Update 1.8 in Season 1 cut it to 1,250."),
    F("item", "From Season 7 (Update v7.10), how much health did a Supply Drop have in Solos?", "250", ["100", "500", "750"], "Duos was 500 and Squads 750."),
    F("item", "From Season 7 (Update v7.10), how much health did a Supply Drop have in Squads?", "750", ["500", "1,000", "1,250"], "Solos was 250 and Duos 500."),
    F("map", "In which season was Tilted Towers destroyed by the volcano?", "Chapter 1 Season 8", ["Chapter 1 Season 4", "Chapter 1 Season 9", "Chapter 1 Season X"], "It was destroyed in The Unvaulting live event. Only the No Sweat Insurance building survived, and the ruins became Neo Tilted in Season 9."),
    F("map", "How many seasons was Pleasant Park in the game, from Season 1 to Season X?", "10", ["7", "8", "9"], "Every season of Chapter 1. It was there in the Pre-Season too."),
    F("map", "What replaced the ruins of Tilted Towers in Season 9?", "Neo Tilted", ["Tilted Town", "Mega Mall", "Pressure Plant"]),
    F("map", "In which season was Tilted Towers first added?", "Chapter 1 Season 2", ["Chapter 1 Pre-Season", "Chapter 1 Season 4", "Chapter 1 Season 3"], "It arrived in Update 2.2.0 in January 2018."),
    F("map", "What did the meteor turn Dusty Depot into in Season 4?", "Dusty Divot", ["Dusty Crater", "Risky Reels", "Loot Lake"]),
    F("map", "In Season 5, which desert location replaced Moisty Mire?", "Paradise Palms", ["Lazy Links", "Sunny Steps", "Mega Mall"]),
    F("map", "In Season 9, which location was rebuilt into Mega Mall?", "Retail Row", ["Salty Springs", "Paradise Palms", "Lucky Landing"]),
    F("map", "In Season 7, which mountain was the Infinity Blade found on?", "Polar Peak", ["Snobby Shores", "Frosty Flights", "Happy Hamlet"]),
    F("map", "What was the Chapter 1 island known as?", "Athena", ["Hermes", "Olympus", "Orion"]),
    F("map", "What did the Cube turn Loot Lake into when it dissolved in Season 5?", "A bouncy lake", ["A frozen lake", "A lava lake", "A dried-up crater"]),
    # seasons and history
    F("season", "In which season was the Battle Pass introduced?", "Chapter 1 Season 2", ["Chapter 1 Season 1", "Chapter 1 Season 3", "Chapter 1 Season 4"], "It replaced the Season Shop."),
    F("season", "In which season was Fortnite Creative released?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 8", "Chapter 1 Season 9"]),
    F("season", "In which season did planes (the X-4 Stormwing) arrive?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 9", "Chapter 1 Season 4"]),
    F("season", "In which season were All Terrain Karts (the golf carts) added?", "Chapter 1 Season 5", ["Chapter 1 Season 3", "Chapter 1 Season 7", "Chapter 1 Season 9"]),
    F("season", "In which season were the B.R.U.T.E. mechs added?", "Chapter 1 Season X", ["Chapter 1 Season 7", "Chapter 1 Season 8", "Chapter 1 Season 9"]),
    F("season", "In which season were Pets added?", "Chapter 1 Season 6", ["Chapter 1 Season 4", "Chapter 1 Season 8", "Chapter 1 Season 9"]),
    F("season", "In which season were Fortbytes added?", "Chapter 1 Season 9", ["Chapter 1 Season 7", "Chapter 1 Season X", "Chapter 1 Season 6"]),
    F("season", "How many seasons did Chapter 1 have, not counting the Pre-Season?", "10", ["8", "9", "12"], "Seasons 1 to 9, then Season X."),
    F("season", "What was the last season of Chapter 1 called?", "Season X", ["Season 10", "Season Zero", "Season Omega"]),
    F("season", "What was the first collaboration in Fortnite, in Season 4?", "The Infinity Gauntlet LTM (Avengers: Infinity War)", ["John Wick", "Godzilla", "Batman"]),
    F("season", "In the Infinity Gauntlet LTM, who did you become when you picked up the Gauntlet?", "Thanos", ["Loki", "Ultron", "Red Skull"]),
    F("season", "What was the first Mythic item to appear in normal Battle Royale?", "The Infinity Blade", ["The Infinity Gauntlet", "The Drum Gun", "The Scar"], "It arrived in Season 7."),
    F("season", "In which month and year did Fortnite open to everyone on iPhone?", "April 2018", ["September 2017", "December 2018", "July 2019"]),
    F("season", "What did fans name the purple cube that rolled across the island in Season 5?", "Kevin", ["Steve", "Gary", "Dave"], "It rolled into Loot Lake and dissolved, turning the lake bouncy."),
    F("season", 'What happened in the live event "The End" in October 2019?', "The island was sucked into a black hole", ["The volcano erupted", "A rocket launched", "The island flooded"], "Fortnite showed only the black hole for about two days."),
    F("season", "Which live event let players vote to bring back an item?", "The Unvaulting", ["The Final Showdown", "The End", "The Butterfly"], "Players chose the Drum Gun."),
    F("season", "In The Unvaulting, which weapon did players vote to bring back?", "The Drum Gun", ["The Double Barrel Shotgun", "The Zapotron", "The Infinity Blade"]),
    F("season", "In The Final Showdown event in Season 9, what fought the giant monster?", "A giant robot", ["The Battle Bus", "Kevin the Cube", "The Ice King"]),
    F("season", "Which DJ played the first big in-game concert, at Pleasant Park in February 2019?", "Marshmello", ["Diplo", "Steve Aoki", "Deadmau5"]),
    F("season", "Which character launched the rocket in Season 4?", "The Visitor", ["The Ice King", "The Scientist", "The Prisoner"]),
    # Battle Pass outfits
    F("outbp", "Which outfit was nicknamed \"John Wick\" by players long before the real John Wick arrived?", "The Reaper", ["Raven", "Omega", "Drift"], "The Reaper was the Season 3 Tier 100 reward."),
    # items
    F("item", "How much health does one Bandage heal?", "15", ["10", "25", "50"], "Bandages can't heal you above 75."),
    F("item", "What is the most health Bandages can heal you up to?", "75", ["50", "90", "100"]),
    F("item", "How much health does a Medkit heal?", "100", ["50", "75", "15"]),
    F("item", "How much shield does a Small Shield Potion give?", "25", ["15", "50", "75"], "They only work up to 50 shield."),
    F("item", "What is the most shield Small Shield Potions can give you?", "50", ["25", "75", "100"]),
    F("item", "How much shield does a (big) Shield Potion give?", "50", ["25", "75", "100"]),
    F("item", "What does a Chug Jug do?", "Restores full health and shield", ["Gives 50 shield", "Heals 75 health over time", "Makes you invisible"]),
    F("item", "In which season was the Chug Jug first added?", "Chapter 1 Season 2", ["Chapter 1 Season 1", "Chapter 1 Season 4", "Chapter 1 Pre-Season"], "It came in Update 2.3.0, in January 2018."),
    F("item", "When was the Small Shield Potion added?", "Chapter 1 Pre-Season", ["Chapter 1 Season 1", "Chapter 1 Season 2", "Chapter 1 Season 3"], "It was in Battle Royale from the start."),
    F("item", "What is the most health you can have in Battle Royale?", "100", ["150", "200", "250"]),
    F("item", "What is the most shield you can have in Battle Royale?", "100", ["50", "150", "200"]),
    F("item", "Which rarity colour is Legendary?", "Gold/orange", ["Purple", "Blue", "Green"]),
    F("item", "Which rarity colour is Epic?", "Purple", ["Blue", "Gold/orange", "Green"]),
    F("item", "Which rarity colour is Rare?", "Blue", ["Green", "Purple", "Grey"]),
    F("item", "Which rarity colour is Uncommon?", "Green", ["Grey", "Blue", "Purple"]),
    F("item", "What are the three building materials in Battle Royale?", "Wood, stone and metal", ["Wood, glass and metal", "Stone, metal and plastic", "Wood, brick and ice"]),
    F("item", "Which thrown item makes nearby players dance for a few seconds?", "Boogie Bomb", ["Shockwave Grenade", "Port-a-Fort", "Impulse Grenade"]),
    F("item", "What does a Port-a-Fort do?", "Builds an instant tower fort", ["Teleports you", "Heals your team", "Calls in a Supply Drop"]),
    F("item", "What does a Launch Pad do?", "Launches you into the air so you can glide", ["Builds a ramp", "Heals you", "Spawns a vehicle"]),
    F("item", "Which loot container looks like a piñata?", "Loot Llama", ["Supply Drop", "Ammo Box", "Rare Chest"]),
    F("item", "How much shield does a Shield Mushroom give?", "5", ["1", "10", "25"], "Shield Mushrooms arrived in Season 4."),
    F("item", "How much health does an Apple give?", "5", ["2", "10", "15"]),
    F("item", "What did Hop Rocks do?", "Gave you low gravity for a short time", ["Made you invisible", "Healed you over time", "Fired a homing missile"], "They came from the meteor in Season 4."),
    F("item", "In which season was the Jetpack added?", "Chapter 1 Season 4", ["Chapter 1 Season 3", "Chapter 1 Season 6", "Chapter 1 Season 7"]),
    F("item", "What does a Cozy Campfire do?", "Heals players standing near it", ["Gives your team shield", "Burns nearby enemies", "Revives downed players"]),
    F("item", "What did the Bush item do?", "Disguised you as a bush", ["Healed you inside a bush", "Hid your footsteps", "Grew a wall of bushes"]),
    F("item", "What does Slurp Juice do?", "Restores health and shield over time", ["Gives 50 shield instantly", "Makes you run faster", "Lowers gravity"]),
    F("item", 'Which gun did players call the "SCAR"?', "The gold (Legendary) Assault Rifle", ["The Pump Shotgun", "The Heavy Sniper", "The Tactical SMG"]),
    # general
    F("fact", "Which company makes Fortnite?", "Epic Games", ["Activision", "EA", "Ubisoft"]),
    F("fact", "In which year did Fortnite Battle Royale come out?", "2017", ["2015", "2016", "2018"]),
    F("fact", "Which Fortnite mode came first?", "Save the World", ["Battle Royale", "Creative", "Playground"], "Battle Royale came out a couple of months later in 2017."),
    F("fact", "What do players ride across the island before dropping in?", "The Battle Bus", ["The Loot Llama", "The Storm Wagon", "The Drop Ship"]),
    F("fact", "What is Fortnite's in-game currency called?", "V-Bucks", ["Gold Coins", "Fortcoins", "Tickets"]),
    F("fact", "What do you get for winning a match of Battle Royale?", "A Victory Royale", ["A Chicken Dinner", "A Crown of Victory", "A Golden Bus"]),
    F("fact", "Which banana-themed outfit from Season 8 became one of Fortnite's mascots?", "Peely", ["Fishstick", "Beef Boss", "Tomatohead"]),
    F("fact", "Which character is the face of Fortnite's default outfits?", "Jonesy", ["Raven", "Drift", "Omega"]),
    F("fact", "Who won the solo Fortnite World Cup in 2019?", "Bugha", ["Ninja", "Aqua", "Tfue"], "He won $3 million at 16."),
    F("fact", "How much did the Fortnite World Cup solo champion win in 2019?", "$3 million", ["$1 million", "$500,000", "$10 million"]),
    F("fact", "Where was the 2019 Fortnite World Cup held?", "Arthur Ashe Stadium, New York", ["Wembley Stadium, London", "Staples Center, Los Angeles", "Madison Square Garden, New York"]),
    F("fact", "Who won the duos at the 2019 Fortnite World Cup?", "Aqua and Nyhrox", ["Ninja and Tfue", "Bugha and Mongraal", "Benjyfishy and Mrsavage"], "They shared $3 million."),
    F("fact", "What closes in on players during a match?", "The Storm", ["The Lava", "The Fog", "The Rift"]),
    F("fact", "How many players start a normal Battle Royale match?", "100", ["50", "64", "150"]),
    F("fact", "Which limited-time mode split the players into two teams of 50?", "50v50", ["Playground", "Solid Gold", "Disco Domination"]),
    F("fact", "Which limited-time mode gave out only gold (Legendary) weapons?", "Solid Gold", ["Gold Standard", "Golden Touch", "Golden Ticket"]),
]
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ show seasons as "Season 4", and nothing from Chapter 2 or later, anywhere
def show(t):
    return re.sub(r"Chapter 1 (?=Season|Pre-Season)", "", t) if isinstance(t, str) else t


LATER = re.compile(r"Chapter [2-9]|Season OG|Remix|Apollo|Artemis|Asteria|Helios|Midas|Meowscles|Galactus|Travis Scott|Ariana|Party Royale|Gold Bars|"
                   r"The Agency|Mandalorian|Update v1[1-9]")
for v in Q.values():
    for q in v:
        for key in ("q", "a", "x"):
            if key in q:
                q[key] = show(q[key])
        q["o"] = [show(o) for o in q["o"]]
        if LATER.search(" ".join([q["q"], q["a"], q.get("x", "")] + q["o"])):
            raise SystemExit(f"not Chapter 1: {q}")

# ------------------------------------------------------------------ assemble exactly 1,000
total = sum(len(v) for v in Q.values())
print({k: len(v) for k, v in Q.items()}, total, file=sys.stderr)
bank = [q for v in Q.values() for q in v]
extra = len(bank) - 1000
if extra > 0:   # trim the most obscure outfits
    drop = set(id(q) for q in Q["outseason"][-extra:])
    bank = [q for q in bank if id(q) not in drop]
if len(bank) != 1000:
    raise SystemExit(f"bank has {len(bank)} questions")
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank), collections.Counter(q["c"] for q in bank).most_common(), file=sys.stderr)
