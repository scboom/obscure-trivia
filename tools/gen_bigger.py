"""Build the 'This or That' bank (first called Which Is Bigger?): 1,000 head-to-head questions.

Every item has a value and an uncertainty ("fuzz", as a fraction, or in years for dates).
Two items are only paired when the gap between them is clearly bigger than both
uncertainties together, so no answer depends on which source you read.
Usage: gen_bigger.py OUT.json population.csv countries.json pl.json
"""
import sys, json, csv, math, random, collections

OUT, POP_CSV, WC_JSON, PL_JSON = sys.argv[1:5]
rng = random.Random(20261122)


def item(id, name, val, fuzz=0.0, desc="", **kw):
    d = {"id": id, "name": name, "val": val, "fuzz": fuzz, "desc": desc}
    d.update(kw)
    return d


def about(fz):
    return "about " if fz >= 0.04 else ""


def comma(v, nd=0):
    s = f"{v:,.{nd}f}"
    if nd and "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def neg(s):
    return s.replace("-", "−")


# ------------------------------------------------------------------ formatters
def f_height(it):
    v, fz = it["val"], it["fuzz"]
    if v < 10:
        ft = v * 3.28084
        return f"{about(fz)}{comma(v, 2)} m ({int(ft)} ft {round((ft - int(ft)) * 12)} in)"
    r = -2 if v >= 5000 and fz >= 0.04 else 0
    return f"{about(fz)}{comma(round(v, r))} m ({comma(round(v * 3.28084, r))} ft)"


def f_area(it):
    v, fz = it["val"], it["fuzz"]
    if v >= 1e6:
        return f"{about(fz)}{comma(v / 1e6, 1)} million km²"
    if v >= 100:
        return f"{about(fz)}{comma(round(v, -2 if fz >= 0.04 and v >= 10000 else 0))} km²"
    return f"{about(fz)}{comma(v, 1)} km²"


def f_pop(it):
    v = it["val"]
    if v >= 1e9:
        return f"about {v / 1e9:.2f} billion"
    if v >= 1e8:
        return f"about {comma(v / 1e6)} million"
    if v >= 1e6:
        return f"about {comma(v / 1e6, 1)} million"
    return f"about {comma(round(v, -3))}"


def f_len(it):
    v, fz = it["val"], it["fuzz"]
    if v < 1:
        return f"{about(fz)}{comma(v * 1000)} m"
    if v < 100:
        return f"{about(fz)}{comma(v, 1)} km ({comma(v * 0.621371, 1)} miles)"
    r = -1 if fz >= 0.04 else 0
    return f"{about(fz)}{comma(round(v, r))} km ({comma(round(v * 0.621371, r))} miles)"


def f_weight(it):
    v = it["val"]
    if v >= 1000:
        t = v / 1000
        return f"about {comma(t, 1 if t < 10 else 0)} tonnes"
    if v >= 1:
        return f"about {comma(v, 1 if v < 10 else 0)} kg"
    return f"about {comma(v * 1000, 1 if v < 0.01 else 0)} g"


def f_speed(it):
    v, fz = it["val"], it["fuzz"]
    if v < 1:
        return f"{about(fz)}{v:.2f} km/h"
    return f"{about(fz)}{comma(v)} km/h ({comma(v * 0.621371)} mph)"


def f_life(it):
    v = it["val"]
    if v >= 1:
        return f"up to about {comma(v)} years"
    days = v * 365.25
    if days < 14:
        return "about a day" if round(days) <= 1 else f"about {round(days)} days"
    return f"about {round(days / 7)} weeks"


def f_year(it):
    y, fz = it["val"], it["fuzz"]
    if y <= -1e6:
        return f"about {comma(-y / 1e6)} million years ago"
    if y <= -10000:
        return f"about {comma(-y)} years ago"
    if y < 0:
        return f"{'around ' if fz else ''}{-y} BC"
    if y < 1000:
        return f"{'around ' if fz else ''}AD {y}"
    return f"{'around ' if fz else ''}{y}"


def f_num(it):
    return f"{about(it['fuzz'])}{comma(it['val'])}"


def f_km_across(it):
    return f"{about(it['fuzz'])}{comma(it['val'])} km across"


def f_spin(it):
    h = it["val"]
    if h >= 48:
        return f"{about(it['fuzz'])}{comma(h / 24, 1)} Earth days"
    return f"{about(it['fuzz'])}{comma(h, 1)} hours"


def f_grav(it):
    return f"{round(it['val'] / 9.81 * 100)}% of Earth's"


def f_temp(it):
    v, fz = it["val"], it["fuzz"]
    if abs(v) >= 1e6:
        return neg(f"about {comma(v / 1e6)} million °C")
    if abs(v) >= 10000:
        return neg(f"about {comma(round(v, -3))} °C")
    return neg(f"{about(fz)}{comma(v, 0 if v == int(v) else 1)} °C")


def f_protons(it):
    return f"{it['val']} proton{'' if it['val'] == 1 else 's'}"


def f_density(it):
    v = it["val"]
    s = f"{v:.2f}" if v >= 1 else (f"{v:.3f}" if v >= 0.1 else f"{v:.5f}")
    return f"{about(it['fuzz'])}{s.rstrip('0').rstrip('.')} g/cm³"


def f_seats(it):
    return f"{about(it['fuzz'])}{comma(round(it['val'], -2 if it['fuzz'] >= 0.04 else 0))} people"


def f_grams(it):
    v = it["val"]
    return f"about {comma(v, 1 if v < 10 else 0)} g"


def f_seasons(it):
    return f"{it['val']} seasons"


def f_kcal(it):
    return f"{about(it['fuzz'])}{comma(it['val'])} kcal"


def f_scoville(it):
    lo, hi = it["lo"], it["hi"]
    if lo == hi:
        return f"{'about ' if lo else ''}{comma(lo)} Scoville"
    return f"{comma(lo)}–{comma(hi)} Scoville"


def f_mg(it):
    return f"about {comma(it['val'])} mg"


def f_dist(it):
    v = it["val"]
    return f"about {comma(round(v, -1))} km ({comma(round(v * 0.621371, -1))} miles)"


# ------------------------------------------------------------------ data: countries
pop = {}
with open(POP_CSV, newline="") as f:
    for row in csv.DictReader(f):
        if row["Year"] == "2025" and row["Value"]:
            pop[row["Country Code"]] = float(row["Value"])
wc = {c["cca3"]: c for c in json.load(open(WC_JSON))}

COUNTRIES = ("GBR FRA DEU ITA ESP PRT NLD BEL CHE AUT IRL ISL NOR SWE FIN DNK POL CZE SVK HUN ROU BGR GRC HRV SRB SVN UKR BLR RUS TUR "
             "LUX MLT CYP EST LVA LTU ALB BIH MKD MNE GEO ARM AZE "
             "CHN IND JPN KOR PRK IDN PHL VNM THA MYS SGP PAK BGD LKA NPL AFG IRN IRQ SAU ARE QAT KWT ISR JOR LBN SYR YEM OMN KAZ UZB MNG MMR KHM "
             "NGA EGY ZAF KEN ETH GHA DZA TUN LBY SDN TZA UGA AGO MOZ ZWE ZMB CMR CIV SEN MDG COD RWA NAM BWA MLI NER TCD "
             "USA CAN MEX BRA ARG CHL PER COL VEN ECU BOL PRY URY CUB JAM DOM HTI GTM HND CRI PAN SLV "
             "AUS NZL PNG FJI").split()
NAME_FIX = {"GBR": "United Kingdom", "USA": "United States", "COD": "DR Congo", "CIV": "Ivory Coast", "CZE": "Czechia",
            "KOR": "South Korea", "PRK": "North Korea", "TUR": "Turkey", "MKD": "North Macedonia", "BIH": "Bosnia and Herzegovina"}
# area figures differ between sources (inland water, overseas parts, disputed land): widen those
AREA_FUZZ = {"USA": 0.06, "CHN": 0.05, "IND": 0.08, "PAK": 0.08, "FRA": 0.17, "NOR": 0.2, "NLD": 0.2, "DNK": 0.05, "CAN": 0.06,
             "SRB": 0.15, "CYP": 0.1, "GEO": 0.15, "ISR": 0.1, "AZE": 0.1, "MDA": 0.1, "UKR": 0.04, "FIN": 0.05, "SWE": 0.04,
             "MLT": 0.03, "SGP": 0.08, "PRK": 0.04, "KOR": 0.03, "SYR": 0.05, "LBN": 0.05, "JOR": 0.04}


def continent(c):
    r, s = c.get("region"), c.get("subregion", "")
    if r == "Americas":
        return "South America" if s == "South America" else "North America"
    return r


country_pop, country_area = [], []
for code in COUNTRIES:
    c = wc[code]
    nm = NAME_FIX.get(code, c["name"]["common"])
    desc = "country, " + continent(c)
    if code in pop:
        country_pop.append(item("c:" + code, nm, pop[code], 0.06, desc))
    area = {"USA": 9833520.0}.get(code, float(c["area"]))   # the usual total, with lakes and rivers
    country_area.append(item("c:" + code, {"FRA": "France (mainland)", "NOR": "Norway (mainland)"}.get(code, nm), area, AREA_FUZZ.get(code, 0.03), desc))

POP_EXTRA = [
    item("p:eng", "England", 58.5e6, 0.03, "UK nation"), item("p:sco", "Scotland", 5.5e6, 0.02, "UK nation"),
    item("p:wal", "Wales", 3.2e6, 0.02, "UK nation"), item("p:nir", "Northern Ireland", 1.92e6, 0.02, "UK nation"),
    item("p:london", "London", 9.0e6, 0.04, "city, United Kingdom"), item("p:nyc", "New York City", 8.5e6, 0.04, "city, United States"),
    item("p:cal", "California", 39.4e6, 0.02, "US state"), item("p:tex", "Texas", 31.3e6, 0.02, "US state"),
    item("p:fla", "Florida", 23.4e6, 0.02, "US state"), item("p:nys", "New York State", 19.9e6, 0.02, "US state"),
]

