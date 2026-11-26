"""Build the Animals question bank (exactly 1,000 questions).

Sources (English Wikipedia and Wikidata, CC BY-SA / CC0):
- "List of animal names": young, female, male and group names, and the adjectives (feline, bovine...)
- "List of national animals"
- each animal's class and IUCN status from the taxonomy box of its Wikipedia article (animals_check.py)
- dog and cat breeds' countries of origin from Wikidata
- records, bodies, behaviour, habitats and diets written from Wikipedia articles, each with the exact text behind it,
  which is checked again here
Usage: gen_animals.py WORK_DIR OUT.json [--avail|--show|--loose]
"""
import sys, json, random, re, collections, os, unicodedata

W, OUT = sys.argv[1:3]
rng = random.Random(20261126)
Q = collections.defaultdict(list)
SEEN = set()
NAMES = json.load(open(f"{W}/names.json"))

GROUP = {}
for g, kinds in {
    "Baby animals": "young younghard", "Animal groups": "group", "Males & females": "male female", "Animal words": "adj adjrev",
    "Classification": "cls clspick clsnot legs", "Endangered": "iucn iucnpick", "Dogs & cats": "dog dogpick cat", "National animals": "nat natrev",
    "Records": "records", "Bodies": "bodies", "Behaviour": "behaviour", "Habitats": "habitats", "Diet": "diet dietpick",
}.items():
    for k in kinds.split():
        GROUP[k] = g
TARGET = {"Baby animals": 105, "Animal groups": 95, "Males & females": 60, "Animal words": 25, "Classification": 143, "Endangered": 50,
          "Dogs & cats": 90, "National animals": 70, "Records": 90, "Bodies": 80, "Behaviour": 77, "Habitats": 45, "Diet": 70}


def add(c, k, q, a, opts, x=None, ks=None):
    a = str(a)
    opts = [o for o in dict.fromkeys(str(o) for o in opts) if o and o.lower() != a.lower()]
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
    Q[c].append(d)
    return True


def pick(pool, n=3, avoid=()):
    avoid = {a.lower() for a in avoid}
    pool = [p for p in dict.fromkeys(pool) if p.lower() not in avoid]
    return rng.sample(pool, min(n, len(pool)))


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


BANNED = {"bitch", "she-bear"}          # correct terms, but not for this site
cap = lambda s: s[:1].upper() + s[1:]


def plural(name):
    n = name.lower()
    special = {"mouse": "mice", "goose": "geese", "ox": "oxen", "deer": "deer", "sheep": "sheep", "fish": "fish", "moose": "moose",
               "bison": "bison", "salmon": "salmon", "cod": "cod", "herring": "herring", "sardine": "sardines", "octopus": "octopuses",
               "fly": "flies", "butterfly": "butterflies", "ladybug": "ladybugs", "wolf": "wolves", "starfish": "starfish",
               "hippopotamus": "hippos", "rhinoceros": "rhinos", "cattle": "cattle", "human": "humans", "giant panda": "giant pandas",
               "polar bear": "polar bears", "guinea pig": "guinea pigs", "guinea fowl": "guinea fowl", "prairie dog": "prairie dogs",
               "sea otter": "sea otters", "sea urchin": "sea urchins", "grouse": "grouse", "quail": "quail", "gnu": "gnus", "elk": "elk",
               "wildebeest": "wildebeest", "lynx": "lynxes", "fox": "foxes", "finch": "finches", "goldfinch": "goldfinches",
               "ass": "asses", "donkey": "donkeys", "turkey": "turkeys", "monkey": "monkeys", "jay": "jays", "toucan": "toucans",
               "peafowl": "peafowl", "seahorse": "seahorses", "platypus": "platypuses", "kinkajou": "kinkajous", "wild boar": "wild boar",
               "squid": "squid", "chinchilla": "chinchillas", "mongoose": "mongooses", "porcupine": "porcupines"}
    if n in special:
        return special[n]
    if n.endswith(("s", "sh", "ch", "x")):
        return n + "es"
    if n.endswith("y") and n[-2:-1] not in "aeiou":
        return n[:-1] + "ies"
    return n + "s"


