"""Build the Football question bank (1,000 questions).

Premier League questions are calculated from every match result 1992-93 to 2025-26 (openfootball,
public domain); World Cup questions from openfootball's worldcup.json (1930-2026). The rest is
hand-written and limited to settled facts (records are dated where they could change).
"""
import sys, os, json, random, hashlib, collections

PL, WC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
rng = random.Random(20261122)
Q = collections.defaultdict(list)


def add(cat, key, q, a, opts):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) not in (1, 3):
        raise SystemExit(f"bad options for {q!r}: {opts}")
    Q[cat].append({"c": cat, "k": key, "q": q, "a": a, "o": opts})


def pick(pool, n, exclude=()):
    cand = [x for x in dict.fromkeys(pool) if x not in exclude]
    rng.shuffle(cand)
    if len(cand) < n:
        raise SystemExit(f"not enough options: {pool[:6]}")
    return cand[:n]


def near(v, lo, hi, n=3, spread=3):
    while True:
        cand = [x for x in range(max(lo, v - spread), min(hi, v + spread) + 1) if x != v]
        if len(cand) >= n:
            break
        spread += 1
    rng.shuffle(cand)
    return cand[:n]


# ------------------------------------------------------------------ Premier League (from results)
d = json.load(open(PL))
SEASONS = [s for s in sorted(d) if s <= "2025-26"]
NEXT = {s: d[sorted(d)[i + 1]] for i, s in enumerate(sorted(d)[:-1])}
SHORT = {"West Bromwich Albion": "West Brom", "Wolverhampton Wanderers": "Wolves", "Brighton & Hove Albion": "Brighton",
         "Tottenham Hotspur": "Tottenham", "Queens Park Rangers": "QPR"}
def club(n): return SHORT.get(n, n)
def sname(s): return s[:4] + "–" + s[5:]
table = {s: [t[0] for t in d[s]["table"]] for s in SEASONS}
pts = {s: {t[0]: t[-1] for t in d[s]["table"]} for s in SEASONS}
inS = {s: set(table[s]) for s in SEASONS}
clubs = collections.defaultdict(list)
for s in SEASONS:
    for t in table[s]:
        clubs[t].append(s)
everyone = sorted(clubs)

for s in SEASONS:
    t = table[s]
    champ, second, third = t[0], t[1], t[2]
    add("plchamp", "pl:c" + s, f"Who won the Premier League in {sname(s)}?", club(champ), [club(x) for x in pick(t[1:7], 3)])
    add("plsecond", "pl:2" + s, f"Who finished second in the Premier League in {sname(s)}?", club(second), [club(x) for x in [champ] + pick(t[2:7], 2)])
    add("plthird", "pl:3" + s, f"Who finished third in the Premier League in {sname(s)}?", club(third), [club(x) for x in [champ, second] + pick(t[3:8], 1)])
    p = pts[s][champ]
    add("plpoints", "pl:p" + s, f"How many points did {club(champ)} win the {sname(s)} Premier League with?", f"{p} points", [f"{x} points" for x in near(p, 60, 105, spread=6)])
    add("plbottom", "pl:b" + s, f"Which club finished bottom of the Premier League in {sname(s)}?", club(t[-1]), [club(x) for x in pick(t[-6:-1], 3)])
    add("plfourth", "pl:4" + s, f"Who finished fourth in the Premier League in {sname(s)}?", club(t[3]), [club(x) for x in [t[2]] + pick(t[4:9], 2)])
    four = sorted(rng.sample(range(len(t)), 4))
    add("pllowest", "pl:l" + s, f"Which of these clubs finished lowest in the {sname(s)} Premier League?", club(t[four[-1]]), [club(t[j]) for j in four[:-1]])
    # who went down: in this season, not in the next one
    nxt = {x[0] for x in NEXT[s]["table"]} if s in NEXT else None
    if nxt:
        down = [x for x in t if x not in nxt]
        safe = [x for x in t[10:] if x in nxt]
        for i, r in enumerate(down[:2]):
            add("pldown", f"pl:d{s}{i}", f"Which of these clubs was relegated from the Premier League at the end of {sname(s)}?", club(r), [club(x) for x in pick(safe, 3)])
    # who came up: in this season, not in the previous one
    i = SEASONS.index(s)
    if i > 0:
        new = [x for x in t if x not in inS[SEASONS[i - 1]]]
        absent = [c for c in everyone if c not in inS[s]]
        if new:
            add("plup", "pl:u" + s, f"Which of these clubs was promoted to the Premier League for {sname(s)}?", club(new[0]), [club(x) for x in pick(absent, 3)])
    # who finished highest of four
    for k in range(2):
        four = sorted(rng.sample(range(len(t)), 4))
        add("plhigher", f"pl:h{s}{k}", f"Which of these clubs finished highest in the {sname(s)} Premier League?", club(t[four[0]]), [club(t[j]) for j in four[1:]])
# promoted for the season now under way
cur = sorted(d)[-1]
newest = [x[0] for x in d[cur]["table"] if x[0] not in inS[SEASONS[-1]]]
for i, n in enumerate(newest):
    add("plup", f"pl:u{cur}{i}", f"Which of these clubs was promoted to the Premier League for {sname(cur)}?", club(n), [club(x) for x in pick([c for c in everyone if c not in {x[0] for x in d[cur]['table']}], 3)])


def streak(ss):
    idx = [SEASONS.index(x) for x in ss]
    best = cur_ = 1; bs = be = st = idx[0]
    for a, b in zip(idx, idx[1:]):
        if b == a + 1:
            cur_ += 1
        else:
            cur_ = 1; st = b
        if cur_ > best:
            best, bs, be = cur_, st, b
    return best, SEASONS[bs], SEASONS[be]


EVER = [c for c in everyone if len(clubs[c]) == len(SEASONS)]
for c in everyone:
    n = len(clubs[c])
    if c in EVER or n < 2:
        continue
    b, s0, s1 = streak(clubs[c])
    add("plstreak", "pl:s" + c, f"Up to 2025–26, what is the longest run of consecutive Premier League seasons {club(c)} have had?",
        f"{b} seasons" if b > 1 else "1 season", [f"{x} seasons" if x > 1 else "1 season" for x in near(b, 1, 34, spread=3)])
    add("plseasons", "pl:n" + c, f"Up to the end of 2025–26, how many seasons have {club(c)} spent in the Premier League?",
        f"{n} seasons" if n > 1 else "1 season", [f"{x} seasons" if x > 1 else "1 season" for x in near(n, 1, 34, spread=4)])
    first = clubs[c][0]
    if first != SEASONS[0]:
        others = [x for x in SEASONS if x != first]
        add("plfirst", "pl:f" + c, f"In which season did {club(c)} first play in the Premier League?", sname(first),
            [sname(x) for x in pick([x for x in others if abs(SEASONS.index(x) - SEASONS.index(first)) <= 8], 3)])
FOUNDERS = table[SEASONS[0]]
for c in FOUNDERS:
    if c in EVER:
        continue
    add("plfounder", "pl:o" + c, "Which of these clubs played in the very first Premier League season, 1992–93?", club(c),
        [club(x) for x in pick([x for x in everyone if x not in FOUNDERS and len(clubs[x]) >= 3], 3)])
