"""Character pages -> intro text and section texts. Usage: dbd_pages.py PAGES_DIR OUT.json"""
import sys, json, os, re
from bs4 import BeautifulSoup
D, OUT = sys.argv[1:3]
out = {}
for f in sorted(os.listdir(D)):
    data = json.load(open(os.path.join(D, f)))
    s = BeautifulSoup(data["parse"]["text"]["*"], "lxml")
    root = s.find(class_="mw-parser-output") or s
    for bad in root.select("table, .toc, .mw-editsection, style, script, .reference, sup, figure, .gallery, .thumb"):
        bad.decompose()
    sections, cur, title = {}, [], "intro"
    for el in root.find_all(["h2", "h3", "h4", "p", "ul", "ol", "dl", "blockquote"], recursive=True):
        if el.find_parent(["ul", "ol", "dl", "blockquote"]) and el.name not in ("h2", "h3", "h4"):
            continue
        if el.name in ("h2", "h3", "h4"):
            sections.setdefault(title, []).extend(cur)
            cur, title = [], el.get_text(" ", strip=True)
            continue
        t = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        if t:
            cur.append(t)
    sections.setdefault(title, []).extend(cur)
    out[f[:-5]] = {"title": data["parse"]["title"], "sections": {k: "\n".join(v) for k, v in sections.items() if v}}
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
for k, v in list(out.items())[:3] + list(out.items())[44:46]:
    print(k, {s: len(t) for s, t in v["sections"].items()})
    print("   ", v["sections"].get("intro", "")[:500])
