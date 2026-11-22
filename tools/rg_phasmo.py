"""Phasmophobia ghosts from the Phasmophobia Wiki: evidence, strengths, weaknesses, journal quotes. Usage: rg_phasmo.py DIR OUT.json"""
import sys, re, json, glob
D, OUT = sys.argv[1:3]
EV = {"EMF": "EMF Level 5", "Spirit Box": "Spirit Box", "Ultraviolet": "Ultraviolet (fingerprints)", "Fingerprint": "Ultraviolet (fingerprints)",
      "Ghost Orb": "Ghost Orbs", "Ghost Writing": "Ghost Writing", "Freezing": "Freezing Temperatures", "D.O.T.S": "D.O.T.S. Projector"}


def plain(s):
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}|<[^>]+>|'{2,}", "", s)
    return re.sub(r"\s+", " ", s).strip(" *")


ghosts = {}
for f in glob.glob(D + "/*.json"):
    d = json.load(open(f))
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    box = w[:w.find("}}\n")] if "}}\n" in w else w[:3000]
    ev = []
    for m in re.finditer(r"\|\s*Evidence\d\s*=\s*([^\n|]*\|[^\n]*)", box):
        link = re.search(r"(?:link|alt)=([^\]|]+)", m.group(1))
        name = next((v for k, v in EV.items() if link and k.lower() in link.group(1).lower()), None)
        if name and name not in ev:
            ev.append(name)
    def fld(k):
        m = re.search(r"\|\s*" + k + r"\s*=(.*?)(?=\n\s*\|[A-Za-z]|\}\}\n|$)", box, re.S)
        return [plain(x) for x in re.split(r"\n\*|^\s*\*", m.group(1).strip()) if plain(x)] if m else []
    q = re.search(r"\{\{Quote\s*\|\s*quote\s*=\s*(.*?)\n", w)
    ghosts[d["parse"]["title"]] = {"evidence": ev, "strength": fld(r"strength(?:s|\(s\))?"), "weakness": fld(r"weakness(?:es|\(es\))?"),
                                   "ability": fld(r"abilit(?:y|ies|i\(es\))"), "quote": plain(q.group(1)) if q else ""}
json.dump(ghosts, open(OUT, "w"), indent=1, ensure_ascii=False)
for n, g in sorted(ghosts.items()):
    print(f"{n:12} {g['evidence']} | S: {g['strength'][:1]} | W: {g['weakness'][:1]}")