for c in EVER:
    add("plever", "pl:e" + c, "Which of these clubs has played in every Premier League season from 1992–93 to 2025–26?", club(c),
        [club(x) for x in pick(["Manchester City", "Newcastle United", "Aston Villa", "West Ham United", "Southampton", "Leeds United", "Blackburn Rovers", "Leicester City"], 3)])
TITLES = collections.Counter(table[s][0] for s in SEASONS)
for c, n in TITLES.items():
    add("pltitles", "pl:t" + c, f"Up to 2025–26, how many Premier League titles have {club(c)} won?", str(n), [str(x) for x in near(n, 0, 16, spread=3)])
rec = []
allrows = [(s, t) for s in SEASONS for t in d[s]["table"]]
mp = max(allrows, key=lambda x: x[1][-1]); rec.append(("What is the most points a team has won in a Premier League season?", f"{mp[1][-1]} points ({club(mp[1][0])}, {sname(mp[0])})", ["95 points (Chelsea, 2004–05)", "99 points (Liverpool, 2019–20)", "98 points (Manchester City, 2018–19)"]))
lp = min(allrows, key=lambda x: x[1][-1]); rec.append(("Which club got the fewest points ever in a Premier League season, just 11?", f"{club(lp[1][0])} ({sname(lp[0])})", ["Sunderland (2005–06)", "Aston Villa (2015–16)", "Sheffield United (2020–21)"]))
mg = max(allrows, key=lambda x: x[1][5]); rec.append(("Which team scored a record 106 goals in a single Premier League season?", f"{club(mg[1][0])} ({sname(mg[0])})", ["Chelsea (2009–10)", "Liverpool (2013–14)", "Manchester United (1999–2000)"]))
fc = min([r for r in allrows if d[r[0]]["matches"] == 380], key=lambda x: x[1][6]); rec.append(("Which team conceded only 15 goals in a 38-game Premier League season?", f"{club(fc[1][0])} ({sname(fc[0])})", ["Arsenal (2003–04)", "Manchester City (2018–19)", "Liverpool (2018–19)"]))
un = [(s, t[0]) for s, t in [(s, t) for s, t in allrows] if t[4] == 0]
rec.append(("Which club went a whole Premier League season unbeaten?", f"{club(un[0][1])} ({sname(un[0][0])})", ["Chelsea (2004–05)", "Manchester United (1998–99)", "Manchester City (2017–18)"]))
for i, (q, a, o) in enumerate(rec):
    add("plrecord", f"pl:r{i}", q, a, o)

# ------------------------------------------------------------------ World Cup (from results)
HOST = {1930: "Uruguay", 1934: "Italy", 1938: "France", 1950: "Brazil", 1954: "Switzerland", 1958: "Sweden", 1962: "Chile", 1966: "England",
        1970: "Mexico", 1974: "West Germany", 1978: "Argentina", 1982: "Spain", 1986: "Mexico", 1990: "Italy", 1994: "the United States",
        1998: "France", 2002: "South Korea and Japan", 2006: "Germany", 2010: "South Africa", 2014: "Brazil", 2018: "Russia", 2022: "Qatar",
        2026: "the United States, Canada and Mexico"}
WIN, LOSE, FINAL = {}, {}, {}
for f in sorted(os.listdir(WC)):
    y = int(f[:4])
    j = json.load(open(os.path.join(WC, f)))
    ms = j.get("matches") or [m for r in j.get("rounds", []) for m in r.get("matches", [])]
    fin = [m for m in ms if str(m.get("round", "")).lower().startswith("final")][-1]
    sc = fin["score"]
    if isinstance(sc, list):
        sc = {"ft": sc}
    a, b = sc.get("p") or sc.get("et") or sc["ft"]
    t1, t2 = fin["team1"], fin["team2"]
    WIN[y], LOSE[y] = (t1, t2) if a > b else (t2, t1)
    w, l = sc.get("et") or sc["ft"], None
    FINAL[y] = (WIN[y], LOSE[y], sc)
TEAMS = sorted(set(WIN.values()) | set(LOSE.values()) | {"Netherlands", "Portugal", "Belgium", "Croatia", "Sweden", "Hungary"})
YEARS = sorted(WIN)
OLD_ONLY, NEW_ONLY = {"West Germany", "Czechoslovakia", "Hungary"}, {"Croatia"}
def era(y): return [t for t in TEAMS if (t not in OLD_ONLY if y >= 1994 else t not in NEW_ONLY)]
for y in YEARS:
    add("wcwin", f"wc:w{y}", f"Who won the {y} World Cup?", WIN[y], pick([t for t in era(y) if t != LOSE[y]], 2, exclude={WIN[y]}) + [LOSE[y]])
    add("wcfinal", f"wc:l{y}", f"Who did {WIN[y]} beat in the {y} World Cup final?" if y != 1950 else "Which team lost the deciding match of the 1950 World Cup to Uruguay?",
        LOSE[y], pick(era(y), 3, exclude={WIN[y], LOSE[y]}))
    hosts = sorted(set(HOST.values()))
    add("wchost", f"wc:h{y}", f"Which country hosted the {y} World Cup?" if " and " not in HOST[y] else f"Which countries hosted the {y} World Cup?",
        HOST[y][0].upper() + HOST[y][1:], [h[0].upper() + h[1:] for h in pick(hosts, 3, exclude={HOST[y]})])
COUNT = collections.Counter("Germany" if w == "West Germany" else w for w in WIN.values())
for t, n in COUNT.items():
    add("wccount", "wc:n" + t, f"Up to and including 2026, how many World Cups have {t} won?" + (" (count West Germany too)" if t == "Germany" else ""), str(n), [str(x) for x in near(n, 1, 6, spread=2)])
    last = max(y for y, w in WIN.items() if ("Germany" if w == "West Germany" else w) == t)
    add("wclast", "wc:z" + t, f"When did {t} last win the World Cup?", str(last), [str(x) for x in pick([y for y in YEARS if abs(y - last) <= 24], 3, exclude={last})])
pens = [y for y in YEARS if "p" in FINAL[y][2]]
for y in pens:
    add("wcpens", f"wc:p{y}", "Which of these World Cup finals was decided by a penalty shoot-out?", str(y), [str(x) for x in pick([z for z in YEARS if z not in pens and z >= 1970], 3)])

