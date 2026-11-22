"""Hay Day crops, trees, bushes, animals and machines from the Hay Day Wiki. Usage: rg_hayday.py DIR names.txt OUT.json"""
import sys, re, json
D, NAMES, OUT = sys.argv[1:4]
out = {}
for n in open(NAMES).read().split("\n"):
    try:
        d = json.load(open(f"{D}/{n.replace(' ', '_').replace('/', '_')}.json"))
    except Exception:
        continue
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    m = re.search(r"\{\{Infobox(.*?)\n\}\}", w, re.S)
    box = {}
    if m:
        for k, v in re.findall(r"\|\s*(\w+)\s*=\s*([^\n]*)", m.group(1)):
            box[k.strip()] = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", re.sub(r"\{\{[^}]*\}\}", "", v)).strip()
    prods = []
    pm = re.search(r"\{\{Building Products\s*\n?(.*?)\}\}", w, re.S)
    if pm:
        parts = [p.strip() for p in pm.group(1).split("|")]
        parts = [p for p in parts if p != ""] if False else parts[1:] if parts and parts[0] == "" else parts
        for i in range(0, len(parts) - 2, 4):
            if parts[i] and not parts[i].isdigit():
                prods.append({"name": parts[i], "level": parts[i + 1], "time": parts[i + 2]})
    intro = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", re.sub(r"\{\{[^}]*\}\}|\[\[File:[^\]]*\]\]|'{2,}", "", w))
    first = next((l.strip() for l in intro.split("\n") if len(l.strip()) > 40 and not l.startswith(("|", "{", "=", "!"))), "")
    out[n] = {"kind": box.get("title", ""), "level": box.get("level", ""), "time": box.get("time", ""), "price": box.get("price", ""), "products": prods, "intro": first}
json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
for n, v in out.items():
    print(f"{n:22} {v['kind'][:16]:16} lvl {v['level']:4} t {v['time'][:10]:10} p {v['price'][:10]:10} prods {[p['name'] for p in v['products']][:6]} | {v['intro'][:70]}")
