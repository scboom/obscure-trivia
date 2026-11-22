"""Build the Fortnite question bank (1,000 questions).

Outfit and emote seasons come from the Fortnite-API cosmetics database (fortnite-api.com). Seasons, named
locations (season by season, per island) and live events come from the Fortnite Wiki (fortnite.fandom.com).
A small set of hand-written questions covers items, records and general facts, each checked against the wiki.
Only the main Battle Royale island counts for map questions (not Reload, Blitz, OG mode or Creative).
Usage: gen_fortnite.py cosmetics.json data.json OUT.json
"""
import sys, json, random, re, collections

COS, DATA, OUT = sys.argv[1:4]
rng = random.Random(20261124)
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


# ------------------------------------------------------------------ season labels, in order
def wiki_label(chapter, page):
    if page == "Chapter 2 Remix":
        return "Chapter 2 Remix"
    m = re.match(r"Chapter (\d+): (.+)", page)
    if m:
        return f"Chapter {m.group(1)} {m.group(2)}"
    return f"Chapter {chapter} {page}"


SEASONS = [dict(s, name=wiki_label(s["chapter"], s["page"])) for s in data["seasons"]]
ORDER = [s["name"] for s in SEASONS]                       # Chapter 1 Pre-Season ... Chapter 7 Season 4
POS = {n: i for i, n in enumerate(ORDER)}


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


# ------------------------------------------------------------------ outfits and emotes (Chapters 1-5, where the database's season numbers match the game's)
def cos_label(intro):
    ch, s = intro.get("chapter"), intro.get("season")
    if s == "OG":
        return "Chapter 4 Season OG"
    if s == "Remix":
        return "Chapter 2 Remix"
    return f"Chapter {ch} Season {s}"


cos = json.load(open(COS))["data"]
first = {}
for c in cos:
    intro = c.get("introduction")
    if not intro or c["type"]["value"] not in ("outfit", "emote"):
        continue
    if not intro.get("chapter", "").isdigit() or int(intro["chapter"]) > 5:
        continue
    lab = cos_label(intro)
    if lab not in POS:
        continue
    key = (c["type"]["value"], c["name"])
    if key not in first or POS[lab] < POS[first[key]["season"]]:
        first[key] = {"name": c["name"], "type": c["type"]["value"], "season": lab, "series": (c.get("series") or {}).get("value"), "id": c["id"]}
FAMOUS = """Renegade Raider|Aerial Assault Trooper|Ghoul Trooper|Black Knight|Blue Squire|Royale Knight|Sparkle Specialist|The Reaper|Raven|Rex|Tricera Ops|Omega|Carbide|Zoey|Teknique|Valor|Ragnarok|Drift|Calamity|Dire|Chomp Sr.|Peely|The Ice King|Zenith|Lynx|Luxe|Blackheart|Hybrid|Sentinel|Rox|Vendetta|Ultima Knight|Catalyst|Eternal Voyager|Fishstick|Cuddle Team Leader|Rabbit Raider|Dark Bomber|Brite Bomber|Love Ranger|Crackshot|Tomatohead|Beef Boss|Leviathan|Midas|Meowscles|Skye|Brutus|TNTina|Agent Jones|Mancake|Kit|Jules|Eternal Knight|Fusion|Lexa|Raz|Lara Croft|Predator|Kratos|Master Chief|Ariana Grande|Travis Scott|Marshmello|Ninja|LeBron James|Naruto Uzumaki|Peter Griffin|Solid Snake|Darth Vader|Spider-Man|Iron Man|Thor|Deadpool|Wolverine|Black Panther|Captain America|Harley Quinn|Superman|Wonder Woman|The Joker|Aquaman|Snoop Dogg|The Weeknd|Doctor Doom|Storm|Groot|Venom|Carnage|Spider-Gwen|Rey|Kylo Ren|Boba Fett|Obi-Wan Kenobi|Luke Skywalker|Leia Organa|Han Solo|Chewbacca|Indiana Jones|Optimus Prime|Ezio Auditore|Aloy|Chun-Li|Ryu|Cammy|Guile|Doom Slayer|Geralt of Rivia|Leon S. Kennedy|Jill Valentine|Chris Redfield|Neymar Jr|Slim Shady|Ice Spice|Juice WRLD|Hatsune Miku|Daredevil|Sora|Lewis Hamilton|Nick Eh 30|Loserfruit|Lachlan|Bugha|Agent Peely|Fennix|Lt. John Llama|Jonesy The First|Sgt. Winter|Wildcat|Spike|Whiplash|Moisty Merman|Galaxy|Wonder|Glow|Scorpion|Nog Ops|Merry Marauder|Crystal|Skull Ranger|Dark Voyager|Elite Agent|Sun Strider|Funk Ops|Rust Lord|Mission Specialist|Moonwalker|Burnout|Lucky Rider|John Wick""".split("|")
SERIES_OK = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series", "Gaming Legends Series"}
outfits = {n: o for (t, n), o in first.items() if t == "outfit"}
pool = [outfits[n] for n in FAMOUS if n in outfits]
famous_names = {o["name"] for o in pool}
series_pool = [o for o in outfits.values() if o["series"] in SERIES_OK and o["name"] not in famous_names]
rng.shuffle(series_pool)
OUTFITS = pool + series_pool[:150]
print("outfits", len(pool), "famous +", min(150, len(series_pool)), "collab", file=sys.stderr)