# ------------------------------------------------------------------ names: young, female, male, groups, adjectives
def clean_animal(a):
    a = re.sub(r"\(\s*list\s*\)", "", a)
    a = re.sub(r"\s*(See|Also see)\b.*$", "", a).strip()
    a = {"Ass/donkey": "Donkey", "Boar /wild pig": "Wild boar", "Elk /wapiti": "Elk", "Bear": "Bear"}.get(a.replace("  ", " ").strip(), a.strip())
    return a


SKIP = {"Human", "Pug", "Junglefowl", "Ram", "Mallard", "Dogfish", "Cardinal", "Kingbird", "Goosander", "Dunlin", "Chough", "Peccary",
        "Sand dollar", "Sandpiper", "Binturong", "Bobcat", "Gecko"}
N = {}
for n in NAMES["names"]:
    a = clean_animal(n["animal"])
    if a in SKIP or not a or "See" in n["animal"] and not any(n[k] for k in ("young", "female", "male", "group")):
        continue
    if not any(n[k] for k in ("young", "female", "male", "group")):
        continue
    N[a] = {k: [t.lower() for t in n[k] if t.lower() not in BANNED and len(t) < 20] for k in ("young", "female", "male", "group", "adjective")}
# related animals that shouldn't be wrong answers for each other's names
KIN = [{"Crow", "Raven", "Rook", "Jay"}, {"Lion", "Tiger", "Leopard", "Jaguar", "Cheetah", "Cat"}, {"Whale", "Dolphin", "Narwhal", "Seal"},
       {"Horse", "Zebra", "Donkey"}, {"Deer", "Elk", "Moose", "Antelope", "Gnu", "Wildebeest", "Giraffe", "Camel", "Llama", "Alpaca", "Guanaco",
        "Goat", "Sheep", "Cattle"}, {"Kangaroo", "Wallaby", "Koala", "Wombat", "Opossum"}, {"Duck", "Goose", "Swan"}, {"Rabbit", "Hare"},
       {"Bee", "Wasp", "Hornet", "Ant", "Termite"}, {"Frog", "Toad", "Newt", "Salamander"}, {"Rat", "Mouse", "Hamster", "Gerbil", "Guinea pig"},
       {"Hawk", "Eagle", "Falcon"}, {"Pig", "Wild boar"}, {"Dog", "Wolf", "Fox"}, {"Shark", "Stingray"}, {"Moth", "Butterfly"},
       {"Bear", "Polar bear", "Giant panda"}, {"Gorilla", "Ape", "Monkey", "Baboon", "Lemur"}, {"Chicken", "Turkey", "Pheasant", "Quail",
        "Partridge", "Grouse", "Guinea fowl", "Peafowl"}, {"Otter", "Sea otter", "Weasel", "Ferret", "Badger", "Skunk"}, {"Squid", "Octopus"}]
kin_of = lambda a: set().union(*[k for k in KIN if a in k]) if any(a in k for k in KIN) else {a}
GENERIC_YOUNG = {"calf", "cub", "pup", "puppy", "chick", "kit", "kitten", "larva", "pupa", "hatchling", "infant", "baby", "nymph", "nestling",
                 "fledgling", "whelp", "juvenile", "child"}
GENERIC_GROUP = {"herd", "flock", "group", "colony", "swarm", "nest", "family", "troop", "school", "litter", "brood", "clutch", "team", "band",
                 "bunch", "cluster", "shoal", "cloud", "flight", "cast", "singular", "drove", "gang", "horde", "rabble", "mob", "army", "pack",
                 "pod", "kennel", "stand", "hive", "nursery", "tribe", "field", "string", "stable", "brace", "yoke", "host"}
KNOWN_YOUNG = set("joey cygnet gosling eaglet leveret elver kid foal fawn piglet puggle cria owlet tadpole squab poult hoglet duckling lamb "
                  "calf cub pup kitten chick kit spiderling peachick froglet puppy caterpillar maggot colt filly porcupette".split())
