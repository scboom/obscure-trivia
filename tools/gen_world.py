"""Build the General Knowledge question bank (1,000 questions).

Country questions (capitals, currencies, languages, continents, flags, landlocked, size) use the
mledoze/countries dataset (ODbL) and flag-icons (MIT). Everything else is hand-written below and
sticks to well-established, easy-to-medium fun facts.
"""
import sys, os, json, random, hashlib, collections, shutil

COUNTRIES, FLAGDIR, OUT, OUTFLAGS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
rng = random.Random(20261121)
C = {x["cca2"]: x for x in json.load(open(COUNTRIES))}
Q = collections.defaultdict(list)


def add(cat, key, q, a, opts, img=None, rich=False):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) not in (1, 3):
        raise SystemExit(f"bad options for {q!r}: {opts}")
    rec = {"c": cat, "k": key, "q": q, "a": a, "o": opts}
    if img:
        rec["i"] = img
    if rich:
        rec["r"] = 1
    Q[cat].append(rec)


def pick(pool, n, exclude=()):
    cand = [x for x in dict.fromkeys(pool) if x not in exclude]
    rng.shuffle(cand)
    if len(cand) < n:
        raise SystemExit(f"not enough options in {pool[:5]}")
    return cand[:n]


# ------------------------------------------------------------------ countries
NAME = {"MV": "the Maldives", "TR": "Turkey", "CI": "Ivory Coast", "CD": "DR Congo", "VA": "Vatican City", "US": "the United States", "GB": "the United Kingdom",
        "NL": "the Netherlands", "PH": "the Philippines", "AE": "the United Arab Emirates", "BS": "the Bahamas", "CZ": "Czechia"}
PLAIN = {"US": "United States", "GB": "United Kingdom", "NL": "Netherlands", "PH": "Philippines", "AE": "United Arab Emirates", "BS": "Bahamas"}
def nm(code): return NAME.get(code, C[code]["name"]["common"])       # for use inside a sentence
def opt(code): return PLAIN.get(code, nm(code))                        # for use as an answer option
CAPFIX = {"Ulan Bator": "Ulaanbaatar", "Washington D.C.": "Washington, D.C.", "Reykjavik": "Reykjavík"}
def cap(code): return CAPFIX.get(C[code]["capital"][0], C[code]["capital"][0])

LIST = """GB FR DE IT ES PT NL BE CH AT IE SE NO DK FI IS PL CZ HU GR TR RO HR UA RU EE LT MT LU MC VA CN JP KR KP IN PK BD NP BT MV TH VN KH
MY SG PH MN KZ AF IR IQ SA AE QA KW JO EG MA DZ TN NG GH KE ET TZ UG RW ZW ZM SN CM CI MG SO CD BW NA US CA MX CU JM HT CR PA GT BR AR CL
PE CO VE EC UY PY BS AU NZ FJ PG MM SD LY""".split()
SKIP_CAP = {"BO", "ZA", "ID", "IL"}
def region(code):
    x = C[code]
    if x["region"] == "Americas":
        return "South America" if x.get("subregion") == "South America" else "North America"
    return x["region"]
def same_region(code):
    return [c for c in LIST if c != code and region(c) == region(code)]

TRICK = {"AU": "Sydney Melbourne Perth Brisbane", "CA": "Toronto|Vancouver|Montreal", "US": "New York City|Los Angeles|Chicago",
         "TR": "Istanbul|Izmir|Antalya", "BR": "Rio de Janeiro|São Paulo|Salvador", "CH": "Zurich|Geneva|Basel",
         "NZ": "Auckland|Christchurch|Queenstown", "IN": "Mumbai|Kolkata|Bangalore", "NG": "Lagos|Kano|Ibadan", "PK": "Karachi|Lahore|Peshawar",
         "VN": "Ho Chi Minh City|Da Nang|Hue", "MA": "Casablanca|Marrakesh|Fez", "KZ": "Almaty|Shymkent|Karaganda",
         "CN": "Shanghai|Hong Kong|Guangzhou", "JP": "Osaka|Kyoto|Hiroshima", "KR": "Busan|Incheon|Daegu", "DE": "Munich|Hamburg|Frankfurt",
         "IT": "Milan|Venice|Naples", "ES": "Barcelona|Seville|Valencia", "NL": "Rotterdam|The Hague|Utrecht", "SA": "Jeddah|Mecca|Dammam",
         "AE": "Dubai|Sharjah|Al Ain", "EG": "Alexandria|Giza|Luxor", "TZ": "Dar es Salaam|Arusha|Zanzibar City", "CI": "Abidjan|Bouaké|San-Pédro",
         "MM": "Yangon|Mandalay|Bagan", "PH": "Cebu City|Davao City|Baguio", "CO": "Medellín|Cali|Cartagena", "EC": "Guayaquil|Cuenca|Manta",
         "PE": "Cusco|Arequipa|Trujillo", "KE": "Mombasa|Kisumu|Nakuru", "RU": "Saint Petersburg|Kazan|Novosibirsk", "PL": "Kraków|Gdańsk|Wrocław",
         "GB": "Manchester|Birmingham|Liverpool", "IE": "Cork|Galway|Limerick", "GR": "Thessaloniki|Patras|Heraklion", "PT": "Porto|Faro|Coimbra",
         "MX": "Guadalajara|Cancún|Monterrey", "AR": "Córdoba|Rosario|Mendoza", "CL": "Valparaíso|Concepción|Antofagasta"}
TRICK["AU"] = "Sydney|Melbourne|Perth"
for code in LIST:
    if code in SKIP_CAP:
        continue
    c = cap(code)
    if code in ("VA", "MC", "SG", "KW"):
        continue      # capital shares the country's name
    ds = TRICK[code].split("|") if code in TRICK else [cap(x) for x in pick(same_region(code), 3)]
    add("capital", "c:" + code, f"What is the capital of {nm(code)}?", c, ds)
REV = "AU CA TR BR CH NZ NG PK VN MA KZ MM TZ CI EG JP KR TH KE PE CO AR CL CU IS NO SE FI PL HU CZ RO UA GR PT IE DZ GH ET UG NP MN SA AE QA".split()
for code in REV:
    add("capitalwho", "c:" + code, f"{cap(code)} is the capital of which country?", opt(code), [opt(x) for x in pick(same_region(code), 3)])

CUR = "GB US JP CN KR IN RU BR MX CH SE NO DK PL CZ HU TR TH VN ID MY PH SA AE EG NG KE IL IS AU NZ CA AR CL CO PE BD PK UA RO MA GH ET MN MM QA KW JO ZA DE IE HR FI".split()
def curname(code):
    return list(C[code]["currencies"].values())[0]["name"]
ALLCUR = sorted({curname(c) for c in CUR})
for code in CUR:
    a = curname(code)
    near_ = [curname(x) for x in same_region(code) if x in CUR and curname(x) != a]
    pool = near_ + [x for x in ALLCUR if x != a]
    ds = pick(near_, min(2, len(set(near_)))) if near_ else []
    ds += pick([x for x in pool if x not in ds], 3 - len(ds), exclude={a})
    add("currency", "c:" + code, f"What is the currency of {nm(code)}?", a, ds)
add("currency", "c:EC", "Which currency does Ecuador use?", "United States dollar", ["Ecuadorian sucre", "Colombian peso", "Peruvian sol"])
UNIT = {"JP": "yen", "CN": "yuan", "BR": "real", "PL": "złoty", "HU": "forint", "TR": "lira", "TH": "baht", "VN": "đồng", "ID": "rupiah",
        "MY": "ringgit", "NG": "naira", "IL": "shekel", "ZA": "rand", "UA": "hryvnia", "BD": "taka", "GH": "cedi", "ET": "birr", "MN": "tögrög",
        "MM": "kyat", "RU": "ruble", "CZ": "koruna", "GT": "quetzal", "CR": "colón", "PE": "sol", "VE": "bolívar", "HT": "gourde", "PG": "kina",
        "AF": "afghani", "RO": "leu", "SE": "krona"}
SHARE = {"RU": {"BY"}, "RO": {"MD"}, "SE": {"IS"}, "CZ": set()}
for code, unit in UNIT.items():
    ds = [opt(x) for x in pick([x for x in LIST if x not in (code, "IS") and x not in SHARE.get(code, set())], 3)]
    add("currencywho", "c:" + code, f"Which country uses the {unit} as its currency?", opt(code), ds)