AREA_EXTRA = [
    # islands
    item("i:greenland", "Greenland", 2166086, 0.01, "island"), item("i:newguinea", "New Guinea", 785753, 0.01, "island"),
    item("i:borneo", "Borneo", 743330, 0.02, "island"),
    item("i:baffin", "Baffin Island", 507451, 0.02, "island, Canada"), item("i:sumatra", "Sumatra", 473481, 0.03, "island, Indonesia"),
    item("i:honshu", "Honshu", 227960, 0.01, "Japan's main island"), item("i:gb", "Great Britain", 209331, 0.01, "island"),
    item("i:sulawesi", "Sulawesi", 180681, 0.02, "island, Indonesia"), item("i:java", "Java", 128297, 0.04, "island, Indonesia"),
    item("i:ireland", "Ireland (the whole island)", 84421, 0.01, "island"), item("i:tasmania", "Tasmania", 64519, 0.06, "island, Australia"),
    item("i:sicily", "Sicily", 25711, 0.01, "island, Italy"), item("i:sardinia", "Sardinia", 24090, 0.01, "island, Italy"),
    item("i:bigisland", "Hawaii's Big Island", 10432, 0.02, "island, United States"), item("i:corsica", "Corsica", 8680, 0.01, "island, France"),
    item("i:crete", "Crete", 8336, 0.02, "island, Greece"), item("i:majorca", "Majorca", 3640, 0.02, "island, Spain"),
    item("i:tenerife", "Tenerife", 2034, 0.01, "island, Spain"), item("i:skye", "Isle of Skye", 1656, 0.02, "island, Scotland"),
    item("i:man", "Isle of Man", 572, 0.01, "island"), item("i:wight", "Isle of Wight", 380, 0.02, "island, England"),
    item("i:jersey", "Jersey", 118, 0.02, "Channel Island"), item("i:manhattan", "Manhattan", 59.1, 0.02, "island, New York City"),
    # deserts and continents
    item("d:antarctica", "Antarctica", 14200000, 0.03, "continent and the biggest desert of all"),
    item("d:sahara", "The Sahara", 9200000, 0.05, "desert, Africa"), item("d:arabian", "The Arabian Desert", 2330000, 0.1, "desert, Asia"),
    item("d:gobi", "The Gobi Desert", 1295000, 0.1, "desert, Asia"), item("d:kalahari", "The Kalahari Desert", 900000, 0.1, "desert, Africa"),
    item("d:victoria", "The Great Victoria Desert", 348750, 0.05, "desert, Australia"), item("d:thar", "The Thar Desert", 200000, 0.1, "desert, India and Pakistan"),
    item("k:asia", "Asia", 44580000, 0.02, "continent"), item("k:africa", "Africa", 30370000, 0.02, "continent"),
    item("k:namerica", "North America", 24710000, 0.02, "continent"), item("k:samerica", "South America", 17840000, 0.02, "continent"),
    item("k:europe", "Europe", 10180000, 0.03, "continent"), item("s:moon", "The Moon's whole surface", 37930000, 0.01, "all of it, both sides"),
    # lakes and seas
    item("l:caspian", "The Caspian Sea", 371000, 0.03, "the world's biggest lake"), item("l:superior", "Lake Superior", 82100, 0.01, "lake, North America"),
    item("l:victoria", "Lake Victoria", 68870, 0.02, "lake, Africa"), item("l:michigan", "Lake Michigan", 58000, 0.01, "lake, United States"),
    item("l:tanganyika", "Lake Tanganyika", 32900, 0.01, "lake, Africa"), item("l:baikal", "Lake Baikal", 31500, 0.02, "lake, Russia"),
    item("l:erie", "Lake Erie", 25700, 0.01, "lake, North America"), item("l:ontario", "Lake Ontario", 18960, 0.01, "lake, North America"),
    item("l:titicaca", "Lake Titicaca", 8372, 0.03, "lake, Peru and Bolivia"), item("l:geneva", "Lake Geneva", 580, 0.01, "lake, Switzerland and France"),
    item("l:neagh", "Lough Neagh", 392, 0.02, "the UK's biggest lake"), item("l:lomond", "Loch Lomond", 71, 0.02, "loch, Scotland"),
    item("l:ness", "Loch Ness", 56, 0.03, "loch, Scotland"),
    item("l:med", "The Mediterranean Sea", 2500000, 0.03, "sea"), item("l:north", "The North Sea", 575000, 0.03, "sea"),
    item("l:black", "The Black Sea", 436400, 0.02, "sea"),
    # parts of countries
    item("u:eng", "England", 130279, 0.01, "UK nation"), item("u:sco", "Scotland", 77910, 0.03, "UK nation"),
    item("u:wal", "Wales", 20779, 0.02, "UK nation"), item("u:nir", "Northern Ireland", 14130, 0.02, "UK nation"),
    item("u:alaska", "Alaska", 1723337, 0.02, "US state"), item("u:texas", "Texas", 695662, 0.02, "US state"),
    item("u:california", "California", 423967, 0.02, "US state"), item("u:florida", "Florida", 170312, 0.03, "US state"),
    item("u:london", "Greater London", 1572, 0.01, "city, United Kingdom"), item("u:lakes", "The Lake District National Park", 2362, 0.01, "national park, England"),
]

# ------------------------------------------------------------------ data: heights (metres)
HEIGHT = [
    item("everest", "Mount Everest", 8849, 0.002, "mountain, Nepal and China"), item("k2", "K2", 8611, 0.003, "mountain, Pakistan and China"),
    item("aconcagua", "Aconcagua", 6961, 0.003, "mountain, Argentina"), item("denali", "Denali", 6190, 0.003, "mountain, Alaska"),
    item("kilimanjaro", "Mount Kilimanjaro", 5895, 0.003, "mountain, Tanzania"), item("elbrus", "Mount Elbrus", 5642, 0.003, "mountain, Russia"),
    item("mtkenya", "Mount Kenya", 5199, 0.003, "mountain, Kenya"), item("montblanc", "Mont Blanc", 4806, 0.003, "mountain, France and Italy"),
    item("matterhorn", "The Matterhorn", 4478, 0.003, "mountain, Switzerland and Italy"), item("maunakea", "Mauna Kea (above sea level)", 4207, 0.003, "volcano, Hawaii"),
    item("fuji", "Mount Fuji", 3776, 0.003, "volcano, Japan"), item("etna", "Mount Etna", 3357, 0.02, "volcano, Sicily"),
    item("olympus", "Mount Olympus", 2917, 0.003, "mountain, Greece"), item("kosciuszko", "Mount Kosciuszko", 2228, 0.003, "Australia's highest mountain"),
    item("bennevis", "Ben Nevis", 1345, 0.002, "the UK's highest mountain"), item("vesuvius", "Mount Vesuvius", 1281, 0.01, "volcano, Italy"),
    item("snowdon", "Snowdon (Yr Wyddfa)", 1085, 0.002, "Wales's highest mountain"), item("carrauntoohil", "Carrauntoohil", 1039, 0.002, "Ireland's highest mountain"),
    item("scafell", "Scafell Pike", 978, 0.002, "England's highest mountain"), item("donard", "Slieve Donard", 850, 0.003, "Northern Ireland's highest mountain"),
    item("olympusmons", "Olympus Mons", 21900, 0.1, "volcano on Mars"),
    item("burj", "The Burj Khalifa", 828, 0.005, "skyscraper, Dubai"), item("merdeka", "Merdeka 118", 679, 0.005, "skyscraper, Kuala Lumpur"),
    item("skytree", "Tokyo Skytree", 634, 0.005, "tower, Tokyo"), item("shanghai", "Shanghai Tower", 632, 0.005, "skyscraper, Shanghai"),
    item("clock", "Makkah Royal Clock Tower", 601, 0.005, "skyscraper, Mecca"), item("cntower", "The CN Tower", 553, 0.005, "tower, Toronto"),
    item("onewtc", "One World Trade Center", 541, 0.005, "skyscraper, New York"), item("taipei", "Taipei 101", 508, 0.005, "skyscraper, Taiwan"),
    item("petronas", "The Petronas Towers", 452, 0.005, "skyscrapers, Kuala Lumpur"), item("empire", "The Empire State Building", 443, 0.02, "skyscraper, New York (to the tip)"),
    item("eiffel", "The Eiffel Tower", 330, 0.02, "tower, Paris"), item("chrysler", "The Chrysler Building", 319, 0.005, "skyscraper, New York"),
    item("shard", "The Shard", 310, 0.005, "skyscraper, London"), item("goldengate", "The Golden Gate Bridge's towers", 227, 0.01, "bridge, San Francisco"),
    item("arch", "The Gateway Arch", 192, 0.005, "monument, St. Louis"), item("needle", "The Space Needle", 184, 0.01, "tower, Seattle"),
    item("blackpool", "Blackpool Tower", 158, 0.01, "tower, England"), item("pyramid", "The Great Pyramid of Giza (today)", 138.5, 0.01, "pyramid, Egypt"),
    item("eye", "The London Eye", 135, 0.01, "observation wheel, London"), item("harbour", "Sydney Harbour Bridge", 134, 0.01, "bridge, Sydney (top of the arch)"),
    item("wembley", "Wembley Stadium's arch", 133, 0.02, "stadium, London"), item("hyperion", "Hyperion", 116, 0.02, "the world's tallest known tree"),
    item("bigben", "Elizabeth Tower (Big Ben)", 96, 0.01, "clock tower, London"), item("liberty", "The Statue of Liberty (with its pedestal)", 93, 0.01, "statue, New York"),
    item("tower", "Tower Bridge", 65, 0.02, "bridge, London"), item("pisa", "The Leaning Tower of Pisa", 56, 0.02, "bell tower, Italy"),
    item("nelson", "Nelson's Column", 52, 0.01, "monument, London"), item("arc", "The Arc de Triomphe", 50, 0.01, "monument, Paris"),
    item("christ", "Christ the Redeemer (with its pedestal)", 38, 0.02, "statue, Rio de Janeiro"), item("angelnorth", "The Angel of the North", 20, 0.01, "sculpture, Gateshead"),
    item("angelfalls", "Angel Falls", 979, 0.01, "waterfall, Venezuela (total drop)"), item("yosemite", "Yosemite Falls", 739, 0.01, "waterfall, California (total drop)"),
    item("vicfalls", "Victoria Falls", 108, 0.03, "waterfall, Zambia and Zimbabwe"), item("iguazu", "Iguazu Falls", 82, 0.1, "waterfall, Argentina and Brazil"),
    item("niagara", "Niagara Falls (Horseshoe Falls)", 51, 0.05, "waterfall, Canada and the USA"),
    item("wadlow", "The tallest man ever (Robert Wadlow)", 2.72, 0.005, "person"), item("giraffe", "A giraffe", 5.5, 0.1, "the tallest animal"),
]