# outfits people mix up, explained after answering
OUTFIT_NOTE = {
    "John Wick": "The official John Wick outfit came with the John Wick: Chapter 3 crossover in May 2019. Players had already nicknamed The Reaper (Season 3) \"John Wick\".",
    "The Reaper": "Players nicknamed it \"John Wick\". The official John Wick outfit didn't arrive until Chapter 1 Season 9.",
}
for o in OUTFITS:
    the = "" if o["name"].startswith("The ") else "the "
    add("outseason", "outseason:" + o["name"], f"In which season was {the}{o['name']} outfit added to Fortnite?", o["season"], near_seasons(o["season"]),
        OUTFIT_NOTE.get(o["name"]), ks=["outfit:" + o["name"]] + (["outfit:John Wick"] if o["name"] == "The Reaper" else []))
tries = 0
while len(Q["outfirst"]) < 55 and tries < 50000:
    tries += 1
    os_ = sorted(rng.sample(pool, 4), key=lambda o: POS[o["season"]])
    ps = [POS[o["season"]] for o in os_]
    if any(b - a < 2 for a, b in zip(ps, ps[1:])) or ps[-1] - ps[0] > 16:
        continue
    add("outfirst", "outfirst:" + "|".join(sorted(o["name"] for o in os_)), "Which of these outfits came out first?", os_[0]["name"], [o["name"] for o in os_[1:]],
        " · ".join(f"{o['name']}: {o['season']}" for o in os_) + ".", ks=["outfit:" + o["name"] for o in os_])
SERIES_NAME = {"Icon Series": "the Icon Series (real-life stars)", "MARVEL SERIES": "the Marvel Series", "DC SERIES": "the DC Series",
               "Star Wars Series": "the Star Wars Series", "Gaming Legends Series": "the Gaming Legends Series"}
nonseries = [o for o in pool if not o["series"]]
for ser, nice in SERIES_NAME.items():
    members = [o for o in OUTFITS if o["series"] == ser]
    rng.shuffle(members)
    for o in members[:9]:
        wrong = [w["name"] for w in rng.sample(nonseries, 3)]
        add("outseries", f"outseries:{o['name']}", f"Which of these outfits is part of {nice}?", o["name"], wrong, ks=["outfit:" + o["name"]])
EMOTES = """Floss|Default Dance|Take The L|Orange Justice|Best Mates|Electro Shuffle|Fresh|Hype|Scenario|Laugh It Up|Ride the Pony|Dab|Groove Jam|Rambunctious|Breakin'|Pure Salt|Smooth Moves|Infinite Dab|Rollie|Tidy|Boogie Down|Get Griddy|Toosie Slide|Renegade|Say So|Distraction|Jabba Switchway|Gangnam Style|Billy Bounce|The Robot|Leave the Door Open|Pump Up the Jam|Lil' Treat|Hot Marat|Zany|Bring It Around""".split("|")
emotes = {n: o for (t, n), o in first.items() if t == "emote"}
for n in EMOTES:
    if n in emotes:
        o = emotes[n]
        add("emote", "emote:" + n, f"In which season was the '{n}' emote added?", o["season"], near_seasons(o["season"]), ks=["emote:" + n])