KNOWN_GROUP = set("pride murder parliament gaggle pod crash tower dazzle bloat business unkindness conspiracy flamboyance prickle romp raft sleuth "
                  "skulk leap ambush streak mischief kaleidoscope murmuration cackle clowder mob army exaltation charm bevy wisdom coalition "
                  "waddle embarrassment parade memory shiver fever smack bale knot rafter scurry huddle caravan scold confusion".split())
KNOWN_MALE = set("drake gander cob tom stallion ram bull boar buck stag cock rooster billy jack tod hob boomer gobbler peacock hart drone silverback".split())
KNOWN_FEMALE = set("pen queen mare ewe cow sow doe hind hen nanny jenny vixen jill peahen lioness tigress leopardess flyer gilt".split())
YOUNG_POOL = sorted({t for v in N.values() for t in v["young"]} & KNOWN_YOUNG)
GROUP_POOL = sorted({t for v in N.values() for t in v["group"]} & KNOWN_GROUP)
BIRD_LIKE = {"chick", "nestling", "fledgling", "hatchling"}
ADJ_KNOWN = set("feline canine bovine equine porcine ovine caprine lupine vulpine ursine leonine aquiline asinine corvine anserine cervine murine "
                "leporine elephantine serpentine simian avian piscine apian".split())


def name_distractors(a, field, pool):
    own = set(N[a][field])
    for k in kin_of(a):
        own |= set(N.get(k, {}).get(field, []))
    return [t for t in pool if t not in own]


def article(w):
    return ("an " if w[:1] in "aeiou" else "a ") + w


for a, v in N.items():
    ys = v["young"]
    if ys:
        fun = [t for t in ys if t not in GENERIC_YOUNG]
        known = [t for t in ys if t in KNOWN_YOUNG]
        ans = next((t for t in known if t not in GENERIC_YOUNG), None) or (known[0] if known else (fun[0] if fun else ys[0]))
        if ans in ("larva", "pupa", "baby", "infant", "juvenile") and not fun:
            continue
        hard = ans in fun and len(ans) > 3
        others = [t for t in ys if t != ans]
        q = f"What is a baby {a.lower()} called?" if not others else f"Which of these is a name for a baby {a.lower()}?"
        x = f"A baby {a.lower()} is {article(ans)}" + (f"; it can also be called {', '.join(others[:3])}." if others else ".")
        add("younghard" if hard else "young", f"young:{a}", q, cap(ans), [cap(t) for t in pick(name_distractors(a, "young", YOUNG_POOL))], x, [f"a:{a}"])
    gs = [t for t in v["group"] if t not in GENERIC_GROUP]
    if gs:
        ans = gs[0]
        q = f"Which of these is a name for a group of {plural(a)}?" if len(v["group"]) > 1 else f"What is a group of {plural(a)} called?"
        x = f"A group of {plural(a)} can be called {article(ans)}" + (f". Other names: {', '.join(t for t in v['group'] if t != ans)}." if len(v["group"]) > 1 else ".")
        add("group", f"group:{a}", q, cap(ans), [cap(t) for t in pick(name_distractors(a, "group", GROUP_POOL))], x, [f"a:{a}"])
    for sex in ("male", "female"):
        ts = [t for t in v[sex] if t not in ("male", "female", a.lower(), "dam", "sire") and t in (KNOWN_MALE if sex == "male" else KNOWN_FEMALE)]
        if not ts or (sex == "female" and ts[0] in ("cow", "hen", "sow", "doe") and len(N) and rng.random() < 0.5) or \
                (sex == "male" and ts[0] in ("bull", "cock", "boar", "buck") and rng.random() < 0.5):
            continue
        ans = ts[0]
        pool = sorted({t for b, w in N.items() for t in w[sex] if t not in BANNED} - set(v[sex]) - {"male", "female", "dam", "sire"} -
                      {t for b in kin_of(a) for t in N.get(b, {}).get(sex, [])})
        pool = [t for t in pool if t != a.lower() and t not in {x.lower() for x in N} and t in (KNOWN_MALE if sex == "male" else KNOWN_FEMALE)]
        q = f"What is a {sex} {a.lower()} called?" if len(ts) == 1 else f"Which of these is a name for a {sex} {a.lower()}?"
        add(sex, f"{sex}:{a}", q, cap(ans), [cap(t) for t in pick(pool)], f"A {sex} {a.lower()} is {article(ans)}" +
            (f"; also {', '.join(t for t in ts if t != ans)}." if len(ts) > 1 else "."), [f"a:{a}"])
    ADJ_COUNT = collections.Counter(t for w in N.values() for t in w["adjective"])
    adj = sorted([t for t in v["adjective"] if t in ADJ_KNOWN], key=lambda t: ADJ_COUNT[t])
    if adj:
        ans = adj[0]
        pool = sorted({t for b, w in N.items() if b not in kin_of(a) for t in w["adjective"] if t in ADJ_KNOWN} - set(adj))
        who = "cattle" if a == "Cattle" else plural(a)
        add("adj", f"adj:{a}", f"Which word means \u201cto do with {who}\u201d?", cap(ans), [cap(t) for t in pick(pool)],
            f"{cap(ans)} means to do with {who}.", [f"a:{a}"])
        animals = [b for b, w in N.items() if b not in kin_of(a) and set(w["adjective"]) & ADJ_KNOWN]
        if ADJ_COUNT[ans] == 1: add("adjrev", f"adjrev:{a}", f"Which animals does the word \u201c{ans}\u201d describe?", cap(who), [cap("cattle" if b == "Cattle" else plural(b)) for b in pick(animals)],
            f"{cap(ans)} means to do with {who}.", [f"a:{a}"])