# ------------------------------------------------------------------ lengths (km)
LENGTH = [
    item("nile", "The Nile", 6650, 0.03, "river, Africa"), item("amazon", "The Amazon", 6400, 0.06, "river, South America"),
    item("yangtze", "The Yangtze", 6300, 0.02, "river, China"), item("yellow", "The Yellow River", 5464, 0.02, "river, China"),
    item("congo", "The Congo", 4700, 0.02, "river, Africa"), item("mekong", "The Mekong", 4350, 0.05, "river, Southeast Asia"),
    item("niger", "The Niger", 4180, 0.02, "river, Africa"), item("mississippi", "The Mississippi", 3730, 0.03, "river, United States"),
    item("volga", "The Volga", 3530, 0.01, "river, Russia"), item("riogrande", "The Rio Grande", 3051, 0.04, "river, USA and Mexico"),
    item("danube", "The Danube", 2850, 0.01, "river, Europe"), item("zambezi", "The Zambezi", 2574, 0.03, "river, Africa"),
    item("ganges", "The Ganges", 2525, 0.03, "river, India and Bangladesh"), item("colorado", "The Colorado River", 2330, 0.02, "river, USA and Mexico"),
    item("rhine", "The Rhine", 1233, 0.03, "river, Europe"), item("elbe", "The Elbe", 1094, 0.01, "river, Czechia and Germany"),
    item("loire", "The Loire", 1006, 0.01, "river, France"), item("seine", "The Seine", 777, 0.01, "river, France"),
    item("po", "The Po", 652, 0.01, "river, Italy"), item("tiber", "The Tiber", 406, 0.01, "river, Italy"),
    item("shannon", "The River Shannon", 360, 0.02, "river, Ireland"), item("severn", "The River Severn", 354, 0.01, "the UK's longest river"),
    item("thames", "The River Thames", 346, 0.01, "river, England"), item("trent", "The River Trent", 297, 0.02, "river, England"),
    item("clyde", "The River Clyde", 176, 0.02, "river, Scotland"), item("liffey", "The River Liffey", 125, 0.02, "river, Ireland"),
    item("greatwall", "The Great Wall of China (all its sections)", 21196, 0.05, "wall, China"),
    item("transsib", "The Trans-Siberian Railway", 9289, 0.01, "railway, Moscow to Vladivostok"),
    item("route66", "Route 66 (the original road)", 3940, 0.02, "road, Chicago to Los Angeles"),
    item("lejog", "Land's End to John o' Groats (by road)", 1407, 0.05, "the length of Great Britain"),
    item("tdf", "The Tour de France (the whole race)", 3400, 0.06, "bike race, France"),
    item("tube", "The London Underground (all its track)", 402, 0.02, "railway, London"),
    item("m6", "The M6 motorway", 373, 0.03, "motorway, England"), item("m1", "The M1 motorway", 311, 0.03, "motorway, England"),
    item("m25", "The M25 motorway", 188, 0.01, "the ring road around London"),
    item("danyang", "The Danyang–Kunshan Grand Bridge", 164.8, 0.005, "the world's longest bridge, China"),
    item("hadrian", "Hadrian's Wall", 117.5, 0.02, "Roman wall, northern England"),
    item("gotthard", "The Gotthard Base Tunnel", 57.1, 0.005, "rail tunnel, Switzerland"), item("hzmb", "The Hong Kong–Zhuhai–Macau Bridge", 55, 0.02, "bridge and tunnel, China"),
    item("seikan", "The Seikan Tunnel", 53.85, 0.005, "rail tunnel, Japan"), item("chunnel", "The Channel Tunnel", 50.45, 0.005, "rail tunnel, England to France"),
    item("marathon", "A marathon", 42.195, 0.0, "running race"), item("dover", "The English Channel at its narrowest", 33.3, 0.02, "Dover to Cap Gris-Nez"),
    item("oresund", "The Øresund Bridge", 7.845, 0.005, "bridge, Denmark to Sweden"), item("goldengatelen", "The Golden Gate Bridge", 2.737, 0.005, "bridge, San Francisco"),
    item("forth", "The Forth Bridge", 2.528, 0.005, "rail bridge, Scotland"), item("humber", "The Humber Bridge", 2.22, 0.005, "bridge, England"),
    item("towerlen", "Tower Bridge", 0.244, 0.01, "bridge, London"),
]

# ------------------------------------------------------------------ weights (kg, typical adult)
WEIGHT = [
    item("bluewhale", "A blue whale", 140000, 0.3, "the biggest animal ever"), item("spermwhale", "A male sperm whale", 41000, 0.25, "whale"),
    item("humpback", "A humpback whale", 30000, 0.3, "whale"), item("argentino", "Argentinosaurus", 70000, 0.4, "dinosaur, one of the biggest"),
    item("trex", "Tyrannosaurus rex", 8000, 0.4, "dinosaur"), item("orca", "An orca", 5500, 0.3, "killer whale"),
    item("elephant", "An African elephant", 6000, 0.3, "the heaviest land animal"), item("rhino", "A white rhino", 2300, 0.3, "rhinoceros"),
    item("hippo", "A hippo", 1500, 0.3, "hippopotamus"), item("giraffew", "A giraffe", 1200, 0.3, "the tallest animal"),
    item("car", "A family car", 1500, 0.25, "about the size of a Ford Focus"), item("cow", "A dairy cow", 700, 0.3, "farm animal"),
    item("horse", "A horse", 500, 0.3, "farm animal"), item("piano", "A concert grand piano", 480, 0.15, "musical instrument"),
    item("polarbear", "A polar bear", 450, 0.3, "bear"), item("grizzly", "A grizzly bear", 270, 0.3, "bear"),
    item("lion", "A lion", 190, 0.2, "big cat"), item("gorilla", "A gorilla", 160, 0.25, "great ape"),
    item("ostrich", "An ostrich", 115, 0.2, "the heaviest bird"), item("panda", "A giant panda", 100, 0.2, "bear, China"),
    item("human", "An adult human", 70, 0.2, "person"), item("chimp", "A chimpanzee", 50, 0.25, "great ape"),
    item("penguin", "An emperor penguin", 30, 0.3, "the heaviest penguin"), item("golden", "A golden eagle", 5, 0.3, "bird of prey"),
    item("cat", "A pet cat", 4.5, 0.3, "pet"), item("chicken", "A chicken", 2.5, 0.3, "farm bird"),
    item("hedgehog", "A hedgehog", 0.8, 0.3, "garden animal"), item("rat", "A brown rat", 0.3, 0.3, "rodent"),
    item("hamster", "A hamster", 0.12, 0.3, "pet"), item("mouse", "A house mouse", 0.02, 0.3, "rodent"),
    item("hummingbird", "A bee hummingbird", 0.002, 0.2, "the smallest bird"),
]

# ------------------------------------------------------------------ top speeds (km/h)
SPEED = [
    item("peregrine", "A peregrine falcon (diving)", 320, 0.15, "the fastest animal"), item("cheetah", "A cheetah", 110, 0.1, "the fastest land animal"),
    item("pronghorn", "A pronghorn", 88, 0.1, "antelope, North America"), item("lion_s", "A lion", 80, 0.1, "big cat"),
    item("greyhound", "A greyhound", 72, 0.05, "dog"), item("racehorse", "A racehorse", 70, 0.1, "horse"),
    item("grizzly_s", "A grizzly bear", 56, 0.1, "bear"), item("housecat", "A pet cat", 48, 0.1, "pet"),
    item("bolt", "Usain Bolt (at full speed)", 44.7, 0.01, "the fastest person ever"), item("elephant_s", "An elephant", 40, 0.1, "animal"),
    item("dolphin", "A bottlenose dolphin", 35, 0.15, "sea mammal"), item("chicken_s", "A chicken", 14, 0.2, "farm bird"),
    item("sloth", "A three-toed sloth", 0.24, 0.3, "the slowest mammal"),
    item("iss", "The International Space Station", 27600, 0.01, "orbiting Earth"), item("concorde", "Concorde (cruising)", 2180, 0.02, "supersonic jet"),
    item("sound", "The speed of sound (in air)", 1235, 0.02, "at sea level"), item("thrust", "Thrust SSC (land speed record)", 1228, 0.01, "jet car, 1997"),
    item("jet", "A passenger jet (cruising)", 900, 0.08, "airliner"), item("bugatti", "The fastest Bugatti (record run)", 490, 0.005, "Chiron Super Sport 300+"),
    item("wind", "The fastest wind gust ever recorded", 408, 0.01, "Barrow Island, Australia, 1996"), item("f1", "A Formula 1 car (top speed)", 350, 0.07, "racing car"),
    item("shinkansen", "A Japanese bullet train", 320, 0.02, "fastest service speed"), item("eurostar", "The Eurostar", 300, 0.02, "train, London to Paris"),
    item("rossa", "Formula Rossa", 240, 0.01, "the fastest roller coaster, Abu Dhabi"), item("cricket", "The fastest ball ever bowled in cricket", 161.3, 0.005, "Shoaib Akhtar, 2003"),
    item("motorway", "The UK motorway speed limit", 112.65, 0.0, "70 mph"),
]

