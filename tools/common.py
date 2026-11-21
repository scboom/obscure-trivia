import json, re
def load(p):
    cards = json.load(open(p))
    return cards, {c["dbf"]: c for c in cards}, {c["id"]: c for c in cards}

PLURAL = re.compile(r"(\d+)(\s*)\|4\(([^,()]*),([^()]*)\)")
def clean_text(c, keep_bold=True):
    t = c.get("CARDTEXT")
    if not t: return None
    t = t.split("@")[0]
    tg = c["tags"]
    for i in range(1, 6):
        v = tg.get("TAG_SCRIPT_DATA_NUM_%d" % i)
        if v is not None:
            # numeric placeholders only: "+{0}", "{0} damage", "({0})" etc. Race/card ids are not numbers.
            if v > 40: return None
            t = t.replace("{%d}" % (i - 1), str(v))
    # remove italic counters like <i>(3 turns left!)</i> that still carry placeholders
    t = re.sub(r"<i>\(.*?\)</i>", lambda m: "" if re.search(r"left|\{|\|4|/\d|\d/", m.group(0)) else m.group(0), t)
    t = re.sub(r"\([^)]*\{\d\}[^)]*\)", "", t)
    t = PLURAL.sub(lambda m: m.group(1) + m.group(2) + (m.group(3) if m.group(1) == "1" else m.group(4)), t)
    t = t.replace("[x]", "").replace("_", " ").replace("\n", " ")
    t = re.sub(r"\$(\d+)", r"\1", t)
    t = re.sub(r"#(\d+)", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,:!?])", r"\1", t)
    t = t.replace("<b> ", " <b>").replace(" </b>", "</b> ")
    # flatten nested bold tags
    out, depth = [], 0
    for part in re.split(r"(</?b>)", t):
        if part == "<b>":
            depth += 1
            if depth == 1: out.append(part)
        elif part == "</b>":
            if depth == 1: out.append(part)
            depth = max(0, depth - 1)
        else:
            out.append(part)
    t = "".join(out).replace("<b></b>", "")
    if not keep_bold:
        t = re.sub(r"</?[bi]>", "", t)
    if re.search(r"[{}|@$#]|<(?!/?[bi]>)", t): return None
    if len(re.sub(r"<[^>]+>", "", t)) < 8: return None
    return t
