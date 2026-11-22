import re, os, sys, json, collections
D = sys.argv[1]
LINE = re.compile(r"^\s*(?:\d{1,2}[.:]\d{2}\s+)?(?P<h>[A-Za-z0-9&'.\- ]+?)\s{2,}(?P<hg>\d+)-(?P<ag>\d+)(?:\s*\(\d+-\d+\))?\s{2,}(?P<a>[A-Za-z0-9&'.\- ]+?)\s*$")
VLINE = re.compile(r"^\s*(?:\d{1,2}[.:]\d{2}\s+)?(?P<h>[A-Za-z0-9&'.\- ]+?)\s+v\s+(?P<a>[A-Za-z0-9&'.\- ]+?)\s{2,}(?P<hg>\d+)-(?P<ag>\d+)(?:\s*\(\d+-\d+\))?\s*$")
def norm(t):
    t = re.sub(r"^AFC ", "", t.strip())
    t = re.sub(r"\s+(A?FC)$", "", t)
    return {"Wolves": "Wolverhampton Wanderers", "Brighton": "Brighton & Hove Albion", "Spurs": "Tottenham Hotspur", "Man City": "Manchester City",
            "Man United": "Manchester United", "Newcastle": "Newcastle United", "West Ham": "West Ham United", "Leeds": "Leeds United",
            "Nottm Forest": "Nottingham Forest", "Nott'm Forest": "Nottingham Forest", "Sheffield Utd": "Sheffield United", "Leicester": "Leicester City",
            "Tottenham": "Tottenham Hotspur", "Ipswich": "Ipswich Town", "Luton": "Luton Town", "Norwich": "Norwich City", "Cardiff": "Cardiff City",
            "Hull": "Hull City", "Swansea": "Swansea City", "Stoke": "Stoke City", "Wigan": "Wigan Athletic", "Bolton": "Bolton Wanderers",
            "Blackburn": "Blackburn Rovers", "Birmingham": "Birmingham City", "QPR": "Queens Park Rangers", "West Brom": "West Bromwich Albion",
            "Burnley": "Burnley", "Sunderland": "Sunderland", "Leeds Utd": "Leeds United", "Bradford": "Bradford City", "Coventry": "Coventry City",
            "Derby": "Derby County", "Newcastle Utd": "Newcastle United", "Sheffield Wed": "Sheffield Wednesday"}.get(t, t)
out = {}
for f in sorted(os.listdir(D)):
    season = f[:-4]
    teams = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0])   # P W D L GF GA
    n = 0
    for line in open(os.path.join(D, f), encoding="utf-8"):
        m = VLINE.match(line.rstrip("\n")) or LINE.match(line.rstrip("\n"))
        if not m:
            continue
        h, a, hg, ag = norm(m["h"]), norm(m["a"]), int(m["hg"]), int(m["ag"])
        n += 1
        for t, gf, ga in ((h, hg, ag), (a, ag, hg)):
            r = teams[t]; r[0] += 1; r[4] += gf; r[5] += ga
            r[1 if gf > ga else 2 if gf == ga else 3] += 1
    table = sorted(teams.items(), key=lambda kv: (-(kv[1][1] * 3 + kv[1][2]), -(kv[1][4] - kv[1][5]), -kv[1][4]))
    out[season] = {"matches": n, "table": [[t, *r, r[1] * 3 + r[2]] for t, r in table]}
    print(season, n, "teams", len(teams), "| top:", table[0][0], table[0][1][1] * 3 + table[0][1][2], "| 2nd:", table[1][0])
json.dump(out, open(sys.argv[2], "w"), indent=0)