# ------------------------------------------------------------------ lifespans (years, a long life for that animal)
LIFE = [
    item("greenland", "A Greenland shark", 400, 0.3, "shark, Arctic"), item("bowhead", "A bowhead whale", 200, 0.15, "whale, Arctic"),
    item("humanl", "A human", 120, 0.05, "the oldest person ever reached 122"), item("elephantl", "An elephant", 70, 0.15, "animal"),
    item("queenant", "A queen garden ant", 28, 0.3, "insect"), item("horsel", "A horse", 30, 0.2, "farm animal"),
    item("catl", "A pet cat", 20, 0.2, "pet"), item("dogl", "A pet dog", 15, 0.25, "pet"), item("rabbit", "A rabbit", 10, 0.2, "pet"),
    item("hamsterl", "A hamster", 3, 0.3, "pet"), item("bee", "A worker honeybee (in summer)", 6 / 52, 0.3, "insect"),
    item("mayfly", "An adult mayfly", 1 / 365.25, 0.5, "insect"), item("tortoise", "A giant tortoise", 150, 0.2, "reptile, Galápagos"),
    item("parrot", "A macaw", 60, 0.25, "parrot"), item("goldfish", "A goldfish", 15, 0.3, "pet fish"),
]

# ------------------------------------------------------------------ dates (year; negative = BC)
DATES = [
    item("pyramidb", "The Great Pyramid of Giza is built", -2560, 30), item("stonehenge", "Stonehenge's first stage is built", -3000, 100),
    item("mammoth", "The last woolly mammoths die out", -2000, 150), item("olympia", "The first ancient Olympic Games", -776, 0),
    item("caesar", "Julius Caesar is killed", -44, 0), item("vending", "The first vending machine (it sold holy water)", 50, 30),
    item("oxford", "Teaching starts at Oxford University", 1096, 10), item("hastings", "The Battle of Hastings", 1066, 0),
    item("magna", "Magna Carta is signed", 1215, 0), item("aztec", "The Aztec Empire is founded", 1428, 0),
    item("press", "Gutenberg's printing press", 1440, 5), item("columbus", "Columbus reaches the Americas", 1492, 0),
    item("shakespeare", "William Shakespeare is born", 1564, 0), item("telescope", "The first telescope", 1608, 0),
    item("harvard", "Harvard University is founded", 1636, 0), item("fire", "The Great Fire of London", 1666, 0),
    item("taj", "The Taj Mahal is finished", 1653, 5), item("usa", "The USA declares independence", 1776, 0),
    item("balloon", "The first hot-air balloon flight with people on board", 1783, 0), item("bicycle", "The first bicycle (with no pedals)", 1817, 0),
    item("lighter", "The first lighter", 1823, 0), item("match", "The first friction match", 1826, 0),
    item("railway", "The first public railway opens (Stockton and Darlington)", 1825, 0), item("fax", "The first fax machine is patented", 1843, 0),
    item("tube_d", "The London Underground opens", 1863, 0), item("facup", "The first FA Cup final", 1872, 0),
    item("phone", "The telephone is patented", 1876, 0), item("bulb", "Edison's light bulb", 1879, 0),
    item("benz", "The first car (Benz Patent-Motorwagen)", 1886, 0), item("nintendo", "Nintendo is founded (making playing cards)", 1889, 0),
    item("olympics", "The first modern Olympic Games", 1896, 0), item("wright", "The Wright brothers' first flight", 1903, 0),
    item("titanic", "The Titanic sinks", 1912, 0), item("ww1", "The First World War begins", 1914, 0),
    item("disney", "Walt Disney's company is founded", 1923, 0), item("queen", "Queen Elizabeth II is born", 1926, 0),
    item("sliced", "Sliced bread goes on sale", 1928, 0), item("penicillin", "Penicillin is discovered", 1928, 0),
    item("worldcup", "The first football World Cup", 1930, 0), item("lego", "The LEGO company is founded", 1932, 0),
    item("ww2end", "The Second World War ends", 1945, 0), item("everest1", "Mount Everest is first climbed", 1953, 0),
    item("sputnik", "Sputnik, the first satellite, is launched", 1957, 0), item("gagarin", "The first person goes to space", 1961, 0),
    item("moon", "People first walk on the Moon", 1969, 0), item("pong", "Pong, one of the first video games, comes out", 1972, 0),
    item("rubik", "The Rubik's Cube is invented", 1974, 0), item("starwars", "The first Star Wars film", 1977, 0),
    item("pacman", "Pac-Man comes out", 1980, 0), item("tetris", "Tetris is created", 1984, 0),
    item("mario", "Super Mario Bros. comes out", 1985, 0), item("web", "The World Wide Web is invented", 1989, 0),
    item("pl", "The Premier League starts", 1992, 0), item("ps1", "The first PlayStation comes out", 1994, 0),
    item("pokemon", "The first Pokémon games come out", 1996, 0), item("hp", "The first Harry Potter book", 1997, 0),
    item("google", "Google is founded", 1998, 0), item("wiki", "Wikipedia starts", 2001, 0),
    item("facebook", "Facebook starts", 2004, 0), item("youtube", "YouTube starts", 2005, 0),
    item("roblox", "Roblox is released", 2006, 0), item("iphone", "The first iPhone", 2007, 0),
    item("minecraft", "The first version of Minecraft", 2009, 0), item("instagram", "Instagram starts", 2010, 0),
    item("fortnite", "Fortnite comes out", 2017, 0), item("chatgpt", "ChatGPT is released", 2022, 0),
    item("coke", "Coca-Cola is invented", 1886, 0), item("eiffel_d", "The Eiffel Tower is finished", 1889, 0),
    item("wembley_d", "The old Wembley Stadium opens", 1923, 0), item("berlin", "The Berlin Wall falls", 1989, 0),
    item("eurotunnel", "The Channel Tunnel opens", 1994, 0), item("euro", "Euro coins and notes come in", 2002, 0),
    # deep time
    item("sharks", "The first sharks", -450e6, 20e6), item("trees", "The first trees", -385e6, 10e6),
    item("dinos", "The first dinosaurs", -230e6, 10e6), item("flowers", "The first flowers", -130e6, 10e6),
    item("stego", "Stegosaurus", -152e6, 3e6), item("trex_d", "Tyrannosaurus rex", -67e6, 1e6),
    item("himalaya", "The Himalayas start to rise", -50e6, 5e6), item("humans", "The first modern humans", -300000, 50000),
]

# ------------------------------------------------------------------ numbers (exact counts)
NUMBERS = [
    item("bones", "Bones in an adult human", 206), item("babybones", "Bones in a newborn baby", 300, 0.1),
    item("teeth", "Teeth in an adult's mouth", 32), item("babyteeth", "Baby teeth", 20), item("pianokeys", "Keys on a piano", 88),
    item("cards", "Cards in a deck (no jokers)", 52), item("chess", "Squares on a chessboard", 64), item("chesspieces", "Pieces in a chess set", 32),
    item("states", "States in the USA", 50), item("un", "Member countries of the United Nations", 193), item("elements", "Elements on the periodic table", 118),
    item("leap", "Days in a leap year", 366), item("week", "Hours in a week", 168), item("day", "Minutes in a day", 1440),
    item("hour", "Seconds in an hour", 3600), item("abc", "Letters in the English alphabet", 26), item("greek", "Letters in the Greek alphabet", 24),
    item("plclubs", "Clubs in the Premier League", 20), item("rugby", "Players in a rugby union team", 15), item("football", "Players in a football team", 11),
    item("netball", "Players in a netball team", 7), item("basketball", "Players in a basketball team (on court)", 5),
    item("guitar", "Strings on a guitar", 6), item("violin", "Strings on a violin", 4), item("harp", "Strings on a concert harp", 47),
    item("hpbooks", "Harry Potter books", 7), item("die", "Dots on a dice (all six faces)", 21), item("monopoly", "Squares on a Monopoly board", 40),
    item("dominoes", "Dominoes in a double-six set", 28), item("snooker", "Balls on a snooker table at the start (with the cue ball)", 22),
    item("147", "The maximum break in snooker", 147), item("180", "The most you can score with three darts", 180),
    item("300", "A perfect score in ten-pin bowling", 300), item("golf", "Holes on a golf course", 18), item("sonnet", "Lines in a sonnet", 14),
    item("spider", "Legs on a spider", 8), item("insect", "Legs on an insect", 6), item("lobster", "Legs on a lobster", 10),
    item("octohearts", "Hearts in an octopus", 3), item("chromo", "Chromosomes in a human cell", 46), item("hand", "Bones in one human hand", 27),
    item("foot", "Bones in one human foot", 26), item("ribs", "Ribs in a human", 24), item("eu", "Countries in the European Union", 27),
    item("ukc", "Countries in the United Kingdom", 4), item("canada", "Provinces in Canada", 10), item("russia", "Time zones in Russia", 11),
    item("stripes", "Stripes on the US flag", 13), item("scrabble", "Squares on a Scrabble board", 225), item("scrabbletiles", "Tiles in a Scrabble set", 100),
    item("pokedex", "Pokémon in the original Pokédex", 151), item("africa", "Countries in Africa", 54), item("samerica", "Countries in South America", 12),
    item("boroughs", "Boroughs in London", 32), item("tubestations", "Stations on the London Underground", 272, 0.01),
    item("plgames", "Matches in a Premier League season", 380), item("skull", "Bones in the human skull", 22),
    item("roulette", "Numbers on a roulette wheel (European)", 37), item("sudoku", "Squares in a sudoku grid", 81),
    item("dalmatians", "Dalmatians in the Disney film's title", 101), item("mile", "Yards in a mile", 1760), item("feet", "Feet in a mile", 5280),
    item("minutes", "Minutes in a football match (no extra time)", 90), item("rugbymins", "Minutes in a rugby match", 80),
    item("wc2026", "Teams at the 2026 World Cup", 48), item("ucl", "Teams in the Champions League (league phase)", 36),
    item("century", "Years in a century", 100), item("stone", "Pounds in a stone", 14), item("pound", "Ounces in a pound", 16),
]