# ------------------------------------------------------------------ seasons
named = [s for s in SEASONS if s["subtitle"] and s["subtitle"] not in ("Chapter 2 Remix", "Fortnite: OG")]
subs = [s["subtitle"] for s in named]
for s in named:
    same = [t["subtitle"] for t in named if t["chapter"] == s["chapter"] and t is not s]
    other = [t for t in subs if t != s["subtitle"] and t not in same]
    opts = (rng.sample(same, min(2, len(same))) + rng.sample(other, 3))[:3]
    add("seasonname", "seasonname:" + s["name"], f"What was {s['name']} called?", s["subtitle"], opts, f"It started on {s['start']}.", ks=["season:" + s["name"]])
    add("seasonname", "seasonwhich:" + s["name"], f"Which season was called '{s['subtitle']}'?", s["name"], near_seasons(s["name"], pool=[t["name"] for t in named]),
        ks=["season:" + s["name"]])
themes = collections.Counter(s["theme"] for s in SEASONS)
for s in SEASONS:
    if s["theme"] in ("None", "") or themes[s["theme"]] > 1 or "/" in s["theme"] and len(s["theme"]) > 40:
        continue
    add("seasontheme", "seasontheme:" + s["name"], f"Which season's theme was '{s['theme']}'?", s["name"], near_seasons(s["name"]), ks=["season:" + s["name"]])
MONTHS = "January February March April May June July August September October November December".split()


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

# ------------------------------------------------------------------ the map: named locations on each Battle Royale island
def note(t):
    """Wiki notes as tidy sentences."""
    parts = [p.strip().rstrip(".") for p in t.split(" / ") if p.strip()]
    return ". ".join(parts) + "."


CHAPTER_OF = {"Athena": 1, "Apollo": 2, "Artemis": 3, "Asteria": 4, "Helios": 5, "Oninoshima": 6, "Golden Coast": 7, "Shattered Coast": 7}
NORMAL = lambda col: not re.search(r"Pre-Season|Season OG|Remix|Mini Season", col)
islands = {k: v for k, v in data["islands"].items() if k in CHAPTER_OF}
where = collections.defaultdict(set)
for isl, info in islands.items():
    for l in info["locations"]:
        if any(NORMAL(c) for c in l["present"]):
            where[l["name"]].add(CHAPTER_OF[isl])
for isl, info in islands.items():
    ch = CHAPTER_OF[isl]
    cols = [c for c in info["seasons"] if NORMAL(c)]
    for l in info["locations"]:
        pres = [c for c in l["present"] if NORMAL(c)]
        if not pres:
            continue
        name, firstcol = l["name"], pres[0]
        label = wiki_label(ch, firstcol)
        if firstcol != cols[0] and label in POS:
            add("locadded", f"locadded:{isl}:{name}", f"In which season was {name} added to the Battle Royale map?", label,
                near_seasons(label, pool=[wiki_label(ch, c) for c in cols if wiki_label(ch, c) in POS] if len(cols) >= 4 else None),
                note(l["note"].split(" / ")[0]) if l["note"] else None, ks=["loc:" + name])
        if len(where[name]) == 1:
            add("locchapter", f"locchapter:{name}", f"In which chapter was {name} a named location on the Battle Royale map?", f"Chapter {ch}",
                rng.sample([f"Chapter {c}" for c in range(1, 8) if c != ch], 3), ks=["loc:" + name])
        if len(cols) >= 4 and isl in ("Athena", "Apollo", "Artemis", "Asteria", "Helios", "Oninoshima"):
            n = len(pres)
            opts = sorted({max(1, n + d) for d in (-3, -2, -1, 1, 2, 3)} - {n}, key=lambda v: (abs(v - n), rng.random()))[:3]
            if 1 < n:
                add("loccount", f"loccount:{isl}:{name}", f"How many seasons was {name} on the Chapter {ch} map?", str(n), [str(v) for v in opts],
                    f"Counting the main Battle Royale island only (not OG, Remix or mini-seasons).", ks=["loc:" + name])
        m = re.search(r"Replaced by ([^.]+?) in Update", l["note"])
        if m and len(m.group(1)) < 30:
            repl = m.group(1).strip()
            back = {x["name"]: x["note"] for x in info["locations"]}.get(repl, "")
            # skip temporary swaps where the original came straight back (Shining Span -> Shattered Span -> Shining Span)
            if repl in l["note"].split("Replaced by")[0] or re.search(r"Replaced by " + re.escape(name) + r" in Update", back) \
                    or re.search(r"(?:Returned replacing|Replaced) " + re.escape(repl) + r" in Update", l["note"].split("Replaced by")[-1]):
                continue
            others = [x["name"] for x in info["locations"] if x["name"] not in (name, repl)]
            add("locreplaced", f"locreplaced:{isl}:{name}", f"Which location replaced {name} on the Chapter {ch} map?", repl, rng.sample(others, 3),
                note(l["note"]), ks=["loc:" + name, "loc:" + repl])
