"""Clash Royale Wiki pages -> structured card data.
Usage: cr_extract.py PAGES_DIR OUT.json
Reads every current card page plus its /Evolution and /Hero subpages and the Arenas page.
"""
import sys, re, json, os

D, OUT = sys.argv[1:3]


def wt(name):
    f = f"{D}/{name.replace(' ', '_').replace('/', '_')}.json"
    if not os.path.exists(f):
        return None
    d = json.load(open(f))
    return d["parse"]["wikitext"]["*"] if "parse" in d else None


def plain(s):
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\{\{Rarity\|([^}|]*)\}\}", r"\1", s)
    s = re.sub(r"\{\{Icon\|[^}]*\}\}", "", s)
    s = re.sub(r"\{\{Dps\|[^}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<br\s*/?\s*>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def infobox(w):
    m = re.search(r"\{\{((?:Evolved |Heroic )?Card[ _]Infobox)\|(.*?)\}\}\s*(?:\n|\{\{|$)", w, re.S)
    if not m:
        return None
    body = m.group(2)
    return {k.strip(): v.strip() for k, v in re.findall(r"(\w+)\s*=\s*((?:[^|{}]|\{\{[^}]*\}\})*)", body)}


def first_quote(w):
    q = re.search(r"\{\{Quote\|(.*?)\}\}", w, re.S)
    return plain(q.group(1)) if q else ""


def tables(w):
    """Attribute tables in the statistics block: [(headers, first data row)]."""
    stop = len(w)
    for mark in ("{{StatisticsSubheader|Card Mastery}}", "==History==", "==Gallery=="):
        i = w.find(mark)
        if i >= 0:
            stop = min(stop, i)
    start = w.find("{{Statistics")
    if start < 0:
        start = w.find('id="unit-attributes-table"')
    if start < 0:
        return []
    seg = w[start:stop]
    out = []
    for m in re.finditer(r"\{\|(.*?)\n\|\}", seg, re.S):
        t = m.group(1)
        rows = re.split(r"\n\|-[^\n]*\n", t)
        hdr = [plain(re.sub(r"^.*?\|(?!\|)", "", h, count=1) if re.match(r"\s*(scope|style|width)", h) else h)
               for h in re.findall(r"^!(.*)$", rows[0], re.M)]
        hdr = [plain(re.sub(r'^\s*(?:scope="col"\s*)?(?:style="[^"]*"\s*)?(?:width="[^"]*"\s*)?\|', "", h)) for h in re.findall(r"^!(.*)$", rows[0], re.M)]
        if len(rows) < 2 or not hdr:
            continue
        data = rows[1]
        data = "\n".join(l for l in data.split("\n") if not l.startswith("!"))
        cells = [plain(c) for c in re.split(r"\|\||\n\|", "\n" + data.strip())][1:]
        cells = [c for c in cells]
        if "Level" in hdr[0] or hdr[0].startswith("Type"):
            continue
        out.append((hdr, cells))
    return out


def vars_(w):
    return {k: v.strip() for k, v in re.findall(r"\{\{#vardefine:\s*(\w+)\s*\|\s*([^}]*?)\s*\}\}", w)}


def ability(w):
    m = re.search(r"==\s*Ability:\s*([^=]+?)\s*==\s*\n?\s*\{\{Quote\|(.*?)\}\}", w, re.S)
    return {"name": plain(m.group(1)), "desc": plain(m.group(2))} if m else None


def history(w):
    """The page's History bullets, oldest first, as plain text."""
    i = w.find("==History==")
    if i < 0:
        return []
    j = w.find("\n==", i + 5)
    return [plain(l.lstrip("* ")) for l in w[i:j if j > 0 else None].split("\n") if l.startswith("*")]


def intro(w):
    """The page's first prose paragraph (after the infobox and quote)."""
    body = re.sub(r"\{\{[^{}]*\}\}", "", w.split("==")[0])
    body = re.sub(r"\{\{[^{}]*\}\}", "", body)
    paras = [plain(p) for p in body.split("\n") if len(plain(p)) > 80]
    return paras[0] if paras else ""


cards = {}
names = [l for l in open(f"{D}/../pages.txt").read().split("\n") if l and "/" not in l]
for n in names:
    w = wt(n)
    if not w:
        continue
    box = infobox(w)
    if not box or "Rarity" not in box:
        continue
    c = {"name": n, "cost": box.get("Cost", ""), "abilityCost": box.get("AbilityCost", ""), "rarity": box.get("Rarity", ""),
         "type": box.get("Type", ""), "arena": box.get("Arena", ""), "released": box.get("ReleaseDate", ""),
         "quote": first_quote(w), "intro": intro(w), "history": history(w), "tables": tables(w), "vars": vars_(w), "ability": ability(w)}
    for sub, key in (("Evolution", "evo"), ("Hero", "hero")):
        sw = wt(f"{n}/{sub}")
        if sw:
            sb = infobox(sw) or {}
            c[key] = {"cycles": sb.get("CycleCost", ""), "released": sb.get("ReleaseDate", ""), "abilityCost": sb.get("AbilityCost", ""),
                      "quote": first_quote(sw), "intro": intro(sw), "ability": ability(sw), "tables": tables(sw)}
    cards[n] = c

# arenas
w = wt("Arenas")
arenas = []
for m in re.finditer(r"<br>\s*([^<>\[\]]+?)\s*\(Arena (\d+)\)\s*<br>\s*([\d,]+)-([\d,]+)\s*\{\{Icon\|I=Trophy\}\}(.*?)\n\|", w, re.S):
    arenas.append({"n": int(m.group(2)), "name": m.group(1).strip(), "lo": int(m.group(3).replace(",", "")), "hi": int(m.group(4).replace(",", "")),
                   "cards": re.findall(r"Name=([^|}]+)", m.group(5))})
late = re.search(r"added four Arenas: (.*?) at ([\d,]+), ([\d,]+), ([\d,]+), and ([\d,]+)", w)
names29 = re.findall(r"([A-Z][^,()]+?) \(Season", late.group(1))
for i, nm in enumerate(names29):
    lo = int(late.group(2 + i).replace(",", ""))
    if not any(a["n"] == 29 + i for a in arenas):
        arenas.append({"n": 29 + i, "name": nm.replace("’", "'").strip(), "lo": lo, "hi": lo + 500, "cards": []})
tc = re.search(r"Training Camp \(Tutorial\)(.*?)\n", w).group(1)
arenas.insert(0, {"n": 0, "name": "Training Camp", "lo": 0, "hi": 0, "cards": re.findall(r"Name=([^|}]+)", tc)})

def listing(page, first_ability_cell):
    """'List of Evolutions' / 'List of Heroes' tables: card, cost, cycles or ability cost, ability name and text."""
    w = wt(page)
    out = {}
    t = w[w.index("{|", w.index("==List of")):]
    t = t[:t.index("\n|}")]
    for row in re.split(r"\n\|-\n", t)[1:]:
        cells = [c.strip() for c in re.split(r"\n\|", "\n" + row.strip())[1:]]
        name = re.search(r"\[\[[^|\]]*\|([^\]]+)\]\]", cells[0]).group(1).strip()
        ab = re.search(r"'''([^']+)'''\s*-?\s*(.*)", "\n".join(cells[first_ability_cell:]), re.S)
        out[name] = {"cost": plain(cells[1]), "n": plain(cells[2]), "total": plain(cells[3]),
                     "boost": plain(cells[4]) if first_ability_cell == 5 else "",
                     "ability": plain(ab.group(1)).strip(" -") if ab else "", "desc": plain(ab.group(2)) if ab else ""}
    return out


evolist = listing("Card Evolution", 5)
herolist = listing("Heroes", 4)

json.dump({"cards": cards, "arenas": arenas, "evolist": evolist, "herolist": herolist}, open(OUT, "w"), indent=1, ensure_ascii=False)

import collections
print(len(cards), "cards", collections.Counter(c["rarity"] for c in cards.values()), collections.Counter(c["type"] for c in cards.values()))
print(sum("evo" in c for c in cards.values()), "evos;", sum("hero" in c for c in cards.values()), "heroes;", len(arenas), "arenas")
print([(a["n"], a["name"], a["lo"]) for a in arenas][-6:])
for k, v in list(evolist.items()) + list(herolist.items()):
    print(k, v["cost"], v["n"], v["total"], "|", v["boost"], "|", v["ability"], "|", v["desc"][:90])