# ------------------------------------------------------------------ space
DIAM = [
    item("sun", "The Sun", 1392700, 0.005, "star"), item("jupiter", "Jupiter", 139820, 0.005, "planet"), item("saturn", "Saturn", 116460, 0.005, "planet"),
    item("uranus", "Uranus", 50724, 0.005, "planet"), item("neptune", "Neptune", 49244, 0.005, "planet"), item("earth", "Earth", 12742, 0.002, "planet"),
    item("venus", "Venus", 12104, 0.002, "planet"), item("mars", "Mars", 6779, 0.002, "planet"), item("ganymede", "Ganymede", 5268, 0.003, "Jupiter's biggest moon"),
    item("titan", "Titan", 5150, 0.003, "Saturn's biggest moon"), item("mercury", "Mercury", 4879, 0.002, "planet"),
    item("callisto", "Callisto", 4821, 0.003, "moon of Jupiter"), item("io", "Io", 3643, 0.003, "moon of Jupiter"),
    item("themoon", "The Moon", 3474, 0.002, "Earth's moon"), item("europa", "Europa", 3122, 0.003, "moon of Jupiter"),
    item("pluto", "Pluto", 2377, 0.005, "dwarf planet"), item("ceres", "Ceres", 940, 0.01, "dwarf planet"),
    item("ozwidth", "Australia (from west to east)", 4000, 0.05, "country"), item("usawidth", "The USA (from coast to coast)", 4500, 0.05, "country"),
]
SPIN = [  # time to spin round once (sidereal), hours
    item("venus_r", "Venus", 243 * 24, 0.005, "planet"), item("mercury_r", "Mercury", 58.6 * 24, 0.005, "planet"),
    item("moon_r", "The Moon", 27.3 * 24, 0.005, "Earth's moon"), item("pluto_r", "Pluto", 6.39 * 24, 0.005, "dwarf planet"),
    item("earth_r", "Earth", 23.93, 0.001, "planet"), item("mars_r", "Mars", 24.62, 0.001, "planet"),
    item("uranus_r", "Uranus", 17.24, 0.005, "planet"), item("neptune_r", "Neptune", 16.11, 0.005, "planet"),
    item("saturn_r", "Saturn", 10.66, 0.01, "planet"), item("jupiter_r", "Jupiter", 9.93, 0.005, "planet"),
]
GRAV = [
    item("jupiter_g", "Jupiter", 24.79, 0.005, "planet"), item("neptune_g", "Neptune", 11.15, 0.005, "planet"),
    item("saturn_g", "Saturn", 10.44, 0.005, "planet"), item("earth_g", "Earth", 9.81, 0.001, "planet"),
    item("venus_g", "Venus", 8.87, 0.005, "planet"), item("uranus_g", "Uranus", 8.69, 0.005, "planet"),
    item("mars_g", "Mars", 3.72, 0.005, "planet"), item("moon_g", "The Moon", 1.62, 0.005, "Earth's moon"),
    item("pluto_g", "Pluto", 0.62, 0.01, "dwarf planet"), item("titan_g", "Titan", 1.35, 0.01, "Saturn's biggest moon"),
]

# ------------------------------------------------------------------ heat (degrees C)
HEAT = [
    item("lightning", "A bolt of lightning", 30000, 0.15, "the air inside it"),
    item("sunsurface", "The surface of the Sun", 5500, 0.03, "star"), item("earthcore", "Earth's inner core", 5400, 0.12, "deep underground"),
    item("lava", "Lava", 1000, 0.25, "molten rock"), item("venus_t", "Venus (the surface)", 464, 0.02, "the hottest planet"),
    item("pizza", "A wood-fired pizza oven", 450, 0.15, "kitchen"), item("mercury_t", "Mercury (average at the surface)", 167, 0.2, "planet"),
    item("oven", "A home oven on its hottest setting", 250, 0.1, "kitchen"), item("boil", "Boiling water (at sea level)", 100, 0.0, "kitchen"),
    item("hottest", "The hottest air ever recorded on Earth", 56.7, 0.01, "Death Valley, 1913"), item("body", "The human body", 37, 0.01, "inside you"),
    item("earth_t", "Earth (average at the surface)", 15, 0.1, "planet"), item("mars_t", "Mars (average at the surface)", -65, 0.1, "planet"),
    item("coldest", "The coldest air ever recorded on Earth", -89.2, 0.005, "Vostok Station, Antarctica, 1983"),
    item("freezer", "A home freezer", -18, 0.1, "kitchen"), item("dryice", "Dry ice", -78.5, 0.01, "frozen carbon dioxide"),
    item("nitrogen", "Liquid nitrogen", -196, 0.005, "used in labs"),
]

# ------------------------------------------------------------------ science
PROTONS = [item("pe:" + s, n, z, 0, "element") for s, n, z in [
    ("H", "Hydrogen", 1), ("He", "Helium", 2), ("C", "Carbon", 6), ("N", "Nitrogen", 7), ("O", "Oxygen", 8), ("Ne", "Neon", 10),
    ("Na", "Sodium", 11), ("Al", "Aluminium", 13), ("Si", "Silicon", 14), ("S", "Sulfur", 16), ("Cl", "Chlorine", 17), ("K", "Potassium", 19),
    ("Ca", "Calcium", 20), ("Ti", "Titanium", 22), ("Fe", "Iron", 26), ("Ni", "Nickel", 28), ("Cu", "Copper", 29), ("Zn", "Zinc", 30),
    ("Ag", "Silver", 47), ("Sn", "Tin", 50), ("I", "Iodine", 53), ("Pt", "Platinum", 78), ("Au", "Gold", 79), ("Hg", "Mercury", 80),
    ("Pb", "Lead", 82), ("U", "Uranium", 92), ("Pu", "Plutonium", 94)]]
DENSITY = [
    item("os", "Osmium", 22.59, 0.005, "the densest element"), item("pt", "Platinum", 21.45, 0.005, "metal"), item("au", "Gold", 19.32, 0.005, "metal"),
    item("hg", "Mercury", 13.53, 0.005, "liquid metal"), item("pb", "Lead", 11.34, 0.005, "metal"), item("ag", "Silver", 10.49, 0.005, "metal"),
    item("cu", "Copper", 8.96, 0.005, "metal"), item("fe", "Iron", 7.87, 0.005, "metal"), item("ti", "Titanium", 4.51, 0.005, "metal"),
    item("diamond", "Diamond", 3.51, 0.01, "gem"), item("al", "Aluminium", 2.70, 0.005, "metal"), item("water", "Water", 1.00, 0.002, "liquid"),
    item("ice", "Ice", 0.917, 0.005, "frozen water"), item("oak", "Oak wood", 0.75, 0.15, "wood"), item("cork", "Cork", 0.24, 0.2, "tree bark"),
    item("air", "Air", 0.0012, 0.02, "gas"), item("helium_d", "Helium", 0.00018, 0.02, "gas"),
]
MELT = [
    item("w", "Tungsten", 3422, 0.002, "metal"), item("ti_m", "Titanium", 1668, 0.002, "metal"), item("fe_m", "Iron", 1538, 0.002, "metal"),
    item("au_m", "Gold", 1064, 0.002, "metal"), item("ag_m", "Silver", 962, 0.002, "metal"), item("salt", "Table salt", 801, 0.005, "crystal"),
    item("al_m", "Aluminium", 660, 0.002, "metal"), item("pb_m", "Lead", 327, 0.003, "metal"), item("sn_m", "Tin", 232, 0.005, "metal"),
    item("ice_m", "Ice", 0, 0.0, "frozen water"), item("hg_m", "Mercury", -39, 0.01, "metal"), item("n_m", "Nitrogen", -210, 0.005, "gas"),
    item("choc", "Chocolate", 34, 0.06, "food"),
]