THE = {"United States", "United Kingdom", "Netherlands", "Philippines", "Democratic Republic of the Congo", "United Arab Emirates", "Czech Republic",
       "Bahamas", "Gambia", "Maldives", "Central African Republic", "Dominican Republic", "Solomon Islands", "Marshall Islands", "Comoros",
       "Republic of the Congo", "Seychelles", "Vatican City"}
the = lambda c: ("the " + c) if c in THE else c
poss = lambda c: the(c) + ("'" if c.endswith("s") else "'s")
low1 = lambda n: n if n[:1].isupper() and (" " in n and n.split()[0][0].isupper() and n.split()[0].lower() not in ("red", "golden", "brown", "gray", "grey", "white", "black", "blue", "bald", "giant", "snow", "great", "common", "lion")) else n[:1].lower() + n[1:]
# ------------------------------------------------------------------ national animals
COUNTRIES = {}
for r in json.load(open(f"{W}/../wd/countries.json")):
    COUNTRIES[r["cLabel"]] = max(COUNTRIES.get(r["cLabel"], 0), int(r["n"]))
FAMOUS = {c for c, n in COUNTRIES.items() if n >= 250} | {"Scotland", "Wales", "England"}
NAT = collections.defaultdict(list)
for r in NAMES["national"]:
    m = re.match(r"^(.*?)\s*\(\s*([^)]*)\)\s*$", r["animal"])
    name, kind = (m.group(1), m.group(2)) if m else (r["animal"], "")
    name = name.strip().replace("Eurasian elk/moose", "Moose")
    if r["country"] == "United Kingdom":
        nation = {"England": "England", "Wales": "Wales", "Scotland": "Scotland"}.get(kind.strip())
        if nation and name in ("Lion", "Unicorn"):
            NAT[(nation, "national animal")].append(name)
        continue
    NAT[(r["country"], kind.strip())].append(name)
NAT[("Wales", "national animal")] = ["Red dragon"]
for kind, label in (("national animal", "national animal"), ("national bird", "national bird")):
    entries = {c: v[0] for (c, k), v in NAT.items() if k == kind and len(v) == 1}
    names_pool = sorted(set(entries.values()) - {"Unicorn", "Red dragon", "Lion"})
    for c, animal in entries.items():
        if c not in FAMOUS:
            continue
        theirs = {x.lower() for (cc, k), v in NAT.items() if cc == c for x in v}
        opts = [o for o in pick(names_pool, 8) if o.lower() not in theirs and o.lower() != animal.lower()]
        add("nat", f"nat:{c}:{kind}", f"What is the {label} of {the(c)}?", animal, opts,
            f"{cap(poss(c))} {label} is the {low1(animal)}.", [f"country:{c}"])
        others = [cc for cc, a2 in entries.items() if a2.lower() != animal.lower() and cc in FAMOUS and
                  not any(x.lower() == animal.lower() for (c3, k3), v3 in NAT.items() if c3 == cc for x in v3)]
        if sum(1 for a2 in entries.values() if a2.lower() == animal.lower()) == 1:
            add("natrev", f"natrev:{c}:{kind}", f"Which country has the {low1(animal)} as its {label}?", c, pick(others),
                f"The {low1(animal)} is the {label} of {the(c)}.", [f"country:{c}"])

