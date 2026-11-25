"""Perks page -> [{name, side, desc, quote, author, who}]. Usage: dbd_perks.py PERKS.html OUT.json"""
import sys, json, re
from bs4 import BeautifulSoup
s = BeautifulSoup(open(sys.argv[1]).read(), "lxml")
out = []
for h in s.find_all("h3"):
    t = h.get_text(" ", strip=True)
    side = "S" if t.startswith("Survivor Perks") else "K" if t.startswith("Killer Perks") else None
    if not side:
        continue
    for r in h.find_next("table").find_all("tr")[1:]:
        cells = r.find_all(["th", "td"], recursive=False)
        if len(cells) < 4:
            continue
        name = cells[1].get_text(" ", strip=True)
        d = cells[2]
        for bad in d.select(".mw-editsection, sup, style"):
            bad.decompose()
        notes = [x.get_text(" ", strip=True) for x in d.select(".formattedPerkDesc .patchNote, .descNote")]
        text = re.sub(r"\s+", " ", d.get_text(" ", strip=True)).replace(" .", ".").replace(" ,", ",").replace(" :", ":").replace("( ", "(").replace(" )", ")")
        text = re.sub(r"This description is based on the changes announced for or featured in the upcoming Patch [\d.]+ ?", "", text)
        quote, author = "", ""
        m = re.search(r'["“]([^"”]{8,})["”](?:\s*[—–-]\s*([^"“”]+))?\s*$', text)
        if m:
            quote, author = m.group(1).strip(), (m.group(2) or "").strip()
            text = text[:m.start()].strip()
        out.append({"name": name, "side": side, "desc": text, "quote": quote, "author": author, "who": cells[3].get_text(" ", strip=True)})
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print(len(out), sum(1 for p in out if p["quote"]), "with quotes", sum(1 for p in out if p["author"]), "with author")
for p in out[:3] + out[200:202]:
    print(p)
