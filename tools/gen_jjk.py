"""Build the Jujutsu Kaisen question bank (1,000 questions), from the anime only.

Seasons 1 to 3 (The Culling Game Part 1, 59 TV episodes) and the Jujutsu Kaisen 0 film. Nothing from manga chapters the
anime hasn't reached. Episode titles, arcs, fights, first appearances and which character uses which technique come from
the Jujutsu Kaisen Wiki's episode pages (only techniques the episodes list as used on screen). Voice actors and birthdays
come from its character pages. Hand-written questions cover the story, the jujutsu world and the anime itself.
Usage: gen_jjk.py data.json domains.json OUT.json
"""
import sys, json, random, re, collections

DATA, DOMS, OUT = sys.argv[1:4]
rng = random.Random(20261125)
Q = collections.defaultdict(list)
SEEN = set()


def add(c, k, q, a, opts, x=None, ks=None):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) != 3:
        raise SystemExit(f"bad options for {q!r}: {a!r} {opts}")
    if k in SEEN:
        return False
    SEEN.add(k)
    q = re.sub(r"(?<![A-Za-z])'([^']+?)'(?![A-Za-z])", r'"\1"', q)   # quoted names in double quotes; apostrophes (Zen'in) untouched
    d = {"c": c, "k": k, "q": q, "a": a, "o": opts}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = ks
    Q[c].append(d)
    return True


data = json.load(open(DATA))
EPS = data["episodes"]
CH = data["characters"]
DOMAINS = set(json.load(open(DOMS))) - {"Domain Expansion"}
SEASONS4 = ["Season 1", "Season 2", "Season 3", "Jujutsu Kaisen 0 (the film)"]


def arc_name(a):
    a = re.sub(r"\s*\((?:1st|2nd) Half\)", "", a).strip()
    a = re.sub(r" Arc$", "", a)
    return {"Kyoto Goodwill Event": "Kyoto Goodwill Event", "Gojo's Past": "Gojo's Past (Hidden Inventory / Premature Death)"}.get(a, a) + " arc"


for e in EPS:
    e["arcs"] = list(dict.fromkeys(arc_name(a) for a in e["arc"]))
ARCS = list(dict.fromkeys(a for e in EPS for a in e["arcs"]))
cnt = collections.Counter()
for e in EPS:
    for n in {c["name"] for c in e["chars"] if c["note"] in ("", "Pictured")}:
        cnt[n] += 1
KNOWN = [n for n, k in cnt.most_common() if k >= 3]   # characters on screen in 3+ episodes


MONTHS = "January February March April May June July August September October November December".split()


def nice_date(d):
    d = re.sub(r"\{\{[^}]*\}\}", "", d)
    d = re.split(r"<br\s*/?>", d)[-1].strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", d)
    return f"{MONTHS[int(m.group(2)) - 1]} {int(m.group(3))}, {m.group(1)}" if m else d


def gives_away(title, arc):
    words = [w for w in re.findall(r"[A-Za-z]+", arc.replace(" arc", "")) if len(w) > 3 and w not in ("Past", "Event")]
    return any(w.lower() in title.lower() for w in words)


# ------------------------------------------------------------------ episodes
for s in (1, 2, 3):
    se = [e for e in EPS if e["season"] == s]
    for e in se:
        near = sorted((x for x in se if x is not e), key=lambda x: (abs(x["sn"] - e["sn"]), rng.random()))
        opts = [x["title"] for x in near if x["title"].split(",")[0] != e["title"].split(",")[0]][:3]
        if len(opts) == 3:
            add("ep_title", f"eptitle:{e['n']}", f"What is Season {s}, Episode {e['sn']} called?", e["title"], opts,
                f"It aired in Japan on {nice_date(e['aired'])}." if e["aired"] else None, ks=["ep:" + str(e["n"])])
        if len(e["arcs"]) == 1 and not gives_away(e["title"], e["arcs"][0]):
            add("ep_arc", f"eparc:{e['n']}", f'Which arc is the episode "{e["title"]}" (Season {s}) part of?', e["arcs"][0],
                rng.sample([a for a in ARCS if a != e["arcs"][0]], 3), ks=["ep:" + str(e["n"])])
        add("ep_season", f"epseason:{e['n']}", f'Which season is the episode "{e["title"]}" from?', f"Season {s}",
            [x for x in SEASONS4 if x != f"Season {s}"], ks=["ep:" + str(e["n"])])

# ------------------------------------------------------------------ fights
EVENTS = re.compile(r"Execution|Watching|Race|Baseball|Culling Game$|^The Shibuya Incident$|Mentioned|Goodwill Event$|Evacuation|Offscreen")
fights = {}
for e in EPS:
    for b in e["battles"]:
        n = re.sub(r"\s*\((?:Started|Concluded|Continued|Resumed|Interrupted|Flashback|Ended)[^)]*\)", "", b).strip()
        if " vs. " in n and not EVENTS.search(n):
            fights.setdefault(n, e)
for n, e in fights.items():
    arc = e["arcs"][0]
    add("fight_arc", f"fightarc:{n}", f'In which arc does the fight "{n}" happen?', arc, rng.sample([a for a in ARCS if a != arc], 3),
        f"Season {e['season']}, Episode {e['sn']}.", ks=["fight:" + n])
by_arc = collections.defaultdict(list)
for n, e in fights.items():
    by_arc[e["arcs"][0]].append(n)
for arc, ns in by_arc.items():
    others = [n for a, v in by_arc.items() if a != arc for n in v]
    for n in ns:
        add("fight_in", f"fightin:{n}", f"Which of these fights happens in the {arc}?", n, rng.sample(others, 3), ks=["fight:" + n])

# ------------------------------------------------------------------ techniques shown on screen
GENERIC = {"Domain Expansion", "Reverse Cursed Technique", "Simple Domain", "Shikigami", "Cursed Technique", "Domain Amplification", "Cursed Energy",
           "Kogane", "Prison Realm", "Black Flash", "Playful Cloud", "Hollow Wicker Basket", "Falling Blossom Emotion", "Barrier Techniques",
           "Curtain", "Binding Vow", "Cursed Energy Discharge", "Cursed Tool", "Heavenly Restriction", "Maximum Technique", "Extension Technique"}