for ch in range(1, 8):
    here = [n for n, chs in where.items() if chs == {ch}]
    not_here = [n for n, chs in where.items() if ch not in chs]
    rng.shuffle(here)
    for n in here[:7]:
        add("locwhich", f"locwhich:{ch}:{n}", f"Which of these was a named location on the Chapter {ch} map?", n, rng.sample(not_here, 3), ks=["loc:" + n])
# your example: Pleasant Park across Chapters 1 and 2
def count(isl, name):
    l = next((x for x in islands[isl]["locations"] if x["name"] == name), None)
    return len([c for c in l["present"] if NORMAL(c)]) if l else 0


for name in ("Pleasant Park", "Retail Row", "Salty Springs", "Lazy Lake", "Holly Hedges"):
    a, b = count("Athena", name), count("Apollo", name)
    if a and b:
        tot = a + b
        add("map", f"loccount12:{name}", f"Counting Chapters 1 and 2, how many seasons was {name} on the Battle Royale map?", str(tot),
            [str(tot + d) for d in (-4, -2, 2)], f"{a} seasons in Chapter 1 and {b} in Chapter 2 (not counting the Pre-Season, OG or Remix).", ks=["loc:" + name])

# ------------------------------------------------------------------ live events
evs = [e for e in data["events"] if e["name"] and not re.search(r"Aftermath|Rift$|Phase|Part \d", e["name"])]
for e in evs:
    lab = e["season"] if e["season"].startswith("Chapter") else f"Chapter 1 {e['season']}"
    lab = wiki_label(e["chapter"], lab) if lab.startswith("Chapter") and ":" in lab else lab
    if lab not in POS:
        continue
    add("event", "event:" + e["name"], f"In which season did the '{e['name']}' live event take place?", lab, near_seasons(lab),
        f"{e['summary']} ({e['date'].split(' / ')[0]})" if e["summary"] else None, ks=["event:" + e["name"]])

