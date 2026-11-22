"""Character facts from Jujutsu Kaisen Wiki pages: voices, birthday, height, anime debut.
Usage: jjk_chars.py CHAR_DIR data.json  (adds "characters" to data.json)
"""
import sys, re, json, glob
CD, DATA = sys.argv[1:3]
data = json.load(open(DATA))


def plain(s):
    s = re.sub(r"\{\{Ref[^}]*\}\}", "", s)
    s = re.sub(r"\{\{Sub\|([^}]*)\}\}", r"(\1)", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"<br\s*/?>", " / ", s)
    s = re.sub(r"<[^>]+>|'{2,}", "", s)
    return re.sub(r"\s+", " ", s).strip(" /")


chars = {}
for f in glob.glob(CD + "/*.json"):
    d = json.load(open(f))
    if "error" in d:
        continue
    w = d["parse"]["wikitext"]["*"]
    i = w.find("_Infobox"); i = w.find("Infobox") if i < 0 else i
    box = w[i:w.find("\n}}", i)] if i >= 0 else ""
    def get(k):
        m = re.search(r"^\|\s*" + k + r"\s*=\s*(.*)$", box, re.M)
        if not m:
            return ""
        v = m.group(1)
        while re.search(r"\{\{[^{}]*\}\}", v):            # drop references and other templates, innermost first
            v = re.sub(r"\{\{(?:[Rr]ef|cite)[^{}]*\}\}", "", v)
            v = re.sub(r"\{\{Sub\|([^{}]*)\}\}", r"(\1)", v)
            v = re.sub(r"\{\{(?![Rr]ef|cite|Sub)[^{}]*\}\}", "", v)
        v = re.split(r"\|\s*[a-z ]+\s*=", v)[0]                # an empty field can run into the next one
        return re.sub(r"\{\{.*|\}\}", "", v).strip()
    name = plain(get("name")) or d["parse"]["title"]
    chars[d["parse"]["title"]] = {
        "name": name, "kanji": plain(get("kanji")), "birthday": plain(get("birthday")), "height": plain(get("height")),
        "gender": plain(get("gender")), "debutanime": plain(get("debutanime")), "jp": plain(get("voice")), "en": plain(get("eng voice")),
        "race": plain(get("race")), "alias": plain(get("alias"))}
    for k, f in (("jp", "voice"), ("en", "eng voice")):   # some pages keep the voices outside the first infobox
        if not chars[d["parse"]["title"]][k] and (m := re.search(r"^\|\s*" + f + r"\s*=\s*(.+)$", w, re.M)):
            chars[d["parse"]["title"]][k] = plain(re.sub(r"\{\{[^{}]*\}\}", "", m.group(1)))
data["characters"] = chars
json.dump(data, open(DATA, "w"), indent=1, ensure_ascii=False)
print(len(chars), "characters")
for n in ("Satoru Gojo", "Yuji Itadori", "Kirara Hoshi", "Kinji Hakari", "Sukuna", "Hiromi Higuruma", "Choso"):
    print(n, chars.get(n))