LANG = {"BR": "Portuguese", "AO": "Portuguese", "MZ": "Portuguese", "MX": "Spanish", "AR": "Spanish", "CL": "Spanish", "CO": "Spanish", "CU": "Spanish",
        "EG": "Arabic", "SA": "Arabic", "IR": "Persian", "AT": "German", "NL": "Dutch", "SR": "Dutch", "JP": "Japanese", "KR": "Korean", "TH": "Thai",
        "VN": "Vietnamese", "TR": "Turkish", "GR": "Greek", "HU": "Hungarian", "PL": "Polish", "SE": "Swedish", "DK": "Danish", "IS": "Icelandic",
        "CZ": "Czech", "RO": "Romanian", "UA": "Ukrainian", "MN": "Mongolian", "ID": "Indonesian", "BD": "Bengali", "MM": "Burmese", "KH": "Khmer",
        "SN": "French", "CI": "French", "IT": "Italian"}
LANGS = sorted(set(LANG.values()) | {"English", "Hindi", "Russian", "Mandarin Chinese", "Swahili", "Malay"})
CLOSE = {"Portuguese": ["Spanish", "Italian", "French"], "Spanish": ["Portuguese", "Italian", "French"], "Dutch": ["German", "Danish", "English"],
         "German": ["Dutch", "Hungarian", "Czech"], "Arabic": ["Persian", "Turkish", "French"], "Persian": ["Arabic", "Turkish", "Hindi"]}
for code, lang in LANG.items():
    ds = CLOSE.get(lang) or pick(LANGS, 3, exclude={lang})
    add("language", "c:" + code, f"What is the main official language of {nm(code) if code in C else code}?", lang, ds)

CONT = {"EG": "Africa", "MG": "Africa", "IS": "Europe", "MX": "North America", "PA": "North America", "CU": "North America", "JM": "North America",
        "BS": "North America", "CR": "North America", "GT": "North America", "PG": "Oceania", "FJ": "Oceania", "NZ": "Oceania", "MA": "Africa",
        "MN": "Asia", "SA": "Asia", "SR": "South America", "GY": "South America", "SC": "Africa", "MU": "Africa", "CV": "Africa", "MT": "Europe",
        "LK": "Asia", "MV": "Asia", "PH": "Asia", "ET": "Africa", "UY": "South America", "VE": "South America", "BZ": "North America", "GL": "North America",
        "TN": "Africa", "NP": "Asia", "PY": "South America", "QA": "Asia", "IE": "Europe"}
CONTS = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "Antarctica"]
for code, cont in CONT.items():
    n = nm(code) if code in C else code
    q = f"Greenland is geographically part of which continent?" if code == "GL" else f"Which continent is {n} in?"
    if code == "EG":
        q = "Most of Egypt is in which continent?"
    near_ = {"Africa": ["Asia", "Europe"], "Asia": ["Africa", "Europe", "Oceania"], "Europe": ["Asia", "North America"],
             "North America": ["South America", "Europe"], "South America": ["North America", "Africa"], "Oceania": ["Asia", "South America"]}[cont]
    ds = near_[:2] + pick([c for c in CONTS if c not in near_ and c != cont and c != "Antarctica"], 1)
    add("continent", "c:" + code, q, cont, ds)

LANDLOCKED = "CH AT CZ HU LU NP BT MN KZ AF ET UG RW ZW ZM BW PY BO SK RS LA ML NE TD UZ".split()
for code in LANDLOCKED:
    x = C[code]
    coastal = [c for c in LIST if not C[c].get("landlocked") and region(c) == region(code)]
    add("landlocked", "c:" + code, "Which of these countries has no coastline?", opt(code) if code in PLAIN else C[code]["name"]["common"], [opt(c) for c in pick(coastal, 3)])

AREA = {c: C[c]["area"] for c in LIST}
seen = set()
for _ in range(2000):
    four = rng.sample(LIST, 4)
    s = sorted(four, key=lambda c: -AREA[c])
    if AREA[s[0]] >= 1.4 * AREA[s[1]] and s[0] not in seen and AREA[s[3]] > 10000:
        seen.add(s[0] + s[1])
        add("bigger", "c:" + s[0], "Which of these countries is the biggest by area?", opt(s[0]), [opt(c) for c in s[1:]])
    if len(Q["bigger"]) >= 40:
        break

FLAGS = [c for c in LIST if c not in ("VA",)] + ["SK", "RS", "LK", "IL", "ZA", "ID", "BO", "GY", "SR"]
os.makedirs(OUTFLAGS, exist_ok=True)
for code in FLAGS:
    src = os.path.join(FLAGDIR, code.lower() + ".svg")
    if not os.path.exists(src):
        continue
    shutil.copy(src, os.path.join(OUTFLAGS, code.lower() + ".svg"))
    others = [c for c in FLAGS if c != code and region(c) == region(code)]
    ds = pick(others, 2) + pick([c for c in FLAGS if c != code and region(c) != region(code)], 1)
    add("flag", "c:" + code, "Which country does this flag belong to?", opt(code), [opt(c) for c in ds], img="flags/" + code.lower() + ".svg")