# ------------------------------------------------------------------ dog and cat breeds (Wikidata)
FIX = {"People's Republic of China": "China", "German Empire": "Germany", "Siberia": "Russia", "Alaska": "United States", "Siam": "Thailand",
       "Tsardom of Russia": "Russia", "Kingdom of Great Britain": "United Kingdom", "Cornwall": "England", "California": "United States"}
UKISH = {"United Kingdom", "England", "Scotland", "Wales"}
DROP = {"Soviet Central Asia", "Ancient Rome", "Czechoslovakia", "Arabian Peninsula", "North America", "Soviet Union", "Tibet"}
UNSURE = {"Pyrenean Mountain Dog", "Bloodhound", "Akita (dog breed)", "Labrador Retriever", "Jack Russell Terrier", "Australian Shepherd",
          "Abyssinian cat", "Saluki", "European Shorthair", "Birman", "Cymric cat", "Javanese cat", "Tonkinese cat", "Balinese cat", "Tibetan Mastiff"}


def breeds(f, min_n):
    by = collections.defaultdict(set)
    n = {}
    for r in json.load(open(f)):
        by[r["title"]].add(FIX.get(r["cLabel"], r["cLabel"])); n[r["title"]] = int(r["n"])
    out = {}
    for t, cs in by.items():
        if t in UNSURE or n[t] < min_n or cs & DROP:
            continue
        if len(cs) > 1:
            if cs <= UKISH:
                cs = (cs - {"United Kingdom"}) or {"United Kingdom"}
            if len(cs) > 1:
                continue
        name = re.sub(r"\s*\((dog|cat) breed\)|\s+dog$|\s+cat$", "", t).replace("Dalmatian", "Dalmatian").strip()
        out[name] = next(iter(cs))
    return out, n


DOGS, dn = breeds(f"{W}/../wd/dogs.json", 34)
CATS, cn = breeds(f"{W}/../wd/cats.json", 22)
same_place = lambda a, b: a == b or (a in UKISH and b in UKISH)
COUNTRY_POOL = sorted(set(DOGS.values()) | set(CATS.values()) | {"Denmark", "Netherlands", "Poland", "Spain", "Portugal", "Austria", "Canada", "Brazil",
                                                                  "India", "Egypt", "Turkey", "Hungary", "Mexico", "Norway"})
GIVEAWAY = {"Germany": "german", "Italy": "italian", "United States": "american boston carolina", "United Kingdom": "english british welsh scottish",
            "England": "english british", "Scotland": "scottish scotch", "Wales": "welsh", "France": "french", "Ireland": "irish", "Russia": "russian siberian",
            "Turkey": "turkish", "Japan": "japanese", "Norway": "norwegian", "Australia": "australian", "Belgium": "belgian", "China": "chinese",
            "Egypt": "egyptian", "Brazil": "brazilian", "Thailand": "thai siamese", "Afghanistan": "afghan", "Canada": "canadian", "Mexico": "mexican",
            "Spain": "spanish", "Portugal": "portuguese", "Hungary": "hungarian", "Croatia": "croatian", "Switzerland": "swiss", "Greece": "greek",
            "Myanmar": "burmese", "Iran": "persian", "Isle of Man": "manx", "Argentina": "argentino", "Netherlands": "dutch", "Denmark": "danish",
            "Finland": "finnish", "Greenland": "greenland", "Tibet": "tibetan", "Kenya": "kenyan", "Ukraine": "ukrainian", "Czech Republic": "czech"}
