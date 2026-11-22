"""Clash of Clans Home Village troops, spells, heroes, sieges and pets from the Clash of Clans Wiki. Usage: rg_coc.py DIR names.txt OUT.json"""
import sys, re, json
D, NAMES, OUT = sys.argv[1:4]


def plain(s):
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\{\{(?:H|Res)\|[^|}]*\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}|<[^>]+>|'{2,}|&nbsp;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


units = {}
for n in open(NAMES).read().split("\n"):
    try:
        d = json.load(open(f"{D}/{n.replace(' ', '_').replace('/', '_')}.json"))
    except Exception:
        continue
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    stats = {}
    for tbl in re.findall(r"\{\|(.*?)\n\|\}", w, re.S):
        if not re.search(r"Level Required|Housing Space", tbl):
            continue
        heads = [plain(h) for h in re.findall(r"^!(.*)$", tbl, re.M)]
        rows = tbl.split("\n|-")
        vals = None
        for r in rows:
            cells = [plain(c) for c in re.findall(r"^\|(?!-)(.*)$", r, re.M)]
            if len(cells) >= len(heads) - 1 and cells:
                vals = cells; break
        if heads and vals:
            stats = {h: v for h, v in zip(heads, vals)}
            break
    q = re.search(r"'''''\"(.+?)\"'''''", w)
    kind = ("hero" if re.search(r"Town Hall Level Required|Hero Hall Level Required", " ".join(stats)) else
            "siege" if "Workshop" in " ".join(stats) else "pet" if "Pet House" in " ".join(stats) else
            "spell" if "Spell Factory" in " ".join(stats) else "troop" if "Barracks" in " ".join(stats) else "")
    units[n] = {"kind": kind, "stats": stats, "quote": plain(q.group(1)) if q else "", "dark": "Dark" in " ".join(stats)}
json.dump(units, open(OUT, "w"), indent=1, ensure_ascii=False)
import collections
print(collections.Counter(u["kind"] for u in units.values()))
for n, u in units.items():
    if u["kind"]:
        print(f"{n:22} {u['kind']:6} {dict(list(u['stats'].items())[:8])}")