# ------------------------------------------------------------------ hand-written fun facts: category|question|answer|wrong|wrong|wrong
FACTS = r"""
space|What is the largest planet in our solar system?|Jupiter|Saturn|Neptune|Earth
space|Which planet is closest to the Sun?|Mercury|Venus|Mars|Earth
space|Which planet is known as the Red Planet?|Mars|Jupiter|Venus|Mercury
space|Which is the hottest planet in our solar system?|Venus|Mercury|Mars|Jupiter
space|How many planets are in our solar system?|8|7|9|10
space|Which planet is famous for its huge, bright rings?|Saturn|Mars|Mercury|Venus
space|What is the name of the galaxy we live in?|The Milky Way|Andromeda|The Whirlpool Galaxy|The Sombrero Galaxy
space|Who was the first person to walk on the Moon?|Neil Armstrong|Buzz Aldrin|Yuri Gagarin|John Glenn
space|In which year did humans first land on the Moon?|1969|1959|1972|1965
space|Who was the first person to travel into space?|Yuri Gagarin|Neil Armstrong|Alan Shepard|John Glenn
space|Who was the first woman in space?|Valentina Tereshkova|Sally Ride|Mae Jemison|Christa McAuliffe
space|Roughly how long does sunlight take to reach Earth?|About 8 minutes|About 8 seconds|About 8 hours|About 8 days
space|According to scientific models, which planet may have diamonds raining inside it?|Neptune|Mars|Venus|Mercury
space|Which former planet was reclassified as a dwarf planet in 2006?|Pluto|Mercury|Neptune|Uranus
space|Which planet spins on its side, tilted about 98 degrees?|Uranus|Neptune|Saturn|Mars
space|What's the name of the giant volcano on Mars, the tallest known in the solar system?|Olympus Mons|Mauna Loa|Valles Marineris|Mount Sharp
space|Which planet has the Great Red Spot, a storm bigger than Earth?|Jupiter|Mars|Saturn|Neptune
space|On which planet does one spin (a day) take longer than one trip around the Sun (a year)?|Venus|Mars|Jupiter|Saturn
space|Which planet has the most known moons?|Saturn|Jupiter|Uranus|Mars
space|What is the closest star to Earth?|The Sun|Proxima Centauri|Sirius|Polaris
space|Which is the brightest star in the night sky?|Sirius|Polaris|Betelgeuse|Vega
space|The North Star is also called…|Polaris|Sirius|Vega|Rigel
space|How strong is the Moon's gravity compared with Earth's?|About one-sixth|About half|About one-tenth|About the same
space|What are Saturn's rings mostly made of?|Chunks of ice and rock|Gas|Lava|Metal
space|How long does Earth take to travel once around the Sun?|About 365 days|About 24 hours|About 30 days|About 1,000 days
space|Which planet is farthest from the Sun?|Neptune|Uranus|Saturn|Jupiter
space|What does a light-year measure?|Distance|Time|Brightness|Weight
space|What was the first artificial satellite, launched in 1957?|Sputnik 1|Explorer 1|Vostok 1|Apollo 1
space|Which space telescope, launched in 2021, studies the universe in infrared light?|James Webb Space Telescope|Hubble Space Telescope|Kepler Space Telescope|Chandra X-ray Observatory
space|What does ISS stand for?|International Space Station|Interstellar Satellite System|International Star Survey|Integrated Space Shuttle
space|Which planet has a moon called Titan, with lakes of liquid methane?|Saturn|Jupiter|Neptune|Mars
space|Which planet's moon Europa may hide an ocean under its icy crust?|Jupiter|Saturn|Mars|Neptune
space|What are shooting stars actually?|Small space rocks burning up in the air|Stars falling from the sky|Exploding planets|Satellites breaking apart
space|What causes Earth's seasons?|The tilt of Earth's axis|Earth's distance from the Sun|The Moon's phases|Sunspots
space|What is the Sun mostly made of?|Hydrogen and helium|Oxygen and nitrogen|Iron and nickel|Carbon and oxygen
space|Roughly how many Earths could fit inside the Sun?|About 1.3 million|About 1,000|About 100|About 1 billion
space|How many moons does Mars have?|2|0|1|4
space|Which two planets have no moons at all?|Mercury and Venus|Mars and Venus|Mercury and Mars|Uranus and Neptune
space|Which planet is often called Earth's twin because of its size?|Venus|Mars|Mercury|Neptune
space|Which is the smallest planet in our solar system?|Mercury|Mars|Venus|Earth
space|What do we call a huge explosion of a star at the end of its life?|A supernova|A black hole|A comet|A nebula
space|Which planet has the fastest winds in the solar system, over 2,000 km/h?|Neptune|Earth|Mars|Venus
space|Roughly how old is the universe?|About 13.8 billion years|About 4.5 billion years|About 1 million years|About 100 billion years
space|Roughly how old is Earth?|About 4.5 billion years|About 6,000 years|About 13.8 billion years|About 500 million years
space|Which space program first put people on the Moon?|Apollo|Gemini|Artemis|Vostok
space|Footprints left on the Moon could last for millions of years. Why?|There's no wind or rain to wipe them away|The Moon's dust is sticky like glue|Astronauts sealed them|They're kept under a dome
space|Astronauts can get slightly taller in space. Why?|Their spine stretches out without gravity|They eat special food|Their bones grow faster|Their suits stretch them
space|What color is the Sun really, seen from space?|White|Yellow|Orange|Red
space|Which planet is less dense than water, so it would float in a giant bathtub?|Saturn|Jupiter|Mars|Earth
space|Which constellation looks like a hunter with a belt of three stars?|Orion|Ursa Major|Cassiopeia|Scorpius
space|The Big Dipper is part of which constellation?|Ursa Major|Ursa Minor|Orion|Draco
space|What is the edge around a black hole, past which nothing can escape, called?|The event horizon|The ozone layer|The asteroid belt|The Kuiper belt
space|Between which two planets is the main asteroid belt?|Mars and Jupiter|Earth and Mars|Jupiter and Saturn|Venus and Earth
space|What gives Mars its red color?|Rusty iron in its dust|Red plants|Lava|Red clouds
space|About how long does Neptune take to go once around the Sun?|About 165 Earth years|About 12 Earth years|About 1 Earth year|About 1,000 Earth years
space|What is at the center of our solar system?|The Sun|Earth|Jupiter|A black hole
space|What is a comet's glowing tail made of?|Gas and dust|Fire|Lightning|Smoke from the Sun
space|Which dog became the first animal to orbit Earth, in 1957?|Laika|Belka|Lassie|Hachiko
space|Which country launched the first person into space?|The Soviet Union|The United States|China|France
space|Which planet is named after the Roman god of war?|Mars|Jupiter|Saturn|Mercury
animals|How many hearts does an octopus have?|3|1|2|8
animals|What is the largest animal that has ever lived?|Blue whale|African elephant|Megalodon|Brachiosaurus
animals|What is the fastest land animal?|Cheetah|Lion|Greyhound|Horse
animals|Which bird is the fastest, diving at over 300 km/h?|Peregrine falcon|Bald eagle|Ostrich|Pigeon
animals|What is the tallest animal?|Giraffe|Elephant|Ostrich|Moose
animals|What gives flamingos their pink color?|The food they eat|Sunburn|Their blood|They're born pink
animals|What is a baby kangaroo called?|A joey|A kit|A cub|A calf
animals|What do koalas mostly eat?|Eucalyptus leaves|Bamboo|Insects|Grass
animals|What is a group of crows called?|A murder|A pride|A pod|A gaggle
animals|What is a group of lions called?|A pride|A pack|A herd|A school
animals|What is a group of owls called?|A parliament|A murder|A gaggle|A pod
animals|What is a group of flamingos called?|A flamboyance|A parliament|A murder|A troop
animals|What is a group of whales or dolphins called?|A pod|A pride|A swarm|A gaggle
animals|Which mammal can truly fly, not just glide?|The bat|The flying squirrel|The sugar glider|The flying lemur
animals|Which of these mammals lays eggs?|The platypus|The kangaroo|The koala|The sloth
animals|How many legs does a spider have?|8|6|10|12
animals|How many legs does an insect have?|6|8|4|10
animals|Which animal has the largest eyes of any creature?|Colossal squid|Blue whale|Ostrich|Owl
animals|Which bird can fly backwards?|Hummingbird|Sparrow|Eagle|Pigeon
animals|What color is a polar bear's skin?|Black|White|Pink|Grey
animals|A polar bear's fur isn't really white. What is it?|See-through (transparent)|Cream|Light grey|Pale yellow
animals|Sea otters often hold hands while sleeping. Why?|So they don't drift apart|To keep warm|To scare predators|To talk to each other
animals|How do butterflies taste their food?|With their feet|With their wings|With their eyes|With their antennae only
animals|Where is a shrimp's heart?|In its head|In its tail|In its legs|It doesn't have one
animals|How do dolphins sleep?|With half their brain at a time|Upside down|On the sea floor|They never sleep
animals|How far can an owl turn its head?|About 270 degrees|About 90 degrees|About 180 degrees|A full 360 degrees
animals|What's special about each zebra's stripe pattern?|No two zebras have the same one|They change every year|They're the same in every family|They glow in the dark
animals|What is the largest bird in the world?|Ostrich|Emu|Albatross|Condor
animals|Which bird lays the biggest eggs?|Ostrich|Emu|Eagle|Swan
animals|What is the largest lizard?|Komodo dragon|Green iguana|Gila monster|Chameleon
animals|Which snake is the heaviest?|Green anaconda|King cobra|Black mamba|Boa constrictor
animals|Which snake is the longest?|Reticulated python|King cobra|Black mamba|Rattlesnake
animals|Which continent has no native ants?|Antarctica|Australia|Europe|South America
animals|Koalas can sleep for up to how many hours a day?|About 20|About 8|About 12|About 4
animals|Which animal has the strongest bite ever measured?|Saltwater crocodile|Great white shark|Lion|Grizzly bear
animals|A cow's stomach has how many compartments?|4|2|3|6
animals|What is the national animal of Scotland?|The unicorn|The lion|The stag|The golden eagle
animals|Which animal can regrow lost legs and even parts of its heart and brain?|Axolotl|Goldfish|Turtle|Hamster
animals|A starfish has no…|Brain|Arms|Mouth|Eye spots
animals|Roughly how much of a jellyfish is water?|About 95%|About 50%|About 70%|About 30%
animals|What is a baby goat called?|A kid|A lamb|A calf|A foal
animals|What is a baby swan called?|A cygnet|A duckling|A gosling|A puppy
animals|What is a male honeybee called?|A drone|A worker|A queen|A soldier
animals|Which insect makes the honey we eat?|Honeybee|Wasp|Hornet|Dragonfly
animals|How many eyes does a honeybee have?|5|2|4|8
animals|Which of these is the slowest mammal?|Three-toed sloth|Koala|Panda|Hedgehog
animals|What do giant pandas mostly eat?|Bamboo|Eucalyptus|Fish|Fruit
animals|Which animal has fingerprints so like ours they could confuse a crime scene?|Koala|Dog|Cat|Panda
animals|Penguins live almost entirely in which half of the world?|The Southern Hemisphere|The Northern Hemisphere|Both halves equally|Only along the equator
animals|What is the largest kind of fish?|Whale shark|Great white shark|Blue marlin|Giant tuna
animals|Which tiny animal has survived being exposed to outer space?|The tardigrade (water bear)|The cockroach|The ant|The goldfish
animals|What is the largest land animal?|African elephant|Hippopotamus|White rhinoceros|Giraffe
animals|Which small, furry animal is one of the elephant's closest living relatives?|The hyrax|The mouse|The rabbit|The armadillo
animals|Which gentle sea mammal is nicknamed the "sea cow"?|Manatee|Walrus|Seal|Dolphin
animals|Which is the only mammal covered in scales?|Pangolin|Hedgehog|Porcupine|Anteater
animals|Which reptile is famous for changing color?|Chameleon|Gecko|Turtle|Crocodile
animals|Which big cat can't roar, but can purr?|Cheetah|Lion|Tiger|Jaguar
animals|What do you call an animal that only eats plants?|A herbivore|A carnivore|An omnivore|An insectivore
animals|Goldfish are said to have a 3-second memory. How long can they really remember things?|Months|3 seconds|1 minute|1 hour
animals|What is a female deer called?|A doe|A mare|A ewe|A sow
animals|What is a baby frog called?|A tadpole|A cub|A kit|A calf
animals|What do camels store in their humps?|Fat|Water|Air|Milk
animals|Which is the largest kind of penguin?|Emperor penguin|King penguin|Adélie penguin|Little penguin
animals|Some giant tortoises can live for how long?|Over 150 years|About 20 years|About 50 years|About 10 years
animals|Which animals are humans' closest living relatives?|Chimpanzees and bonobos|Gorillas|Orangutans|Gibbons
animals|Which animal has the longest pregnancy, about 22 months?|African elephant|Blue whale|Giraffe|Rhinoceros
animals|A hummingbird's heart can beat about how many times a minute?|Over 1,000|About 60|About 200|About 10
animals|What is a group of wolves called?|A pack|A pride|A herd|A colony
animals|Which animal is called the "king of the jungle", even though it lives on grasslands?|Lion|Tiger|Gorilla|Leopard
animals|What do bees collect from flowers to make honey?|Nectar|Leaves|Water|Tree sap
animals|Which animal is on the WWF logo?|Giant panda|Tiger|Elephant|Polar bear
animals|How many arms does a starfish usually have?|5|4|6|8
animals|Which dog breed is the smallest?|Chihuahua|Pomeranian|Pug|Beagle
animals|What is the heaviest invertebrate (animal without a backbone)?|Colossal squid|Giant Pacific octopus|Japanese spider crab|American lobster
animals|An ostrich's eye is bigger than its…|Brain|Heart|Stomach|Beak
animals|Which of these animals can sleep standing up?|Horse|Dog|Cat|Rabbit
animals|What is a baby owl called?|An owlet|A cub|A kit|A cygnet
animals|Which animal is famous for building dams in rivers?|Beaver|Otter|Muskrat|Badger
animals|What is the largest rodent in the world?|Capybara|Beaver|Porcupine|Rat
animals|Which bird can't fly but is the fastest runner?|Ostrich|Emu|Penguin|Kiwi
animals|The kiwi bird is a symbol of which country?|New Zealand|Australia|South Africa|Chile
animals|Which sea creature has blue blood and eight arms?|Octopus|Shark|Starfish|Dolphin
animals|How many teeth does a typical great white shark lose and replace over its life?|Thousands|About 10|About 50|None, they keep the same teeth
animals|Which animal can go weeks without water by getting moisture from its food?|Camel|Hippo|Elephant|Polar bear
animals|What is the main job of a worker bee?|Collecting food and caring for the hive|Laying eggs|Ruling the hive|Fighting other hives only
animals|Which big cat has spots called rosettes and loves climbing trees?|Leopard|Cheetah|Lion|Tiger
animals|Which mammal has the thickest fur?|Sea otter|Polar bear|Arctic fox|Yak
animals|What is a group of fish swimming together called?|A school|A herd|A pack|A colony
animals|Which bird is known for its colorful tail feathers that it fans out?|Peacock|Parrot|Flamingo|Toucan
animals|What is special about a chameleon's eyes?|They can move separately|They glow at night|They have no eyelids|They see only black and white
animals|Which big animal secretes a reddish oily fluid that helps protect its skin from the sun?|Hippopotamus|Elephant|Rhinoceros|Walrus
body|How many bones are in the adult human body?|206|186|256|306
body|What is the largest organ of the human body?|Skin|Liver|Brain|Lungs
body|What is the largest organ inside the human body?|Liver|Heart|Brain|Stomach
body|Where is the smallest bone in the human body?|In the ear|In the little toe|In the nose|In the little finger
body|What is the longest bone in the human body?|Femur (thigh bone)|Tibia (shin bone)|Humerus (upper arm)|Spine
body|How many chambers does the human heart have?|4|2|3|6
body|How many teeth does an adult usually have, counting wisdom teeth?|32|28|24|36
body|How many baby teeth do children usually have?|20|24|16|32
body|Babies are born with about how many bones?|About 300|About 206|About 150|About 500
body|What carries oxygen around your body?|Red blood cells|White blood cells|Platelets|Plasma
body|What do white blood cells do?|Fight germs and infections|Carry oxygen|Help blood clot|Digest food
body|Which gas do we breathe out?|Carbon dioxide|Helium|Neon|Hydrogen
body|About how many times does a human heart beat in a day?|About 100,000|About 10,000|About 1 million|About 1,000
body|Which organ uses about 20% of your body's energy?|Brain|Heart|Liver|Stomach
body|Which grow faster, fingernails or toenails?|Fingernails|Toenails|They grow at the same speed|Neither grows after childhood
body|What is the hardest substance in the human body?|Tooth enamel|Bone|Fingernail|Cartilage
body|Which clear part at the front of the eye has no blood vessels?|The cornea|The retina|The iris|The eyelid
body|What color is the blood in your veins?|Red|Blue|Purple|Green
body|What kind of acid is in your stomach?|Hydrochloric acid|Citric acid|Sulfuric acid|Lactic acid
body|Roughly how much of an adult's body is water?|About 60%|About 30%|About 90%|About 10%
body|Which muscle under your lungs helps you breathe?|Diaphragm|Pectoral|Trapezius|Quadriceps
body|Your left lung is a little smaller than your right one. Why?|To make room for your heart|Because you're right-handed|It shrinks as you grow|To fit your stomach
body|Which sense is most closely linked to memory?|Smell|Sight|Hearing|Touch
body|Can every part of your tongue taste all the basic tastes?|Yes, every part can|No, sweet is only at the tip|No, bitter is only at the back|No, only the middle can taste
body|Which of these is one of the five basic tastes?|Umami|Spicy|Cold|Crunchy
body|What is the colored part of your eye called?|Iris|Pupil|Retina|Cornea
body|The kneecap is also called the…|Patella|Tibia|Femur|Clavicle
body|The collarbone is also called the…|Clavicle|Scapula|Sternum|Patella
body|About how long is an adult's small intestine?|About 6 metres|About 1 metre|About 20 metres|About 50 centimetres
body|Which organs filter your blood to make urine?|Kidneys|Liver|Lungs|Pancreas
body|Which organ makes insulin?|Pancreas|Liver|Kidneys|Stomach
body|Your body makes vitamin D when your skin gets…|Sunlight|Water|Fresh air|Exercise
body|Humans share about how much of their DNA with chimpanzees?|About 98%|About 50%|About 75%|About 25%
body|Which blood type can be given to almost anyone in an emergency?|O negative|AB positive|A positive|B negative
body|Which blood type can receive red blood cells from any type?|AB positive|O negative|A negative|B positive
body|The "funny bone" isn't a bone. What is it really?|A nerve|A muscle|A tendon|A vein
body|What causes goosebumps?|Tiny muscles pulling your hairs upright|Your blood getting cold|Your skin shrinking|Sweat glands closing
body|What is the medical name for the voice box?|Larynx|Pharynx|Trachea|Esophagus
body|Humans and giraffes have the same number of neck bones. How many?|7|5|12|24
body|Which vitamin do carrots help you get, which is good for your eyes?|Vitamin A|Vitamin C|Vitamin D|Vitamin K
body|Oranges and lemons are famous for which vitamin?|Vitamin C|Vitamin D|Vitamin B12|Vitamin K
body|Which protein in red blood cells carries oxygen?|Hemoglobin|Insulin|Keratin|Collagen
body|What are your hair and nails made of?|Keratin|Collagen|Calcium|Cellulose
body|Where is the thinnest skin on your body?|Eyelids|Lips|Ears|Palms
body|How many hours of sleep do most adults need each night?|7 to 9|4 to 5|10 to 12|5 to 6
body|What is one main job of your eyebrows?|Keeping sweat and rain out of your eyes|Keeping your head warm|Helping you hear|Helping you smell
body|Where in your body is the smallest muscle?|In the ear|In the eyelid|In the little finger|In the nose
body|What are the tiny air sacs in your lungs called?|Alveoli|Villi|Neurons|Capillaries
body|Which part of the brain helps you keep your balance?|Cerebellum|Frontal lobe|Brain stem|Hippocampus
body|What is the name of the tube that carries food from your mouth to your stomach?|Esophagus|Trachea|Intestine|Artery
body|Which blood vessels carry blood away from the heart?|Arteries|Veins|Capillaries|Nerves
body|About how many taste buds does a person have?|About 10,000|About 100|About 1 million|About 500
body|Which part of the eye controls how much light gets in?|The pupil and iris|The retina|The cornea|The optic nerve
body|What do we call the bones of your spine?|Vertebrae|Ribs|Phalanges|Carpals
geo|Where is Mount Everest?|On the border of Nepal and China|In India|In Switzerland|In Pakistan
geo|What is the largest desert on Earth?|The Antarctic Desert|The Sahara|The Gobi|The Arabian Desert
geo|What is the largest hot desert on Earth?|The Sahara|The Arabian Desert|The Gobi|The Kalahari
geo|What is the largest ocean?|Pacific Ocean|Atlantic Ocean|Indian Ocean|Arctic Ocean
geo|What is the smallest ocean?|Arctic Ocean|Indian Ocean|Southern Ocean|Atlantic Ocean
geo|Which river is usually listed as the longest in the world?|The Nile|The Mississippi|The Yangtze|The Danube
geo|Which river carries more water than any other?|The Amazon|The Nile|The Mississippi|The Thames
geo|What is the largest country by area?|Russia|Canada|China|United States
geo|What is the smallest country in the world?|Vatican City|Monaco|San Marino|Liechtenstein
geo|Which country has the most people?|India|China|United States|Indonesia
geo|What is the deepest point in the ocean?|The Mariana Trench|The Puerto Rico Trench|The Java Trench|The Bermuda Triangle
geo|What is the tallest waterfall in the world?|Angel Falls|Niagara Falls|Victoria Falls|Iguazu Falls
geo|Angel Falls, the world's tallest waterfall, is in which country?|Venezuela|Brazil|Colombia|Peru
geo|What is the largest lake in the world by area?|The Caspian Sea|Lake Superior|Lake Victoria|Lake Baikal
geo|What is the deepest lake in the world?|Lake Baikal|Lake Superior|Lake Victoria|Loch Ness
geo|Which country has the most islands?|Sweden|Japan|Philippines|Greece
geo|Counting its overseas territories, which country has the most time zones?|France|Russia|United States|China
geo|Australia is wider (east to west) than which of these?|The Moon|Africa|Russia|Canada
geo|Which country has the longest coastline?|Canada|Australia|Brazil|Norway
geo|Which country has the most lakes?|Canada|Brazil|Australia|Egypt
geo|Where is the lowest point on land?|The shore of the Dead Sea|Death Valley|The Grand Canyon|The Netherlands
geo|Mount Kilimanjaro is in which country?|Tanzania|Kenya|Uganda|Ethiopia
geo|How many countries are in Africa?|54|44|64|34
geo|Which is the largest continent?|Asia|Africa|North America|Europe
geo|Which continent has no countries?|Antarctica|Australia|Europe|South America
geo|Which imaginary line divides Earth into Northern and Southern Hemispheres?|The Equator|The Prime Meridian|The Tropic of Cancer|The International Date Line
geo|The Prime Meridian (0° longitude) runs through which city?|London (Greenwich)|Paris|New York|Lisbon
geo|Which river flows through Egypt?|The Nile|The Tigris|The Danube|The Niger
geo|Which river runs through Paris?|The Seine|The Thames|The Rhine|The Loire
geo|Which river runs through London?|The Thames|The Seine|The Danube|The Severn
geo|Which river carved the Grand Canyon?|The Colorado River|The Mississippi|The Rio Grande|The Missouri
geo|The Great Barrier Reef is off the coast of which country?|Australia|Indonesia|Philippines|New Zealand
geo|Which is the longest mountain range on land?|The Andes|The Himalayas|The Rockies|The Alps
geo|Which mountain range has the world's highest peaks?|The Himalayas|The Andes|The Alps|The Rockies
geo|Which country is shaped like a boot?|Italy|Greece|Portugal|Chile
geo|Which long, thin country runs down most of South America's west coast?|Chile|Peru|Argentina|Ecuador
geo|Which city is built on more than 100 small islands linked by bridges?|Venice|Paris|Prague|Vienna
geo|Which country has more ancient pyramids than Egypt?|Sudan|Mexico|Peru|Greece
geo|Machu Picchu is in which country?|Peru|Bolivia|Mexico|Chile
geo|In which country is the Taj Mahal?|India|Pakistan|Iran|Bangladesh
geo|Petra, a city carved into pink rock, is in which country?|Jordan|Egypt|Turkey|Morocco
geo|Angkor Wat, the world's largest religious monument, is in which country?|Cambodia|Thailand|Vietnam|Laos
geo|The Colosseum is in which city?|Rome|Athens|Istanbul|Naples
geo|The Christ the Redeemer statue overlooks which city?|Rio de Janeiro|São Paulo|Buenos Aires|Lisbon
geo|Which city sits on two continents, Europe and Asia?|Istanbul|Cairo|Moscow|Athens
geo|The ancient trading city of Timbuktu is in which country?|Mali|Chad|Kenya|Morocco
geo|In which sea is the water so salty you float easily?|The Dead Sea|The Red Sea|The Black Sea|The North Sea
geo|What is the largest island in the world (not counting Australia)?|Greenland|New Guinea|Borneo|Madagascar
geo|Greenland belongs to which country?|Denmark|Canada|Norway|Iceland
geo|What is the highest mountain in North America?|Denali|Mount Whitney|Mount Rainier|Pikes Peak
geo|What is the largest rainforest in the world?|The Amazon|The Congo Basin|The Daintree|The Black Forest
geo|Which desert is the driest non-polar place on Earth?|The Atacama Desert|The Sahara|Death Valley|The Gobi
geo|Mount Fuji is in which country?|Japan|China|South Korea|Indonesia
geo|Which two countries share the longest border in the world?|Canada and the United States|Russia and China|Argentina and Chile|India and China
geo|Which ocean lies between Africa and Australia?|The Indian Ocean|The Atlantic Ocean|The Pacific Ocean|The Arctic Ocean
geo|What's the name of the narrow sea passage between Spain and Morocco?|The Strait of Gibraltar|The Bosporus|The English Channel|The Panama Canal
geo|Which canal lets ships cross Central America between the Atlantic and Pacific?|The Panama Canal|The Suez Canal|The Kiel Canal|The Grand Canal
geo|The Suez Canal is in which country?|Egypt|Saudi Arabia|Turkey|Greece
geo|Which country is called the Land of the Rising Sun?|Japan|China|South Korea|Thailand
geo|Which country is nicknamed the Land of a Thousand Lakes?|Finland|Canada|Sweden|Switzerland
geo|Which city is nicknamed the Big Apple?|New York City|Chicago|Los Angeles|Boston
geo|Which city is nicknamed the City of Light?|Paris|Rome|Vienna|London
geo|Iceland is known as the land of…|Fire and ice|Sun and sand|Rain and wind|Snow and forests
geo|Which tiny country is completely surrounded by Italy, along with Vatican City?|San Marino|Monaco|Andorra|Malta
geo|Which country is completely surrounded by South Africa?|Lesotho|Botswana|Namibia|Zimbabwe
geo|How many states are in the United States?|50|48|52|51
geo|Which US state is made up entirely of islands?|Hawaii|Alaska|Florida|Rhode Island
geo|What is the coldest continent?|Antarctica|Asia|Europe|North America
geo|Which desert covers much of Mongolia and northern China?|The Gobi|The Sahara|The Kalahari|The Atacama
geo|Victoria Falls lies on the border of which two countries?|Zambia and Zimbabwe|Kenya and Tanzania|Brazil and Argentina|Egypt and Sudan
geo|Niagara Falls is on the border between which two countries?|Canada and the United States|Brazil and Argentina|Zambia and Zimbabwe|Mexico and the United States
geo|The Amazon River flows mostly through which country?|Brazil|Peru|Colombia|Argentina
geo|Which is the largest country in South America?|Brazil|Argentina|Peru|Colombia
geo|Which is the largest country in Africa by area?|Algeria|Nigeria|Egypt|South Africa
geo|Which is the biggest country with no coastline?|Kazakhstan|Mongolia|Switzerland|Bolivia
geo|Which country has the most volcanoes that have erupted in recorded history?|Indonesia|Italy|Iceland|Mexico
geo|Stonehenge is in which country?|England|Ireland|France|Scotland
geo|Which sea lies between Europe and Africa?|The Mediterranean Sea|The Caribbean Sea|The Baltic Sea|The Arabian Sea
geo|The Statue of Liberty stands in which city?|New York City|Washington, D.C.|Boston|Philadelphia
geo|What is the capital of the U.S. state of Hawaii?|Honolulu|Hilo|Maui|Waikiki
history|Which country invented paper?|China|Egypt|Greece|India
history|Who built the first printing press with movable metal type in Europe, around 1440?|Johannes Gutenberg|Leonardo da Vinci|Isaac Newton|Galileo Galilei
history|Who is usually credited with inventing the telephone?|Alexander Graham Bell|Thomas Edison|Nikola Tesla|Guglielmo Marconi
history|Which brothers made the first powered airplane flight in 1903?|The Wright brothers|The Grimm brothers|The Lumière brothers|The Marx brothers
history|In which country are the Great Pyramids of Giza?|Egypt|Mexico|Sudan|Peru
history|In which year did the Titanic sink?|1912|1905|1920|1898
history|In which year did World War II end?|1945|1939|1950|1918
history|In which year did the Berlin Wall fall?|1989|1961|1991|1975
history|Which of the Seven Wonders of the Ancient World is still standing?|The Great Pyramid of Giza|The Colossus of Rhodes|The Hanging Gardens of Babylon|The Lighthouse of Alexandria
history|True or false: Cleopatra lived closer in time to the Moon landing than to the building of the Great Pyramid.|True|False
history|True or false: Oxford University is older than the Aztec Empire.|True|False
history|Who painted the Mona Lisa?|Leonardo da Vinci|Michelangelo|Raphael|Vincent van Gogh
history|Who painted The Starry Night?|Vincent van Gogh|Claude Monet|Pablo Picasso|Salvador Dalí
history|Who painted the ceiling of the Sistine Chapel?|Michelangelo|Leonardo da Vinci|Raphael|Donatello
history|Which country gave the Statue of Liberty to the United States?|France|United Kingdom|Spain|Italy
history|In which year did Christopher Columbus first reach the Americas?|1492|1607|1776|1066
history|Which empire built Machu Picchu?|The Inca|The Aztecs|The Maya|The Romans
history|Which ancient civilization built Chichén Itzá in Mexico?|The Maya|The Inca|The Egyptians|The Romans
history|Who was the first emperor of Rome?|Augustus|Julius Caesar|Nero|Caligula
history|The ancient Olympic Games began in which country?|Greece|Italy|Egypt|Turkey
history|Chess is believed to have started in which country?|India|China|Egypt|Greece
history|Pizza Margherita was created in which country?|Italy|Greece|France|United States
history|Fortune cookies, common in Chinese restaurants, were most likely invented in which country?|The United States|China|Korea|Vietnam
history|In the 1830s, which sauce was sold as a medicine?|Ketchup|Mustard|Mayonnaise|Soy sauce
history|Who discovered penicillin in 1928?|Alexander Fleming|Louis Pasteur|Marie Curie|Edward Jenner
history|Who was the first person to win two Nobel Prizes?|Marie Curie|Albert Einstein|Niels Bohr|Alfred Nobel
history|Who came up with the theory of relativity?|Albert Einstein|Isaac Newton|Stephen Hawking|Galileo Galilei
history|Who wrote Romeo and Juliet?|William Shakespeare|Charles Dickens|Jane Austen|Homer
history|Which ship carried the Pilgrims to America in 1620?|The Mayflower|The Santa María|The Endeavour|The Beagle
history|Who was the first President of the United States?|George Washington|Abraham Lincoln|Thomas Jefferson|John Adams
history|Who was the British Prime Minister for most of World War II?|Winston Churchill|Neville Chamberlain|Clement Attlee|Margaret Thatcher
history|Nelson Mandela became president of which country?|South Africa|Kenya|Nigeria|Zimbabwe
history|Which people invented one of the earliest writing systems, cuneiform?|The Sumerians|The Vikings|The Greeks|The Aztecs
history|What did ancient Egyptians write on, made from a river plant?|Papyrus|Parchment|Bamboo|Silk
history|Whose expedition was the first to sail all the way around the world?|Ferdinand Magellan's|Christopher Columbus's|Vasco da Gama's|James Cook's
history|Who is said to have started thinking about gravity after seeing an apple fall?|Isaac Newton|Albert Einstein|Galileo Galilei|Charles Darwin
history|Who proposed the theory of evolution by natural selection?|Charles Darwin|Gregor Mendel|Louis Pasteur|Isaac Newton
history|In which city was the Titanic built?|Belfast|Liverpool|Southampton|New York
history|In which year did the first iPhone come out?|2007|2004|2010|2001
history|Who invented the World Wide Web?|Tim Berners-Lee|Bill Gates|Steve Jobs|Mark Zuckerberg
history|Which inventor is most often credited with the light bulb?|Thomas Edison|Nikola Tesla|Alexander Graham Bell|Benjamin Franklin
history|Who famously flew a kite in a storm to study electricity?|Benjamin Franklin|Thomas Edison|Nikola Tesla|Isaac Newton
history|Where did the Vikings mainly come from?|Scandinavia|Spain|Greece|Egypt
history|Which Viking explorer reached North America about 500 years before Columbus?|Leif Erikson|Erik the Red|Ragnar Lothbrok|Harald Hardrada
history|Which Roman city was buried by the eruption of Mount Vesuvius in 79 AD?|Pompeii|Athens|Carthage|Troy
history|Who was the last active pharaoh of ancient Egypt?|Cleopatra|Nefertiti|Hatshepsut|Tutankhamun
history|Whose tomb did Howard Carter find almost untouched in 1922?|Tutankhamun's|Ramses II's|Cleopatra's|Julius Caesar's
history|The Eiffel Tower was built for which event in 1889?|A World's Fair|The Olympics|A royal wedding|The end of a war
history|The Eiffel Tower was first meant to stand for how long?|20 years|100 years|5 years|Forever
history|Which war was fought between the Northern and Southern states of the USA?|The American Civil War|The Revolutionary War|World War I|The Cold War
history|What do we call the rebirth of art and learning in Europe from the 1300s to the 1600s?|The Renaissance|The Enlightenment|The Middle Ages|The Industrial Revolution
history|Which revolution began in Britain in the 1700s with steam engines and factories?|The Industrial Revolution|The French Revolution|The Russian Revolution|The American Revolution
history|In which year did the French Revolution begin?|1789|1776|1815|1848
history|Which country was ruled by emperors called tsars?|Russia|China|Japan|Spain
history|What did the general Hannibal famously take across the Alps?|Elephants|Camels|Bears|Lions
history|Who was the first person to reach the South Pole?|Roald Amundsen|Robert Falcon Scott|Ernest Shackleton|Christopher Columbus
history|Who were the first climbers confirmed to reach the top of Mount Everest, in 1953?|Edmund Hillary and Tenzing Norgay|George Mallory and Andrew Irvine|Neil Armstrong and Buzz Aldrin|Roald Amundsen and Robert Scott
history|Which sport was invented in 1891 by a teacher using peach baskets?|Basketball|Volleyball|Netball|Baseball
history|What language did the ancient Romans speak?|Latin|Greek|Italian|French
history|Whose diary, written while hiding in Amsterdam during World War II, became world famous?|Anne Frank|Marie Curie|Helen Keller|Florence Nightingale
history|Which nurse became famous as "the Lady with the Lamp"?|Florence Nightingale|Clara Barton|Edith Cavell|Anne Frank
history|Which ancient wonder was a giant bronze statue near a Greek harbor?|The Colossus of Rhodes|The Great Pyramid|The Hanging Gardens|The Statue of Zeus
history|China's first emperor was buried with an army of life-size soldiers made of…|Clay (terracotta)|Gold|Wood|Ice
history|Which country gave Washington, D.C. its famous cherry trees in 1912?|Japan|China|South Korea|France
history|How long did the Hundred Years' War actually last?|116 years|100 years|90 years|50 years
history|Which city hosted the first modern Olympic Games in 1896?|Athens|Paris|London|Rome
history|What did Karl Benz build in 1885–86?|The first practical petrol-powered car|The first bicycle|The first airplane|The first radio
history|Which company did Steve Jobs co-found?|Apple|Microsoft|Google|Amazon
history|What did Galileo improve and turn towards the sky in 1609?|The telescope|The microscope|The compass|The clock
history|Which ancient people treated cats as sacred animals?|The ancient Egyptians|The ancient Greeks|The Romans|The Vikings
history|Which empire was ruled from Constantinople for about a thousand years?|The Byzantine Empire|The Persian Empire|The Mongol Empire|The Inca Empire
history|Who founded the Mongol Empire?|Genghis Khan|Kublai Khan|Attila the Hun|Julius Caesar
history|What was the largest empire of connected land in history?|The Mongol Empire|The Roman Empire|The British Empire|The Persian Empire
history|Which toy was the first ever advertised on TV?|Mr. Potato Head|Barbie|LEGO|Slinky
history|Which ancient city was the site of the legendary wooden horse?|Troy|Rome|Sparta|Carthage
history|Which ship made Charles Darwin's famous voyage?|HMS Beagle|The Mayflower|The Titanic|The Santa María
history|What were the Wright brothers' jobs before they built airplanes?|They ran a bicycle shop|They were farmers|They were pilots in the army|They were sailors
history|Which famous queen ruled the United Kingdom for over 70 years?|Elizabeth II|Victoria|Elizabeth I|Mary I
history|Which famous scientist developed the polio vaccine in the 1950s?|Jonas Salk|Louis Pasteur|Edward Jenner|Alexander Fleming
history|What were the first animals humans domesticated?|Dogs|Cats|Horses|Cows
science|At what temperature does water boil at sea level?|100°C|90°C|120°C|80°C
science|At what temperature does water freeze?|0°C|-10°C|4°C|32°C
science|What is the chemical symbol for gold?|Au|Ag|Go|Gd
science|What is the chemical symbol for silver?|Ag|Si|Au|Sv
science|What is the chemical symbol for iron?|Fe|Ir|In|I
science|What is the chemical symbol for sodium?|Na|So|Sd|S
science|What is the chemical formula for water?|H₂O|CO₂|O₂|H₂O₂
science|Which gas makes up most of the air we breathe?|Nitrogen|Oxygen|Carbon dioxide|Hydrogen
science|What is the hardest natural substance?|Diamond|Gold|Iron|Quartz
science|Diamonds are made of which element?|Carbon|Silicon|Iron|Oxygen
science|Through which of these does sound travel fastest?|Steel|Air|Water|Empty space
science|Can sound travel through space?|No, space is almost empty|Yes, but very slowly|Yes, faster than on Earth|Only near stars
science|Which of these is the hottest?|A bolt of lightning|The surface of the Sun|Lava|A campfire
science|Which of these fruits is technically a berry?|Banana|Strawberry|Raspberry|Cherry
science|Scientifically speaking, a tomato is a…|Fruit|Vegetable|Nut|Grain
science|What force keeps us on the ground?|Gravity|Magnetism|Friction|Wind
science|Absolute zero, the coldest possible temperature, is about…|-273°C|-100°C|0°C|-1,000°C
science|What is the center of an atom called?|The nucleus|The electron|The orbit|The shell
science|Which tiny particle has a negative charge?|Electron|Proton|Neutron|Photon
science|What do plants take from the air to make their food?|Carbon dioxide|Oxygen|Nitrogen|Helium
science|What is the process plants use to make food from sunlight?|Photosynthesis|Respiration|Digestion|Evaporation
science|Which gas do plants give off?|Oxygen|Carbon dioxide|Helium|Methane
science|What is the most common element in the universe?|Hydrogen|Oxygen|Carbon|Iron
science|Which metal is liquid at room temperature?|Mercury|Lead|Aluminium|Tin
science|At what temperature does water boil in Fahrenheit?|212°F|100°F|180°F|32°F
science|What does DNA stand for?|Deoxyribonucleic acid|Dinitrogen acid|Dual nucleic atom|Digital nucleus array
science|What shape is DNA?|A double helix|A pyramid|A cube|A star
science|How many colors are in a rainbow, traditionally?|7|5|6|8
science|What color do you get by mixing blue and yellow paint?|Green|Purple|Orange|Brown
science|What are the three primary colors of light?|Red, green and blue|Red, yellow and blue|Cyan, magenta and yellow|Red, white and blue
science|What kind of energy does a moving object have?|Kinetic energy|Potential energy|Nuclear energy|Chemical energy
science|Who came up with the famous equation E = mc²?|Albert Einstein|Isaac Newton|Marie Curie|Nikola Tesla
science|Light from the Moon takes about how long to reach Earth?|About 1.3 seconds|About 8 minutes|About 1 hour|About 1 day
science|Roughly how fast does light travel?|About 300,000 km per second|About 300 km per second|About 3,000 km per hour|About 300 km per hour
science|Hot air rises because it is…|Less dense than cold air|Heavier than cold air|Magnetic|Wetter
science|What do fish use to breathe underwater?|Gills|Lungs|Fins|Scales
science|What is the study of weather called?|Meteorology|Astronomy|Seismology|Zoology
science|What is the study of plants called?|Botany|Zoology|Geology|Astronomy
science|Which scale measures the strength of earthquakes?|The Richter scale|The Beaufort scale|The Kelvin scale|The pH scale
science|Which scale measures wind speed?|The Beaufort scale|The Richter scale|The Mohs scale|The pH scale
science|Which scale ranks how hard minerals are?|The Mohs scale|The Beaufort scale|The Richter scale|The Kelvin scale
science|What is the pH of pure water?|7|0|14|10
science|Lemon juice is…|Acidic|Alkaline|Neutral|Salty
science|Which gas makes party balloons float?|Helium|Oxygen|Carbon dioxide|Nitrogen
science|Which gas high in the atmosphere protects us from the Sun's UV rays?|Ozone|Helium|Neon|Hydrogen
science|How long can sealed honey last?|Practically forever|About 1 month|About 1 year|About 10 years
science|Which metal is the best conductor of electricity?|Silver|Copper|Gold|Aluminium
science|Water expands when it freezes. That's why ice…|Floats on water|Sinks in water|Melts faster|Feels sticky
science|What are the three everyday states of matter?|Solid, liquid and gas|Hot, warm and cold|Big, medium and small|Ice, steam and fire
science|What is the tallest kind of tree?|Coast redwood|Baobab|Oak|Palm
science|What do you call animals that are active at night?|Nocturnal|Diurnal|Migratory|Hibernating
science|Which part of a plant soaks up water from the soil?|The roots|The leaves|The flowers|The petals
science|How many sides does a hexagon have?|6|5|7|8
science|What is the only even prime number?|2|0|4|6
science|How many degrees are in a right angle?|90|180|45|360
science|What is the value of pi to two decimal places?|3.14|3.41|3.12|3.16
science|Rust forms when iron reacts with…|Oxygen and water|Salt only|Sunlight|Sand
science|Which of these is a renewable energy source?|Solar power|Coal|Oil|Natural gas
science|What is the name of the force that slows things down when they rub together?|Friction|Gravity|Magnetism|Inertia
science|Who is known for the three laws of motion?|Isaac Newton|Albert Einstein|Galileo Galilei|Nikola Tesla
science|What does a magnet attract?|Iron|Wood|Plastic|Glass
science|Which instrument is used to look at very tiny things?|Microscope|Telescope|Periscope|Stethoscope
science|What is the boiling point of water on top of Mount Everest compared with sea level?|Lower|Higher|The same|It never boils there
science|Which planet is the only one known to have life?|Earth|Mars|Venus|Jupiter
science|What is the smallest unit of life?|The cell|The atom|The organ|The molecule
science|What do caterpillars turn into?|Butterflies or moths|Beetles|Dragonflies|Bees
science|How many hours are in a week?|168|144|120|186
science|Which shape has three sides?|Triangle|Square|Pentagon|Circle
science|What is 15% of 200?|30|15|20|45
science|How many minutes are in a day?|1,440|1,200|960|3,600
science|Which way do most hurricanes spin in the Northern Hemisphere?|Counterclockwise|Clockwise|They don't spin|It changes every year
culture|Which country is sushi from?|Japan|China|Korea|Thailand
culture|Paella comes from which country?|Spain|Italy|Portugal|Mexico
culture|Kimchi is a traditional food from which country?|Korea|Japan|China|Vietnam
culture|Which country produces the most coffee?|Brazil|Colombia|Ethiopia|Italy
culture|Which country produces most of the world's maple syrup?|Canada|United States|Norway|Sweden
culture|Chocolate is made from the beans of which plant?|Cacao|Coffee|Vanilla|Carob
culture|Guacamole is made mainly from which fruit?|Avocado|Lime|Tomato|Mango
culture|Which country is most famous for tacos?|Mexico|Spain|Brazil|Argentina
culture|Which country produces the most tea?|China|India|Sri Lanka|United Kingdom
culture|What is the most popular sport in the world?|Football (soccer)|Basketball|Cricket|Tennis
culture|How many rings are on the Olympic flag?|5|4|6|7
culture|How many players does a football (soccer) team have on the pitch?|11|10|9|12
culture|How many players does a basketball team have on the court?|5|6|7|4
culture|In which sport do players hit a shuttlecock?|Badminton|Tennis|Squash|Table tennis
culture|Which country invented the game of cricket?|England|India|Australia|South Africa
culture|How long is a marathon?|About 42 km (26.2 miles)|About 21 km|About 50 km|About 10 km
culture|Which sport is played at Wimbledon?|Tennis|Golf|Cricket|Rugby
culture|What is a perfect score in ten-pin bowling?|300|200|250|100
culture|How many squares are on a chessboard?|64|81|100|49
culture|Which chess piece can only move diagonally?|Bishop|Rook|Knight|King
culture|How many cards are in a standard deck, without jokers?|52|54|48|50
culture|Which country did the Rubik's Cube come from?|Hungary|Japan|Germany|United States
culture|LEGO comes from which country?|Denmark|Sweden|Germany|Netherlands
culture|IKEA was founded in which country?|Sweden|Denmark|Norway|Finland
culture|Nintendo is a company from which country?|Japan|South Korea|China|United States
culture|Samsung is a company from which country?|South Korea|Japan|China|Taiwan
culture|The name LEGO comes from Danish words meaning…|Play well|Build big|Little bricks|Let's go
culture|Which language has the most native speakers?|Mandarin Chinese|English|Spanish|Hindi
culture|Which language has the most speakers overall, including people who learned it?|English|Mandarin Chinese|Spanish|French
culture|How many letters are in the English alphabet?|26|24|28|25
culture|Who wrote the Harry Potter books?|J.K. Rowling|Roald Dahl|J.R.R. Tolkien|C.S. Lewis
culture|Who wrote The Lord of the Rings?|J.R.R. Tolkien|C.S. Lewis|J.K. Rowling|George R.R. Martin
culture|Which composer kept writing music after he went deaf?|Ludwig van Beethoven|Wolfgang Amadeus Mozart|Johann Sebastian Bach|Frédéric Chopin
culture|How many keys does a standard piano have?|88|76|100|64
culture|How many strings does a standard guitar have?|6|4|5|8
culture|Which instrument usually has 47 strings?|Concert harp|Violin|Cello|Guitar
culture|Which band was nicknamed the Fab Four?|The Beatles|The Rolling Stones|Queen|ABBA
culture|Which country is the band ABBA from?|Sweden|Norway|Denmark|Netherlands
culture|Who is known as the King of Pop?|Michael Jackson|Elvis Presley|Prince|Freddie Mercury
culture|At the Spanish festival La Tomatina, what do people throw at each other?|Tomatoes|Oranges|Water balloons|Flour
culture|Día de los Muertos (Day of the Dead) is celebrated mainly in which country?|Mexico|Spain|Brazil|Peru
culture|What is the traditional color of a bride's dress in China?|Red|White|Black|Green
culture|In Japan, what is considered rude to do with chopsticks?|Stand them upright in a bowl of rice|Hold them near the top|Use them for noodles|Rest them on a holder
culture|How many sides does a stop sign have?|8|6|5|10
culture|What does "www" stand for in web addresses?|World Wide Web|World Web Wide|Wide World Web|Web World Wide
culture|Which is the best-selling video game of all time?|Minecraft|Grand Theft Auto V|Pac-Man|Wii Sports
culture|What is the name of Nintendo's famous plumber?|Mario|Luigi|Link|Sonic
culture|Which company created Sonic the Hedgehog?|Sega|Nintendo|Sony|Atari
culture|Which spice is the most expensive by weight?|Saffron|Vanilla|Cinnamon|Black pepper
culture|Which nut is used to make marzipan?|Almond|Peanut|Cashew|Walnut
culture|What is tofu made from?|Soybeans|Rice|Wheat|Chickpeas
culture|Hummus is mainly made from…|Chickpeas|Lentils|Peas|Rice
culture|Which smelly fruit is called the "king of fruits" in Southeast Asia?|Durian|Jackfruit|Mango|Pineapple
culture|After water, what is the most popular drink in the world?|Tea|Coffee|Milk|Orange juice
culture|Popcorn is made from which grain?|Corn (maize)|Rice|Wheat|Barley
culture|The hamburger is named after which city?|Hamburg|Hamilton|Hampton|Amsterdam
culture|Gouda cheese comes from which country?|The Netherlands|France|Switzerland|Italy
culture|Which festival of lights is celebrated by Hindus, Sikhs and Jains?|Diwali|Holi|Eid|Christmas
culture|Which festival is famous for throwing colored powder?|Holi|Diwali|Carnival|Songkran
culture|Songkran, the water-splashing New Year festival, is from which country?|Thailand|Japan|India|Philippines
culture|The tradition of decorated Christmas trees began in which country?|Germany|Norway|United States|Finland
culture|Which country celebrates Thanksgiving on the second Monday of October?|Canada|United States|United Kingdom|Australia
culture|Which musical instrument is Scotland famous for?|Bagpipes|Harp|Accordion|Banjo
culture|"Big Ben" is actually the nickname of…|The great bell inside a London clock tower|A clock in New York|A bridge in London|A palace in Paris
culture|The tango dance comes from which country?|Argentina|Spain|Brazil|Cuba
culture|Flamenco dancing comes from which country?|Spain|Mexico|Portugal|Italy
culture|Which country is famous for the samba?|Brazil|Cuba|Argentina|Colombia
culture|Which film series features Darth Vader?|Star Wars|Star Trek|The Matrix|Dune
culture|On a standard dice, opposite sides always add up to…|7|6|8|12
culture|What is a word that reads the same forwards and backwards called?|A palindrome|An anagram|A homophone|An acronym
culture|The word "emoji" comes from which language?|Japanese|English|Korean|Chinese
culture|The sandwich is named after…|An English earl|An Italian chef|A French king|A German baker
culture|Which famous detective lived at 221B Baker Street?|Sherlock Holmes|Hercule Poirot|Miss Marple|Nancy Drew
culture|Which board game has properties like Mayfair or Boardwalk?|Monopoly|Scrabble|Cluedo (Clue)|Risk
culture|In Scrabble, how many points is the letter Q worth?|10|8|5|1
culture|Which color do you get when you mix red and white?|Pink|Purple|Orange|Brown
culture|How many players are on each side in a game of rugby union?|15|11|13|9
culture|Which country hosts the Tour de France cycling race?|France|Italy|Spain|Belgium
culture|What is the name of the gold statue given out at the Academy Awards?|Oscar|Emmy|Grammy|Tony
culture|Which superhero is known as the Man of Steel?|Superman|Iron Man|Batman|Spider-Man
culture|Which fairy-tale character loses a glass slipper?|Cinderella|Snow White|Rapunzel|Sleeping Beauty
culture|Which country gave the world the Olympic Games and the marathon?|Greece|Italy|Egypt|France
culture|Which instrument has black and white keys?|Piano|Violin|Trumpet|Drum
culture|Which country is famous for windmills and tulips?|The Netherlands|Belgium|Denmark|Austria
culture|What are the colors of the Olympic rings?|Blue, yellow, black, green and red|Red, white and blue|Gold, silver and bronze|Rainbow colors
animals|What is a baby elephant called?|A calf|A kid|A cub|A foal
culture|What is a Japanese poem with three lines of 5, 7 and 5 syllables called?|A haiku|A sonnet|A limerick|A ballad
"""
for line in FACTS.strip().splitlines():
    parts = line.split("|")
    cat, q, a, opts = parts[0], parts[1], parts[2], parts[3:]
    key = "f:" + hashlib.md5(q.encode()).hexdigest()[:8]
    add(cat, key, q, a, opts)

# ------------------------------------------------------------------ quotas -> exactly 1,000
counts = {k: len(v) for k, v in Q.items()}
print("available", counts, "total", sum(counts.values()))
final = []
for cat, items in Q.items():
    final += items
if len(final) > 1000:
    # trim from the data-driven categories with the most spare questions
    rng.shuffle(final)
    by = collections.Counter(x["c"] for x in final)
    order = ["flag", "capital", "bigger", "currency", "capitalwho", "landlocked"]
    while len(final) > 1000:
        for c in order:
            if len(final) <= 1000:
                break
            idx = next(i for i, x in enumerate(final) if x["c"] == c)
            final.pop(idx)
print("final", len(final), collections.Counter(x["c"] for x in final))
used_flags = {x["i"].split("/")[1] for x in final if "i" in x}
for f in os.listdir(OUTFLAGS):
    if f not in used_flags:
        os.remove(os.path.join(OUTFLAGS, f))
with open(OUT, "w") as f:
    f.write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in final) + "\n]\n")