gives = lambda b, c: any(w in b.lower() for w in (GIVEAWAY.get(c, "") + " " + c.lower()).split())
for kind, B in (("dog", DOGS), ("cat", CATS)):
    B = {b: c for b, c in B.items() if not gives(b, c)}
    for b, c in B.items():
        word = "dog breed" if kind == "dog" else "cat breed"
        trap = ["Denmark"] if b == "Great Dane" else []
        opts = trap + pick([x for x in COUNTRY_POOL if not same_place(x, c)], 3)
        add(kind, f"{kind}:{b}", f"Which country does the {b} come from?", cap(the(c)), [cap(the(o)) for o in opts],
            f"The {b} is a {word} from {the(c)}." + (" Despite the name, it isn't Danish." if b == "Great Dane" else ""), [f"breed:{b}"])
    if kind == "dog":
        for c in sorted(set(B.values())):
            mine = [b for b, cc in B.items() if cc == c]
            for b in mine[:3]:
                others = [x for x, cc in B.items() if not same_place(cc, c)]
                others = [x for x in others if not gives(x, c)]
                add("dogpick", f"dogpick:{c}:{b}", f"Which of these dog breeds comes from {the(c)}?", b, pick(others),
                    f"The {b} comes from {the(c)}.", [f"breed:{b}", f"dogcountry:{c}"])

# ------------------------------------------------------------------ class, conservation status, diet (checked against Wikipedia's taxonomy boxes)
A = json.load(open(f"{W}/animals.json")) if os.path.exists(f"{W}/animals.json") else []
CLS_WORD = {"mammal": "a mammal", "bird": "a bird", "reptile": "a reptile", "amphibian": "an amphibian", "fish": "a fish", "insect": "an insect",
            "arachnid": "an arachnid", "crustacean": "a crustacean", "mollusc": "a mollusc"}
CLS_PL = {"mammal": "mammals", "bird": "birds", "reptile": "reptiles", "amphibian": "amphibians", "fish": "fish", "insect": "insects",
          "arachnid": "arachnids", "crustacean": "crustaceans", "mollusc": "molluscs"}
SURPRISE = {"Seahorse", "Whale shark", "Platypus", "Echidna", "Vampire bat", "Fruit bat", "Blue whale", "Orca", "Dolphin", "Narwhal", "Manatee",
            "Tuatara", "Woodlouse", "Krill", "Scorpion", "Tick", "Axolotl", "Stingray", "European eel", "Penguin", "Emperor penguin",
            "Kiwi", "Garden snail", "Giant squid", "Common octopus", "Pangolin", "Green sea turtle", "Hippopotamus", "Walrus", "Great white shark"}
byc = collections.defaultdict(list)
for a in A:
    byc[a["class"]].append(a)
for a in A:
    c = a["class"]
    if a["name"] in SURPRISE or rng.random() < 0.55:
        near = {"mammal": ["fish", "bird", "reptile"], "bird": ["mammal", "reptile", "insect"], "reptile": ["amphibian", "mammal", "fish"],
                "amphibian": ["reptile", "fish", "mammal"], "fish": ["mammal", "amphibian", "reptile"], "insect": ["arachnid", "crustacean", "bird"],
                "arachnid": ["insect", "crustacean", "mollusc"], "crustacean": ["insect", "fish", "mollusc"], "mollusc": ["fish", "crustacean", "insect"]}[c]
        add("cls", f"cls:{a['name']}", f"What kind of animal is the {a['name'].lower() if a['name'] not in ('Tuatara',) else 'tuatara'}?", cap(CLS_WORD[c][2:] if CLS_WORD[c].startswith('a ') else CLS_WORD[c][3:]),
            [cap(n) for n in near], f"The {a['name'].lower()} is {CLS_WORD[c]}.", [f"an:{a['name']}"])
