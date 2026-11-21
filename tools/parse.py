import sys, json
import xml.etree.ElementTree as ET
src, out = sys.argv[1], sys.argv[2]
cards = []
for ev, el in ET.iterparse(src, events=("end",)):
    if el.tag != "Entity":
        continue
    c = {"id": el.get("CardID"), "dbf": int(el.get("ID")), "tags": {}, "refs": []}
    for t in el.findall("Tag"):
        name = t.get("name")
        if not name or name.lstrip("-").isdigit(): name = "E" + t.get("enumID")
        typ = t.get("type")
        if typ == "LocString":
            e = t.find("enUS")
            c[name] = e.text if e is not None else None
        elif typ == "String":
            c[name] = t.text
        else:
            v = t.get("value")
            c["tags"][name] = int(v) if v and v.lstrip("-").isdigit() else v
    for r in el.findall("ReferencedTag"):
        c["refs"].append(r.get("name") or r.get("enumID"))
    mp = el.find("MasterPower")
    if mp is not None: c["masterPower"] = mp.text
    cards.append(c)
    el.clear()
json.dump(cards, open(out, "w"))
print(len(cards))
