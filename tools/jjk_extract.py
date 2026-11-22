"""Turn Jujutsu Kaisen Wiki episode pages into structured data.
Usage: jjk_extract.py EP_DIR OUT.json
"""
import sys, re, json, glob

EP, OUT = sys.argv[1:3]


def plain(s):
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\{\{Sub\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\{\{Nihongo\|([^|}]*)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<br\s*/?>", " / ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" /")


def field(w, name):
    m = re.search(r"^\|\s*" + name + r"\s*=\s*(.*)$", w, re.M)
    return m.group(1).strip() if m else ""


def section(w, title):
    m = re.search(r"^==\s*" + re.escape(title) + r"\s*==\s*$(.*?)(?=^==[^=])", w, re.M | re.S)
    return m.group(1) if m else ""


eps = []
for f in glob.glob(EP + "/Episode_*.json"):
    d = json.load(open(f))
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    chars = []
    for line in section(w, "Characters in Order of Appearance").split("\n"):
        m = re.match(r"\*\s*\[\[([^|\]]+)(?:\|[^\]]*)?\]\]\s*(.*)", line.strip())
        if m:
            chars.append({"name": m.group(1).strip(), "note": plain(m.group(2)).strip("() ")})
    battles = [plain(l.lstrip("* ")) for l in section(w, "Battles & Events").split("\n") if l.strip().startswith("*")]
    tech, who = {}, None
    for line in section(w, "Jujutsu").split("\n"):
        m = re.search(r"\[\[:Category:([^|\]]+?) (?:Techniques|Abilities)\|", line)
        if m:
            who = m.group(1).strip(); tech.setdefault(who, []); continue
        if line.strip() and not line.strip().startswith("*"):   # any other heading (e.g. "Shikigami") has no owner
            who = None; continue
        m = re.match(r"(\*+)\s*(.*)", line.strip())
        if m and who:
            names = re.findall(r"\[\[([^|\]]+)(?:\|[^\]]*)?\]\]", m.group(2))
            if names:
                tech[who].append({"depth": len(m.group(1)), "name": " ".join(names) if len(names) > 1 else names[0], "parts": names})
    eps.append({
        "n": int(field(w, "ep number") or 0), "season": int(field(w, "season number") or 0), "title": plain(field(w, "ep title")),
        "romaji": plain(field(w, "romaji")), "aired": field(w, "jp air date"), "adapted": plain(field(w, "adapted from")),
        "arc": [plain(a) for a in re.split(r"<br\s*/?>", field(w, "arc")) if plain(a)],
        "op": plain(field(w, "opening song")), "ed": plain(field(w, "ending song")),
        "new": [plain(x) for x in re.findall(r"\[\[[^\]]+\]\]", field(w, "new character"))],
        "chars": chars, "battles": battles, "tech": tech})
eps.sort(key=lambda e: e["n"])
first = {}
for i, e in enumerate([e for e in eps if e["season"] == 1] + [e for e in eps if e["season"] > 1]):
    pass
for e in eps:   # number within the season
    e["sn"] = e["n"] - min(x["n"] for x in eps if x["season"] == e["season"]) + 1
json.dump({"episodes": eps}, open(OUT, "w"), indent=1, ensure_ascii=False)
print(len(eps), "episodes;", {s: sum(1 for e in eps if e["season"] == s) for s in (1, 2, 3)})
for e in (eps[0], eps[29], eps[-1]):
    print(e["season"], e["sn"], e["title"], e["aired"], e["arc"], e["op"], "/", e["ed"], "| new:", e["new"], "| battles:", e["battles"][:3], "| tech:", {k: [t["name"] for t in v][:4] for k, v in list(e["tech"].items())[:3]})