for c, lst in byc.items():
    if len(lst) < 3:
        continue
    for a in lst:
        if a["name"] not in SURPRISE and rng.random() < 0.6:
            continue
        wrong = [b["name"] for b in A if b["class"] != c and (b["lives"] == a["lives"] or rng.random() < 0.3)]
        add("clspick", f"clspick:{c}:{a['name']}", f"Which of these animals is {CLS_WORD[c]}?", a["name"], pick(wrong),
            f"The {a['name'].lower()} is {CLS_WORD[c]}; the others aren't {CLS_PL[c]}.", [f"an:{a['name']}", f"kind:clspick{c}"])
        same = [b["name"] for b in lst if b["name"] != a["name"]]
    for b in rng.sample(A, min(len(A), 40)):
        if b["class"] == c or len(lst) < 4:
            continue
        if b["name"] not in SURPRISE and rng.random() < 0.7:
            continue
        three = pick([x["name"] for x in lst if x["lives"] == b["lives"]] or [x["name"] for x in lst], 3)
        if len(three) < 3:
            continue
        add("clsnot", f"clsnot:{c}:{b['name']}", f"Which of these animals is NOT {CLS_WORD[c]}?", b["name"], three,
            f"The {b['name'].lower()} is {CLS_WORD[b['class']]}. {', '.join(three)} are all {CLS_PL[c]}.", [f"an:{b['name']}", f"kind:clsnot{c}"])
LEGS = {"insect": 6, "arachnid": 8}
for lbl, n in (("an insect", 6), ("a spider", 8)):
    add("legs", f"legs:{lbl}", f"How many legs does {lbl} have?", n, [str(v) for v in (4, 6, 8, 10) if v != n], f"Insects have 6 legs and spiders have 8.", [f"legs:{lbl}"])
STATUS_ORDER = ["Least Concern", "Near Threatened", "Vulnerable", "Endangered", "Critically Endangered"]
# conservation status belongs to one species, so these questions use the species' own name (golden hamster, not "hamster")
LATIN = {"Aedes aegypti", "Lucanus cervus", "Atta cephalotes", "Vespula vulgaris", "Latrodectus mactans", "Ixodes ricinus", "Brachypelma hamorii"}
sp = lambda a: a["name"] if a["title"] in LATIN else re.sub(r"\s*\(.*\)$", "", a["title"])
PROPER = r"^(American|African|Atlantic|European|Indian|Mexican|Bornean|Chinese|North|West Indian|Galápagos|Antarctic|German|Komodo|Indo-Pacific)\b"
spl = lambda a: sp(a) if re.match(PROPER, sp(a)) else sp(a)[:1].lower() + sp(a)[1:]
for a in A:
    st = a.get("status")
    if st not in STATUS_ORDER or (st == "Least Concern" and rng.random() < 0.65):     # so "Least Concern" isn't the usual answer
        continue
    add("iucn", f"iucn:{a['name']}", f"How does the IUCN Red List rate the {spl(a)}?", st, [s_ for s_ in STATUS_ORDER if s_ != st],
        f"The {spl(a)} is listed as {st} on the IUCN Red List.", [f"an:{a['name']}"])
risky = [a for a in A if a.get("status") in ("Endangered", "Critically Endangered")]
safe = [a for a in A if a.get("status") == "Least Concern"]
for a in risky:
    add("iucnpick", f"iucnpick:{a['name']}", "Which of these animals is listed as endangered?", cap(sp(a)), pick([cap(sp(b)) for b in safe]),
        f"The {spl(a)} is {a['status']}; the others are Least Concern.", [f"an:{a['name']}", "kind:iucnpick"])
# diet: only animals whose diet is plainly plants or plainly meat (no insect-eaters, blood-feeders or invertebrates)
NOT_PLAIN = {"Giant anteater", "Aardvark", "Pangolin", "Echidna", "Platypus", "Vampire bat", "Gecko", "Tuatara", "Fire salamander", "Great crested newt",
             "Cane toad", "Axolotl", "Hedgehog", "Armadillo"}
DIET_WORD = {"herbivore": "a herbivore (plants only)", "carnivore": "a carnivore (meat eater)", "omnivore": "an omnivore (plants and meat)"}
plain = [x for x in A if x["diet"] in DIET_WORD and x["name"] not in NOT_PLAIN and x["class"] in ("mammal", "bird", "reptile", "fish")]
for d in ("herbivore", "carnivore"):
    for a in [x for x in plain if x["diet"] == d]:
        other = [x["name"] for x in plain if x["diet"] != d and x["class"] == a["class"]]
        add("dietpick", f"dietpick:{d}:{a['name']}", f"Which of these animals is {DIET_WORD[d].split(' (')[0]}?", a["name"], pick(other),
            f"The {a['name'].lower()} is {DIET_WORD[d]}; the others aren't.", [f"an:{a['name']}", f"kind:dietpick{d}"])


