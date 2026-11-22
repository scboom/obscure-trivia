"""Turn Fortnite Wiki pages into structured data: seasons, named locations per season, live events.
Usage: fn_extract.py WIKI_DIR OUT.json
"""
import sys, re, json

WIKI, OUT = sys.argv[1:3]
read = lambda n: open(f"{WIKI}/{n}.txt", encoding="utf-8").read()


def plain(s):
    """Wiki markup to plain text."""
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\{\{(?:Mythic|Legendary|Epic|Rare)\}\}", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<br\s*/?>|<hr\s*/?>", " / ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" /")


# ------------------------------------------------------------------ seasons
seasons = []
for tab in re.split(r"\n\|-\|", read("seasonlist")):
    m = re.match(r"(Chapter \d+)=", tab.strip("<tabber>\n"))
    if not m:
        continue
    chapter = int(m.group(1).split()[1])
    for row in tab.split("\n|-\n")[1:]:
        cells = [c for c in row.split("\n|") if c.strip()]
        cells = [c.lstrip("|") for c in cells]
        if len(cells) < 4:
            continue
        head = cells[0]
        link = re.search(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]", re.sub(r"\[\[File:[^\]]*\]\]", "", head))
        sub = re.search(r"<small>(.*?)</small>", head)
        dur = plain(cells[2])
        dates = [d.strip() for d in re.split(r"\s*/\s*—\s*/\s*|\s+—\s+", dur) if d.strip() and d.strip() != "—"]
        seasons.append({"chapter": chapter, "page": link.group(1) if link else "", "label": (link.group(2) or link.group(1)) if link else "",
                        "subtitle": plain(sub.group(1)) if sub else "", "theme": plain(cells[1]), "start": dates[0] if dates else "",
                        "end": dates[-1] if len(dates) > 1 else "", "additions": plain(cells[3].split("\n|}")[0])})

# ------------------------------------------------------------------ named locations, one table per island
named = read("named")
br = named.split("===[[Fortnite OG]]===")[0]
islands = {}
for tab in re.split(r"\n\|-\||\n(?=[A-Z][A-Za-z ]+=\n)", br):
    m = re.match(r"\s*([A-Za-z' ]+)=\n", tab)
    if not m or "{|" not in tab:
        continue
    name = m.group(1).strip()
    table = tab[tab.index("{|"):]
    cols = re.findall(r"!\[\[([^|\]]+)\|([^\]]+)\]\]", table.split("\n|-\n|")[0] if "\n|-\n|" in table else table)
    rows = table.split("\n|-\n")[2:]
    locs = []
    for row in rows:
        lines = [l for l in row.split("\n") if l.startswith("|") and not l.startswith("|}")]
        if not lines:
            continue
        nm = re.search(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", lines[0])
        marks = ["✓" in l for l in lines[2:2 + len(cols)]]
        note = plain(lines[2 + len(cols)].lstrip("|")) if len(lines) > 2 + len(cols) else ""
        if nm and len(marks) == len(cols):
            locs.append({"name": nm.group(1).strip(), "present": [c[0] for c, p in zip(cols, marks) if p], "note": note})
    islands[name] = {"seasons": [c[0] for c in cols], "locations": locs}

# ------------------------------------------------------------------ live events (Battle Royale)
events = []
for tab in re.split(r"\n\|-\|", read("eventsbr")):
    m = re.match(r"(?:<tabber>\n)?\|?-?\|?(Chapter \d+)=", tab.strip())
    chap = re.search(r"Chapter (\d+)", tab[:40])
    if not chap:
        continue
    for row in tab.split("\n|-\n")[1:]:
        lines = [l for l in row.split("\n") if l.strip()]
        if len(lines) < 4 or not lines[0].startswith("!"):
            continue
        title = plain(re.sub(r"\[\[File:[^\]]*\]\]", "", lines[0].lstrip("!")))
        when = lines[1].lstrip("|")
        season = plain(when.split("<hr")[0])
        date = plain(when.split("<hr />")[-1]) if "<hr" in when else ""
        events.append({"chapter": int(chap.group(1)), "name": title, "season": season, "date": date,
                       "location": plain(lines[2].lstrip("|")), "summary": plain(lines[3].lstrip("|")),
                       "type": plain(lines[4].lstrip("|")) if len(lines) > 4 else ""})

json.dump({"seasons": seasons, "islands": islands, "events": events}, open(OUT, "w"), indent=1, ensure_ascii=False)
print(len(seasons), "seasons;", {k: len(v["locations"]) for k, v in islands.items()}, ";", len(events), "events")