# ------------------------------------------------------------------ hand-written: category|question|answer|wrong|wrong|wrong
FACTS = r"""
rules|How many players does each team have on the pitch at the start of a match?|11|10|12|9
rules|How long is a normal football match, not counting stoppage time?|90 minutes|80 minutes|100 minutes|60 minutes
rules|How long is each half of a normal match?|45 minutes|40 minutes|30 minutes|50 minutes
rules|How long is extra time in total?|30 minutes|20 minutes|15 minutes|45 minutes
rules|How far is the penalty spot from the goal line?|12 yards (11 metres)|10 yards (9 metres)|15 yards (14 metres)|18 yards (16 metres)
rules|What does a referee show a player to send them off?|A red card|A yellow card|A green card|A blue card
rules|How many yellow cards in one match add up to a red card?|2|3|1|4
rules|At which World Cup were yellow and red cards first used?|1970|1930|1966|1990
rules|What is it called when a player scores three goals in one match?|A hat-trick|A brace|A treble|A clean sheet
rules|What is it called when a player scores two goals in one match?|A brace|A hat-trick|A double header|A nutmeg
rules|What is a "clean sheet"?|Not letting in a goal|Getting no cards|Winning every match|Scoring from a free kick
rules|What is a "nutmeg"?|Kicking the ball through an opponent's legs|A long throw-in|A volley from outside the box|A goal straight from a corner
rules|What is a Panenka?|A gently chipped penalty down the middle|A bicycle kick|A curling free kick|A goal from the halfway line
rules|Which player gave his name to the chipped "Panenka" penalty?|Antonín Panenka|Johan Cruyff|Roberto Baggio|Zinedine Zidane
rules|Which player can handle the ball inside their own penalty area?|The goalkeeper|The captain|Any defender|Nobody
rules|What restarts play when the ball goes over the touchline?|A throw-in|A corner kick|A goal kick|A drop ball
rules|If a defender last touches the ball before it goes over their own goal line (not into the goal), what is given?|A corner kick|A goal kick|A throw-in|A penalty
rules|What does VAR stand for?|Video Assistant Referee|Video Action Replay|Virtual Area Review|Visual Assistant Rules
rules|In which season did the Premier League start using VAR?|2019–20|2016–17|2021–22|2014–15
rules|What was the "golden goal" rule?|The first goal in extra time won the match|A goal from outside the box counted double|Penalty goals counted double|The captain's goal counted double
rules|Since 1992, what can't a goalkeeper do with a deliberate back-pass from a teammate's foot?|Pick it up|Kick it|Head it|Chest it
rules|What size ball is used in professional adult football?|Size 5|Size 3|Size 4|Size 6
rules|What is a free kick taken straight at goal called, as opposed to one that must touch another player first?|A direct free kick|An indirect free kick|A drop kick|A penalty kick
rules|How many substitutes can a team normally use in a Premier League match today?|5|3|4|7
rules|When is a player offside?|When they're nearer the goal line than the ball and the second-last defender as the ball is played to them|Whenever they're in the opponent's half|When they stand in the penalty area|When they touch the ball twice
rules|What signal does the assistant referee make for offside?|Raises their flag|Blows a whistle|Shows a card|Points to the centre circle
rules|What is the curved line at the edge of the penalty area called?|The penalty arc ("the D")|The six-yard line|The halfway line|The touchline
rules|What is an "own goal"?|When a player puts the ball into their own net|A goal scored by the goalkeeper|A goal straight from kick-off|A goal in stoppage time
rules|What happens if a knockout match is still level after extra time?|A penalty shoot-out|A replay the next day|The home team goes through|A coin toss
rules|How many penalties does each team take in a shoot-out before it goes to sudden death?|5|3|6|10
rules|Which part of the body can't outfield players use to play the ball on purpose?|Hands and arms|Head|Chest|Knees
rules|What colour card does the referee show as a caution?|Yellow|Red|Green|White
rules|What is the "Golden Boot" given for?|Scoring the most goals|Most assists|Best goalkeeper|Fair play
rules|What is the "Golden Glove" given for?|Best goalkeeper (most clean sheets)|Most goals|Most assists|Best young player
rules|What is a "derby" in football?|A match between two local rivals|A cup final|A friendly match|A match played at night
stadium|What is the name of Arsenal's stadium?|The Emirates Stadium|Highbury|White Hart Lane|Stamford Bridge
stadium|Where did Arsenal play before moving in 2006?|Highbury|Wembley|Craven Cottage|Upton Park
stadium|What is the name of Chelsea's stadium?|Stamford Bridge|Craven Cottage|Selhurst Park|Loftus Road
stadium|What is the name of Liverpool's stadium?|Anfield|Goodison Park|Old Trafford|Villa Park
stadium|What is the name of Manchester United's stadium?|Old Trafford|Etihad Stadium|Maine Road|Anfield
stadium|What is the name of Manchester City's stadium?|The Etihad Stadium|Maine Road|Old Trafford|Turf Moor
stadium|Where did Manchester City play before 2003?|Maine Road|Old Trafford|Bramall Lane|Deepdale
stadium|Where did Everton play before moving to their new stadium in 2025?|Goodison Park|Anfield|Prenton Park|Elland Road
stadium|What is the name of Newcastle United's stadium?|St James' Park|Stadium of Light|Riverside Stadium|Ewood Park
stadium|What is the name of Aston Villa's stadium?|Villa Park|St Andrew's|The Hawthorns|Molineux
stadium|What is the name of West Brom's stadium?|The Hawthorns|Villa Park|Molineux|St Andrew's
stadium|What is the name of Wolves' stadium?|Molineux|The Hawthorns|Bramall Lane|Portman Road
stadium|What is the name of Sunderland's stadium?|The Stadium of Light|St James' Park|Riverside Stadium|Pride Park
stadium|What is the name of Fulham's riverside stadium?|Craven Cottage|Stamford Bridge|Loftus Road|The Valley
stadium|What is the name of Crystal Palace's stadium?|Selhurst Park|The Den|The Valley|Brisbane Road
stadium|What is the name of Nottingham Forest's stadium?|The City Ground|Meadow Lane|Pride Park|The King Power Stadium
stadium|What is the name of Leeds United's stadium?|Elland Road|Hillsborough|Bramall Lane|Valley Parade
stadium|What is the name of Burnley's stadium?|Turf Moor|Ewood Park|Deepdale|Bloomfield Road
stadium|What is the name of Sheffield Wednesday's stadium?|Hillsborough|Bramall Lane|Elland Road|Oakwell
stadium|What is the name of Sheffield United's stadium?|Bramall Lane|Hillsborough|Oakwell|Valley Parade
stadium|What is the name of Ipswich Town's stadium?|Portman Road|Carrow Road|Vicarage Road|Kenilworth Road
stadium|What is the name of Norwich City's stadium?|Carrow Road|Portman Road|Vicarage Road|Fratton Park
stadium|What is the name of Watford's stadium?|Vicarage Road|Kenilworth Road|Carrow Road|Loftus Road
stadium|What is the name of Luton Town's stadium?|Kenilworth Road|Vicarage Road|Portman Road|The Den
stadium|What is the name of Blackburn Rovers' stadium?|Ewood Park|Turf Moor|Deepdale|Gigg Lane
stadium|What is the name of Portsmouth's stadium?|Fratton Park|St Mary's|The Dell|Dean Court
stadium|What is the name of Southampton's stadium?|St Mary's Stadium|Fratton Park|The Dell|Dean Court
stadium|What was Southampton's old ground, before 2001?|The Dell|Fratton Park|Dean Court|The Valley
stadium|What is the name of Charlton Athletic's stadium?|The Valley|The Den|Selhurst Park|Brisbane Road
stadium|What is the name of Millwall's stadium?|The Den|The Valley|Loftus Road|Griffin Park
stadium|What is the name of QPR's stadium?|Loftus Road|Craven Cottage|Griffin Park|Brisbane Road
stadium|Where did Brentford play before their new stadium opened in 2020?|Griffin Park|Loftus Road|Craven Cottage|The Valley
stadium|What is the name of Celtic's stadium?|Celtic Park|Ibrox|Hampden Park|Tynecastle
stadium|What is the name of Rangers' stadium?|Ibrox|Celtic Park|Hampden Park|Pittodrie
stadium|What is the name of England's national stadium?|Wembley Stadium|Twickenham|Old Trafford|Hampden Park
stadium|Roughly how many people does Wembley Stadium hold?|90,000|50,000|60,000|120,000
stadium|What is the name of Barcelona's famous stadium?|Camp Nou|Santiago Bernabéu|Mestalla|San Siro
stadium|What is the name of Real Madrid's stadium?|Santiago Bernabéu|Camp Nou|Mestalla|Wanda Metropolitano
stadium|Which two big Italian clubs share the San Siro?|AC Milan and Inter Milan|Juventus and Torino|Roma and Lazio|Napoli and Juventus
stadium|What is the name of Bayern Munich's stadium?|Allianz Arena|Signal Iduna Park|Olympiastadion|Veltins-Arena
stadium|Borussia Dortmund's stadium is famous for its huge standing terrace. What is the terrace called?|The Yellow Wall|The Kop|The Stretford End|The Holte End
stadium|What is the name of Paris Saint-Germain's stadium?|Parc des Princes|Stade de France|Stade Vélodrome|Allianz Riviera
stadium|What is the name of Boca Juniors' famous stadium?|La Bombonera|El Monumental|Maracanã|Azteca
stadium|The Maracanã stadium is in which city?|Rio de Janeiro|São Paulo|Buenos Aires|Lisbon
stadium|Liverpool's famous home terrace is called…|The Kop|The Stretford End|The Holte End|The Shed End
stadium|Manchester United's famous home end is called…|The Stretford End|The Kop|The Gallowgate End|The North Bank
stadium|Old Trafford is nicknamed…|The Theatre of Dreams|The Fortress|The Cathedral|The Palace
stadium|The Hawthorns is famous for being…|The highest Football League ground above sea level in England|The oldest ground in the world|The smallest Premier League ground|The only ground with an artificial pitch
nickname|What is Arsenal's nickname?|The Gunners|The Blues|The Hammers|The Saints
nickname|What is Manchester United's nickname?|The Red Devils|The Citizens|The Reds|The Magpies
nickname|What is Everton's nickname?|The Toffees|The Magpies|The Cherries|The Seagulls
nickname|What is Newcastle United's nickname?|The Magpies|The Toffees|The Black Cats|The Owls
nickname|What is West Ham United's nickname?|The Hammers|The Gunners|The Eagles|The Bees
nickname|What is West Brom's nickname?|The Baggies|The Clarets|The Blades|The Potters
nickname|What is Sunderland's nickname?|The Black Cats|The Magpies|The Tigers|The Foxes
nickname|What is Leicester City's nickname?|The Foxes|The Tigers|The Wolves|The Owls
nickname|What is Southampton's nickname?|The Saints|The Seagulls|The Cherries|The Hornets
nickname|What is Brighton's nickname?|The Seagulls|The Saints|The Eagles|The Canaries
nickname|What is Crystal Palace's nickname?|The Eagles|The Seagulls|The Hornets|The Bees
nickname|What is Fulham's nickname?|The Cottagers|The Hammers|The Hoops|The Lions
nickname|What is Brentford's nickname?|The Bees|The Hornets|The Hatters|The Cherries
nickname|What is Bournemouth's nickname?|The Cherries|The Saints|The Seagulls|The Canaries
nickname|What is Burnley's nickname?|The Clarets|The Potters|The Baggies|The Blades
nickname|What is Stoke City's nickname?|The Potters|The Clarets|The Rams|The Owls
nickname|What is Sheffield United's nickname?|The Blades|The Owls|The Tykes|The Terriers
nickname|What is Sheffield Wednesday's nickname?|The Owls|The Blades|The Tykes|The Magpies
nickname|What is Ipswich Town's nickname?|The Tractor Boys|The Canaries|The Hornets|The Hatters
nickname|What is Norwich City's nickname?|The Canaries|The Tractor Boys|The Seagulls|The Robins
nickname|What is Watford's nickname?|The Hornets|The Bees|The Hatters|The Cherries
nickname|What is Luton Town's nickname?|The Hatters|The Hornets|The Hoops|The Bees
nickname|What is Derby County's nickname?|The Rams|The Foxes|The Potters|The Owls
nickname|What is Hull City's nickname?|The Tigers|The Black Cats|The Foxes|The Wolves
nickname|What is Coventry City's nickname?|The Sky Blues|The Blues|The Canaries|The Robins
nickname|What is Portsmouth's nickname?|Pompey|The Saints|The Seagulls|The Valiants
nickname|What is Middlesbrough's nickname?|Boro|The Rams|The Magpies|The Tykes
nickname|What is Huddersfield Town's nickname?|The Terriers|The Tykes|The Owls|The Shrimpers
nickname|What is Cardiff City's nickname?|The Bluebirds|The Swans|The Canaries|The Robins
nickname|What is Swansea City's nickname?|The Swans|The Bluebirds|The Seagulls|The Magpies
nickname|What is Nottingham Forest's well-known nickname?|The Tricky Trees|The Magpies|The Rams|The Foxes
nickname|What is Juventus' nickname?|The Old Lady (La Vecchia Signora)|The Red Devils|The Little Donkeys|The Wolves
nickname|What are Real Madrid's players often called, after their white kit?|Los Blancos|Los Rojos|Los Azules|Los Negros
nickname|What is Italy's national team often called, after their blue shirts?|The Azzurri|Les Bleus|La Roja|The Oranje
nickname|What is England's men's national team nicknamed?|The Three Lions|The Red Devils|La Roja|The Bulldogs
nickname|What is the Netherlands national team called, after its shirt colour?|Oranje|Azzurri|La Roja|Les Bleus
nickname|What is Spain's national team nicknamed?|La Roja|La Albiceleste|Les Bleus|The Azzurri
nickname|What is Argentina's national team nicknamed, after its sky-blue and white stripes?|La Albiceleste|La Roja|The Selecao|Oranje
nickname|What is France's national team nicknamed?|Les Bleus|The Azzurri|La Roja|Oranje
nickname|What is Belgium's national team nicknamed?|The Red Devils|The Three Lions|The Azzurri|Oranje
nickname|What is Nigeria's national team nicknamed?|The Super Eagles|The Black Stars|The Indomitable Lions|The Pharaohs
nickname|What is England's women's national team nicknamed?|The Lionesses|The Three Lionesses|The Roses|The Queens
derby|Which two clubs play the North London derby?|Arsenal and Tottenham|Chelsea and Fulham|Arsenal and Chelsea|Tottenham and West Ham
derby|Which two clubs play the Merseyside derby?|Liverpool and Everton|Liverpool and Manchester United|Everton and Tranmere|Liverpool and Wigan
derby|Which two clubs play the Black Country derby?|Wolves and West Brom|Aston Villa and Birmingham|West Brom and Aston Villa|Wolves and Stoke
derby|Which two clubs play the Tyne–Wear derby?|Newcastle and Sunderland|Newcastle and Middlesbrough|Sunderland and Middlesbrough|Newcastle and Leeds
derby|Which two clubs play the Second City derby?|Aston Villa and Birmingham City|West Brom and Wolves|Aston Villa and West Brom|Birmingham and Coventry
derby|Which two clubs play the Steel City derby?|Sheffield United and Sheffield Wednesday|Leeds and Bradford|Barnsley and Sheffield United|Rotherham and Sheffield Wednesday
derby|"El Clásico" is a match between which two clubs?|Real Madrid and Barcelona|Atlético Madrid and Real Madrid|Barcelona and Valencia|Sevilla and Real Betis
derby|"Der Klassiker" is a match between which two clubs?|Bayern Munich and Borussia Dortmund|Schalke and Dortmund|Bayern Munich and Hamburg|Werder Bremen and Hamburg
derby|The "Old Firm" derby is between which two clubs?|Celtic and Rangers|Hearts and Hibs|Aberdeen and Dundee|Celtic and Aberdeen
derby|The "Superclásico" in Argentina is between which two clubs?|Boca Juniors and River Plate|Racing and Independiente|River Plate and San Lorenzo|Boca Juniors and Racing
derby|Which two clubs play the Manchester derby?|Manchester United and Manchester City|Manchester United and Liverpool|Manchester City and Bolton|Manchester United and Oldham
derby|The Derby della Madonnina is played between which two clubs?|AC Milan and Inter Milan|Roma and Lazio|Juventus and Torino|Genoa and Sampdoria
derby|The Derby della Capitale in Rome is played between which two clubs?|Roma and Lazio|AC Milan and Inter Milan|Napoli and Roma|Juventus and Torino
derby|Which two clubs play the East Lancashire derby?|Blackburn Rovers and Burnley|Bolton and Wigan|Preston and Blackpool|Burnley and Bolton
player|Who is the Premier League's all-time top scorer, with 260 goals?|Alan Shearer|Wayne Rooney|Harry Kane|Thierry Henry
player|Who set the record for most goals in a 38-game Premier League season, with 36 in 2022–23?|Erling Haaland|Mohamed Salah|Alan Shearer|Harry Kane
player|Who has won the most Premier League titles as a player, with 13?|Ryan Giggs|Paul Scholes|Gary Neville|John Terry
player|Who scored the Premier League's fastest hat-trick, in under 3 minutes in 2015?|Sadio Mané|Robbie Fowler|Sergio Agüero|Jermain Defoe
player|Who scored the Premier League's fastest goal, after just 7.69 seconds in 2019?|Shane Long|Ledley King|Alan Shearer|Christian Eriksen
player|Who scored in the 93rd minute to win Manchester City the 2011–12 title on the last day?|Sergio Agüero|Edin Džeko|Mario Balotelli|Carlos Tevez
player|Which goalkeeper has kept the most Premier League clean sheets, with 202?|Petr Čech|David de Gea|Edwin van der Sar|David James
player|Who scored the very first Premier League goal, in August 1992?|Brian Deane|Alan Shearer|Teddy Sheringham|Eric Cantona
player|Who is Manchester United's all-time top scorer?|Wayne Rooney|Bobby Charlton|Denis Law|Cristiano Ronaldo
player|Who is Arsenal's all-time top scorer?|Thierry Henry|Ian Wright|Dennis Bergkamp|Robin van Persie
player|Who is Chelsea's all-time top scorer?|Frank Lampard|Didier Drogba|Bobby Tambling|Eden Hazard
player|Who is Liverpool's all-time top scorer?|Ian Rush|Mohamed Salah|Kenny Dalglish|Steven Gerrard
player|Who is Tottenham's all-time top scorer?|Harry Kane|Jimmy Greaves|Gary Lineker|Son Heung-min
player|Who is Newcastle United's all-time top scorer?|Alan Shearer|Jackie Milburn|Andy Cole|Les Ferdinand
player|Who became England's all-time top men's scorer in 2023?|Harry Kane|Wayne Rooney|Bobby Charlton|Gary Lineker
player|Who scored the famous "Hand of God" goal against England in 1986?|Diego Maradona|Pelé|Gabriel Batistuta|Mario Kempes
player|Which French star was sent off for a headbutt in the 2006 World Cup final?|Zinedine Zidane|Thierry Henry|Patrick Vieira|Franck Ribéry
player|Who scored a hat-trick for England in the 1966 World Cup final?|Geoff Hurst|Bobby Charlton|Jimmy Greaves|Roger Hunt
player|Who scored a hat-trick for France in the 2022 World Cup final, and still lost?|Kylian Mbappé|Olivier Giroud|Antoine Griezmann|Karim Benzema
player|Who captained Argentina to the 2022 World Cup?|Lionel Messi|Ángel Di María|Sergio Agüero|Diego Maradona
player|Going into the 2026 World Cup, who held the record for most World Cup goals, with 16?|Miroslav Klose|Ronaldo|Pelé|Lionel Messi
player|How many World Cups did Pelé win?|3|2|1|4
player|How many goals did Just Fontaine score at the 1958 World Cup?|13|9|11|7
player|Brazil's Ronaldo won the Golden Boot at the 2002 World Cup with how many goals?|8|6|10|5
player|Who has scored the most goals ever in men's international football?|Cristiano Ronaldo|Lionel Messi|Ali Daei|Pelé
player|Which country is Mohamed Salah from?|Egypt|Morocco|Senegal|Algeria
player|Which country is Erling Haaland from?|Norway|Sweden|Denmark|Iceland
player|Which country is Kevin De Bruyne from?|Belgium|Netherlands|Germany|Denmark
player|Which country is Son Heung-min from?|South Korea|Japan|China|Vietnam
player|Which country is Luka Modrić from?|Croatia|Serbia|Slovenia|Bosnia and Herzegovina
player|Which country is Virgil van Dijk from?|Netherlands|Belgium|Germany|Denmark
player|Which club did Lionel Messi join after leaving Barcelona in 2021?|Paris Saint-Germain|Inter Miami|Manchester City|Juventus
player|Which club did David Beckham join from Manchester United in 2003?|Real Madrid|AC Milan|LA Galaxy|PSG
player|Which player was involved in the world-record transfer of €222 million in 2017?|Neymar|Kylian Mbappé|Cristiano Ronaldo|Philippe Coutinho
player|Which goalkeeper is the only one ever to win the Ballon d'Or?|Lev Yashin|Gianluigi Buffon|Manuel Neuer|Peter Schmeichel
player|Who won the 2024 Ballon d'Or?|Rodri|Vinícius Júnior|Jude Bellingham|Lionel Messi
player|Who won the 2025 Ballon d'Or?|Ousmane Dembélé|Lamine Yamal|Mohamed Salah|Raphinha
player|Who won the 2023 Ballon d'Or?|Lionel Messi|Erling Haaland|Kylian Mbappé|Kevin De Bruyne
player|Who won the 2022 Ballon d'Or?|Karim Benzema|Robert Lewandowski|Lionel Messi|Sadio Mané
player|Who won the 2018 Ballon d'Or, breaking Messi and Ronaldo's run?|Luka Modrić|Antoine Griezmann|Kylian Mbappé|Mohamed Salah
player|Who won the 2007 Ballon d'Or?|Kaká|Cristiano Ronaldo|Lionel Messi|Ronaldinho
player|Who won the 2005 Ballon d'Or?|Ronaldinho|Frank Lampard|Steven Gerrard|Thierry Henry
player|Who won the 2001 Ballon d'Or, playing for Liverpool?|Michael Owen|Steven Gerrard|Robbie Fowler|Emile Heskey
player|Who won the 1998 Ballon d'Or after France won the World Cup?|Zinedine Zidane|Thierry Henry|Didier Deschamps|Fabien Barthez
player|Up to 2025, how many Ballon d'Or awards has Lionel Messi won?|8|6|7|5
player|Up to 2025, how many Ballon d'Or awards has Cristiano Ronaldo won?|5|4|6|3
player|In which year was the Ballon d'Or not awarded, because of the pandemic?|2020|2019|2021|2008
player|Which manager led Leicester City to the 2015–16 Premier League title?|Claudio Ranieri|Brendan Rodgers|Nigel Pearson|Sven-Göran Eriksson
player|Which manager won 13 league titles with Manchester United?|Sir Alex Ferguson|Matt Busby|José Mourinho|Louis van Gaal
player|Who managed Arsenal's "Invincibles" in 2003–04?|Arsène Wenger|George Graham|Mikel Arteta|Unai Emery
player|Which manager is nicknamed "The Special One"?|José Mourinho|Pep Guardiola|Jürgen Klopp|Carlo Ancelotti
player|Which manager led Liverpool to the 2019–20 Premier League title?|Jürgen Klopp|Arne Slot|Rafael Benítez|Brendan Rodgers
player|Which manager led Liverpool to the 2024–25 Premier League title?|Arne Slot|Jürgen Klopp|Pep Guardiola|Mikel Arteta
player|Which West Brom striker was nicknamed "The King"?|Jeff Astle|Tony Brown|Cyrille Regis|Bob Taylor
player|Which player scored the winning goal for West Brom in the 1968 FA Cup final?|Jeff Astle|Tony Brown|Bryan Robson|Laurie Cunningham
player|Who managed England to their 1966 World Cup win?|Sir Alf Ramsey|Bobby Robson|Don Revie|Terry Venables
player|Who managed England from 2016 to 2024, reaching two Euro finals?|Gareth Southgate|Roy Hodgson|Sam Allardyce|Thomas Tuchel
player|Which famous Dutch player gave his name to the "Cruyff turn"?|Johan Cruyff|Marco van Basten|Ruud Gullit|Dennis Bergkamp
player|Which player is nicknamed "CR7"?|Cristiano Ronaldo|Cristiano Zanetti|Ronaldinho|Ronaldo Nazário
player|Which country does Lamine Yamal play for?|Spain|Morocco|Portugal|France
player|Erling Haaland joined Manchester City from which club?|Borussia Dortmund|RB Salzburg|Bayern Munich|Molde
player|Which player scored the "Goal of the Century" against England at the 1986 World Cup?|Diego Maradona|Jorge Valdano|Gary Lineker|Michel Platini
ucl|Who won the 2025 Champions League final, their first ever?|Paris Saint-Germain|Inter Milan|Arsenal|Barcelona
ucl|Who won the 2024 Champions League?|Real Madrid|Borussia Dortmund|Bayern Munich|Manchester City
ucl|Who won the 2023 Champions League, completing a treble?|Manchester City|Inter Milan|Real Madrid|Bayern Munich
ucl|Who won the 2022 Champions League?|Real Madrid|Liverpool|Manchester City|Villarreal
ucl|Who won the 2021 Champions League?|Chelsea|Manchester City|Real Madrid|PSG
ucl|Who won the 2020 Champions League, in a final played behind closed doors?|Bayern Munich|PSG|Lyon|RB Leipzig
ucl|Who won the 2019 Champions League?|Liverpool|Tottenham|Ajax|Barcelona
ucl|Who did Liverpool beat in the 2019 Champions League final?|Tottenham|Real Madrid|Barcelona|Ajax
ucl|Who won three Champions League finals in a row from 2016 to 2018?|Real Madrid|Barcelona|Bayern Munich|Juventus
ucl|Who won the 2015 Champions League?|Barcelona|Juventus|Real Madrid|Bayern Munich
ucl|Who won the 2014 Champions League, beating their city rivals in the final?|Real Madrid|Atlético Madrid|Barcelona|Bayern Munich
ucl|Who won the 2013 Champions League in an all-German final?|Bayern Munich|Borussia Dortmund|Schalke|Bayer Leverkusen
ucl|Who won the 2012 Champions League on penalties in Munich?|Chelsea|Bayern Munich|Barcelona|Real Madrid
ucl|Who won the 2011 Champions League at Wembley?|Barcelona|Manchester United|Real Madrid|Bayern Munich
ucl|Who won the 2010 Champions League under José Mourinho?|Inter Milan|Bayern Munich|Chelsea|Real Madrid
ucl|Who won the 2009 Champions League?|Barcelona|Manchester United|Chelsea|Liverpool
ucl|Who won the 2008 Champions League final in Moscow, on penalties against Chelsea?|Manchester United|Liverpool|Barcelona|Arsenal
ucl|Who won the 2005 Champions League after coming back from 3–0 down at half-time?|Liverpool|AC Milan|Chelsea|Juventus
ucl|Who did Liverpool beat in the famous 2005 "Miracle of Istanbul" final?|AC Milan|Juventus|Inter Milan|Barcelona
ucl|Who won the 2004 Champions League, managed by José Mourinho?|Porto|Monaco|Chelsea|Deportivo La Coruña
ucl|Who won the 1999 Champions League with two stoppage-time goals?|Manchester United|Bayern Munich|Juventus|Real Madrid
ucl|Who did Manchester United beat in the 1999 Champions League final?|Bayern Munich|Juventus|Real Madrid|Barcelona
ucl|Who won the first Champions League (as it was renamed) in 1993?|Marseille|AC Milan|Barcelona|Ajax
ucl|Who won the 1995 Champions League with a young, homegrown team?|Ajax|AC Milan|Juventus|Bayern Munich
ucl|Who won the 1997 Champions League?|Borussia Dortmund|Juventus|Ajax|Bayern Munich
ucl|Up to 2025, which club has won the most European Cups and Champions Leagues?|Real Madrid|AC Milan|Bayern Munich|Liverpool
ucl|Up to 2025, how many European Cups/Champions Leagues had Real Madrid won?|15|12|13|10
ucl|Which English club won the European Cup in 1982?|Aston Villa|Nottingham Forest|Liverpool|Manchester United
ucl|Which club won back-to-back European Cups in 1979 and 1980?|Nottingham Forest|Liverpool|Ajax|Bayern Munich
ucl|Which club became the first English winner of the European Cup, in 1968?|Manchester United|Liverpool|Tottenham|Celtic
ucl|Which club became the first British winner of the European Cup, in 1967?|Celtic|Rangers|Manchester United|Liverpool
ucl|What is the trophy for the second-tier European club competition called?|The Europa League|The Champions Cup|The Super Cup|The Intertoto Cup
ucl|Which competition did West Ham win in 2023?|The Europa Conference League|The Europa League|The FA Cup|The League Cup
ucl|Which club won the Europa League in 2025?|Tottenham|Manchester United|Athletic Bilbao|Bodø/Glimt
euro|Who won Euro 2024?|Spain|England|France|Netherlands
euro|Who did Spain beat in the Euro 2024 final?|England|France|Germany|Italy
euro|Who won Euro 2020, played in 2021?|Italy|England|Spain|Denmark
euro|Who did Italy beat in the Euro 2020 final at Wembley?|England|Spain|Denmark|Belgium
euro|Who won Euro 2016?|Portugal|France|Wales|Germany
euro|Who won Euro 2012?|Spain|Italy|Germany|Portugal
euro|Who won Euro 2008?|Spain|Germany|Russia|Turkey
euro|Who shocked everyone by winning Euro 2004?|Greece|Portugal|Czech Republic|Netherlands
euro|Who won Euro 2000?|France|Italy|Netherlands|Portugal
euro|Who won Euro 96, held in England?|Germany|England|Czech Republic|France
euro|Which team won Euro 92 after being called in late to replace Yugoslavia?|Denmark|Sweden|Netherlands|Germany
euro|Who won Euro 88?|Netherlands|West Germany|Soviet Union|Italy
euro|Which country hosted Euro 96?|England|Germany|France|Netherlands
euro|Which country hosted Euro 2024?|Germany|France|England|Spain
euro|Which country hosted Euro 2016?|France|Portugal|Germany|Poland
euro|Which two countries co-hosted Euro 2012?|Poland and Ukraine|Austria and Switzerland|Belgium and Netherlands|Spain and Portugal
euro|Which two countries co-hosted Euro 2008?|Austria and Switzerland|Poland and Ukraine|Belgium and Netherlands|Spain and Portugal
euro|Where was the Euro 2020 final played?|Wembley Stadium, London|Stadio Olimpico, Rome|Hampden Park, Glasgow|Allianz Arena, Munich
euro|Which song did England fans sing at Euro 96 with the line "football's coming home"?|Three Lions|Vindaloo|World in Motion|Back Home
euro|Up to 2024, which country had won the most European Championships?|Spain|Germany|Italy|France
euro|Who won the Women's Euro 2022, held in England?|England|Germany|Netherlands|Sweden
euro|Who won the Women's Euro 2025?|England|Spain|Germany|France
euro|Who won the 2023 Women's World Cup?|Spain|England|USA|Sweden
euro|Who won the first ever European Championship, in 1960?|Soviet Union|Spain|Yugoslavia|France
fa|Which is the oldest national football competition in the world?|The FA Cup|The Premier League|The League Cup|The Copa América
fa|In which year was the first FA Cup final played?|1872|1901|1888|1923
fa|Which club won the first FA Cup?|Wanderers|Royal Engineers|Old Etonians|Blackburn Rovers
fa|In which year was the Football Association (the FA) founded?|1863|1888|1904|1923
fa|Who won the 2025 FA Cup, their first major trophy?|Crystal Palace|Manchester City|Nottingham Forest|Aston Villa
fa|Who won the 2024 FA Cup?|Manchester United|Manchester City|Coventry City|Chelsea
fa|Who won the 2013 FA Cup, the same season they were relegated?|Wigan Athletic|Portsmouth|Birmingham City|Cardiff City
fa|Who won the 2008 FA Cup?|Portsmouth|Cardiff City|Chelsea|Manchester United
fa|Who won the 2021 FA Cup, their first ever?|Leicester City|Chelsea|Southampton|Brighton
fa|How many times have West Brom won the FA Cup?|5|3|1|7
fa|In which year did West Brom last win the FA Cup?|1968|1931|1954|1888
fa|In which season were West Brom champions of England?|1919–20|1953–54|1967–68|1890–91
fa|Which team did Wimbledon famously beat in the 1988 FA Cup final?|Liverpool|Manchester United|Everton|Arsenal
fa|What is the English League Cup often called, after its sponsor?|The Carabao Cup|The Emirates Cup|The FA Trophy|The Johnstone's Cup
fa|Which match traditionally opens the English season between the league and FA Cup winners?|The Community Shield|The Super Cup|The Charity Cup|The Trophy of Champions
fa|What is the name of the division just below the Premier League?|The Championship|League One|The First Division|The National League
fa|In which year did the Premier League begin?|1992|1988|1995|2000
fa|How many teams are in the Premier League?|20|18|22|24
fa|How many teams were in the Premier League in its first three seasons?|22|20|24|18
fa|How many teams are relegated from the Premier League each season?|3|2|4|1
fa|What were Leicester City's bookmaker odds to win the Premier League before the 2015–16 season?|5000-1|100-1|500-1|50-1
fa|Arsenal's unbeaten run in the Premier League ended at how many matches, in 2004?|49|38|40|30
fa|Arsenal's unbeaten 2003–04 team is known as…|The Invincibles|The Galácticos|The Busby Babes|The Crazy Gang
fa|What colour shirts do Liverpool play in at home?|Red|Blue|White|Yellow
fa|What colour shirts do Everton play in at home?|Blue|Red|White|Yellow
fa|West Brom play in what colour stripes at home?|Navy blue and white|Claret and blue|Red and white|Black and white
fa|Newcastle United play in what colours at home?|Black and white stripes|Red and white stripes|Blue and white hoops|Claret and blue
fa|Aston Villa and West Ham both play in which colours?|Claret and blue|Red and white|Black and white|Blue and white
fa|Which country does Wrexham AFC, famous for its Hollywood owners, play in?|Wales|England|Scotland|Ireland
fa|Which two Hollywood stars bought Wrexham AFC in 2021?|Ryan Reynolds and Rob McElhenney|Tom Hanks and Will Smith|Brad Pitt and George Clooney|Dwayne Johnson and Kevin Hart
wc|Which country has played at every men's World Cup?|Brazil|Germany|Italy|Argentina
wc|In which year was the first World Cup held?|1930|1920|1934|1950
wc|In which year was Qatar's World Cup held, the first ever in November and December?|2022|2018|2026|2014
wc|How many teams played at the 2026 World Cup?|48|32|40|64
wc|What is the name of the trophy awarded to World Cup winners today?|The FIFA World Cup Trophy|The Jules Rimet Trophy|The Henri Delaunay Trophy|The Golden Ball
wc|What was the original World Cup trophy called?|The Jules Rimet Trophy|The FIFA Cup|The Henri Delaunay Trophy|The Golden Goddess
wc|Which dog found the stolen World Cup trophy in 1966?|Pickles|Lassie|Rover|Buster
wc|What is the shock 1950 result where Uruguay beat Brazil in Rio called?|The Maracanazo|The Miracle of Bern|The Hand of God|The Battle of Santiago
wc|Germany beat which team 7–1 in the 2014 World Cup semi-final?|Brazil|Argentina|Netherlands|France
wc|Which team became the first African nation to reach a World Cup semi-final, in 2022?|Morocco|Senegal|Ghana|Cameroon
wc|Who did England lose to in the 2018 World Cup semi-final?|Croatia|France|Belgium|Sweden
wc|What does the "Golden Ball" award at a World Cup go to?|The best player of the tournament|The top scorer|The best goalkeeper|The best young player
wc|Who won the Golden Ball at both the 2014 and 2022 World Cups?|Lionel Messi|Kylian Mbappé|Luka Modrić|James Rodríguez
wc|Which country did Diego Maradona captain to World Cup glory in 1986?|Argentina|Brazil|Uruguay|Italy
wc|Which goalkeeper captained Spain to the 2010 World Cup?|Iker Casillas|David de Gea|Víctor Valdés|Pepe Reina
wc|Who scored the winning goal in the 2010 World Cup final?|Andrés Iniesta|David Villa|Xavi|Fernando Torres
wc|Who scored the extra-time winner in the 2014 World Cup final?|Mario Götze|Thomas Müller|Miroslav Klose|André Schürrle
player|Who won the 2008 Ballon d'Or?|Cristiano Ronaldo|Lionel Messi|Fernando Torres|Kaká
player|Who won the 2009 Ballon d'Or?|Lionel Messi|Cristiano Ronaldo|Xavi|Andrés Iniesta
player|Who won the 2010 Ballon d'Or?|Lionel Messi|Andrés Iniesta|Xavi|Wesley Sneijder
player|Who won the 2012 Ballon d'Or?|Lionel Messi|Cristiano Ronaldo|Andrés Iniesta|Radamel Falcao
player|Who won the 2013 Ballon d'Or?|Cristiano Ronaldo|Lionel Messi|Franck Ribéry|Zlatan Ibrahimović
player|Who won the 2014 Ballon d'Or?|Cristiano Ronaldo|Lionel Messi|Manuel Neuer|Arjen Robben
player|Who won the 2015 Ballon d'Or?|Lionel Messi|Cristiano Ronaldo|Neymar|Luis Suárez
player|Who won the 2016 Ballon d'Or?|Cristiano Ronaldo|Lionel Messi|Antoine Griezmann|Gareth Bale
player|Who won the 2017 Ballon d'Or?|Cristiano Ronaldo|Lionel Messi|Neymar|Kylian Mbappé
player|Who won the 2019 Ballon d'Or?|Lionel Messi|Virgil van Dijk|Cristiano Ronaldo|Sadio Mané
player|Who won the 2021 Ballon d'Or?|Lionel Messi|Robert Lewandowski|Jorginho|Karim Benzema
player|Who won the 2006 Ballon d'Or after captaining Italy to the World Cup?|Fabio Cannavaro|Gianluigi Buffon|Andrea Pirlo|Francesco Totti
player|Who won the 2004 Ballon d'Or?|Andriy Shevchenko|Thierry Henry|Ronaldinho|Deco
player|Who won the 2003 Ballon d'Or?|Pavel Nedvěd|Thierry Henry|Paolo Maldini|David Beckham
player|Who won the 2002 Ballon d'Or after starring at the World Cup?|Ronaldo|Roberto Carlos|Oliver Kahn|Zinedine Zidane
player|Who won the 2000 Ballon d'Or?|Luís Figo|Zinedine Zidane|Andriy Shevchenko|Rivaldo
player|Who won the 1999 Ballon d'Or?|Rivaldo|David Beckham|Andriy Shevchenko|Gabriel Batistuta
ucl|Who won the 2006 Champions League, beating Arsenal in the final?|Barcelona|Real Madrid|AC Milan|Villarreal
ucl|Who beat Liverpool in the 2007 Champions League final?|AC Milan|Barcelona|Chelsea|Inter Milan
ucl|Who won the 2003 Champions League in an all-Italian final?|AC Milan|Juventus|Inter Milan|Roma
ucl|Who won the 2002 Champions League, with a famous volley from Zidane?|Real Madrid|Bayer Leverkusen|Barcelona|Bayern Munich
ucl|Who won the 2001 Champions League on penalties against Valencia?|Bayern Munich|Real Madrid|Leeds United|Valencia
ucl|Who won the 2000 Champions League in an all-Spanish final?|Real Madrid|Valencia|Barcelona|Deportivo La Coruña
ucl|Who won the 1998 Champions League?|Real Madrid|Juventus|Borussia Dortmund|Bayern Munich
ucl|Who won the 1996 Champions League?|Juventus|Ajax|AC Milan|Real Madrid
ucl|Who won the 1994 Champions League, beating Barcelona 4–0 in the final?|AC Milan|Ajax|Marseille|Juventus
city|Which city are Celtic and Rangers from?|Glasgow|Edinburgh|Aberdeen|Dundee
city|Which city are Bayern Munich from?|Munich|Berlin|Hamburg|Frankfurt
city|Which city are Juventus from?|Turin|Milan|Rome|Naples
city|Which city are Ajax from?|Amsterdam|Rotterdam|Eindhoven|The Hague
city|Which city are Feyenoord from?|Rotterdam|Amsterdam|Eindhoven|Utrecht
city|Which city are PSV from?|Eindhoven|Rotterdam|Amsterdam|Utrecht
city|Which city are Benfica from?|Lisbon|Porto|Braga|Madrid
city|Which city are Galatasaray and Fenerbahçe from?|Istanbul|Ankara|Izmir|Athens
city|Which city are Napoli from?|Naples|Rome|Palermo|Milan
city|Which city are Borussia Dortmund from?|Dortmund|Düsseldorf|Cologne|Gelsenkirchen
city|Which city are Marseille from?|Marseille|Paris|Lyon|Nice
city|Which city are Atlético Madrid from?|Madrid|Barcelona|Valencia|Seville
rules|How long is half-time in a normal match?|15 minutes|10 minutes|20 minutes|5 minutes
rules|How wide is a full-size football goal?|8 yards (7.32 metres)|6 yards (5.5 metres)|10 yards (9.15 metres)|12 yards (11 metres)
rules|How high is a full-size football goal?|8 feet (2.44 metres)|6 feet (1.83 metres)|10 feet (3.05 metres)|7 feet (2.13 metres)
rules|How far must players stand from the ball at a free kick?|10 yards (9.15 metres)|5 yards (4.6 metres)|15 yards (13.7 metres)|3 yards (2.7 metres)
rules|How deep is the penalty area from the goal line?|18 yards (16.5 metres)|12 yards (11 metres)|6 yards (5.5 metres)|20 yards (18.3 metres)
rules|How deep is the "six-yard box"?|6 yards|8 yards|10 yards|4 yards
wc|Which three countries will host the 2030 World Cup's main tournament?|Spain, Portugal and Morocco|England, Scotland and Wales|Argentina, Uruguay and Chile|Italy, France and Germany
wc|Which country was chosen to host the 2034 World Cup?|Saudi Arabia|Australia|China|Egypt
wc|Which team lost three World Cup finals (1974, 1978 and 2010)?|Netherlands|Hungary|Italy|Croatia
wc|Who scored two headers for France in the 1998 World Cup final?|Zinedine Zidane|Thierry Henry|Emmanuel Petit|Lilian Thuram
fa|How many teams play in the Championship?|24|20|22|18
fa|How many teams are promoted from the Championship each season?|3|2|4|1
fa|Where is the FA Cup final played?|Wembley Stadium|Old Trafford|Villa Park|Anfield
fa|Up to 2025, which club had won the most FA Cups?|Arsenal|Manchester United|Chelsea|Tottenham
stadium|What is the name of Everton's new stadium, which opened in 2025?|Hill Dickinson Stadium|Goodison Park|Anfield|Prenton Park
fa|How is the third promotion place from the Championship decided?|By a play-off|By goal difference|By a coin toss|By the FA's vote
wc|Which mascot was the official mascot of the 1966 World Cup in England?|World Cup Willie|Footix|Zakumi|Fuleco
"""
for line in FACTS.strip().splitlines():
    parts = line.split("|")
    cat, q, a, opts = parts[0], parts[1], parts[2], parts[3:]
    add(cat, "f:" + hashlib.md5(q.encode()).hexdigest()[:8], q, a, opts)

counts = {k: len(v) for k, v in Q.items()}
print("available", counts, "total", sum(counts.values()))
final = [x for items in Q.values() for x in items]
# trim from the biggest generated categories down to exactly 1,000
order = ["plhigher", "plthird", "plbottom", "plseasons", "pldown", "plstreak", "plfirst"]
rng.shuffle(final)
while len(final) > 1000:
    for c in order:
        if len(final) <= 1000:
            break
        idx = next((i for i, x in enumerate(final) if x["c"] == c), None)
        if idx is not None:
            final.pop(idx)
print("final", len(final), collections.Counter(x["c"] for x in final))
with open(OUT, "w") as f:
    f.write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in final) + "\n]\n")