# ------------------------------------------------------------------ sport
STADIUM = [
    item("mcg", "Melbourne Cricket Ground", 100024, 0.02, "Australia"), item("wembley_s", "Wembley Stadium", 90000, 0.01, "London"),
    item("croke", "Croke Park", 82300, 0.02, "Dublin"), item("twickenham", "Twickenham", 82000, 0.02, "rugby, London"),
    item("dortmund", "Signal Iduna Park", 81365, 0.02, "Borussia Dortmund"), item("ot", "Old Trafford", 74000, 0.02, "Manchester United"),
    item("cardiff", "The Principality Stadium", 73931, 0.01, "Cardiff"), item("allianz", "The Allianz Arena", 75024, 0.02, "Bayern Munich"),
    item("murrayfield", "Murrayfield", 67144, 0.01, "rugby, Edinburgh"), item("spurs", "Tottenham Hotspur Stadium", 62850, 0.02, "Tottenham"),
    item("anfield", "Anfield", 61276, 0.02, "Liverpool"), item("emirates", "The Emirates Stadium", 60704, 0.02, "Arsenal"),
    item("celtic", "Celtic Park", 60411, 0.02, "Celtic"), item("stjames", "St James' Park", 52305, 0.02, "Newcastle United"),
    item("hampden", "Hampden Park", 51866, 0.02, "Scotland's national stadium"), item("ibrox", "Ibrox", 50817, 0.02, "Rangers"),
    item("sol", "The Stadium of Light", 49000, 0.02, "Sunderland"), item("bridge", "Stamford Bridge", 40343, 0.02, "Chelsea"),
    item("elland", "Elland Road", 37645, 0.02, "Leeds United"), item("molineux", "Molineux", 31750, 0.02, "Wolves"),
    item("lords", "Lord's", 31100, 0.02, "cricket, London"), item("hawthorns", "The Hawthorns", 26850, 0.02, "West Brom"),
    item("o2", "The O2 Arena", 20000, 0.03, "concerts, London"), item("centre", "Wimbledon's Centre Court", 14979, 0.01, "tennis, London"),
    item("rah", "The Royal Albert Hall", 5272, 0.02, "concerts, London"), item("crucible", "The Crucible Theatre", 980, 0.02, "snooker, Sheffield"),
]
BALLS = [
    item("basket", "A basketball", 610, 0.07, "size 7"), item("rugbyb", "A rugby ball", 435, 0.06, "size 5"), item("footb", "A football", 430, 0.05, "size 5"),
    item("volley", "A volleyball", 270, 0.04, "indoor"), item("cricketb", "A cricket ball", 160, 0.03, "men's"), item("baseball", "A baseball", 145, 0.03, "MLB"),
    item("tennis", "A tennis ball", 58, 0.03, "standard"), item("golfb", "A golf ball", 45.9, 0.01, "the heaviest allowed"),
    item("shuttle", "A badminton shuttlecock", 5.1, 0.08, "feather"), item("pingpong", "A table tennis ball", 2.7, 0.01, "standard"),
]

# ------------------------------------------------------------------ food
KCAL = [
    item("oil", "Olive oil", 884, 0.02, "per 100 g"), item("butter", "Butter", 717, 0.03, "per 100 g"), item("pb_f", "Peanut butter", 588, 0.04, "per 100 g"),
    item("milkchoc", "Milk chocolate", 535, 0.04, "per 100 g"), item("cheddar", "Cheddar cheese", 403, 0.03, "per 100 g"), item("honey", "Honey", 304, 0.03, "per 100 g"),
    item("bread", "White bread", 265, 0.06, "per 100 g"), item("salmon", "Salmon", 208, 0.08, "per 100 g"), item("avocado", "Avocado", 160, 0.06, "per 100 g"),
    item("rice", "Cooked white rice", 130, 0.06, "per 100 g"), item("banana", "Banana", 89, 0.06, "per 100 g"), item("milk", "Whole milk", 61, 0.05, "per 100 ml"),
    item("apple", "Apple", 52, 0.08, "per 100 g"), item("cola", "Coca-Cola", 42, 0.03, "per 100 ml"), item("carrot", "Carrot", 41, 0.08, "per 100 g"),
    item("broccoli", "Broccoli", 34, 0.08, "per 100 g"), item("cucumber", "Cucumber", 15, 0.1, "per 100 g"),
]
CHILLI = [item(i, n, (lo + hi) / 2, 0, "chilli", lo=lo, hi=hi, sn=sn) for i, n, sn, lo, hi in [
    ("bell", "Bell pepper", "bell pepper", 0, 0), ("pepperoncini", "Pepperoncini", "pepperoncini", 100, 500),
    ("poblano", "Poblano", "poblano", 1000, 1500), ("jalapeno", "Jalapeño", "jalapeño", 2500, 8000),
    ("serrano", "Serrano", "serrano", 10000, 23000), ("cayenne", "Cayenne", "cayenne", 30000, 50000),
    ("birdseye", "Thai bird's eye chilli", "Thai bird's eye", 50000, 100000), ("habanero", "Habanero", "habanero", 100000, 350000),
    ("ghost", "Ghost pepper", "ghost pepper", 855000, 1041427), ("reaper", "Carolina Reaper", "Carolina Reaper", 1400000, 2200000),
    ("pepperx", "Pepper X", "Pepper X", 2693000, 2693000)]]
CAFFEINE = [
    item("coffee", "A mug of filter coffee", 95, 0.3, "hot drink"), item("espresso", "A single espresso", 63, 0.3, "hot drink"),
    item("tea", "A cup of tea", 47, 0.3, "hot drink"), item("redbull", "A can of Red Bull", 80, 0.02, "250 ml"),
    item("monster", "A can of Monster", 160, 0.03, "500 ml"), item("cokecan", "A can of Coca-Cola", 33, 0.06, "330 ml"),
    item("dietcoke", "A can of Diet Coke", 44, 0.06, "330 ml"),
]

# ------------------------------------------------------------------ distances from London (computed)
CITIES = [("Paris", "France", 48.857, 2.352), ("Rome", "Italy", 41.903, 12.496), ("Madrid", "Spain", 40.417, -3.704),
          ("Barcelona", "Spain", 41.385, 2.173), ("Lisbon", "Portugal", 38.722, -9.139), ("Berlin", "Germany", 52.520, 13.405),
          ("Amsterdam", "Netherlands", 52.370, 4.895), ("Dublin", "Ireland", 53.350, -6.260), ("Edinburgh", "Scotland", 55.953, -3.188),
          ("Reykjavik", "Iceland", 64.146, -21.942), ("Oslo", "Norway", 59.914, 10.752), ("Stockholm", "Sweden", 59.329, 18.069),
          ("Helsinki", "Finland", 60.170, 24.938), ("Warsaw", "Poland", 52.230, 21.012), ("Vienna", "Austria", 48.208, 16.373),
          ("Athens", "Greece", 37.984, 23.728), ("Istanbul", "Turkey", 41.008, 28.978), ("Moscow", "Russia", 55.756, 37.617),
          ("Cairo", "Egypt", 30.044, 31.236), ("Marrakesh", "Morocco", 31.629, -7.981), ("Tenerife", "Canary Islands, Spain", 28.464, -16.252),
          ("Lagos", "Nigeria", 6.524, 3.379), ("Nairobi", "Kenya", -1.292, 36.822), ("Cape Town", "South Africa", -33.925, 18.424),
          ("Dubai", "United Arab Emirates", 25.205, 55.271), ("Mumbai", "India", 19.076, 72.878), ("Delhi", "India", 28.614, 77.209),
          ("Bangkok", "Thailand", 13.756, 100.502), ("Singapore", "Singapore", 1.352, 103.820), ("Hong Kong", "China", 22.320, 114.170),
          ("Beijing", "China", 39.904, 116.407), ("Tokyo", "Japan", 35.676, 139.650), ("Sydney", "Australia", -33.869, 151.209),
          ("Auckland", "New Zealand", -36.848, 174.763), ("Honolulu", "Hawaii, USA", 21.307, -157.858), ("Anchorage", "Alaska, USA", 61.218, -149.900),
          ("Los Angeles", "USA", 34.052, -118.244), ("New York", "USA", 40.713, -74.006), ("Toronto", "Canada", 43.653, -79.383),
          ("Mexico City", "Mexico", 19.433, -99.133), ("Rio de Janeiro", "Brazil", -22.907, -43.173), ("Buenos Aires", "Argentina", -34.604, -58.382),
          ("Lima", "Peru", -12.046, -77.043)]


def gc(lat1, lon1, lat2, lon2):
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


DIST = [item("city:" + n, n, gc(51.507, -0.128, la, lo), 0.02, d) for n, d, la, lo in CITIES]

# ------------------------------------------------------------------ Premier League seasons (from the match data)
pl = json.load(open(PL_JSON))
seasons = collections.Counter(r[0] for s, v in pl.items() if s <= "2025-26" for r in v["table"])
SHORT = {"Brighton & Hove Albion": "Brighton", "Wolverhampton Wanderers": "Wolves", "West Bromwich Albion": "West Brom",
         "Tottenham Hotspur": "Tottenham", "Queens Park Rangers": "QPR", "Bournemouth": "Bournemouth"}
PLS = [item("club:" + c, SHORT.get(c, c), n, 0, "football club") for c, n in seasons.items() if n >= 5]

