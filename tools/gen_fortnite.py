"""Build the OG Fortnite question bank (1,000 questions): Chapter 1 and Chapter 2 only.

Nothing from Chapter 3 onwards, Fortnite OG (2023) or Chapter 2 Remix (2024), in questions or in the wrong answers.
Outfit and emote seasons come from the Fortnite-API cosmetics database (fortnite-api.com). Seasons, named
locations (season by season, on Athena and Apollo) and live events come from the Fortnite Wiki (fortnite.fandom.com).
A set of hand-written questions covers items, Battle Pass outfits, records and history, each checked against the wiki.
Only the main Battle Royale island counts for map questions.
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


# ------------------------------------------------------------------ season labels, in order: Chapter 1 Pre-Season ... Chapter 2 Season 8
def wiki_label(chapter, page):
    m = re.match(r"Chapter (\d+): (.+)", page)
    if m:
        return f"Chapter {m.group(1)} {m.group(2)}"
    return f"Chapter {chapter} {page}"


SEASONS = [dict(s, name=wiki_label(s["chapter"], s["page"])) for s in data["seasons"]]
SEASONS = [s for s in SEASONS if s["chapter"] <= 2 and "Remix" not in s["name"]]
ORDER = [s["name"] for s in SEASONS]
POS = {n: i for i, n in enumerate(ORDER)}
assert ORDER[0] == "Chapter 1 Pre-Season" and ORDER[-1] == "Chapter 2 Season 8", ORDER


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


# ------------------------------------------------------------------ outfits and emotes from Chapters 1 and 2
cos = json.load(open(COS))["data"]
first = {}
for c in cos:
    intro = c.get("introduction")
    if not intro or c["type"]["value"] not in ("outfit", "emote"):
        continue
    if str(intro.get("chapter")) not in ("1", "2"):
        continue
    lab = f"Chapter {intro['chapter']} Season {intro.get('season')}"
    if lab not in POS:
        continue
    key = (c["type"]["value"], c["name"])
    if key not in first or POS[lab] < POS[first[key]["season"]]:
        first[key] = {"name": c["name"], "type": c["type"]["value"], "season": lab, "series": (c.get("series") or {}).get("value"),
                      "rarity": (c.get("rarity") or {}).get("value"), "id": c["id"]}
FAMOUS = """Renegade Raider|Aerial Assault Trooper|Ghoul Trooper|Skull Trooper|Black Knight|Blue Squire|Royale Knight|Sparkle Specialist|The Reaper|Raven|Rex|Tricera Ops|Omega|Carbide|Zoey|Teknique|Valor|Ragnarok|Drift|Calamity|Dire|Chomp Sr.|Peely|The Ice King|Zenith|Lynx|Luxe|Blackheart|Hybrid|Sentinel|Rox|Vendetta|Ultima Knight|Catalyst|Eternal Voyager|Fishstick|Cuddle Team Leader|Rabbit Raider|Dark Bomber|Brite Bomber|Love Ranger|Crackshot|Tomatohead|Beef Boss|Leviathan|Midas|Meowscles|Skye|Brutus|TNTina|Agent Jones|Mancake|Kit|Jules|Eternal Knight|Fusion|Lexa|Raz|Lara Croft|Predator|Kratos|Master Chief|Ariana Grande|Travis Scott|Marshmello|Ninja|Daredevil|Darth Vader|Spider-Man|Iron Man|Thor|Deadpool|Wolverine|Black Panther|Captain America|Harley Quinn|Superman|Wonder Woman|The Joker|Aquaman|Doctor Doom|Storm|Groot|Venom|Carnage|Rey|Kylo Ren|Mandalorian|The Mandalorian|Ryu|Chun-Li|Aloy|Neymar Jr|Loserfruit|Lachlan|Bugha|Agent Peely|Fennix|Lt. John Llama|Jonesy The First|Sgt. Winter|Wildcat|Spike|Whiplash|Moisty Merman|Galaxy|Wonder|Glow|Scorpion|Nog Ops|Merry Marauder|Crystal|Skull Ranger|Dark Voyager|Elite Agent|Sun Strider|Funk Ops|Rust Lord|Mission Specialist|Moonwalker|Burnout|Lucky Rider|John Wick|Red Knight|Cuddle Team Leader|Highland Warrior|Havoc|Ice Queen|Lace|Fable|Hollowhead|Galactus|Silver Surfer|She-Hulk|Mystique|Cyclops|Shuri|Taskmaster|Bunker Jonesy|Kymera|Doctor Slone|Toona Fish|Charlotte|Gunnar|J.B. Chimpanski""".split("|")
SERIES_OK = {"Icon Series", "MARVEL SERIES", "DC SERIES", "Star Wars Series", "Gaming Legends Series"}
outfits = {n: o for (t, n), o in first.items() if t == "outfit"}
pool = list({outfits[n]["name"]: outfits[n] for n in FAMOUS if n in outfits}.values())
famous_names = {o["name"] for o in pool}
series_pool = [o for o in outfits.values() if o["series"] in SERIES_OK and o["name"] not in famous_names]
rng.shuffle(series_pool)
RANK = {"legendary": 0, "epic": 1, "rare": 2, "uncommon": 3}
rest = [o for o in outfits.values() if o["name"] not in famous_names and o["series"] not in SERIES_OK]
rng.shuffle(rest)
rest.sort(key=lambda o: RANK.get(o["rarity"], 4))   # the better-known Legendary and Epic outfits first
OUTFITS = pool + series_pool + rest                    # the bank is trimmed from the end, so the most obscure go first
print("outfits", len(pool), "famous +", len(series_pool), "collab +", len(rest), "others", file=sys.stderr)

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
while len(Q["outfirst"]) < 80 and tries < 80000:
    tries += 1
    os_ = sorted(rng.sample(pool, 4), key=lambda o: POS[o["season"]])
    ps = [POS[o["season"]] for o in os_]
    if any(b - a < 2 for a, b in zip(ps, ps[1:])) or ps[-1] - ps[0] > 14:
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
        wrong = [w["name"] for w in rng.sample(nonseries, 3)]
        add("outseries", f"outseries:{o['name']}", f"Which of these outfits is part of {nice}?", o["name"], wrong, ks=["outfit:" + o["name"]])
EMOTES = """Floss|Take The L|Orange Justice|Best Mates|Electro Shuffle|Fresh|Hype|Scenario|Laugh It Up|Ride the Pony|Dab|Groove Jam|Rambunctious|Breakin'|Pure Salt|Smooth Moves|Infinite Dab|Rollie|Tidy|Boogie Down|Toosie Slide|Renegade|Say So|Distraction|Billy Bounce|The Robot|Leave the Door Open|Pump Up the Jam|Lil' Treat|Zany|Bring It Around|Squat Kick|Wiggle|Flapper|Disco Fever|Jubilation|True Heart|Freestylin'|Pop Lock|Hootenanny|Rawr|Living Large|Crackdown|Poki|Kiss the Cup|Fancy Feet|Intensity|Bendy|Mime Time|Reanimated|Lazy Shuffle|Phone It In|Make it Rain|Confused|Llama Conga|Gun Show|The Worm|Hula|Star Power|Shimmer|Jaywalking|Tai Chi|Slitherin'|Glowsticks|Dance Therapy|Hand Signals|Salute|Clean Groove|Mic Drop|Blinding Lights|Savage|Dynamite|Wake Up""".split("|")
emotes = {n: o for (t, n), o in first.items() if t == "emote"}
for n in EMOTES:
    if n in emotes:
        o = emotes[n]
        add("emote", "emote:" + n, f"In which season was the '{n}' emote added?", o["season"], near_seasons(o["season"]), ks=["emote:" + n])

# ------------------------------------------------------------------ seasons
named = [s for s in SEASONS if s["subtitle"]]
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
    if s["theme"] in ("None", "") or themes[s["theme"]] > 1 or s["theme"] == s["subtitle"]:
        continue
    add("seasontheme", "seasontheme:" + s["name"], f"Which season's theme was '{s['theme']}'?", s["name"], near_seasons(s["name"]), ks=["season:" + s["name"]])


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


# ------------------------------------------------------------------ the map: named locations on Athena (Chapter 1) and Apollo (Chapter 2)
END_UPDATE = {1: 11, 2: 19}   # Chapter 2 began with Update v11.00, Chapter 3 with v19.00


def note(t, ch):
    """Wiki notes as tidy sentences, leaving out anything after the chapter ended (Fortnite OG, Chapter 2 Remix)."""
    parts = [p.strip().rstrip(".") for p in t.split(" / ") if p.strip()]
    parts = [p for p in parts if not (m := re.search(r"Update v(\d+)", p)) or int(m.group(1)) <= END_UPDATE[ch]]
    return ". ".join(parts) + "." if parts else None


CHAPTER_OF = {"Athena": 1, "Apollo": 2}
NORMAL = lambda col: not re.search(r"Pre-Season|Season OG|Remix|Mini Season|Chapter [3-9]", col)
COUNT_NOTE = {1: "Counting Chapter 1 Seasons 1 to X (not the Pre-Season, or the island's return in Fortnite OG).",
              2: "Counting Chapter 2 Seasons 1 to 8 (not Chapter 2 Remix)."}
islands = {k: v for k, v in data["islands"].items() if k in CHAPTER_OF}
where = collections.defaultdict(set)
for isl, info in islands.items():
    for l in info["locations"]:
        if any(NORMAL(c) for c in l["present"]):
            where[l["name"]].add(CHAPTER_OF[isl])
for isl, info in islands.items():
    ch = CHAPTER_OF[isl]
    cols = [c for c in info["seasons"] if NORMAL(c)]
    island_pool = [wiki_label(ch, c) for c in cols]
    for l in info["locations"]:
        pres = [c for c in l["present"] if NORMAL(c)]
        if not pres:
            continue
        name, firstcol, lastcol = l["name"], pres[0], pres[-1]
        label = wiki_label(ch, firstcol)
        if firstcol != cols[0]:
            add("locadded", f"locadded:{isl}:{name}", f"In which season was {name} added to the Chapter {ch} map?", label,
                near_seasons(label, pool=island_pool), note(l["note"].split(" / ")[0], ch) if l["note"] else None, ks=["loc:" + name])
        if lastcol != cols[-1]:
            last = wiki_label(ch, lastcol)
            add("loclast", f"loclast:{isl}:{name}", f"What was the last season {name} was on the Chapter {ch} map?", last,
                near_seasons(last, pool=island_pool), ks=["loc:" + name])
        n = len(pres)
        if 1 < n:
            opts = sorted({max(1, n + d) for d in (-3, -2, -1, 1, 2, 3)} - {n}, key=lambda v: (abs(v - n), rng.random()))[:3]
            add("loccount", f"loccount:{isl}:{name}", f"How many seasons was {name} on the Chapter {ch} map?", str(n), [str(v) for v in opts],
                COUNT_NOTE[ch], ks=["loc:" + name])
        m = re.search(r"Replaced by ([^.]+?) in Update", l["note"])
        if m and len(m.group(1)) < 30:
            repl = m.group(1).strip()
            back = {x["name"]: x["note"] for x in info["locations"]}.get(repl, "")
            # skip temporary swaps where the original came straight back
            if repl in l["note"].split("Replaced by")[0] or re.search(r"Replaced by " + re.escape(name) + r" in Update", back) \
                    or re.search(r"(?:Returned replacing|Replaced) " + re.escape(repl) + r" in Update", l["note"].split("Replaced by")[-1]):
                continue
            others = [x["name"] for x in info["locations"] if x["name"] not in (name, repl)]
            add("locreplaced", f"locreplaced:{isl}:{name}", f"Which location replaced {name} on the Chapter {ch} map?", repl, rng.sample(others, 3),
                note(l["note"], ch), ks=["loc:" + name, "loc:" + repl])
only = {ch: [n for n, chs in where.items() if chs == {ch}] for ch in (1, 2)}
both = [n for n, chs in where.items() if chs == {1, 2}]
for ch in (1, 2):
    for n in only[ch]:
        add("locwhich", f"locwhich:{ch}:{n}", f"Which of these was a named location on the Chapter {ch} map?", n, rng.sample(only[3 - ch], 3), ks=["loc:" + n])
        add("locwhich", f"locnot:{ch}:{n}", f"Which of these was NOT a named location on the Chapter {3 - ch} map?", n,
            rng.sample(only[3 - ch], 3), f"{n} was on the Chapter {ch} map.", ks=["loc:" + n])
for n in both:
    add("locboth", f"locboth:{n}", "Which of these named locations was on both the Chapter 1 and Chapter 2 maps?", n,
        rng.sample(only[1], 2) + rng.sample(only[2], 1), ks=["loc:" + n])


def count(isl, name):
    l = next((x for x in islands[isl]["locations"] if x["name"] == name), None)
    return len([c for c in l["present"] if NORMAL(c)]) if l else 0


for name in both:   # your example: Pleasant Park across Chapters 1 and 2
    a, b = count("Athena", name), count("Apollo", name)
    tot = a + b
    add("map", f"loccount12:{name}", f"Counting Chapters 1 and 2, how many seasons was {name} on the Battle Royale map?", str(tot),
        [str(tot + d) for d in (-4, -2, 2)], f"{a} seasons in Chapter 1 and {b} in Chapter 2 (not counting the Pre-Season, Fortnite OG or Chapter 2 Remix).",
        ks=["loc:" + name])

# ------------------------------------------------------------------ live events
def ev_name(n):
    n = re.sub(r"^.*\|", "", n).strip()
    n = re.sub(r" Event$", "", n)
    n = {"Butterfly": "The Butterfly"}.get(n, n)
    return n.title() if n.isupper() else n


evs = [dict(e, name=ev_name(e["name"])) for e in data["events"] if e["chapter"] <= 2 and e["name"]]
evs = [e for e in evs if not re.search(r"Aftermath|Rift$|Phase|Part \d", e["name"])]
dupes = {n for n, k in collections.Counter(e["name"] for e in evs).items() if k > 1}   # 'The End' happened twice: asked by hand instead
for e in evs:
    lab = e["season"] if e["season"].startswith("Chapter") else f"Chapter 1 {e['season']}"
    lab = wiki_label(e["chapter"], lab) if ":" in lab else lab
    if lab not in POS or e["name"] in dupes:
        continue
    add("event", "event:" + e["name"], f"In which season did the live event '{e['name']}' take place?", lab, near_seasons(lab),
        f"{e['summary']} ({e['date'].split(' / ')[0]})" if e["summary"] else None, ks=["event:" + e["name"]])

# ------------------------------------------------------------------ hand-written, checked against the wiki
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
FACTS = [
    # your examples
    F("item", "When Supply Drops were first added, how much health did they have?", "2,000", ["500", "1,000", "1,250"], "They were in the game from the Pre-Season. Update 1.8 in Season 1 cut it to 1,250."),
    F("item", "From Chapter 1 Season 7 (Update v7.10), how much health did a Supply Drop have in Solos?", "250", ["100", "500", "750"], "Duos was 500 and Squads 750."),
    F("item", "From Chapter 1 Season 7 (Update v7.10), how much health did a Supply Drop have in Squads?", "750", ["500", "1,000", "1,250"], "Solos was 250 and Duos 500."),
    F("map", "In which season was Tilted Towers destroyed by the volcano?", "Chapter 1 Season 8", ["Chapter 1 Season 4", "Chapter 1 Season 9", "Chapter 1 Season X"], "It was destroyed in The Unvaulting live event. Only the No Sweat Insurance building survived, and the ruins became Neo Tilted in Season 9."),
    F("map", "What replaced the ruins of Tilted Towers in Chapter 1 Season 9?", "Neo Tilted", ["Tilted Town", "Mega Mall", "Pressure Plant"]),
    F("map", "In which season was Tilted Towers first added?", "Chapter 1 Season 2", ["Chapter 1 Pre-Season", "Chapter 1 Season 4", "Chapter 1 Season 3"], "It arrived in Update 2.2.0 in January 2018."),
    F("map", "What did the meteor turn Dusty Depot into in Chapter 1 Season 4?", "Dusty Divot", ["Dusty Crater", "Risky Reels", "Loot Lake"]),
    F("map", "In Chapter 1 Season 5, which desert location replaced Moisty Mire?", "Paradise Palms", ["Lazy Links", "Sunny Steps", "Mega Mall"]),
    F("map", "In Chapter 1 Season 9, which location was rebuilt into Mega Mall?", "Retail Row", ["Salty Springs", "Paradise Palms", "Lucky Landing"]),
    F("map", "In Chapter 1 Season 7, which mountain was the Infinity Blade found on?", "Polar Peak", ["Snobby Shoals", "Frosty Flights", "Happy Hamlet"]),
    F("map", "What was the Chapter 1 island known as?", "Athena", ["Apollo", "Artemis", "Asteria"]),
    F("map", "What was the Chapter 2 island known as?", "Apollo", ["Athena", "Artemis", "Helios"]),
    F("map", "In Chapter 2 Season 2, which location in the middle of the map was Midas' headquarters?", "The Agency", ["The Yacht", "The Grotto", "The Shark"]),
    # seasons and history
    F("season", "In which season was the Battle Pass introduced?", "Chapter 1 Season 2", ["Chapter 1 Season 1", "Chapter 1 Season 3", "Chapter 1 Season 4"], "It replaced the Season Shop."),
    F("season", "In which season was Fortnite Creative released?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 8", "Chapter 2 Season 1"]),
    F("season", "In which season were swimming and boats added?", "Chapter 2 Season 1", ["Chapter 1 Season X", "Chapter 2 Season 3", "Chapter 1 Season 8"]),
    F("season", "Which of these could you do for the first time in Chapter 2 Season 1?", "Carry a downed teammate", ["Fly a plane", "Build with metal", "Use a Launch Pad"]),
    F("season", "In which season did planes (the X-4 Stormwing) arrive?", "Chapter 1 Season 7", ["Chapter 1 Season 5", "Chapter 1 Season 9", "Chapter 2 Season 2"]),
    F("season", "In which season were All Terrain Karts (the golf carts) added?", "Chapter 1 Season 5", ["Chapter 1 Season 3", "Chapter 1 Season 7", "Chapter 2 Season 1"]),
    F("season", "In which season were the B.R.U.T.E. mechs added?", "Chapter 1 Season X", ["Chapter 1 Season 8", "Chapter 1 Season 9", "Chapter 2 Season 1"]),
    F("season", "In which season could you first drive cars?", "Chapter 2 Season 3", ["Chapter 1 Season 5", "Chapter 2 Season 1", "Chapter 2 Season 5"], "Cars arrived in Update 13.40, in August 2020."),
    F("season", "In which season were Pets added?", "Chapter 1 Season 6", ["Chapter 1 Season 4", "Chapter 1 Season 8", "Chapter 2 Season 1"]),
    F("season", "In which season were Fortbytes added?", "Chapter 1 Season 9", ["Chapter 1 Season 7", "Chapter 1 Season X", "Chapter 2 Season 1"]),
    F("season", "Which season first had bosses, like Midas and Meowscles, who dropped Mythic weapons?", "Chapter 2 Season 2", ["Chapter 1 Season X", "Chapter 2 Season 1", "Chapter 2 Season 4"]),
    F("season", "In which season did Gold Bars arrive, for buying items and hiring characters?", "Chapter 2 Season 5", ["Chapter 2 Season 2", "Chapter 2 Season 7", "Chapter 1 Season 9"]),
    F("season", "In which season could you first tame wild animals like wolves and boars?", "Chapter 2 Season 6", ["Chapter 2 Season 3", "Chapter 2 Season 8", "Chapter 1 Season 8"]),
    F("season", "How many seasons did Chapter 1 have, not counting the Pre-Season?", "10", ["8", "9", "12"], "Seasons 1 to 9, then Season X."),
    F("season", "How many seasons did Chapter 2 have?", "8", ["6", "10", "4"]),
    F("season", "What was the last season of Chapter 1 called?", "Season X", ["Season 10", "Season Zero", "Season Omega"]),
    F("season", "What was the first collaboration in Fortnite, in Chapter 1 Season 4?", "The Infinity Gauntlet LTM (Avengers: Infinity War)", ["John Wick", "Star Wars", "Batman"]),
    F("season", "In the Infinity Gauntlet LTM, who did you become when you picked up the Gauntlet?", "Thanos", ["Loki", "Ultron", "Galactus"]),
    F("season", "What was the first Mythic item to appear in normal Battle Royale?", "The Infinity Blade", ["The Infinity Gauntlet", "Midas' Drum Gun", "The Scar"], "It arrived in Chapter 1 Season 7."),
    F("season", "In which month and year did Fortnite open to everyone on iPhone?", "April 2018", ["September 2017", "December 2018", "July 2019"]),
    F("season", "What did fans name the purple cube that rolled across the island in Chapter 1 Season 5?", "Kevin", ["Steve", "Gary", "Dave"], "It rolled into Loot Lake and dissolved, turning the lake bouncy."),
    F("season", "What happened to Loot Lake when the Cube dissolved into it in 2018?", "It turned bouncy", ["It froze solid", "It turned to lava", "It drained away"]),
    F("season", "What happened at 'The End' live event in October 2019?", "The island was sucked into a black hole", ["The volcano erupted", "A rocket launched", "The island flooded"], "Fortnite showed only the black hole for about two days before Chapter 2."),
    F("season", "Which Chapter 1 live event let players vote to bring back an item?", "The Unvaulting", ["The Final Showdown", "The End", "The Butterfly"], "Players chose the Drum Gun."),
    F("season", "In The Unvaulting, which weapon did players vote to bring back?", "The Drum Gun", ["The Double Barrel Shotgun", "The Zapotron", "The Infinity Blade"]),
    F("season", "In The Final Showdown event in Chapter 1 Season 9, what fought the giant monster?", "A giant robot", ["The Battle Bus", "Kevin the Cube", "Galactus"]),
    F("season", "Which Marvel villain came to eat the island in Chapter 2 Season 4?", "Galactus", ["Thanos", "Doctor Doom", "Loki"]),
    F("season", "Which DJ played the first big in-game concert, at Pleasant Park in February 2019?", "Marshmello", ["Travis Scott", "Ariana Grande", "Eminem"]),
    F("season", "Which rapper's 'Astronomical' concert happened in April 2020?", "Travis Scott", ["Eminem", "Snoop Dogg", "Juice WRLD"]),
    F("season", "Which singer headlined the 'Rift Tour' in August 2021?", "Ariana Grande", ["Billie Eilish", "Lady Gaga", "Dua Lipa"]),
    # Battle Pass outfits
    F("outbp", "Which bounty hunter was the Chapter 2 Season 5 Battle Pass outfit?", "The Mandalorian", ["Boba Fett", "Master Chief", "Bossk"]),
    F("outbp", "Which footballer was in the Chapter 2 Season 6 Battle Pass?", "Neymar Jr", ["Lionel Messi", "Cristiano Ronaldo", "Harry Kane"]),
    F("outbp", "Which video game hero was in the Chapter 2 Season 6 Battle Pass?", "Lara Croft", ["Master Chief", "Kratos", "Ezio Auditore"]),
    F("outbp", "Which superhero was in the Chapter 2 Season 7 Battle Pass?", "Superman", ["Batman", "Iron Man", "Wonder Woman"]),
    F("outbp", "Which Marvel villain was in the Chapter 2 Season 8 Battle Pass?", "Carnage", ["Venom", "Thanos", "Green Goblin"]),
    F("outbp", "Which cat-themed agent was a Chapter 2 Season 2 Battle Pass outfit?", "Meowscles", ["Kit", "Lynx", "Sgt. Winter"]),
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
    # general
    F("fact", "Which company makes Fortnite?", "Epic Games", ["Activision", "EA", "Ubisoft"]),
    F("fact", "In which year did Fortnite Battle Royale come out?", "2017", ["2015", "2016", "2018"]),
    F("fact", "Which Fortnite mode came first?", "Save the World", ["Battle Royale", "Creative", "Party Royale"], "Battle Royale came out a couple of months later in 2017."),
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
]
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ nothing from Chapter 3 onwards, anywhere
for v in Q.values():
    for q in v:
        txt = " ".join([q["q"], q["a"]] + q["o"])
        if re.search(r"Chapter [3-9]|Season OG|Remix|Mini Season", txt):
            raise SystemExit(f"not OG: {q}")

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
