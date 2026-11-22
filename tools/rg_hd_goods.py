"""Hay Day goods (level, price, time, ingredients, source) from the wiki's Goods List. Usage: rg_hd_goods.py Goods_List.json OUT.json"""
import sys, re, json
SRC, OUT = sys.argv[1:3]
w = json.load(open(SRC))["parse"]["wikitext"]["*"]
lk = lambda s: re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
goods = {}
for tbl in re.findall(r"\{\|(.*?)\n\|\}", w, re.S):
    for row in tbl.split("\n|-")[1:]:
        cells = re.split(r"\n\|(?!-)", "\n" + row.strip("\n"))[1:]
        if len(cells) < 7:
            continue
        name = lk(re.sub(r"<br\s*/?>.*", "", cells[0])).strip(" '")
        needs = [(lk(m.group(1)).strip(), int(m.group(2))) for m in re.finditer(r"(\[\[[^\]]+\]\])(?:&nbsp;|\s)*\((\d+)\)", cells[5])]
        src = lk(cells[6]).strip()
        goods[name] = {"level": re.sub(r"\D", "", cells[1].split("<")[0]) or None, "price": cells[2].strip(), "time": lk(re.sub(r"<br\s*/?>.*", "", cells[3], flags=re.S)).strip(),
                       "needs": needs, "source": re.sub(r"\s*\(.*", "", src), "source_note": src}
json.dump(goods, open(OUT, "w"), indent=1, ensure_ascii=False)
import collections
print(len(goods)); print(collections.Counter(g["source"] for g in goods.values()).most_common(25))
for n in ("Wheat", "Corn", "Carrot", "Egg", "Bacon", "Bread", "Popcorn", "Cheese", "Wool", "Apple", "Honey"):
    print(n, goods.get(n))