# ------------------------------------------------------------------ measures
M = {
    "height": dict(group="Height", q="Which is taller?", items=HEIGHT, fmt=f_height, mode="ratio", max=6, more="taller", as_="as tall", n=88),
    "area": dict(group="Area", q="Which covers a bigger area?", items=country_area + AREA_EXTRA, fmt=f_area, mode="ratio", max=4, more="bigger", as_="as big", n=88),
    "population": dict(group="Population", q="Which has more people?", items=country_pop + POP_EXTRA, fmt=f_pop, mode="ratio", min=1.12, max=3, more="more people", as_="as many people", n=88),
    "length": dict(group="Length", q="Which is longer?", items=LENGTH, fmt=f_len, mode="ratio", max=5, more="longer", as_="as long", n=66),
    "weight": dict(group="Weight", q="Which is heavier?", items=WEIGHT, fmt=f_weight, mode="ratio", max=8, more="heavier", as_="as heavy", n=60),
    "speed": dict(group="Speed", q="Which is faster?", items=SPEED, fmt=f_speed, mode="ratio", max=6, more="faster", as_="as fast", n=70),
    "lifespan": dict(group="Lifespan", q="Which can live longer?", items=LIFE, fmt=f_life, mode="ratio", max=8, more="longer", as_="as long", n=30),
    "dates": dict(group="Dates", q="Which came first?", items=DATES, fmt=f_year, mode="year", max=2.5, n=113),
    "numbers": dict(group="Numbers", q="Which number is bigger?", items=NUMBERS, fmt=f_num, mode="diff", max=2.5, unit="", n=112),
    "diameter": dict(group="Space", t="Size", q="Which is wider across?", items=DIAM, fmt=f_km_across, mode="ratio", max=6, more="wider", as_="as wide", n=25),
    "spin": dict(group="Space", t="Spin", q="Which takes longer to spin round once?", items=SPIN, fmt=f_spin, mode="ratio", max=30, more="longer", as_="as long", n=15),
    "gravity": dict(group="Space", t="Gravity", q="Where would you weigh more?", items=GRAV, fmt=f_grav, mode="ratio", max=8, more="stronger gravity", as_="as strong", n=12),
    "heat": dict(group="Heat", q="Which is hotter?", items=HEAT, fmt=f_temp, mode="kelvin", max=8, unit=" °C", more="hotter", n=40),
    "protons": dict(group="Science", t="Atoms", q="Which element has more protons in each atom?", items=PROTONS, fmt=f_protons, mode="diff", maxdiff=40, unit=" protons", n=20),
    "density": dict(group="Science", t="Density", q="Which is denser (heavier for its size)?", items=DENSITY, fmt=f_density, mode="ratio", max=10, more="denser", as_="as dense", n=18),
    "melting": dict(group="Science", t="Melting point", q="Which melts at a higher temperature?", items=MELT, fmt=f_temp, mode="kelvin", max=5, unit=" °C", more="higher", n=17),
    "stadium": dict(group="Sport", t="Venues", q="Which holds more people?", items=STADIUM, fmt=f_seats, mode="ratio", max=3, more="bigger", as_="as many", n=30),
    "ball": dict(group="Sport", t="Balls", q="Which is heavier?", items=BALLS, fmt=f_grams, mode="ratio", max=6, more="heavier", as_="as heavy", n=15),
    "plseasons": dict(group="Sport", t="Premier League", q="Up to 2025–26, which club has played more Premier League seasons?", items=PLS, fmt=f_seasons, mode="diff", max=3, unit=" seasons", n=15),
    "calories": dict(group="Food", t="Calories", q="Gram for gram, which has more calories?", items=KCAL, fmt=f_kcal, mode="ratio", max=4, more="more calories", as_="as many calories", n=18),
    "chilli": dict(group="Food", t="Chilli heat", q="Which chilli is hotter?", items=CHILLI, fmt=f_scoville, mode="range", n=12),
    "caffeine": dict(group="Food", t="Caffeine", q="Which has more caffeine?", items=CAFFEINE, fmt=f_mg, mode="ratio", max=6, more="more caffeine", as_="as much caffeine", n=8),
    "distance": dict(group="Distance", q="As the crow flies, which is further from London?", items=DIST, fmt=f_dist, mode="ratio", max=2.5, more="further", as_="as far", n=40),
}

# pairs worth having in the bank every time: the surprising ones
MUST = {
    "height": [("olympusmons", "everest"), ("bennevis", "burj"), ("angelfalls", "burj"), ("eiffel", "shard"), ("hyperion", "bigben"),
               ("giraffe", "wadlow"), ("snowdon", "scafell"), ("pisa", "nelson")],
    "area": [("d:sahara", "c:AUS"), ("k:asia", "s:moon"), ("s:moon", "k:africa"), ("c:RUS", "d:antarctica"), ("c:RUS", "k:europe"), ("u:texas", "c:FRA"),
             ("c:ISL", "i:ireland"), ("c:LUX", "u:london"), ("i:greenland", "c:MEX"), ("i:honshu", "i:gb")],
    "population": [("p:london", "p:sco"), ("p:tex", "c:AUS"), ("p:nyc", "c:IRL")],
    "length": [("chunnel", "marathon"), ("m6", "thames"), ("tube", "thames"), ("seikan", "chunnel"), ("greatwall", "transsib"), ("danyang", "hadrian")],
    "speed": [("grizzly_s", "bolt"), ("wind", "peregrine"), ("cricket", "cheetah"), ("concorde", "sound")],
    "weight": [("argentino", "humpback"), ("piano", "lion"), ("car", "horse")],
    "lifespan": [("greenland", "bowhead"), ("queenant", "dogl")],
    "dates": [("oxford", "aztec"), ("nintendo", "titanic"), ("pyramidb", "mammoth"), ("fax", "phone"), ("lighter", "match"), ("vending", "press"),
              ("queen", "sliced"), ("balloon", "bicycle"), ("tube_d", "bulb"), ("coke", "eiffel_d"), ("harvard", "fire"), ("tetris", "web"),
              ("sharks", "trees"), ("dinos", "flowers"), ("stego", "trex_d"), ("rubik", "pacman")],
    "numbers": [("bones", "un"), ("mile", "day"), ("cards", "states"), ("pianokeys", "chess"), ("pokedex", "elements"), ("180", "week"), ("scrabble", "bones"),
                ("un", "147"), ("300", "bones")],
    "diameter": [("ganymede", "mercury"), ("titan", "mercury"), ("ozwidth", "themoon"), ("europa", "pluto")],
    "spin": [("venus_r", "mercury_r")],
    "gravity": [("saturn_g", "earth_g"), ("neptune_g", "saturn_g")],
    "heat": [("lightning", "sunsurface"), ("venus_t", "mercury_t")],
    "density": [("au", "pb"), ("hg", "pb"), ("water", "ice")],
    "melting": [("fe_m", "au_m")],
    "protons": [("pe:Pb", "pe:Au"), ("pe:K", "pe:Na")],
    "caffeine": [("dietcoke", "cokecan")],
    "calories": [("oil", "butter"), ("apple", "cola"), ("avocado", "banana")],
    "stadium": [("molineux", "hawthorns"), ("o2", "centre")],
    "ball": [("cricketb", "baseball"), ("tennis", "golfb")],
}
# a line of extra colour for some pairs (keyed by the winner, then the loser)
NOTES = {
    ("pyramidb", "mammoth"): "Woolly mammoths were still alive on a remote Arctic island when the Great Pyramid was built.",
    ("oxford", "aztec"): "Oxford was already teaching students more than 300 years before the Aztec Empire began.",
    ("nintendo", "titanic"): "Nintendo started out in 1889 making playing cards, 23 years before the Titanic sank.",
    ("fax", "phone"): "Alexander Bain patented a fax machine in 1843, 33 years before the telephone.",
    ("lighter", "match"): "Johann Döbereiner made a lighter in 1823. John Walker's friction match came in 1826.",
    ("queen", "sliced"): "The Queen was born in 1926. Sliced bread first went on sale in 1928.",
    ("vending", "press"): "Hero of Alexandria built a coin machine that gave out holy water, nearly 1,400 years before the printing press.",
    ("stego", "trex_d"): "T. rex lived closer in time to us than to Stegosaurus.",
    ("sharks", "trees"): "Sharks have been around for about 450 million years, longer than trees.",
    ("d:sahara", "c:AUS"): "The Sahara is bigger than the whole of Australia.",
    ("k:asia", "s:moon"): "Asia is bigger than the entire surface of the Moon. Africa isn't.",
    ("s:moon", "k:africa"): "The Moon's surface is bigger than Africa, but smaller than Asia.",
    ("ozwidth", "themoon"): "Australia is about 4,000 km wide. The Moon is 3,474 km across.",
    ("ganymede", "mercury"): "Jupiter's moon Ganymede is bigger than the planet Mercury.",
    ("titan", "mercury"): "Saturn's moon Titan is bigger than the planet Mercury.",
    ("venus_t", "mercury_t"): "Venus is further from the Sun than Mercury, but its thick clouds trap the heat.",
    ("lightning", "sunsurface"): "A lightning bolt heats the air to about five times hotter than the surface of the Sun.",
    ("hg", "pb"): "Mercury is so dense that a lump of lead floats on it.",
    ("water", "ice"): "Ice is less dense than water, which is why ice cubes float.",
    ("au", "pb"): "Gold is about 70% denser than lead.",
    ("dietcoke", "cokecan"): "Diet Coke has more caffeine than regular Coca-Cola.",
    ("grizzly_s", "bolt"): "A grizzly bear can outrun Usain Bolt.",
    ("wind", "peregrine"): "A 408 km/h gust hit Barrow Island in Australia during Cyclone Olivia in 1996.",
    ("olympusmons", "everest"): "Olympus Mons on Mars is about two and a half times as tall as Everest.",
    ("bennevis", "burj"): "Ben Nevis is over 500 m taller than the Burj Khalifa.",
    ("angelfalls", "burj"): "Angel Falls drops 979 m, further than the height of the Burj Khalifa.",
    ("hyperion", "bigben"): "The tallest tree in the world is taller than Big Ben's tower.",
    ("seikan", "chunnel"): "The Channel Tunnel has the longest stretch under the sea, but the Seikan Tunnel is longer overall.",
    ("chunnel", "marathon"): "The Channel Tunnel is about 8 km longer than a marathon.",
    ("m6", "thames"): "The M6 is a little longer than the River Thames.",
    ("c:RUS", "k:europe"): "Russia is bigger than the whole of Europe.",
    ("c:ISL", "i:ireland"): "Iceland is bigger than the whole island of Ireland.",
    ("c:LUX", "u:london"): "Luxembourg is bigger than Greater London.",
    ("p:london", "p:sco"): "London has more people than the whole of Scotland.",
    ("p:tex", "c:AUS"): "Texas has more people than the whole of Australia.",
    ("bones", "un"): "206 bones in you, 193 countries in the UN.",
    ("cricketb", "baseball"): "A cricket ball weighs about 156 to 163 g, a baseball about 142 to 149 g.",
    ("molineux", "hawthorns"): "Molineux holds about 5,000 more than The Hawthorns.",
    ("apple", "cola"): "An apple has more calories than the same amount of Coca-Cola.",
    ("oil", "butter"): "Butter is about 80% fat. Olive oil is pure fat.",
}
SPECIAL = [
    {"c": "height", "ks": ["everest", "mariana"], "k": "special:mariana", "q": "Which is bigger?",
     "a": "The depth of the Mariana Trench", "o": ["The height of Mount Everest"],
     "v": {"The depth of the Mariana Trench": "about 10,935 m", "The height of Mount Everest": "8,849 m"},
     "d": {"The depth of the Mariana Trench": "the deepest point in the ocean", "The height of Mount Everest": "the highest point on land"},
     "x": "You could drop Everest into the Mariana Trench and there would still be about 2 km of water above it."},
    {"c": "spin", "ks": ["venusday"], "k": "special:venus", "q": "On Venus, which is longer?",
     "a": "A day (one full spin)", "o": ["A year (once round the Sun)"],
     "v": {"A day (one full spin)": "243 Earth days", "A year (once round the Sun)": "225 Earth days"},
     "d": {"A day (one full spin)": "Venus spins very slowly", "A year (once round the Sun)": "its trip round the Sun"},
     "x": "Venus takes longer to spin round once than to go round the Sun."},
    {"c": "length", "ks": ["thames", "severn"], "k": "special:severn", "q": "Which is the UK's longest river?",
     "a": "The River Severn", "o": ["The River Thames"],
     "v": {"The River Severn": "about 354 km", "The River Thames": "about 346 km"},
     "d": {"The River Severn": "Wales and England", "The River Thames": "England"},
     "x": "The Severn is the UK's longest river. The Thames is the longest river entirely in England."},
]