names = set(CH) | {c["name"] for e in EPS for c in e["chars"]}
uses = collections.defaultdict(collections.Counter)   # technique -> user -> episodes
first_seen = {}
for e in EPS:
    for who, ts in e["tech"].items():
        for t in ts:
            parts = [x for x in t["parts"] if x != "Domain Expansion"]
            if len(parts) != 1:          # joined names like "Soul Multiplicity Body Repel"
                continue
            nm = parts[0].split("#")[-1].strip()
            if nm in GENERIC or nm in names or len(nm) < 3 or who not in names or "Martial Arts" in nm or nm == "Six Eyes":
                continue
            uses[nm][who] += 1
            first_seen.setdefault(nm, e)
tech = {}
for nm, u in uses.items():
    users = list(u)
    if len(users) >= 3:
        continue
    main = max(users, key=lambda w: (w not in ("Yuta Okkotsu", "Kenjaku"), u[w]))   # Yuta copies, Kenjaku borrows Geto's body
    tech[nm] = (main, set(users))
tech_users = sorted({m for m, _ in tech.values()}, key=lambda n: -cnt[n])
famous_users = [n for n in tech_users if n in KNOWN] or tech_users
per_user = collections.Counter()
for nm, (main, users) in sorted(tech.items(), key=lambda kv: (first_seen[kv[0]]["n"], kv[0])):
    if nm in DOMAINS or per_user[main] >= 5:   # at most 5 per character, earliest first
        continue
    per_user[main] += 1
    pool = [n for n in famous_users if n not in users]
    e = first_seen[nm]
    add("tech_user", f"techuser:{nm}", f'Which character uses "{nm}"?', main, rng.sample(pool[:30], 3),
        f"First used on screen in Season {e['season']}, Episode {e['sn']}.", ks=["tech:" + nm, "techby:" + main])
by_user = collections.defaultdict(list)
for nm, (main, users) in tech.items():
    if nm not in DOMAINS:
        by_user[main].append(nm)
for who in [n for n in famous_users if len(by_user[n]) >= 1]:
    others = [t for w, ts in by_user.items() if w != who for t in ts]
    for nm in by_user[who][:4]:
        add("tech_of", f"techof:{who}:{nm}", f"Which of these techniques does {who} use?", nm, rng.sample(others, 3), ks=["tech:" + nm, "techby:" + who])
for nm, (main, users) in tech.items():
    if main not in famous_users[:40]:
        continue
    arc = first_seen[nm]["arcs"][0]
    add("tech_arc", f"techarc:{nm}", f'In which arc is {main}\'s "{nm}" first used on screen?', arc, rng.sample([a for a in ARCS if a != arc], 3),
        f"Season {first_seen[nm]['season']}, Episode {first_seen[nm]['sn']}.", ks=["tech:" + nm])
doms = {nm: main for nm, (main, users) in tech.items() if nm in DOMAINS}
for nm, who in doms.items():
    add("domain", f"domain:{who}", f"What is the name of {who}'s Domain Expansion?", nm, rng.sample([d for d in doms if d != nm], 3),
        ks=["dom:" + nm, "techby:" + who])
    add("domain", f"domainwho:{nm}", f'Whose Domain Expansion is "{nm}"?', who, rng.sample([w for w in famous_users if w != who][:20], 3),
        ks=["dom:" + nm, "techby:" + who])


# ------------------------------------------------------------------ characters: voices, debut, birthday
def first_voice(v):
    v = re.sub(r"\s*\(.*", "", v.split(" / ")[0]).strip()
    return "" if ("=" in v or v.startswith("|")) else v


GENDER = {n: CH[n].get("gender", "") for n in CH}


jp = {n: first_voice(CH[n]["jp"]) for n in KNOWN if n in CH and first_voice(CH[n]["jp"])}
en = {n: first_voice(CH[n]["en"]) for n in KNOWN if n in CH and first_voice(CH[n]["en"])}
for lang, vmap, nice in (("jp", jp, "Japanese version"), ("en", en, "English dub")):
    voiced = collections.Counter(vmap.values())
    for n, va in vmap.items():
        same = [v for m, v in vmap.items() if v != va and GENDER.get(m) == GENDER.get(n)]
        wrong = list(dict.fromkeys(same if len(set(same)) >= 3 else [v for m, v in vmap.items() if v != va]))
        rng.shuffle(wrong)
        add("va_" + lang, f"va{lang}:{n}", f"Who voices {n} in the {nice}?", va, wrong[:3], ks=["char:" + n])
        if voiced[va] == 1:
            pool = [m for m in vmap if m != n and m in KNOWN[:60] and GENDER.get(m) == GENDER.get(n)]
            add("va_" + lang, f"va{lang}who:{va}", f"Which character does {va} voice in the {nice}?", n,
                rng.sample(pool if len(pool) >= 3 else [m for m in vmap if m != n], 3), ks=["char:" + n])
for n in KNOWN:
    d = CH.get(n, {}).get("debutanime", "")
    if not d or "(" in d or "/" in d:
        continue
    m = re.match(r"Episode (\d+)$", d)
    season = next((f"Season {e['season']}" for e in EPS if m and e["n"] == int(m.group(1))), None) if m else ("Jujutsu Kaisen 0 (the film)" if "0" in d else None)
    if season:
        add("debut", f"debut:{n}", f"In which season does {n} first appear in the anime?", season, [x for x in SEASONS4 if x != season],
            (f"Season {season[-1]}, Episode {next(e['sn'] for e in EPS if e['n'] == int(m.group(1)))}." if m else None), ks=["char:" + n])


debut_ep = {}
for e in EPS:
    for c in e["chars"]:
        if c["note"] == "" and c["name"] not in debut_ep:
            debut_ep[c["name"]] = e
for n in KNOWN:
    e = debut_ep.get(n)
    if not e or len(e["arcs"]) != 1:
        continue
    arc = e["arcs"][0]
    add("debut_arc", f"debutarc:{n}", f"In which arc does {n} first appear on screen?", arc, rng.sample([a for a in ARCS if a != arc], 3),
        f"Season {e['season']}, Episode {e['sn']} (not counting flashbacks or Jujutsu Kaisen 0).", ks=["char:" + n])


def md(b):
    m = re.match(r"([A-Za-z]+) (\d+)", b)
    return f"{m.group(1)} {m.group(2)}" if m else None


