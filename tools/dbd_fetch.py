"""Fetch rendered character pages from the Dead by Daylight Wiki (wiki.gg). Usage: dbd_fetch.py DT.json OUT_DIR"""
import sys, json, os, time, urllib.request, urllib.parse
DT, OUT = sys.argv[1:3]
d = json.load(open(DT))
os.makedirs(OUT, exist_ok=True)
API = "https://deadbydaylight.wiki.gg/api.php"
names = [("K", k["id"], "The " + k["name"]) for k in d["killers"]] + [("S", s["id"], s.get("shortName") or s["name"]) for s in d["survivors"]]
names += [("X", 0, t) for t in sys.argv[3:]]
for kind, i, title in names:
    f = os.path.join(OUT, f"{kind}{i:02d}_{title.replace(' ', '_').replace('/', '_')}.json")
    if os.path.exists(f):
        continue
    q = urllib.parse.urlencode({"action": "parse", "page": title, "redirects": 1, "prop": "text|displaytitle", "format": "json"})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "obscure-trivia-builder/1.0"})
    for attempt in range(3):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=60))
            break
        except Exception as e:
            print("retry", title, e); time.sleep(3)
    if "parse" not in data:
        print("MISSING", title, data.get("error", {}).get("info"))
        continue
    json.dump(data, open(f, "w"))
    print(kind, i, title, "->", data["parse"]["title"], len(data["parse"]["text"]["*"]))
    time.sleep(0.7)