# ------------------------------------------------------------------ pairing
def ok_pair(m, a, b, must=False):
    """Return (big, small) if the pair is safe and interesting, else None. Hand-picked pairs may be lopsided."""
    mode = m["mode"]
    if mode == "range":
        big, small = (a, b) if a["lo"] > b["lo"] else (b, a)
        if not big["lo"] > small["hi"]:
            return None
        order = [x["id"] for x in sorted(m["items"], key=lambda x: x["lo"])]
        if abs(order.index(big["id"]) - order.index(small["id"])) > 3:
            return None
        return big, small
    if mode == "year":
        if a["val"] == b["val"]:
            return None
        first, later = (a, b) if a["val"] < b["val"] else (b, a)
        gap = later["val"] - first["val"]
        if gap < first["fuzz"] + later["fuzz"] + 2:
            return None
        ago_f, ago_l = 2026 - first["val"], 2026 - later["val"]
        if ago_f / ago_l > m["max"] and not must:
            return None
        return first, later
    if a["val"] == b["val"]:
        return None
    big, small = (a, b) if a["val"] > b["val"] else (b, a)
    if mode == "kelvin":
        kb, ks = big["val"] + 273.15, small["val"] + 273.15
        if big["val"] - small["val"] < big["fuzz"] * abs(big["val"]) + small["fuzz"] * abs(small["val"]) + 5:
            return None
        if kb / ks > m["max"]:
            return None
        return big, small
    if mode == "diff":
        d = big["val"] - small["val"]
        if d < big["fuzz"] * big["val"] + small["fuzz"] * small["val"] + 1:
            return None
        if "maxdiff" in m and d > m["maxdiff"]:
            return None
        if "max" in m and big["val"] / max(small["val"], 1e-9) > m["max"]:
            return None
        return big, small
    r = big["val"] / small["val"]
    need = max(m.get("min", 1.0), (1 + big["fuzz"]) * (1 + small["fuzz"]) * 1.03)
    if r < need or r > m["max"]:
        return None
    return big, small


def ratio_line(m, big, small):
    r = big["val"] / small["val"]
    exact = big["fuzz"] == 0 and small["fuzz"] == 0
    pre = "" if exact else "About "
    if r >= 1.95:
        n = f"{r:.1f}".rstrip("0").rstrip(".") if r < 10 else f"{round(r)}"
        s = f"{pre}twice {m['as_']}." if n == "2" else f"{pre}{n} times {m['as_']}."
    else:
        s = f"{pre}{round((r - 1) * 100)}% {m['more']}."
    return s[0].upper() + s[1:]


def explain(m, big, small):
    mode = m["mode"]
    if mode == "range":
        return f"Even the mildest {big['sn']} is hotter than the hottest {small['sn']}."
    if mode == "year":
        gap = small["val"] - big["val"]
        fz = big["fuzz"] or small["fuzz"]
        if gap >= 1e6:
            return f"About {comma(gap / 1e6)} million years earlier."
        if gap >= 1000 and fz:
            return f"About {comma(round(gap, -2))} years earlier."
        return f"{'About ' if fz else ''}{comma(gap)} years earlier."
    if mode == "kelvin":
        d = big["val"] - small["val"]
        fz = max(big["fuzz"], small["fuzz"]) >= 0.04
        rd = round(d, -3 if d >= 10000 else (-1 if fz and d >= 200 else 0))
        if d >= 1e6:
            return f"About {comma(d / 1e6)} million degrees {m['more']}."
        return neg(f"{'About ' if fz else ''}{comma(rd)} °C {m['more']}.")
    if mode == "diff":
        d = big["val"] - small["val"]
        fz = big["fuzz"] or small["fuzz"]
        return f"{'About ' if fz else ''}{comma(d)} more{m['unit']}."
    return ratio_line(m, big, small)


def make_q(key, m, big, small):
    fmt = m["fmt"]
    q = {"c": key, "k": f"{key}:{big['id']}|{small['id']}", "ks": [big["id"], small["id"]], "q": m["q"],
         "a": big["name"], "o": [small["name"]],
         "v": {big["name"]: fmt(big), small["name"]: fmt(small)}}
    d = {x["name"]: x["desc"] for x in (big, small) if x.get("desc")}
    if d:
        q["d"] = d
    if m.get("t"):
        q["t"] = m["t"]
    q["x"] = NOTES.get((big["id"], small["id"])) or explain(m, big, small)
    return q


bank, seen = [], set()
for s in SPECIAL:
    seen.add(s["k"])
    s["t"] = M[s["c"]].get("t")
    if not s["t"]:
        del s["t"]
    bank.append(s)

counts = collections.Counter(s["c"] for s in SPECIAL)
pools = {}
for key, m in M.items():
    items = m["items"]
    ids = {x["id"]: x for x in items}
    assert len(ids) == len(items), key
    names = collections.Counter(x["name"] for x in items)
    assert all(v == 1 for v in names.values()), (key, [n for n, v in names.items() if v > 1])
    cands = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            p = ok_pair(m, items[i], items[j])
            if p:
                cands.append(p)
    rng.shuffle(cands)
    must = []
    for a_id, b_id in MUST.get(key, []):
        a, b = ids[a_id], ids[b_id]
        p = ok_pair(m, a, b, must=True)
        if not p or p[0]["id"] != a_id:
            sys.exit(f"MUST pair rejected or wrong way round: {key} {a_id} vs {b_id} -> {p and p[0]['id']}")
        must.append(p)
    pools[key] = (must, cands)

use = collections.Counter()


def take(key, n, cap):
    m = M[key]
    must, cands = pools[key]
    got = 0
    for big, small in must + cands:
        if got >= n:
            break
        k = f"{key}:{big['id']}|{small['id']}"
        if k in seen:
            continue
        is_must = (big, small) in must
        if not is_must and (use[(key, big["id"])] >= cap or use[(key, small["id"])] >= cap):
            continue
        seen.add(k)
        use[(key, big["id"])] += 1
        use[(key, small["id"])] += 1
        bank.append(make_q(key, m, big, small))
        got += 1
    return got


for key, m in M.items():
    want = m["n"] - counts[key]
    n_items = len(m["items"])
    cap = max(2, math.ceil(2.2 * m["n"] / n_items))
    got = 0
    while got < want and cap < 60:
        got += take(key, want - got, cap)
        cap += 1
    counts[key] += got
    if got < want:
        print(f"short: {key} {got}/{want} (pool {len(pools[key][1])})", file=sys.stderr)

# top up to exactly 1,000 from the biggest pools
top = ["numbers", "dates", "population", "area", "height", "speed", "length"]
i = 0
while len(bank) < 1000:
    key = top[i % len(top)]
    if take(key, 1, 60):
        counts[key] += 1
    i += 1
    if i > 5000:
        sys.exit("could not reach 1,000")
bank = bank[:1000]

# sanity checks
for q in bank:
    assert q["a"] != q["o"][0], q
    assert set(q["v"]) == {q["a"], q["o"][0]}, q
assert len({q["k"] for q in bank}) == len(bank)
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
groups = collections.Counter(M[q["c"]]["group"] for q in bank)
print(len(bank), dict(groups))
print(dict(counts))
