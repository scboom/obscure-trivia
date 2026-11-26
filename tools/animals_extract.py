"""Wikipedia tables -> animal names and national animals.
Usage: animals_extract.py RAW_DIR OUT.json
"""
import sys, json, re
from bs4 import BeautifulSoup
RAW, OUT = sys.argv[1:3]


def soup(p):
    return BeautifulSoup(json.load(open(f"{RAW}/{p}.json"))["parse"]["text"]["*"], "lxml")


def terms(cell):
    """A table cell -> list of names (refs and notes dropped)."""
    for bad in cell.select("sup, .reference, style"):
        bad.decompose()
    for br in cell.find_all("br"):
        br.replace_with("\n")
    t = cell.get_text("")
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"—?\s*N/?A\b", "", t, flags=re.I)
    t = re.sub(r"\([^)]*\)", "", t)
    out = []
    for part in re.split(r"[\n,;/]| or ", t):
        p = re.sub(r"\([^)]*\)", "", part).strip(" . ")
        p = re.sub(r"\s+", " ", p)
        if p and not re.match(r"^(—|-)?\s*N/?a$", p, re.I) and p not in ("—", "-"):
            out.append(p)
    return out


s = soup("List_of_animal_names")
names = []
tab = s.find_all("table", class_="wikitable")[1]
for r in tab.find_all("tr")[1:]:
    cells = r.find_all(["td", "th"])
    if len(cells) < 6:
        continue
    animal = re.sub(r"\[[^\]]*\]", "", cells[0].get_text(" ", strip=True)).strip()
    names.append({"animal": animal, "young": terms(cells[1]), "female": terms(cells[2]), "male": terms(cells[3]),
                  "group": terms(cells[4]), "adjective": terms(cells[5])})

# national animals: the table uses rowspans for countries with several animals
s = soup("List_of_national_animals")
tab = s.find("table", class_="wikitable")
rows, carry = [], {}
for r in tab.find_all("tr")[1:]:
    cells = r.find_all(["td", "th"])
    vals, col, it = [], 0, iter(cells)
    cur = []
    c = 0
    while c < 5:
        if c in carry and carry[c][1] > 0:
            cur.append(carry[c][0]); carry[c] = (carry[c][0], carry[c][1] - 1); c += 1; continue
        try:
            cell = next(it)
        except StopIteration:
            break
        span = int(cell.get("rowspan", 1))
        txt = re.sub(r"\[[^\]]*\]", "", cell.get_text(" ", strip=True)).strip()
        if span > 1:
            carry[c] = (txt, span - 1)
        cur.append(txt); c += 1
    if len(cur) >= 3:
        rows.append({"country": cur[0], "animal": cur[1], "sci": cur[2]})
json.dump({"names": names, "national": rows}, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(names), "animals with names,", len(rows), "national animal rows")
for n in names[:5] + names[60:63]:
    print(n)
for r in rows[:6]:
    print(r)