bdays = {n: md(CH[n]["birthday"]) for n in CH if CH[n]["birthday"] and md(CH[n]["birthday"]) and n in KNOWN}
for n, b in bdays.items():
    if list(bdays.values()).count(b) > 1:      # Maki and Mai are twins: asked by hand instead
        continue
    add("birthday", f"bday:{n}", f"When is {n}'s birthday?", b, rng.sample([v for v in set(bdays.values()) if v != b], 3), ks=["char:" + n])

# ------------------------------------------------------------------ hand-written (checked against the wiki and the episodes)
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
S1, S2, S3, S0 = SEASONS4
FACTS = [
    # your examples
    F("techh", "What is the name of Satoru Gojo's Domain Expansion?", "Unlimited Void", ["Malevolent Shrine", "Chimera Shadow Garden", "Self-Embodiment of Perfection"], "It floods the target's mind with endless information, so they can't do anything."),
    F("charh", "What is Kirara's full name?", "Kirara Hoshi", ["Kirara Hakari", "Kirara Kurusu", "Kirara Kashimo"], "Kirara is a third-year at Tokyo Jujutsu High and Kinji Hakari's partner. Kirara first appears in Season 3."),
    F("charh", "Who is Kirara Hoshi's partner, who runs a fight club while suspended from school?", "Kinji Hakari", ["Aoi Todo", "Toge Inumaki", "Naoya Zenin"]),
    F("world", "How is Jujutsu High protected and hidden?", "By Master Tengen's barriers", ["By Gojo's Infinity", "By a giant shikigami", "By the Zen'in clan's guards"], "Tengen's barriers protect and hide both Jujutsu High schools and many other jujutsu sites across Japan."),
    F("anime", "How many TV episodes of the anime have aired, from Season 1 to Season 3?", "59", ["47", "63", "72"], "Season 1 had 24, Season 2 had 23 and Season 3 (The Culling Game Part 1) had 12. Part 2 is still to come."),
    F("anime", "How many episodes did Season 1 have?", "24", ["12", "23", "26"]),
    F("anime", "How many episodes did Season 2 have?", "23", ["12", "24", "25"], "5 for Hidden Inventory / Premature Death, then 18 for the Shibuya Incident."),
    F("anime", "How many episodes did Season 3 (The Culling Game Part 1) have?", "12", ["10", "13", "24"]),
    F("story", "In which season does Suguru Geto leave Jujutsu High and become a curse user?", S2, [S1, S3, S0], "It happens in the Hidden Inventory / Premature Death episodes, set years before Season 1."),
    F("story", "Who is really controlling Suguru Geto's body in Season 1 and the Shibuya Incident?", "Kenjaku", ["Mahito", "Sukuna", "Uraume"], "The real Geto died at the end of Jujutsu Kaisen 0. Kenjaku moves between bodies by swapping brains, which is why there are stitches across Geto's forehead."),
    F("story", "In which season is it revealed that the 'Geto' working with the curses is really Kenjaku?", S2, [S1, S3, S0], "He shows it during the Shibuya Incident, after sealing Gojo."),
    # Season 1
    F("story", "What does Yuji Itadori swallow to become Sukuna's vessel?", "One of Sukuna's fingers", ["A cursed eye", "A special-grade talisman", "Gojo's blindfold"]),
    F("world", "How many of Sukuna's fingers are there in total?", "20", ["10", "12", "40"]),
    F("story", "Why does Yuji go to his school at night in Episode 1?", "To save his Occult Club seniors", ["To find his grandfather", "To fight Megumi", "To steal a cursed object"], "They had unsealed one of Sukuna's fingers, which drew curses to the school."),
    F("story", "Which club is Yuji in at his first school?", "The Occult Research Club", ["The Track Club", "The Kendo Club", "The Film Club"]),
    F("story", "In Episode 1, how far does Yuji throw a shot put?", "About 30 metres", ["About 10 metres", "About 15 metres", "About 100 metres"], "The track teacher can't believe it."),
    F("story", "Who raised Yuji?", "His grandfather, Wasuke", ["Satoru Gojo", "His older brother", "His aunt"]),
    F("story", "What were Yuji's grandfather's last words to him?", "Help people, and die surrounded by people", ["Never trust a sorcerer", "Become the strongest", "Find your parents"]),
    F("world", "What is the full name of Tokyo Jujutsu High?", "Tokyo Metropolitan Curse Technical College", ["Tokyo Sorcery Academy", "Tokyo Exorcist High School", "Tokyo Special Grade College"]),
    F("charh", "Who is the principal of Tokyo Jujutsu High?", "Masamichi Yaga", ["Yoshinobu Gakuganji", "Satoru Gojo", "Kiyotaka Ijichi"]),
    F("charh", "What does Principal Yaga make?", "Cursed corpses (cursed dolls)", ["Cursed tools", "Barriers", "Talismans"], "Panda is his greatest creation."),
    F("charh", "What is Panda?", "A cursed corpse made by Principal Yaga", ["A cursed spirit", "A shikigami", "A real panda"]),
    F("charh", "How many cores does Panda have?", "3", ["1", "2", "5"], "Panda's own, plus a 'big brother' (the Gorilla core) and a 'big sister'."),
    F("charh", "Why does Toge Inumaki only say rice ball fillings?", "So his Cursed Speech doesn't hurt anyone", ["He's lost his memory", "It's a binding vow with Gojo", "He's from another country"]),
    F("charh", "Why does Maki Zenin wear glasses?", "To see curses, because she has almost no cursed energy", ["To aim her spear", "To hide her Six Eyes", "To read cursed scrolls"]),
    F("charh", "Which jujutsu clan are Maki and Mai from?", "The Zen'in clan", ["The Gojo clan", "The Kamo clan", "The Inumaki clan"]),
    F("charh", "How are Maki and Mai Zenin related?", "They are twins", ["Cousins", "Mother and daughter", "Not related"]),
    F("charh", "When is the birthday of the twins Maki and Mai Zenin?", "January 20", ["March 20", "July 7", "December 22"]),
    F("charh", "Which school does Aoi Todo attend?", "Kyoto Jujutsu High", ["Tokyo Jujutsu High", "Sendai Jujutsu High", "He doesn't attend school"]),
    F("charh", "What question does Aoi Todo ask people he meets?", "What kind of woman is your type?", ["What's your cursed technique?", "Who's the strongest?", "Are you a curse?"]),
    F("charh", "Which idol is Aoi Todo a huge fan of?", "Takada-chan", ["Kirara", "Misato", "Riko"]),
    F("charh", "What does Todo start calling Yuji after hearing his answer about his type?", "His best friend", ["His rival", "His student", "His enemy"]),
    F("techh", "What ratio does Kento Nanami's Ratio Technique use to create a weak point?", "7:3", ["5:5", "6:4", "9:1"]),
    F("charh", "What job did Kento Nanami have before returning to jujutsu?", "Salaryman (office worker)", ["Doctor", "Police officer", "Teacher"]),
    F("charh", "What does Nanami hate, but which also makes his cursed energy stronger?", "Overtime", ["Mondays", "Crowds", "Rain"]),
    F("world", "Whose record of 4 Black Flashes in a row is mentioned in Season 1?", "Kento Nanami", ["Satoru Gojo", "Aoi Todo", "Yuji Itadori"]),
    F("world", "How much stronger is a Black Flash than a normal cursed-energy hit?", "To the power of 2.5", ["Twice as strong", "Ten times as strong", "To the power of 10"]),
    F("world", "What are cursed spirits born from?", "Negative human emotions", ["Dead sorcerers", "Sukuna's fingers", "Broken barriers"]),
    F("charh", "What is Mahito born from?", "Humans' hatred and fear of each other", ["The fear of volcanoes", "The fear of forests", "The fear of the sea"]),
    F("charh", "What is Jogo born from?", "Humans' fear of the earth (volcanoes)", ["Humans' fear of each other", "Humans' fear of forests", "Humans' fear of the sea"]),
    F("charh", "What is Hanami born from?", "Humans' fear of forests and nature", ["Humans' fear of volcanoes", "Humans' fear of disease", "Humans' fear of each other"]),
    F("charh", "What is Dagon born from?", "Humans' fear of the sea", ["Humans' fear of forests", "Humans' fear of volcanoes", "Humans' fear of the dark"]),
    F("charh", "What is Jogo's head shaped like?", "A volcano", ["A skull", "A flame", "A mountain shrine"]),
    F("charh", "What kind of creature is Junpei Yoshino's shikigami, Moon Dregs?", "A jellyfish", ["An octopus", "A snake", "A crow"]),
    F("story", "Which cursed spirit manipulates Junpei Yoshino in Season 1?", "Mahito", ["Jogo", "Hanami", "Dagon"]),
    F("story", "During training, what punched Yuji if his cursed energy slipped while he watched films?", "A cursed doll", ["Gojo", "Panda", "A shikigami"]),
    F("charh", "What does Satoru Gojo cover his eyes with in Season 1?", "A blindfold", ["Sunglasses", "An eyepatch", "Bandages"]),
    F("techh", "What eye ability lets Gojo use his Limitless technique so precisely?", "The Six Eyes", ["The Sharingan", "Black Flash", "Simple Domain"]),
    F("techh", "What does Gojo create by combining Blue and Red?", "Hollow Purple", ["Unlimited Void", "Infinity", "Black Flash"]),
    F("techh", "What is Gojo's Blue called in full?", "Cursed Technique Lapse: Blue", ["Cursed Technique Reversal: Blue", "Hollow Technique: Blue", "Maximum: Blue"]),
    F("techh", "What is Gojo's Red called in full?", "Cursed Technique Reversal: Red", ["Cursed Technique Lapse: Red", "Hollow Technique: Red", "Maximum: Red"]),
    F("world", "How many special grade sorcerers are there, as Gojo explains early on?", "4", ["2", "10", "20"]),
    F("world", "What is the highest sorcerer grade?", "Special Grade", ["Grade 1", "Grade 0", "Semi-Grade 1"]),
    F("world", "What is the lowest sorcerer grade?", "Grade 4", ["Grade 3", "Grade 5", "Grade 10"]),
    F("world", "What is a Domain Expansion?", "A barrier in which your technique is sure to hit", ["A way to heal any wound", "A summoned shikigami army", "A cursed tool"]),
    F("world", "What is Simple Domain used for?", "Defending against a Domain Expansion", ["Healing", "Summoning curses", "Teleporting"]),
    F("world", "What is Reverse Cursed Technique mostly used for?", "Healing", ["Sealing curses", "Reading minds", "Flying"]),
    F("world", "Which three are the great jujutsu families?", "Gojo, Zen'in and Kamo", ["Gojo, Zen'in and Inumaki", "Kamo, Fushiguro and Itadori", "Zen'in, Okkotsu and Gojo"]),
    F("world", "What is the yearly event between the Tokyo and Kyoto schools called?", "The Kyoto Sister School Goodwill Event", ["The Jujutsu Tournament", "The Sorcerer Games", "The Cursed Festival"]),
    F("world", "What did the students play on the second day of the Goodwill Event?", "Baseball", ["Football", "Tug of war", "Volleyball"]),
    F("story", "What secret order were the Kyoto students given at the Goodwill Event?", "To kill Yuji", ["To capture Gojo", "To steal Sukuna's fingers", "To protect Panda"], "Principal Gakuganji wanted Sukuna's vessel dead."),
    F("charh", "Who is the principal of Kyoto Jujutsu High?", "Yoshinobu Gakuganji", ["Masamichi Yaga", "Utahime Iori", "Naobito Zenin"]),
    F("charh", "What instrument does Gakuganji fight with?", "An electric guitar", ["A drum kit", "A violin", "A shamisen"]),
    F("charh", "What is Mechamaru's real name?", "Kokichi Muta", ["Noritoshi Kamo", "Junpei Yoshino", "Takuma Ino"]),
    F("story", "Why did Kokichi Muta (Mechamaru) secretly help the curses?", "So they would heal his frail body", ["For money", "Because Mahito threatened Miwa", "To get Sukuna's fingers"]),
    F("charh", "Who is Mei Mei's younger brother?", "Ui Ui", ["Yu Haibara", "Junpei Yoshino", "Takuma Ino"]),
    F("charh", "What does Mei Mei care about more than anything?", "Money", ["Family", "Fame", "Revenge"]),
    F("charh", "Which doctor at Jujutsu High heals others with Reverse Cursed Technique?", "Shoko Ieiri", ["Utahime Iori", "Mei Mei", "Momo Nishimiya"]),
    F("charh", "Who usually drives the Tokyo students to their missions?", "Kiyotaka Ijichi", ["Masamichi Yaga", "Takuma Ino", "Kento Nanami"]),
    F("charh", "Who made the Cursed Womb: Death Paintings?", "Noritoshi Kamo, 'the worst sorcerer in history'", ["Sukuna", "Tengen", "Toji Fushiguro"]),
    F("charh", "How many Cursed Womb: Death Paintings are there?", "9", ["3", "7", "12"]),
    F("charh", "Which two Death Painting brothers do Yuji and Nobara fight at the end of Season 1?", "Eso and Kechizu", ["Choso and Eso", "Choso and Kechizu", "Bayer and Kokun"]),
    F("story", "Which Season 1 villains steal Sukuna's fingers from Jujutsu High during the Goodwill Event?", "Mahito's group", ["The Zen'in clan", "The Kyoto students", "The Time Vessel Association"]),
    F("story", "Who fights Sukuna (in Yuji's body) at the end of Episode 1 and in Episode 2?", "Satoru Gojo", ["Megumi Fushiguro", "Masamichi Yaga", "Kento Nanami"]),
    F("story", "What do the jujutsu higher-ups decide to do with Yuji after he swallows the finger?", "Execute him, but only once he has eaten all the fingers", ["Lock him in Tengen's barrier", "Make him a special grade sorcerer", "Remove the finger"]),
    F("story", "What does Sukuna do to Yuji's body in the detention centre in Episode 5?", "Tears out his heart", ["Takes it over for good", "Seals it in a barrier", "Swaps it with Megumi's"]),
    F("story", "Where do Yuji, Megumi and Nobara face a special grade curse in Episode 4?", "A juvenile detention centre", ["A hospital", "A school gym", "A shopping mall"]),
    F("story", "What does Sukuna's vow to revive Yuji give him?", "One minute in control when he says 'Enchain', and Yuji must forget the vow", ["Two of his fingers back", "Control of Yuji every night", "The right to kill Megumi"]),
    F("story", "Who do the other first-years think is dead until the Goodwill Event?", "Yuji Itadori", ["Megumi Fushiguro", "Toge Inumaki", "Panda"]),
    F("story", "Which special grade curse attacks Gojo and Yuji while Gojo is teaching him about domains?", "Jogo", ["Hanami", "Mahito", "Dagon"]),
    F("story", "Where does Gojo take the first-years for Nobara's first mission?", "Roppongi", ["Shibuya", "Harajuku", "Shinjuku"]),
    F("charh", "Which Kyoto student flies on a broom?", "Momo Nishimiya", ["Kasumi Miwa", "Mai Zenin", "Utahime Iori"]),
    F("charh", "Which Kyoto student uses a sword and the New Shadow Style?", "Kasumi Miwa", ["Momo Nishimiya", "Mai Zenin", "Noritoshi Kamo"]),
    F("charh", "Which Kyoto student fights with a revolver?", "Mai Zenin", ["Kasumi Miwa", "Momo Nishimiya", "Utahime Iori"]),
    F("charh", "What does Nobara Kugisaki fight with?", "A hammer and nails", ["A spear", "Paper talismans", "A sword"]),
    F("techh", "What does Megumi use to summon his shadow shikigami?", "Hand signs (shadow puppets)", ["Paper talismans", "His blood", "A flute"]),
    F("techh", "Why can Megumi summon Divine Dog: Totality?", "His white Divine Dog was destroyed and its power passed to the black one", ["Gojo gave it to him", "It was Toji's", "He made a binding vow with Sukuna"]),
    F("techh", "How does Megumi gain a new Ten Shadows shikigami?", "By defeating it in a taming ritual", ["By eating a finger", "By buying it", "By drawing it"]),
    F("techh", "Which Ten Shadows shikigami has no user ever managed to tame?", "Mahoraga", ["Nue", "Max Elephant", "Toad"]),
    F("techh", "What makes Mahoraga so dangerous?", "It adapts to any attack", ["It can't be seen", "It copies techniques", "It heals other shikigami"]),
    F("techh", "What does Todo's Boogie Woogie do?", "Swaps the places of two things when he claps", ["Makes him dance faster", "Copies techniques", "Stops time"]),
    F("techh", "What does Mahito's Idle Transfiguration change?", "The shape of a person's soul, and so their body", ["Their memories", "Their cursed technique", "Their age"]),
    F("techh", "What does Gojo's Infinity do?", "Stops anything from reaching him", ["Makes him invisible", "Copies attacks", "Heals him"]),
    F("techh", "What is special about Yuji's Divergent Fist?", "His cursed energy hits a moment after his fist", ["It never misses", "It heals him", "It uses Sukuna's power"]),
    F("techh", "Which cursed tool does Toji use to cut through Gojo's Infinity?", "The Inverted Spear of Heaven", ["Playful Cloud", "Split Soul Katana", "Dragon-Bone"]),
    F("techh", "How does Toji carry his cursed tools around?", "Inside a worm-like curse wrapped around his body", ["In a backpack", "In a pocket dimension", "Megumi carries them"]),
    F("techh", "What is Nobara's Resonance?", "Hitting a straw doll linked to a piece of the target, to hurt them from afar", ["Copying the target's technique", "Swapping places with the doll", "Healing with nails"]),
    F("techh", "What is Jogo's strongest attack, a giant falling rock of fire, called?", "Maximum: Meteor", ["Maximum: Uzumaki", "Disaster Flames", "Ember Insects"]),
    F("techh", "What is the attack where Geto (and later Kenjaku) compresses his curses into one blast?", "Maximum: Uzumaki", ["Hollow Purple", "Maximum: Meteor", "Piercing Blood"]),
    F("techh", "What fire technique does Sukuna use against Mahoraga in Shibuya?", "A flaming arrow (Fuga)", ["Hollow Purple", "Maximum: Meteor", "Disaster Flames"]),
    F("world", "What is a 'curtain' in jujutsu?", "A barrier that hides fights from ordinary people", ["A cursed tool", "A type of shikigami", "A binding vow"]),
    F("world", "What is a Binding Vow?", "A promise that gives power in exchange for a limit", ["A cursed weapon", "A wedding between sorcerers", "A school rule"]),
    F("world", "What does 'Heavenly Restriction' mean?", "A trade-off made at birth, giving up one thing for another", ["A punishment from Tengen", "A rule of the Culling Game", "A type of domain"]),
    F("world", "Who is the 'King of Curses'?", "Sukuna", ["Mahito", "Kenjaku", "Jogo"]),
    F("world", "Who is called 'the strongest' jujutsu sorcerer of today?", "Satoru Gojo", ["Yuta Okkotsu", "Yuki Tsukumo", "Kento Nanami"]),
    F("story", "What does Choso feel when Yuji kills his brothers Eso and Kechizu?", "Their deaths, through his blood link with them", ["Nothing at all", "Relief", "Sukuna's presence"]),
    F("story", "Which special grade curse do Yuji and Todo fight together during the Goodwill Event?", "Hanami", ["Jogo", "Mahito", "Dagon"]),
    F("story", "Who uses Hollow Purple to stop Hanami at the Goodwill Event?", "Satoru Gojo", ["Yuta Okkotsu", "Sukuna", "Mei Mei"]),
    # Season 2
    F("story", "Who were Gojo and Geto protecting in Hidden Inventory?", "Riko Amanai", ["Tsumiki Fushiguro", "Mimiko Hasaba", "Nobuko Takada"], "Riko was the Star Plasma Vessel, due to merge with Tengen."),
    F("story", "What was Riko Amanai?", "The Star Plasma Vessel", ["A cursed corpse", "A Death Painting", "Tengen's daughter"]),
    F("charh", "Who was Riko Amanai's caretaker?", "Misato Kuroi", ["Shoko Ieiri", "Utahime Iori", "Mei Mei"]),
    F("story", "Who killed Riko Amanai?", "Toji Fushiguro", ["Suguru Geto", "Kenjaku", "Mahito"]),
    F("charh", "What was Toji Fushiguro known as?", "The Sorcerer Killer", ["The King of Curses", "The Strongest", "The Honored One"]),
    F("charh", "Who is Toji Fushiguro's son?", "Megumi Fushiguro", ["Yuji Itadori", "Yuta Okkotsu", "Naoya Zenin"]),
    F("charh", "Which clan was Toji born into?", "The Zen'in clan", ["The Gojo clan", "The Kamo clan", "The Fushiguro clan"]),
    F("charh", "Toji has no cursed energy at all. What is this kind of trade-off called?", "A Heavenly Restriction", ["A Binding Vow", "A Simple Domain", "A Black Flash"]),
    F("story", "How did Gojo survive Toji's attack in Hidden Inventory?", "He awakened Reverse Cursed Technique", ["Shoko healed him", "Geto took the hit", "He was never hit"]),
    F("story", "What does Gojo say after coming back from Toji's attack?", "Throughout heaven and earth, I alone am the honored one", ["Stand proud, you're strong", "I'm the strongest", "Domain Expansion"]),
    F("story", "Which group celebrated Riko Amanai's death?", "The Time Vessel Association", ["The Zen'in clan", "Kyoto Jujutsu High", "The Culling Game players"]),
    F("charh", "Who were Gojo's two classmates in his year at Jujutsu High?", "Suguru Geto and Shoko Ieiri", ["Kento Nanami and Yu Haibara", "Utahime Iori and Mei Mei", "Toji and Riko"]),
    F("charh", "Which junior of Gojo and Geto died on a mission, which hit Nanami hard?", "Yu Haibara", ["Junpei Yoshino", "Takuma Ino", "Kokichi Muta"]),
    F("story", "Which two girls did Geto rescue from the villagers who had locked them up?", "Mimiko and Nanako", ["Maki and Mai", "Riko and Misato", "Tsumiki and Nobara"]),
    F("story", "How many villagers did Geto kill when he turned against non-sorcerers?", "112", ["12", "50", "300"]),
    F("world", "On which date does the Shibuya Incident begin?", "October 31 (Halloween)", ["December 24", "January 1", "August 15"]),
    F("story", "What is Gojo sealed inside during the Shibuya Incident?", "The Prison Realm", ["A Domain Expansion", "Tengen's barrier", "A cursed coffin"]),
    F("story", "For how long did Gojo open his domain in Shibuya, so he wouldn't kill the people around him?", "0.2 seconds", ["2 seconds", "10 seconds", "A full minute"]),
    F("story", "Where was Gojo sealed?", "Shibuya Station", ["Tokyo Tower", "Jujutsu High", "Shinjuku Station"]),
    F("story", "Who kills Jogo during the Shibuya Incident?", "Sukuna", ["Satoru Gojo", "Yuji Itadori", "Toji Fushiguro"]),
    F("story", "Who kills Kento Nanami during the Shibuya Incident?", "Mahito", ["Jogo", "Dagon", "Choso"]),
    F("story", "What does Nanami tell Yuji in his final moments?", "It's up to you now", ["Run away", "Avenge me", "Find Gojo"]),
    F("story", "Which shikigami does Megumi summon as a last resort in Shibuya, forcing Sukuna to fight it?", "Mahoraga", ["Max Elephant", "Nue", "Divine Dog: Totality"]),
    F("techh", "What is unusual about Sukuna's domain, Malevolent Shrine?", "It doesn't close off the space with a barrier", ["It heals everyone inside", "It only works at night", "It has no sure-hit effect"], "Sukuna compares it to painting without a canvas."),
    F("story", "Who absorbs Mahito at the end of the Shibuya Incident?", "Kenjaku", ["Sukuna", "Yuji Itadori", "Uraume"]),
    F("charh", "Who does Choso come to believe is his little brother?", "Yuji Itadori", ["Megumi Fushiguro", "Junpei Yoshino", "Yuta Okkotsu"]),
    F("charh", "What is Choso?", "A Cursed Womb: Death Painting", ["A cursed corpse", "A shikigami", "A vengeful spirit"]),
    F("story", "Which Tokyo student is hit by Mahito's Idle Transfiguration in Shibuya?", "Nobara Kugisaki", ["Maki Zenin", "Panda", "Toge Inumaki"]),
    F("story", "Who arrives to help Yuji defeat Mahito near the end of Shibuya?", "Aoi Todo", ["Yuta Okkotsu", "Satoru Gojo", "Mei Mei"]),
    F("story", "What does Todo lose in the fight against Mahito?", "One of his hands", ["His eyesight", "His cursed energy", "His memory"]),
    # Jujutsu Kaisen 0
    F("story", "Who is the main character of Jujutsu Kaisen 0?", "Yuta Okkotsu", ["Yuji Itadori", "Megumi Fushiguro", "Toge Inumaki"]),
    F("charh", "What is the name of the curse attached to Yuta Okkotsu?", "Rika Orimoto", ["Riko Amanai", "Saori", "Mimiko"]),
    F("charh", "Who was Rika to Yuta?", "His childhood friend, who promised to marry him", ["His sister", "His teacher", "His rival"]),
    F("story", "What was Geto's attack in Jujutsu Kaisen 0 called?", "The Night Parade of a Hundred Demons", ["The Shibuya Incident", "The Culling Game", "The Hidden Inventory"]),
    F("story", "On which date was the Night Parade of a Hundred Demons?", "December 24", ["October 31", "January 1", "December 31"]),
    F("story", "Which two cities did Geto attack in the Night Parade of a Hundred Demons?", "Shinjuku and Kyoto", ["Shibuya and Sendai", "Osaka and Kyoto", "Shinjuku and Sapporo"]),
    F("charh", "What weapon does Yuta mainly fight with?", "A katana", ["A spear", "Nunchaku", "A bow"]),
    F("story", "Who kills Suguru Geto at the end of Jujutsu Kaisen 0?", "Satoru Gojo", ["Yuta Okkotsu", "Toji Fushiguro", "Maki Zenin"]),
    F("charh", "Who were Yuta's classmates in Jujutsu Kaisen 0?", "Maki, Inumaki and Panda", ["Yuji, Megumi and Nobara", "Todo, Mai and Miwa", "Hakari, Kirara and Panda"]),
    F("charh", "Which foreign sorcerer fought for Geto in Jujutsu Kaisen 0?", "Miguel", ["Reggie Star", "Charles Bernard", "Dhruv Lakdawalla"]),
    F("anime", "When was Jujutsu Kaisen 0 released in Japanese cinemas?", "December 2021", ["October 2020", "July 2023", "January 2026"]),
    F("music", "Which band performed both songs for Jujutsu Kaisen 0, 'Ichizu' and 'Sakayume'?", "King Gnu", ["Eve", "Hitsujibungaku", "Cö shu Nie"]),
    # Season 3
    F("story", "Who is ordered to execute Yuji at the start of Season 3?", "Yuta Okkotsu", ["Satoru Gojo", "Maki Zenin", "Aoi Todo"]),
    F("story", "Does Yuta really kill Yuji in Season 3?", "No, he fakes it", ["Yes, but Yuji is revived by Sukuna", "Yes, but it's a dream", "He refuses and leaves"]),
    F("story", "Which Zen'in fights Choso while chasing Yuji at the start of Season 3?", "Naoya Zenin", ["Naobito Zenin", "Ogi Zenin", "Jinichi Zenin"]),
    F("story", "Who wipes out most of the Zen'in clan in Season 3?", "Maki Zenin", ["Megumi Fushiguro", "Toji Fushiguro", "Naoya Zenin"]),
    F("story", "Who gives her life so that Maki becomes as strong as Toji?", "Mai Zenin", ["Momo Nishimiya", "Kasumi Miwa", "Utahime Iori"]),
    F("story", "Who is named the next head of the Zen'in clan in Naobito's will?", "Megumi Fushiguro", ["Naoya Zenin", "Maki Zenin", "Ogi Zenin"]),
    F("story", "What is the deadly game Kenjaku starts across Japan called?", "The Culling Game", ["The Night Parade", "The Hidden Inventory", "The Goodwill Event"]),
    F("world", "How many colonies (barriers) does the Culling Game have?", "10", ["4", "8", "20"]),
    F("world", "In the Culling Game, how many points do you get for killing a player who is a sorcerer?", "5", ["1", "10", "100"]),
    F("world", "In the Culling Game, how many points do you get for killing a non-sorcerer player?", "1", ["5", "10", "0"]),
    F("world", "In the Culling Game, what happens to a player whose points don't change for 19 days?", "Their cursed technique is removed", ["They are sent home", "They lose all their points", "They become a curse"], "Having your technique removed kills you."),
    F("world", "How many points does a player need to add a new rule to the Culling Game?", "100", ["10", "50", "1,000"]),
    F("world", "What are the floating creatures that explain the Culling Game rules called?", "Kogane", ["Judgeman", "Mahoraga", "Nue"]),
    F("charh", "What was Hiromi Higuruma's job before the Culling Game?", "Lawyer", ["Police officer", "Doctor", "Teacher"]),
    F("charh", "What is the name of the shikigami in Higuruma's domain that judges people?", "Judgeman", ["Kogane", "Garuda", "Rika"]),
    F("techh", "What does Higuruma's domain take away if the accused is found guilty?", "Their cursed technique", ["Their memories", "Their name", "Their cursed energy for a year"], "For the worst crimes, it gives Higuruma an Executioner's Sword instead."),
    F("story", "Which colony does Yuji enter to find Higuruma in Season 3?", "Tokyo No. 1 Colony", ["Sendai Colony", "Tokyo No. 2 Colony", "Sakurajima Colony"]),
    F("story", "Which colony does Yuta enter at the end of Season 3?", "Sendai Colony", ["Tokyo No. 1 Colony", "Tokyo No. 2 Colony", "Shibuya Colony"]),
    F("charh", "Who is the girl Megumi meets in Tokyo No. 1 Colony, known as the 'Angel'?", "Hana Kurusu", ["Kirara Hoshi", "Remi", "Takako Uro"]),
    F("charh", "Which Culling Game player recreates things from receipts?", "Reggie Star", ["Haba", "Iori Hazenoki", "Fumihiko Takaba"]),
    F("charh", "Which Culling Game player is a struggling comedian?", "Fumihiko Takaba", ["Reggie Star", "Charles Bernard", "Haba"]),
    F("charh", "What kind of cursed spirit is Kurourushi?", "A giant cockroach", ["A giant spider", "A dragon", "A snake"]),
    F("charh", "What does Hakari run while he is suspended from Jujutsu High?", "An underground fight club", ["A casino", "A ramen shop", "A pachinko parlour"]),
    F("charh", "Which special grade sorcerer, who also asks people their 'type', appears in Season 3?", "Yuki Tsukumo", ["Mei Mei", "Utahime Iori", "Shoko Ieiri"]),
    F("story", "Who explains Kenjaku's plan and the Culling Game to the sorcerers in Season 3?", "Tengen", ["Yuki Tsukumo", "Gakuganji", "Uraume"]),
    # the anime itself
    F("anime", "Which studio animates Jujutsu Kaisen?", "MAPPA", ["Ufotable", "Bones", "Wit Studio"]),
    F("anime", "Who created Jujutsu Kaisen?", "Gege Akutami", ["Koyoharu Gotouge", "Tatsuki Fujimoto", "Kohei Horikoshi"]),
    F("anime", "In which magazine did the Jujutsu Kaisen manga run?", "Weekly Shōnen Jump", ["Weekly Shōnen Magazine", "Monthly Shōnen Sunday", "Young Jump"]),
    F("anime", "When did the Jujutsu Kaisen anime first air?", "October 2020", ["April 2019", "January 2021", "July 2020"]),
    F("anime", "When did Season 2 start airing?", "July 2023", ["October 2022", "January 2023", "April 2024"]),
    F("anime", "When did Season 3 (The Culling Game Part 1) start airing?", "January 2026", ["October 2025", "July 2025", "April 2026"]),
    F("anime", "What does 'Jujutsu Kaisen' roughly mean in English?", "Sorcery Fight", ["Cursed Blade", "Spirit Hunter", "Demon School"]),
    F("anime", "What are the two parts of Season 2 called?", "Hidden Inventory / Premature Death, and The Shibuya Incident", ["Fearsome Womb and Vs. Mahito", "The Culling Game Parts 1 and 2", "Perfect Preparation and Execution"]),
    F("anime", "Who directed Season 1?", "Sunghoo Park", ["Shota Goshozono", "Haruo Sotozaki", "Tetsuro Araki"]),
    F("anime", "Who directed Season 2?", "Shota Goshozono", ["Sunghoo Park", "Hiroyuki Imaishi", "Masashi Kudo"]),
    F("music", "Which song was the first opening of Season 1?", "Kaikai Kitan", ["VIVID VICE", "SPECIALZ", "Ao no Sumika"]),
    F("music", "Who sings 'Kaikai Kitan'?", "Eve", ["King Gnu", "Tatsuya Kitani", "Who-ya Extended"]),
    F("music", "Which song was the second opening of Season 1?", "VIVID VICE", ["Kaikai Kitan", "AIZO", "SPECIALZ"]),
    F("music", "Who performs 'VIVID VICE'?", "Who-ya Extended", ["Eve", "King Gnu", "Cö shu Nie"]),
    F("music", "Who performs the Season 1 ending 'Lost in Paradise'?", "ALI (feat. AKLO)", ["Eve", "Hitsujibungaku", "jo0ji"]),
    F("music", "Who performs the Season 1 ending 'give it back'?", "Cö shu Nie", ["ALI", "Soushi Sakiyama", "Who-ya Extended"]),
    F("music", "What is the opening song of Hidden Inventory / Premature Death?", "Ao no Sumika", ["SPECIALZ", "Kaikai Kitan", "AIZO"]),
    F("music", "Who sings 'Ao no Sumika'?", "Tatsuya Kitani", ["Eve", "Soushi Sakiyama", "King Gnu"]),
    F("music", "What is the ending song of Hidden Inventory / Premature Death?", "Akari", ["more than words", "give it back", "Yoake no Uta"]),
    F("music", "Who performs the Hidden Inventory ending 'Akari'?", "Soushi Sakiyama", ["Tatsuya Kitani", "Hitsujibungaku", "jo0ji"]),
    F("music", "What is the opening song of the Shibuya Incident?", "SPECIALZ", ["AIZO", "Ao no Sumika", "VIVID VICE"]),
    F("music", "Which band performs 'SPECIALZ'?", "King Gnu", ["Hitsujibungaku", "Who-ya Extended", "Cö shu Nie"]),
    F("music", "What is the ending song of the Shibuya Incident?", "more than words", ["Akari", "Lost in Paradise", "Yoake no Uta"]),
    F("music", "Who performs the Shibuya Incident ending 'more than words'?", "Hitsujibungaku", ["King Gnu", "ALI", "Soushi Sakiyama"]),
    F("music", "What is the opening song of Season 3 (The Culling Game Part 1)?", "AIZO", ["SPECIALZ", "Kaikai Kitan", "Ao no Sumika"]),
    F("music", "Who performs the Season 3 ending 'Yoake no Uta'?", "jo0ji", ["Eve", "King Gnu", "Tatsuya Kitani"]),
    F("music", "Which band performs the openings of both the Shibuya Incident and Season 3?", "King Gnu", ["Eve", "Who-ya Extended", "Hitsujibungaku"]),
]
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ assemble exactly 1,000
total = sum(len(v) for v in Q.values())
print({k: len(v) for k, v in Q.items()}, total, file=sys.stderr)
LIMIT = {"ep_season": 59, "va_en": 60, "va_jp": 60}
FAME = {n: i for i, n in enumerate(KNOWN)}
for k, n in LIMIT.items():
    if k.startswith("va_"):   # the best-known characters first
        Q[k].sort(key=lambda q: FAME.get(q["ks"][0][5:], 999))
    else:
        rng.shuffle(Q[k])
    Q[k] = Q[k][:n]
bank = [q for v in Q.values() for q in v]
print("after limits", len(bank), file=sys.stderr)
if len(bank) > 1000:
    order = ["fight_in", "tech_arc", "fight_arc", "tech_of", "debut_arc", "ep_title", "ep_season"]
    extra = len(bank) - 1000
    for k in order:
        while extra and len(Q[k]) > 20:
            Q[k].pop(); extra -= 1
    bank = [q for v in Q.values() for q in v]
if len(bank) != 1000:
    raise SystemExit(f"bank has {len(bank)} questions")
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank), collections.Counter(q["c"] for q in bank).most_common(), file=sys.stderr)
