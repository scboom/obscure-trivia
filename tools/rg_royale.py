"""Clash Royale cards from the Clash Royale Wiki infoboxes. Usage: rg_royale.py DIR names.txt OUT.json"""
import sys, re, json
D, NAMES, OUT = sys.argv[1:4]
cards = {}
for n in open(NAMES).read().split("\n"):
    f = f"{D}/{n.replace(' ', '_').replace('/', '_')}.json"
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    m = re.search(r"\{\{Card Infobox\|([^}]*)\}\}", w)
    if not m:
        continue
    box = dict(re.findall(r"(\w+)\s*=\s*([^|]*)", m.group(1)))
    q = re.search(r"\{\{Quote\|(.*?)\}\}", w)
    cost = box.get("Cost", "").strip()
    if not cost.isdigit():
        continue
    cards[n] = {"cost": int(cost), "rarity": box.get("Rarity", "").strip(), "type": box.get("Type", "").strip(), "arena": box.get("Arena", "").strip(),
                "released": box.get("ReleaseDate", "").strip(), "quote": re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", q.group(1)).strip() if q else ""}
json.dump(cards, open(OUT, "w"), indent=1, ensure_ascii=False)
import collections
print(len(cards), collections.Counter(c["rarity"] for c in cards.values()), collections.Counter(c["type"] for c in cards.values()))
print(collections.Counter(c["arena"] for c in cards.values()).most_common(30))
for n in ("Hog Rider", "Three Musketeers", "Mirror", "Goblin Barrel", "The Log", "Mega Knight", "Archer Queen", "Golem", "Skeletons"):
    print(n, cards.get(n))