# ------------------------------------------------------------------ hand-written, checked against the wiki
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
FACTS = [
    # your examples
    F("item", "When Supply Drops were first added, how much health did they have?", "2,000", ["500", "1,000", "1,250"], "They came in Update v1.6.4. Season 1 (v1.8) cut it to 1,250."),
    F("item", "From Chapter 1 Season 7 (Update v7.10), how much health did a Supply Drop have in Solos?", "250", ["100", "500", "750"], "Duos was 500 and Squads 750."),
    F("item", "From Chapter 1 Season 7 (Update v7.10), how much health did a Supply Drop have in Squads?", "750", ["500", "1,000", "1,250"], "Solos was 250 and Duos 500."),
    F("map", "In which season was Tilted Towers destroyed by the volcano?", "Chapter 1 Season 8", ["Chapter 1 Season 4", "Chapter 1 Season 9", "Chapter 1 Season X"], "It was destroyed in The Unvaulting live event. Only the No Sweat Insurance building survived, and the ruins became Neo Tilted in Season 9."),
    F("map", "What replaced the ruins of Tilted Towers in Chapter 1 Season 9?", "Neo Tilted", ["Tilted Town", "Mega Mall", "Pressure Plant"]),
    F("map", "In which season was Tilted Towers first added?", "Chapter 1 Season 2", ["Chapter 1 Pre-Season", "Chapter 1 Season 4", "Chapter 1 Season 3"]),
    F("map", "What did the meteor turn Dusty Depot into in Chapter 1 Season 4?", "Dusty Divot", ["Dusty Crater", "Risky Reels", "Loot Lake"]),
    F("map", "In Chapter 1 Season 5, which desert location replaced Moisty Mire?", "Paradise Palms", ["Lazy Links", "Sunny Steps", "Mega Mall"]),
    F("map", "What was the Chapter 1 island known as?", "Athena", ["Apollo", "Artemis", "Asteria"]),
    F("map", "What is the Chapter 2 island known as?", "Apollo", ["Athena", "Artemis", "Helios"]),
    F("map", "What is the Chapter 3 island known as?", "Artemis", ["Apollo", "Asteria", "Helios"]),
    F("map", "What is the Chapter 4 island known as?", "Asteria", ["Artemis", "Helios", "Athena"]),
    F("map", "What is the Chapter 5 island known as?", "Helios", ["Asteria", "Artemis", "Apollo"]),
    F("map", "Chapter 6's island was based on which country?", "Japan", ["China", "South Korea", "Brazil"], "It's called Oninoshima."),
    F("map", "In Chapter 1 Season 7, which mountain was the Infinity Blade found on?", "Polar Peak", ["Snobby Shoals", "Frosty Flights", "Happy Hamlet"]),
    # seasons and history
    F("season", "In which season was the Battle Pass introduced?", "Chapter 1 Season 2", ["Chapter 1 Season 1", "Chapter 1 Season 3", "Chapter 1 Season 4"]),
    F("season", "In which season was Fortnite Creative released?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 8", "Chapter 2 Season 1"]),
    F("season", "In which season were swimming and boats added?", "Chapter 2 Season 1", ["Chapter 1 Season X", "Chapter 2 Season 3", "Chapter 1 Season 8"]),
    F("season", "In which season did planes (the X-4 Stormwing) arrive?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 9", "Chapter 2 Season 2"]),
    F("season", "In which season were Gliders added?", "Chapter 1 Season 2", ["Chapter 1 Season 3", "Chapter 1 Season 5", "Chapter 1 Pre-Season"]),
    F("season", "In which season were Pets added?", "Chapter 1 Season 6", ["Chapter 1 Season 4", "Chapter 1 Season 8", "Chapter 2 Season 1"]),
    F("season", "In which season were Fortbytes added?", "Chapter 1 Season 9", ["Chapter 1 Season 7", "Chapter 1 Season X", "Chapter 2 Season 1"]),
    F("season", "In which season could you first drive the Battle Bus?", "Chapter 7 Season 2", ["Chapter 6 Season 4", "Chapter 7 Season 1", "Chapter 7 Season 3"]),
    F("season", "How many seasons did Chapter 1 have, not counting the Pre-Season?", "10", ["8", "9", "12"], "Seasons 1 to 9, then Season X."),
    F("season", "How many seasons did Chapter 2 have (not counting Chapter 2 Remix)?", "8", ["6", "10", "4"]),
    F("season", "How many seasons did Chapter 3 have?", "4", ["3", "5", "8"]),
    F("season", "What was the last season of Chapter 1 called?", "Season X", ["Season 10", "Season Zero", "Season Omega"]),
    F("season", "What was the first collaboration in Fortnite, in Chapter 1 Season 4?", "The Infinity Gauntlet LTM (Avengers: Infinity War)", ["John Wick", "Star Wars", "Batman"]),
    F("season", "What was the first Mythic item to appear in normal Battle Royale?", "The Infinity Blade", ["The Infinity Gauntlet", "Midas' Drum Gun", "The Scar"], "It arrived in Chapter 1 Season 7."),
    F("season", "In which month and year did Fortnite come to iPhones?", "April 2018", ["September 2017", "December 2018", "July 2019"]),
    F("season", "What happened at 'The End' live event in October 2019?", "The island was sucked into a black hole", ["The volcano erupted", "A rocket launched", "The island flooded"], "Fortnite showed only the black hole for about two days before Chapter 2."),
    F("season", "Which Chapter 1 live event let players vote to bring back an item?", "The Unvaulting", ["The Final Showdown", "The End", "The Butterfly"], "Players chose the Drum Gun."),
    F("season", "In The Unvaulting, which weapon did players vote to bring back?", "The Drum Gun", ["The Double Barrel Shotgun", "The Zapotron", "The Infinity Blade"]),
    F("season", "Which DJ played the first big in-game concert, at Pleasant Park in February 2019?", "Marshmello", ["Travis Scott", "Ariana Grande", "Eminem"]),
    F("season", "Which rapper's 'Astronomical' concert happened in April 2020?", "Travis Scott", ["Eminem", "Snoop Dogg", "Juice WRLD"]),
    F("season", "Which singer headlined the 'Rift Tour' in August 2021?", "Ariana Grande", ["Billie Eilish", "Lady Gaga", "Dua Lipa"]),
    F("season", "Which rapper starred in 'The Big Bang' live event that started Chapter 5?", "Eminem", ["Snoop Dogg", "Travis Scott", "Ice Spice"]),
    # items
    F("item", "How much health does one Bandage heal?", "15", ["10", "25", "50"], "Bandages can't heal you above 75."),
    F("item", "What is the most health Bandages can heal you up to?", "75", ["50", "90", "100"]),
    F("item", "How much health does a Medkit heal?", "100", ["50", "75", "15"]),
    F("item", "How much shield does a Small Shield Potion give?", "25", ["15", "50", "75"], "They only work up to 50 shield."),
    F("item", "What is the most shield Small Shield Potions can give you?", "50", ["25", "75", "100"]),
    F("item", "How much shield does a (big) Shield Potion give?", "50", ["25", "75", "100"]),
    F("item", "What does a Chug Jug do?", "Restores full health and shield", ["Gives 50 shield", "Heals 75 health over time", "Makes you invisible"]),
    F("item", "In which season was the Chug Jug first added?", "Chapter 1 Season 2", ["Chapter 1 Season 1", "Chapter 1 Season 4", "Chapter 1 Pre-Season"]),
    F("item", "In which season was the Small Shield Potion first added?", "Chapter 1 Season 2", ["Chapter 1 Pre-Season", "Chapter 1 Season 3", "Chapter 1 Season 5"]),
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
    # general
    F("fact", "Which company makes Fortnite?", "Epic Games", ["Activision", "EA", "Ubisoft"]),
    F("fact", "In which year did Fortnite Battle Royale come out?", "2017", ["2015", "2016", "2018"]),
    F("fact", "Which Fortnite mode came first?", "Save the World", ["Battle Royale", "Creative", "LEGO Fortnite"], "Battle Royale came out a couple of months later in 2017."),
    F("fact", "What do players ride across the island before dropping in?", "The Battle Bus", ["The Loot Llama", "The Storm Wagon", "The Drop Ship"]),
    F("fact", "What is Fortnite's in-game currency called?", "V-Bucks", ["Gold Bars", "Fortcoins", "Tickets"]),
    F("fact", "What do you get for winning a match of Battle Royale?", "A Victory Royale", ["A Chicken Dinner", "A Crown of Victory", "A Golden Bus"]),
    F("fact", "Which banana-themed outfit is one of Fortnite's mascots?", "Peely", ["Fishstick", "Beef Boss", "Tomatohead"]),
    F("fact", "Which character is the face of Fortnite's default outfits and the Imagined Order story?", "Jonesy", ["Midas", "Drift", "Raven"]),
    F("fact", "Who won the solo Fortnite World Cup in 2019?", "Bugha", ["Ninja", "Aqua", "Tfue"], "He won $3 million at 16."),
    F("fact", "How much did the Fortnite World Cup solo champion win in 2019?", "$3 million", ["$1 million", "$500,000", "$10 million"]),
    F("fact", "Where was the 2019 Fortnite World Cup held?", "Arthur Ashe Stadium, New York", ["Wembley Stadium, London", "Staples Center, Los Angeles", "Madison Square Garden, New York"]),
    F("fact", "What closes in on players during a match?", "The Storm", ["The Lava", "The Fog", "The Zero Point"]),
    F("fact", "Which famous streamer was the first to get his own Icon Series outfit?", "Ninja", ["Tfue", "Lachlan", "Bugha"], "It came out in January 2020."),
    F("fact", "Which actor voices The Foundation?", "Dwayne Johnson", ["Vin Diesel", "Keanu Reeves", "Jason Momoa"]),
    F("fact", "What is the name of the group led by The Foundation?", "The Seven", ["The Imagined Order", "Ghost", "Shadow"]),
    F("fact", "Which two agencies fought each other in Chapter 2 Season 2?", "Ghost and Shadow", ["The Seven and the IO", "Alpha and Omega", "Red and Blue"]),
    F("fact", "Who was the boss of The Agency in Chapter 2 Season 2?", "Midas", ["Meowscles", "Brutus", "Skye"]),
    F("fact", "Which cat-themed agent was a Chapter 2 Season 2 Battle Pass outfit?", "Meowscles", ["Kit", "Lynx", "Sgt. Winter"]),
]
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ assemble exactly 1,000
total = sum(len(v) for v in Q.values())
print({k: len(v) for k, v in Q.items()}, total, file=sys.stderr)
# a balance of question types: not too much of the map, plenty of outfits and seasons
LIMIT = {"locchapter": 90, "locreplaced": 60, "locadded": 60, "loccount": 45}
for k, n in LIMIT.items():
    Q[k] = Q[k][:n]
bank = [q for v in Q.values() for q in v]
extra = len(bank) - 1000
if extra > 0:
    drop = set(id(q) for q in Q["outseason"][-extra:])
    bank = [q for q in bank if id(q) not in drop]
if len(bank) != 1000:
    raise SystemExit(f"bank has {len(bank)} questions")
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank), file=sys.stderr)
