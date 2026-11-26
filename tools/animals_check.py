"""Check each animal's class against the taxonomy box of its English Wikipedia article, and read its IUCN status there.
Usage: animals_check.py ANIMALS.txt CACHE_DIR OUT.json"""
import sys, json, time, os, re, urllib.request, urllib.parse
from bs4 import BeautifulSoup
SRC, CACHE, OUT = sys.argv[1:4]
TEXTS = sys.argv[4] if len(sys.argv) > 4 else None       # plain-text pages already saved (they keep the taxonomy box text)
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "obscure-trivia-builder/1.0 (quiz data)"}
TAXA = {"mammal": ["Mammalia"], "bird": ["Aves"], "reptile": ["Reptilia", "Testudines", "Squamata", "Crocodilia", "Rhynchocephalia"],
        "amphibian": ["Amphibia"], "fish": ["Actinopterygii", "Chondrichthyes"], "insect": ["Insecta"], "arachnid": ["Arachnida"],
        "crustacean": ["Crustacea", "Malacostraca", "Isopoda"], "mollusc": ["Mollusca"]}
STATUSES = ["Least Concern", "Near Threatened", "Vulnerable", "Critically Endangered", "Endangered", "Extinct in the Wild", "Data Deficient", "Domesticated"]


def lead(title):
    f = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", title) + ".json")
    if not os.path.exists(f):
        q = urllib.parse.urlencode({"title": title, "action": "render"})
        d = None
        for a in range(10):
            try:
                r = urllib.request.urlopen(urllib.request.Request(f"https://en.wikipedia.org/w/index.php?{q}", headers=UA), timeout=60)
                html = r.read().decode("utf-8")
                d = {"parse": {"title": title, "text": {"*": html}}}; break
            except Exception as e:
                print("retry", title, e, flush=True); time.sleep(15 + 10 * a)
        if d is None:
            print("gave up at", title, flush=True)
            return {}
        json.dump(d, open(f, "w")); time.sleep(1.2)
    return json.load(open(f))


out, bad = [], 0
for line in open(SRC, encoding="utf-8").read().splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    name, title, cls, diet, flies, lives = line.split("|")
    tf = os.path.join(TEXTS, title.replace(" ", "_") + ".txt") if TEXTS else None
    cached = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", title) + ".json")
    if tf and os.path.exists(tf) and not os.path.exists(cached) and "Scientific classification" in open(tf).read():
        raw = open(tf).read()
        i = raw.find("Scientific classification")
        text = re.sub(r"\s+", " ", raw[max(0, i - 400):i + 900]) if i >= 0 else ""
        real_title = title
    else:
        d = lead(title)
        if "parse" not in d:
            print("NOT FOUND", title); bad += 1; continue
        s = BeautifulSoup(d["parse"]["text"]["*"], "lxml")
        box = s.select_one("table.infobox.biota") or s.select_one("table.infobox")
        text = re.sub(r"\s+", " ", box.get_text(" ", strip=True)) if box else ""
        real_title = d["parse"]["title"]
    ok = any(re.search(rf"\b{t}\b", text) for t in TAXA[cls])
    others = [c for c, ts in TAXA.items() if c != cls and any(re.search(rf"\b{t}\b", text) for t in ts) and not (cls == "reptile" and c == "bird")]
    status = next((st for st in STATUSES if st in text.split("Scientific classification")[0]), None)
    if not ok or others:
        bad += 1; print("CLASS?", name, "we say", cls, "| box mentions", others, "|", text[:160])
    out.append({"name": name, "title": real_title, "class": cls, "diet": diet, "flies": flies, "lives": lives, "status": status})
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(out), "animals,", bad, "problems;", sum(1 for x in out if x["status"] and x["status"] != "Domesticated"), "with an IUCN status")