# ------------------------------------------------------------------ written facts, each with the Wikipedia text behind it
def evidence_ok(text, ev):
    f = lambda s: norm(s).replace("’", "'").replace("“", '"').replace("”", '"').lower()
    return f(ev) in f(text)


def page_file(p):
    return f"{W}/../facts/{re.sub(r'[^A-Za-z0-9_.()-]', '', p.replace(' ', '_'))}.txt"


if os.path.exists(f"{W}/facts_q.json"):
    items, bad = json.load(open(f"{W}/facts_q.json")), 0
    DROP = {"Which is the fastest mammal of all, reaching about 160 km/h in level flight?"}     # the bat's own page only calls this "claimed"
    for it in items:
        if it["q"] in DROP:
            bad += 1; continue
        f = page_file(it["page"])
        cands = [f] + [os.path.join(f"{W}/../facts", x) for x in os.listdir(f"{W}/../facts") if x.lower().startswith(it["page"].replace(" ", "_").lower()[:20])]
        if not any(os.path.exists(c) and evidence_ok(open(c).read(), it["evidence"]) for c in cands):
            bad += 1; continue
        add(it["topic"], f"{it['topic']}:{it['q']}", it["q"], it["a"], it["o"], it.get("x"), [f"an:{it.get('animal', '')}", f"fact:{it['q']}"])
    print(f"facts: {len(items) - bad} kept, {bad} failed the evidence check")

# ================================================================== balance
WEIGHT = {"dietpick": 1, "young": 3, "younghard": 3, "group": 1, "male": 1, "female": 1, "adj": 1, "adjrev": 1, "cls": 3, "clspick": 2, "clsnot": 2, "legs": 0.2,
          "iucn": 2, "iucnpick": 1, "dog": 3, "dogpick": 1.5, "cat": 1.5, "nat": 2, "natrev": 1, "diet": 1, "dietpick": 1}
if "--show" in sys.argv:
    for k in Q:
        for q in rng.sample(Q[k], min(3, len(Q[k]))):
            print(f"[{k}] {q['q']}\n      A: {q['a']}  |  {' / '.join(q['o'])}\n      x: {q.get('x', '')}")
    sys.exit()
if "--avail" in sys.argv:
    for g in TARGET:
        print(f"{g:20} " + ", ".join(f"{k} {len(Q[k])}" for k in Q if GROUP[k] == g), "=", sum(len(Q[k]) for k in Q if GROUP[k] == g), "/", TARGET[g])
    sys.exit()
assert sum(TARGET.values()) == 1000, sum(TARGET.values())
out = []
for g, want in TARGET.items():
    kinds = [k for k in Q if GROUP[k] == g]
    pools = {k: rng.sample(Q[k], len(Q[k])) for k in kinds}
    took = collections.Counter()
    got = []
    while len(got) < want and any(pools.values()):
        k = min((k for k in kinds if pools[k]), key=lambda k: (took[k] / WEIGHT.get(k, 1), rng.random()))
        got.append(pools[k].pop()); took[k] += 1
    print(f"{g:20} {len(got):4}/{want}  " + ", ".join(f"{k} {took[k]}/{len(Q[k])}" for k in kinds))
    assert len(got) == want or "--loose" in sys.argv, g
    out += got
ONE_PER_GAME = {"legs", "iucnpick", "adjrev"}
for q in out:
    if q["c"] in ONE_PER_GAME:
        q["ks"] = (q.get("ks") or [q["k"]]) + ["kind:" + q["c"]]
for q in out:
    assert len(q["o"]) == 3 and q["a"] not in q["o"] and len(set(q["o"])) == 3, q
    for s in [q["q"], q["a"], *q["o"], q.get("x", "")]:
        assert not re.search(r"\bbitch\b", s, re.I), s
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
print(len(out), "questions")
