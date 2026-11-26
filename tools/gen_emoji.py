"""Build the Emoji Puzzle bank (exactly 1,000 puzzles) from emoji/work/puzzles.json.

Every clue is checked again: emoji only (no letters, digits, flags, keycaps or letter symbols), from Emoji 13.0 or earlier so it
shows on older phones and computers, 2 to 7 emojis long. Each category is then filled to its target, keeping the mix of
easy, medium and hard.
Usage: gen_emoji.py SCRATCH_DIR OUT.json [--avail|--loose]
"""
import sys, json, random, re, collections, os

D, OUT = sys.argv[1:3]
sys.path.insert(0, f"{D}/emoji/pkg")
import emoji          # the emoji package (installed into emoji/pkg): Unicode's emoji list with the version each one arrived in

rng = random.Random(20261126)
QTEXT = {"Films": "Which film is this?", "Animated films": "Which animated film is this?", "TV shows": "Which TV show is this?",
         "Video games": "Which video game is this?", "Songs": "Which song is this?", "Books": "Which book is this?", "Places": "Which place is this?",
         "Food & drink": "Which food or drink is this?", "Sport": "Which sport or sporting thing is this?", "Sayings": "Which saying is this?",
         "Heroes & characters": "Which character is this?", "Brands & apps": "Which brand or app is this?"}
TARGET = {"Films": 205, "Animated films": 85, "TV shows": 85, "Video games": 115, "Songs": 85, "Books": 40, "Places": 85, "Food & drink": 65,
          "Sport": 40, "Sayings": 85, "Heroes & characters": 60, "Brands & apps": 50}
assert sum(TARGET.values()) == 1000


def clue_ok(clue):
    """emoji only, Emoji 13.0 or earlier, no flags / keycaps / letter symbols; returns the number of emojis or 0"""
    if any(c.isascii() for c in clue):
        return 0
    found = emoji.emoji_list(clue)
    if "".join(e["emoji"] for e in found) != clue:
        return 0
    for e in found:
        ch = e["emoji"]
        data = emoji.EMOJI_DATA.get(ch) or emoji.EMOJI_DATA.get(ch.replace("️", "")) or emoji.EMOJI_DATA.get(ch + "️")
        base = re.sub("[\U0001F3FB-\U0001F3FF]", "", ch)                # skin tones
        data = data or emoji.EMOJI_DATA.get(base) or emoji.EMOJI_DATA.get(base.replace("️", ""))
        if not data or data["E"] > 13:
            return 0
        if any(0x1F1E6 <= ord(c) <= 0x1F1FF for c in ch) or "⃣" in ch:       # flags and keycaps
            return 0
        if any(0x1F170 <= ord(c) <= 0x1F251 for c in ch) or ch.strip("️") in ("ℹ", "Ⓜ", "™", "©", "®"):   # letter symbols
            return 0
    return len(found)


P = json.load(open(f"{D}/emoji/work/puzzles.json"))
by = collections.defaultdict(list)
bad = collections.Counter()
seen = set()
for p in P:
    n = clue_ok(p["clue"])
    if p["cat"] not in QTEXT:
        bad["category"] += 1; continue
    if not 2 <= n <= 7:
        bad["clue"] += 1; continue
    if p["a"] in p["o"] or len(set(p["o"])) != 3 or p["a"].lower() in seen:
        bad["options"] += 1; continue
    if any(re.search("[–—]", s) for s in [p["a"], *p["o"], p.get("x", "")]):
        bad["dash"] += 1; continue
    seen.add(p["a"].lower())
    q = {"c": re.sub(r"[^a-z]+", "", p["cat"].lower())[:12], "k": "emoji:" + p["a"], "q": QTEXT[p["cat"]] + "\n" + p["clue"], "a": p["a"], "o": p["o"],
         "x": p.get("x", ""), "lv": p.get("level", 2)}
    if max(len(s) for s in [p["a"]] + p["o"]) > 26:
        q["r"] = 1
    by[p["cat"]].append(q)
print(f"{sum(len(v) for v in by.values())} puzzles kept;", dict(bad) or "none dropped")
if "--avail" in sys.argv:
    for c in TARGET:
        print(f"{c:20} {len(by[c]):4} / {TARGET[c]}   levels " + str(dict(collections.Counter(q['lv'] for q in by[c]))))
    sys.exit()
out = []
for c, want in TARGET.items():
    lst = by[c]
    rng.shuffle(lst)
    lst.sort(key=lambda q: 0 if q["lv"] == 1 else 1 if q["lv"] == 2 else 2 if rng.random() < 0.85 else 1)
    # keep the easy and medium ones, then hard ones up to the target, in a random order
    got = lst[:want]
    print(f"{c:20} {len(got)}/{want}")
    assert len(got) == want or "--loose" in sys.argv, c
    out += got
for q in out:
    q.pop("lv", None)
groups = {re.sub(r"[^a-z]+", "", c.lower())[:12]: c for c in TARGET}
json.dump(out, open(OUT, "w"), indent=0, ensure_ascii=False)
json.dump(groups, open(os.path.join(os.path.dirname(OUT) or ".", "emoji_groups.json"), "w"), ensure_ascii=False)
print(len(out), "puzzles")
