"""Bee Swarm Simulator bees and fields from the Bee Swarm Simulator Wiki. Usage: rg_bss.py DIR names.txt OUT.json"""
import sys, re, json
D, NAMES, OUT = sys.argv[1:4]
bees, fields, other = {}, {}, {}
for n in open(NAMES).read().split("\n"):
    try:
        d = json.load(open(f"{D}/{n.replace(' ', '_').replace('/', '_')}.json"))
    except Exception:
        continue
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    get = lambda k, box: (m.group(1).strip() if (m := re.search(r"\|\s*" + k + r"\s*=\s*([^\n|]*)", box)) else "")
    if (m := re.search(r"\{\{Bee\s*\n(.*?)\n\}\}", w, re.S)):
        box = m.group(1)
        treat = re.search(r"favou?rite treat is \{\{Cost\|([^|}]+)", w)
        likes = re.search(r"likes the (.*?)\. ", w)
        bees[n] = {"color": get("color", box), "rarity": get("rarity", box), "desc": re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", get("description", box)),
                   "energy": get("energy", box), "speed": get("speed", box), "attack": get("attack", box), "treat": treat.group(1).strip() if treat else ""}
    elif (m := re.search(r"\{\{Field\s*(.*?)\}\}", w, re.S)):
        box = "|" + m.group(1).replace("\n", "")
        fields[n] = {"color": get("fieldcolor", box), "bees": get("bees", box), "nectar": get("nectar", box)}
json.dump({"bees": bees, "fields": fields}, open(OUT, "w"), indent=1, ensure_ascii=False)
import collections
print(len(bees), "bees", collections.Counter(b["rarity"] for b in bees.values()), collections.Counter(b["color"] for b in bees.values()))
for n, b in list(bees.items())[:60]: print(f"  {n:16} {b['rarity']:10} {b['color']:10} treat {b['treat']:16} | {b['desc'][:60]}")
print(len(fields), "fields"); [print(f"  {n:22} {f}") for n, f in fields.items()]
