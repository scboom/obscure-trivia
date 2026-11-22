"""Build the Music question bank (1,000 questions).

US chart questions are calculated from every Billboard Hot 100 since 1958 (utdata/rwd-billboard-data).
Everything else is hand-written from settled facts: famous songs and albums, artists, bands,
records, Eurovision winners, film songs and general music knowledge. Records that can change
are dated. No lyrics are quoted.
Usage: gen_music.py hot-100-current.csv OUT.json
"""
import sys, csv, json, random, collections, re

CSV, OUT = sys.argv[1:3]
rng = random.Random(20261123)
Q = collections.defaultdict(list)
SEEN = set()


def add(c, k, q, a, opts, x=None, ks=None):
    opts = [o for o in dict.fromkeys(opts) if o and o != a]
    if len(opts) != 3:
        raise SystemExit(f"bad options for {q!r}: {a!r} {opts}")
    if k in SEEN:
        return False
    SEEN.add(k)
    d = {"c": c, "k": k, "q": q, "a": a, "o": opts}
    if x:
        d["x"] = x
    if ks:
        d["ks"] = ks
    Q[c].append(d)
    return True


# ------------------------------------------------------------------ US number ones (Billboard Hot 100)
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with", "n'"}


def title_case(t):
    t = re.sub(r'\s*\(From "[^"]*"\)', "", t)
    words = t.split(" ")
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        out.append(lw if 0 < i < len(words) - 1 and lw in SMALL else w)
    return " ".join(out)


ACCENTS = {"Beyonce": "Beyoncé", "Sinead O'Connor": "Sinéad O'Connor", "Ace Of Base": "Ace of Base", "Celine Dion": "Céline Dion",
           "Michael Buble": "Michael Bublé", "Shakira Featuring Wyclef Jean": "Shakira featuring Wyclef Jean", "Jose Feliciano": "José Feliciano"}


def credit(p):
    for a, b in ACCENTS.items():
        p = p.replace(a, b)
    return p.replace(" Featuring ", " featuring ").replace(" With ", " with ")


def lead(p):
    return re.split(r" featuring | & | X | x | with | \+ |, | And ", credit(p))[0].strip()


def tkey(t):
    return "t:" + re.sub(r"[^a-z0-9]", "", t.lower())


def decades(d):
    """Three wrong decades near d, never later than the 2020s."""
    near = sorted({d - 30, d - 20, d - 10, d + 10, d + 20} - {d}, key=lambda x: (abs(x - d), rng.random()))
    return [f"{x}s" for x in near if 1940 <= x <= 2020][:3]


rows = [r for r in csv.DictReader(open(CSV)) if r["current_week"] == "1"]
last_week = max(r["chart_week"] for r in rows)
recent = sorted({r["chart_week"] for r in rows})[-10:]
songs = {}
for r in rows:
    key = (r["title"], r["performer"])
    s = songs.setdefault(key, {"title": title_case(r["title"]), "perf": credit(r["performer"]), "lead": lead(r["performer"]), "first": r["chart_week"], "weeks": 0, "active": False})
    s["weeks"] += 1
    s["first"] = min(s["first"], r["chart_week"])
    if r["chart_week"] in recent:
        s["active"] = True       # still at number one in the last few weeks: its total may still grow
for s in songs.values():
    s["year"] = int(s["first"][:4])
    s["id"] = tkey(s["title"])
# the well-known ones: a decent run at number one, from the mid-1960s on
POOL = [s for s in songs.values() if 1964 <= s["year"] <= 2025 and (s["weeks"] >= 3 or (s["year"] >= 1990 and s["weeks"] >= 2))]
POOL.sort(key=lambda s: (-s["weeks"], s["first"]))
print("US pool", len(POOL), file=sys.stderr)


def song_label(s):
    return f"{s['title']} ({s['lead']})"


def nearby(s, pool, years=6):
    return [o for o in pool if o is not s and abs(o["year"] - s["year"]) <= years and o["lead"] != s["lead"]]


for s in POOL[:230]:
    others = nearby(s, POOL)
    perfs = list(dict.fromkeys(o["perf"] for o in others if o["lead"] not in s["perf"] and s["lead"] not in o["perf"]))
    if len(perfs) < 3:
        continue
    add("usno1", "usno1:" + s["id"], f"Who had a US number one with '{s['title']}'?", s["perf"], rng.sample(perfs, 3),
        f"It first reached number one in the US in {s['year']} and stayed there for {s['weeks']} week{'s' if s['weeks'] != 1 else ''}.", ks=[s["id"]])

tries = 0
while len(Q["usfirst"]) < 55 and tries < 50000:
    tries += 1
    ss = sorted(rng.sample(POOL[:260], 4), key=lambda s: s["first"])
    years = [s["year"] for s in ss]
    if any(b - a < 3 for a, b in zip(years, years[1:])) or years[-1] - years[0] > 16:
        continue
    x = " · ".join(f"{song_label(s)}: {s['year']}" for s in ss) + "."
    add("usfirst", "usfirst:" + "|".join(sorted(s["id"] for s in ss)), "Which of these songs was a US number one first?", song_label(ss[0]),
        [song_label(s) for s in ss[1:]], x, ks=[s["id"] for s in ss])

WEEKPOOL = [s for s in POOL if not s["active"]]
tries = 0
while len(Q["usweeks"]) < 45 and tries < 50000:
    tries += 1
    ss = sorted(rng.sample(WEEKPOOL[:200], 4), key=lambda s: -s["weeks"])
    if ss[0]["weeks"] - ss[1]["weeks"] < 2:
        continue
    x = " · ".join(f"{song_label(s)}: {s['weeks']} weeks" for s in ss) + "."
    add("usweeks", "usweeks:" + "|".join(sorted(s["id"] for s in ss)), "Which of these spent the most weeks at number one in the US?", song_label(ss[0]),
        [song_label(s) for s in ss[1:]], x, ks=[s["id"] for s in ss])

for s in POOL[:260]:
    if len(Q["usdecade"]) >= 60:
        break
    if s["year"] % 10 in (0, 9) or s["id"] in {q["ks"][0] for q in Q["usno1"][:0]}:
        continue
    d = s["year"] // 10 * 10
    opts = decades(d)
    if len(opts) < 3:
        continue
    add("usdecade", "usdecade:" + s["id"], f"In which decade did '{s['title']}' by {s['lead']} top the US chart?", f"{d}s", opts,
        f"It reached number one in {s['year']}.", ks=[s["id"]])

# ------------------------------------------------------------------ famous songs (hand-checked)
S = lambda t, a, y: (t, a, y)
SONGS = [
    S("Wonderwall", "Oasis", 1995), S("Don't Look Back in Anger", "Oasis", 1996), S("Live Forever", "Oasis", 1994), S("Common People", "Pulp", 1995),
    S("Song 2", "Blur", 1997), S("Parklife", "Blur", 1994), S("Bitter Sweet Symphony", "The Verve", 1997), S("Angels", "Robbie Williams", 1997),
    S("Rock DJ", "Robbie Williams", 2000), S("Back for Good", "Take That", 1995), S("Rule the World", "Take That", 2007), S("Patience", "Take That", 2006),
    S("Chasing Cars", "Snow Patrol", 2006), S("Yellow", "Coldplay", 2000), S("Fix You", "Coldplay", 2005), S("The Scientist", "Coldplay", 2002),
    S("Mr. Brightside", "The Killers", 2004), S("Valerie", "Mark Ronson featuring Amy Winehouse", 2007), S("Rehab", "Amy Winehouse", 2006),
    S("Shout Out to My Ex", "Little Mix", 2016), S("Black Magic", "Little Mix", 2015), S("What Makes You Beautiful", "One Direction", 2011),
    S("Story of My Life", "One Direction", 2013), S("Wannabe", "Spice Girls", 1996), S("Spice Up Your Life", "Spice Girls", 1997),
    S("Sound of the Underground", "Girls Aloud", 2002), S("Don't Stop Me Now", "Queen", 1979), S("Bohemian Rhapsody", "Queen", 1975),
    S("We Will Rock You", "Queen", 1977), S("Under Pressure", "Queen and David Bowie", 1981), S("Heroes", "David Bowie", 1977),
    S("Space Oddity", "David Bowie", 1969), S("Imagine", "John Lennon", 1971), S("Hey Jude", "The Beatles", 1968), S("Yesterday", "The Beatles", 1965),
    S("Here Comes the Sun", "The Beatles", 1969), S("(I Can't Get No) Satisfaction", "The Rolling Stones", 1965), S("Paint It Black", "The Rolling Stones", 1966),
    S("Waterloo", "ABBA", 1974), S("Dancing Queen", "ABBA", 1976), S("Mamma Mia", "ABBA", 1975), S("Running Up That Hill", "Kate Bush", 1985),
    S("Wuthering Heights", "Kate Bush", 1978), S("Stairway to Heaven", "Led Zeppelin", 1971), S("Smells Like Teen Spirit", "Nirvana", 1991),
    S("Sweet Child o' Mine", "Guns N' Roses", 1987), S("Livin' on a Prayer", "Bon Jovi", 1986), S("Africa", "Toto", 1982),
    S("Mr. Blue Sky", "Electric Light Orchestra", 1978), S("Sweet Caroline", "Neil Diamond", 1969), S("Hotel California", "Eagles", 1977),
    S("Don't Stop Believin'", "Journey", 1981), S("Billie Jean", "Michael Jackson", 1983), S("Thriller", "Michael Jackson", 1983),
    S("Like a Prayer", "Madonna", 1989), S("Vogue", "Madonna", 1990), S("Purple Rain", "Prince", 1984), S("Take On Me", "a-ha", 1985),
    S("Tainted Love", "Soft Cell", 1981), S("Don't You Want Me", "The Human League", 1981), S("Come On Eileen", "Dexys Midnight Runners", 1982),
    S("Karma Chameleon", "Culture Club", 1983), S("Wake Me Up Before You Go-Go", "Wham!", 1984), S("Last Christmas", "Wham!", 1984),
    S("Never Gonna Give You Up", "Rick Astley", 1987), S("Toxic", "Britney Spears", 2004), S("...Baby One More Time", "Britney Spears", 1998),
    S("Crazy in Love", "Beyoncé featuring Jay-Z", 2003), S("Single Ladies (Put a Ring on It)", "Beyoncé", 2008), S("Umbrella", "Rihanna featuring Jay-Z", 2007),
    S("Rolling in the Deep", "Adele", 2010), S("Someone Like You", "Adele", 2011), S("Hello", "Adele", 2015), S("Shape of You", "Ed Sheeran", 2017),
    S("Perfect", "Ed Sheeran", 2017), S("Thinking Out Loud", "Ed Sheeran", 2014), S("Bad Habits", "Ed Sheeran", 2021), S("Someone You Loved", "Lewis Capaldi", 2018),
    S("Bad Guy", "Billie Eilish", 2019), S("Levitating", "Dua Lipa", 2020), S("Don't Start Now", "Dua Lipa", 2019), S("New Rules", "Dua Lipa", 2017),
    S("As It Was", "Harry Styles", 2022), S("Watermelon Sugar", "Harry Styles", 2019), S("Blinding Lights", "The Weeknd", 2019),
    S("Drivers License", "Olivia Rodrigo", 2021), S("Espresso", "Sabrina Carpenter", 2024), S("Flowers", "Miley Cyrus", 2023), S("Anti-Hero", "Taylor Swift", 2022),
    S("Shake It Off", "Taylor Swift", 2014), S("Love Story", "Taylor Swift", 2008), S("Murder on the Dancefloor", "Sophie Ellis-Bextor", 2001),
    S("Freed from Desire", "Gala", 1996), S("Seven Nation Army", "The White Stripes", 2003), S("I Bet You Look Good on the Dancefloor", "Arctic Monkeys", 2005),
    S("Do I Wanna Know?", "Arctic Monkeys", 2013), S("Uptown Funk", "Mark Ronson featuring Bruno Mars", 2014), S("Happy", "Pharrell Williams", 2013),
    S("Gangnam Style", "Psy", 2012), S("Dynamite", "BTS", 2020), S("Viva la Vida", "Coldplay", 2008), S("Use Somebody", "Kings of Leon", 2008),
    S("Hallelujah", "Leonard Cohen", 1984), S("Hound Dog", "Elvis Presley", 1956), S("Jailhouse Rock", "Elvis Presley", 1957), S("Johnny B. Goode", "Chuck Berry", 1958),
    S("Respect", "Aretha Franklin", 1967), S("What's Going On", "Marvin Gaye", 1971), S("Superstition", "Stevie Wonder", 1972), S("Stayin' Alive", "Bee Gees", 1977),
    S("I Will Survive", "Gloria Gaynor", 1978), S("Le Freak", "Chic", 1978), S("Y.M.C.A.", "Village People", 1978), S("Born to Run", "Bruce Springsteen", 1975),
    S("Rocket Man", "Elton John", 1972), S("Your Song", "Elton John", 1970), S("Tiny Dancer", "Elton John", 1971), S("Total Eclipse of the Heart", "Bonnie Tyler", 1983),
    S("I Wanna Dance with Somebody", "Whitney Houston", 1987), S("Careless Whisper", "George Michael", 1984), S("Faith", "George Michael", 1987),
    S("Everybody Wants to Rule the World", "Tears for Fears", 1985), S("Sweet Dreams (Are Made of This)", "Eurythmics", 1983),
    S("Girls Just Want to Have Fun", "Cyndi Lauper", 1983), S("Zombie", "The Cranberries", 1994), S("Creep", "Radiohead", 1992),
    S("Teenage Dirtbag", "Wheatus", 2000), S("All Star", "Smash Mouth", 1999), S("Bring Me to Life", "Evanescence", 2003), S("In the End", "Linkin Park", 2001),
    S("Numb", "Linkin Park", 2003), S("Chandelier", "Sia", 2014), S("Royals", "Lorde", 2013), S("Somebody That I Used to Know", "Gotye featuring Kimbra", 2011),
    S("Pompeii", "Bastille", 2013), S("Riptide", "Vance Joy", 2013), S("Shotgun", "George Ezra", 2018), S("Budapest", "George Ezra", 2014),
    S("Dance Monkey", "Tones and I", 2019), S("Heat Waves", "Glass Animals", 2020), S("Sweater Weather", "The Neighbourhood", 2012), S("Stay with Me", "Sam Smith", 2014),
    S("Hold Back the River", "James Bay", 2014), S("Love Yourself", "Justin Bieber", 2015), S("Firework", "Katy Perry", 2010), S("Roar", "Katy Perry", 2013),
    S("Poker Face", "Lady Gaga", 2008), S("Bad Romance", "Lady Gaga", 2009), S("Titanium", "David Guetta featuring Sia", 2011), S("Wake Me Up", "Avicii", 2013),
    S("Levels", "Avicii", 2011), S("Summer", "Calvin Harris", 2014), S("One Kiss", "Calvin Harris and Dua Lipa", 2018), S("Sandstorm", "Darude", 1999),
    S("Cotton Eye Joe", "Rednex", 1994), S("Mambo No. 5", "Lou Bega", 1999), S("Barbie Girl", "Aqua", 1997), S("Ice Ice Baby", "Vanilla Ice", 1990),
    S("U Can't Touch This", "MC Hammer", 1990), S("Stan", "Eminem featuring Dido", 2000), S("Without Me", "Eminem", 2002), S("Hotline Bling", "Drake", 2015),
]
names = collections.Counter(t for t, _, _ in SONGS)
assert all(v == 1 for v in names.values()), [n for n, v in names.items() if v > 1]
ARTISTS_OF = collections.defaultdict(list)
for t, a, y in SONGS:
    ARTISTS_OF[a].append(t)


def era(y, items, key, years=8, n=3, exclude=()):
    near = list(dict.fromkeys(key(i) for i in items if abs(i[2] - y) <= years and key(i) not in exclude))
    if len(near) < n:
        near = list(dict.fromkeys(key(i) for i in items if key(i) not in exclude))
    return rng.sample(near, n)


def same_act(a, b):
    return a == b or a in b or b in a


for t, a, y in SONGS:
    pool = [s for s in SONGS if not same_act(s[1], a)]
    add("song", "song:" + t, f"Who is the song '{t}' by?", a, era(y, pool, lambda s: s[1]), f"It came out in {y}.", ks=[tkey(t)])
acts = [a for a in ARTISTS_OF if not any(same_act(a, b) for b in ARTISTS_OF if b != a)]
rng.shuffle(acts)
for a in acts[:70]:
    t = rng.choice(ARTISTS_OF[a]); y = next(s[2] for s in SONGS if s[0] == t)
    pool = [s for s in SONGS if not same_act(s[1], a)]
    add("songby", "songby:" + a, f"Which of these songs is by {a}?", t, era(y, pool, lambda s: s[0]), ks=[tkey(t)])
dec_songs = [s for s in SONGS if s[2] % 10 not in (0, 9)]
rng.shuffle(dec_songs)
for t, a, y in dec_songs[:55]:
    d = y // 10 * 10
    opts = decades(d)
    add("songdecade", "songdecade:" + t, f"In which decade did '{t}' by {a} come out?", f"{d}s", opts, f"It came out in {y}.", ks=[tkey(t)])
tries = 0
while len(Q["songfirst"]) < 35 and tries < 20000:
    tries += 1
    ss = sorted(rng.sample(SONGS, 4), key=lambda s: s[2])
    ys = [s[2] for s in ss]
    if any(b - a < 3 for a, b in zip(ys, ys[1:])) or ys[-1] - ys[0] > 30:
        continue
    lab = lambda s: f"{s[0]} ({s[1]})"
    add("songfirst", "songfirst:" + "|".join(sorted(s[0] for s in ss)), "Which of these songs came out first?", lab(ss[0]), [lab(s) for s in ss[1:]],
        " · ".join(f"{lab(s)}: {s[2]}" for s in ss) + ".", ks=[tkey(s[0]) for s in ss])

# ------------------------------------------------------------------ albums
ALBUMS = [("Thriller", "Michael Jackson", 1982), ("Bad", "Michael Jackson", 1987), ("Off the Wall", "Michael Jackson", 1979), ("Rumours", "Fleetwood Mac", 1977),
          ("Abbey Road", "The Beatles", 1969), ("Sgt. Pepper's Lonely Hearts Club Band", "The Beatles", 1967), ("The Dark Side of the Moon", "Pink Floyd", 1973),
          ("The Wall", "Pink Floyd", 1979), ("(What's the Story) Morning Glory?", "Oasis", 1995), ("Definitely Maybe", "Oasis", 1994), ("21", "Adele", 2011),
          ("25", "Adele", 2015), ("÷ (Divide)", "Ed Sheeran", 2017), ("1989", "Taylor Swift", 2014), ("Midnights", "Taylor Swift", 2022),
          ("Folklore", "Taylor Swift", 2020), ("Lemonade", "Beyoncé", 2016), ("Back to Black", "Amy Winehouse", 2006), ("Nevermind", "Nirvana", 1991),
          ("Purple Rain", "Prince", 1984), ("Born in the U.S.A.", "Bruce Springsteen", 1984), ("Appetite for Destruction", "Guns N' Roses", 1987),
          ("A Night at the Opera", "Queen", 1975), ("Like a Prayer", "Madonna", 1989), ("Whatever People Say I Am, That's What I'm Not", "Arctic Monkeys", 2006),
          ("AM", "Arctic Monkeys", 2013), ("A Rush of Blood to the Head", "Coldplay", 2002), ("Parachutes", "Coldplay", 2000), ("OK Computer", "Radiohead", 1997),
          ("The Marshall Mathers LP", "Eminem", 2000), ("Future Nostalgia", "Dua Lipa", 2020), ("Sour", "Olivia Rodrigo", 2021),
          ("When We All Fall Asleep, Where Do We Go?", "Billie Eilish", 2019), ("Harry's House", "Harry Styles", 2022), ("Hounds of Love", "Kate Bush", 1985),
          ("Parklife", "Blur", 1994), ("Spice", "Spice Girls", 1996), ("Brothers in Arms", "Dire Straits", 1985), ("Bat Out of Hell", "Meat Loaf", 1977),
          ("Hotel California", "Eagles", 1976), ("Back in Black", "AC/DC", 1980), ("The Joshua Tree", "U2", 1987), ("Jagged Little Pill", "Alanis Morissette", 1995),
          ("Graceland", "Paul Simon", 1986), ("Random Access Memories", "Daft Punk", 2013), ("Scorpion", "Drake", 2018), ("After Hours", "The Weeknd", 2020),
          ("Starboy", "The Weeknd", 2016), ("Un Verano Sin Ti", "Bad Bunny", 2022), ("SOS", "SZA", 2022), ("Renaissance", "Beyoncé", 2022),
          ("Short n' Sweet", "Sabrina Carpenter", 2024), ("The Tortured Poets Department", "Taylor Swift", 2024), ("Pet Sounds", "The Beach Boys", 1966),
          ("Led Zeppelin IV", "Led Zeppelin", 1971), ("The Rise and Fall of Ziggy Stardust and the Spiders from Mars", "David Bowie", 1972),
          ("Songs in the Key of Life", "Stevie Wonder", 1976), ("Arrival", "ABBA", 1976), ("Urban Hymns", "The Verve", 1997), ("Come Away with Me", "Norah Jones", 2002),
          ("Fearless", "Taylor Swift", 2008), ("Blue", "Joni Mitchell", 1971), ("x (Multiply)", "Ed Sheeran", 2014), ("Born This Way", "Lady Gaga", 2011)]
for t, a, y in ALBUMS:
    pool = [s for s in ALBUMS if s[1] != a]
    add("album", "album:" + t, f"Who released the album '{t}'?", a, era(y, pool, lambda s: s[1]), f"It came out in {y}.", ks=["album:" + t])
tries = 0
while len(Q["albumfirst"]) < 14 and tries < 20000:
    tries += 1
    ss = sorted(rng.sample(ALBUMS, 4), key=lambda s: s[2])
    ys = [s[2] for s in ss]
    if any(b - a < 3 for a, b in zip(ys, ys[1:])) or ys[-1] - ys[0] > 30:
        continue
    lab = lambda s: f"{s[0]} ({s[1]})"
    add("albumfirst", "albumfirst:" + "|".join(sorted(s[0] for s in ss)), "Which of these albums came out first?", lab(ss[0]), [lab(s) for s in ss[1:]],
        " · ".join(f"{lab(s)}: {s[2]}" for s in ss) + ".", ks=["album:" + s[0] for s in ss])

# ------------------------------------------------------------------ artists: real names, bands, where they're from
REAL = [("Elton John", "Reginald Dwight"), ("Freddie Mercury", "Farrokh Bulsara"), ("Lady Gaga", "Stefani Germanotta"), ("Bruno Mars", "Peter Hernandez"),
        ("Katy Perry", "Katheryn Hudson"), ("Sting", "Gordon Sumner"), ("Bono", "Paul Hewson"), ("Stormzy", "Michael Omari"), ("Lizzo", "Melissa Jefferson"),
        ("Post Malone", "Austin Post"), ("Eminem", "Marshall Mathers"), ("Drake", "Aubrey Graham"), ("Rihanna", "Robyn Fenty"), ("Snoop Dogg", "Calvin Broadus"),
        ("Jay-Z", "Shawn Carter"), ("50 Cent", "Curtis Jackson"), ("The Weeknd", "Abel Tesfaye"), ("Cher", "Cherilyn Sarkisian"), ("Bob Dylan", "Robert Zimmerman"),
        ("David Bowie", "David Jones"), ("Cliff Richard", "Harry Webb"), ("Tom Jones", "Thomas Woodward"), ("Lorde", "Ella Yelich-O'Connor"),
        ("Skepta", "Joseph Adenuga"), ("Dave", "David Omoregie"), ("Jessie J", "Jessica Cornish"), ("Lil Nas X", "Montero Hill"), ("Little Simz", "Simbiatu Ajikawo"),
        ("Ringo Starr", "Richard Starkey"), ("Slash", "Saul Hudson"), ("Iggy Pop", "James Osterberg"), ("Marilyn Manson", "Brian Warner"), ("Elvis Costello", "Declan MacManus"),
        ("Alice Cooper", "Vincent Furnier"), ("Boy George", "George O'Dowd")]
for star, real in REAL:
    add("realname", "real:" + star, f"What is {star}'s real name?", real, rng.sample([r for s, r in REAL if s != star], 3), ks=["artist:" + star])
BANDS = [("Freddie Mercury", "Queen"), ("Brian May", "Queen"), ("Mick Jagger", "The Rolling Stones"), ("Keith Richards", "The Rolling Stones"),
         ("Paul McCartney", "The Beatles"), ("Ringo Starr", "The Beatles"), ("Liam Gallagher", "Oasis"), ("Damon Albarn", "Blur"), ("Jarvis Cocker", "Pulp"),
         ("Chris Martin", "Coldplay"), ("Alex Turner", "Arctic Monkeys"), ("Thom Yorke", "Radiohead"), ("Bono", "U2"), ("Kurt Cobain", "Nirvana"),
         ("Robert Plant", "Led Zeppelin"), ("Ozzy Osbourne", "Black Sabbath"), ("Roger Daltrey", "The Who"), ("Sting", "The Police"), ("Phil Collins", "Genesis"),
         ("Brandon Flowers", "The Killers"), ("Harry Styles", "One Direction"), ("Niall Horan", "One Direction"), ("Gary Barlow", "Take That"),
         ("Cheryl", "Girls Aloud"), ("Perrie Edwards", "Little Mix"), ("Geri Halliwell", "Spice Girls"), ("Beyoncé", "Destiny's Child"),
         ("Justin Timberlake", "NSYNC"), ("Debbie Harry", "Blondie"), ("Annie Lennox", "Eurythmics"), ("Simon Le Bon", "Duran Duran"), ("Morrissey", "The Smiths"),
         ("Ian Brown", "The Stone Roses"), ("Richard Ashcroft", "The Verve"), ("Gwen Stefani", "No Doubt"), ("Adam Levine", "Maroon 5"),
         ("Chester Bennington", "Linkin Park"), ("Billie Joe Armstrong", "Green Day"), ("Axl Rose", "Guns N' Roses"), ("Angus Young", "AC/DC"),
         ("Steven Tyler", "Aerosmith"), ("Dave Grohl (after Nirvana)", "Foo Fighters"), ("Florence Welch", "Florence + the Machine"), ("Anthony Kiedis", "Red Hot Chili Peppers")]
for who, band in BANDS:
    add("band", "band:" + who, f"Which band was {who} in?" if "(" not in who else "Which band did Dave Grohl start after Nirvana?", band,
        rng.sample(sorted({b for _, b in BANDS if b != band}), 3), ks=["band:" + band])
SPICE = [("Posh Spice", "Victoria Beckham"), ("Scary Spice", "Mel B"), ("Sporty Spice", "Mel C"), ("Baby Spice", "Emma Bunton"), ("Ginger Spice", "Geri Halliwell")]
for nick, who in SPICE:
    add("band", "spice:" + nick, f"Which Spice Girl was known as {nick}?", who, [w for n, w in SPICE if n != nick][:3], ks=["band:Spice Girls"])
CITY = [("The Beatles", "Liverpool"), ("Oasis", "Manchester"), ("The Smiths", "Manchester"), ("The Stone Roses", "Manchester"), ("Arctic Monkeys", "Sheffield"),
        ("Pulp", "Sheffield"), ("Def Leppard", "Sheffield"), ("Black Sabbath", "Birmingham"), ("Duran Duran", "Birmingham"), ("UB40", "Birmingham"),
        ("Electric Light Orchestra", "Birmingham"), ("Queen", "London"), ("The Rolling Stones", "London"), ("Coldplay", "London"), ("Franz Ferdinand", "Glasgow"),
        ("Simple Minds", "Glasgow"), ("Travis", "Glasgow"), ("The Killers", "Las Vegas"), ("Pearl Jam", "Seattle"), ("Kings of Leon", "Nashville"),
        ("U2", "Dublin"), ("The Cranberries", "Limerick"), ("AC/DC", "Sydney"), ("a-ha", "Oslo"), ("ABBA", "Stockholm"), ("BTS", "Seoul")]
UKCITIES = ["Liverpool", "Manchester", "Sheffield", "Birmingham", "London", "Glasgow", "Leeds", "Bristol", "Newcastle"]
WORLDCITIES = ["Las Vegas", "Seattle", "Nashville", "Dublin", "Limerick", "Sydney", "Oslo", "Stockholm", "Seoul", "Los Angeles", "New York", "Melbourne", "Copenhagen", "Tokyo"]
for band, city in CITY:
    pool = UKCITIES if city in UKCITIES else WORLDCITIES
    add("from", "city:" + band, f"Which city did {band} come from?", city, rng.sample([c for c in pool if c != city], 3), ks=["band:" + band])
COUNTRY = [("Rihanna", "Barbados"), ("Shakira", "Colombia"), ("Bob Marley", "Jamaica"), ("Björk", "Iceland"), ("Céline Dion", "Canada"),
           ("Justin Bieber", "Canada"), ("Drake", "Canada"), ("The Weeknd", "Canada"), ("Kylie Minogue", "Australia"), ("Sia", "Australia"),
           ("Lorde", "New Zealand"), ("Bad Bunny", "Puerto Rico"), ("Enrique Iglesias", "Spain"), ("Rosalía", "Spain"), ("Stromae", "Belgium"),
           ("Avicii", "Sweden"), ("Lewis Capaldi", "Scotland"), ("Tom Jones", "Wales"), ("Shirley Bassey", "Wales"), ("Enya", "Ireland"), ("Hozier", "Ireland"),
           ("Psy", "South Korea"), ("Shania Twain", "Canada"), ("Avril Lavigne", "Canada"), ("Tones and I", "Australia"), ("Daft Punk", "France"),
           ("Kraftwerk", "Germany"), ("Rammstein", "Germany"), ("Måneskin", "Italy"), ("ABBA", "Sweden")]
CPOOL = sorted({c for _, c in COUNTRY} | {"USA", "England", "Mexico", "Brazil", "Norway", "Denmark", "Netherlands", "Japan"})
for who, ctry in COUNTRY:
    add("from", "ctry:" + who, f"Which country is {who} from?", ctry, rng.sample([c for c in CPOOL if c != ctry], 3), ks=["artist:" + who])

# ------------------------------------------------------------------ hand-written facts
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
FACTS = [
    # the most popular songs and records
    F("record", "Which song has been streamed the most times on Spotify?", "Blinding Lights (The Weeknd)", ["Shape of You (Ed Sheeran)", "Someone You Loved (Lewis Capaldi)", "Dance Monkey (Tones and I)"], "It became the most-streamed song on Spotify in 2023 and was the first to pass 4 billion streams."),
    F("record", "Which was the first song to pass 3 billion streams on Spotify?", "Shape of You (Ed Sheeran)", ["Blinding Lights (The Weeknd)", "Despacito (Luis Fonsi)", "One Dance (Drake)"], "It got there in December 2021."),
    F("record", "What is the most-viewed video ever on YouTube?", "Baby Shark Dance", ["Despacito", "Gangnam Style", "See You Again"]),
    F("record", "Which was the first YouTube video to reach 1 billion views?", "Gangnam Style (Psy)", ["Baby (Justin Bieber)", "Despacito", "Shape of You"], "It got there in December 2012."),
    F("record", "Which music video was the first to reach 5 billion views on YouTube?", "Despacito", ["Gangnam Style", "Shape of You", "See You Again"]),
    F("record", "What is the best-selling single of all time?", "White Christmas (Bing Crosby)", ["Candle in the Wind 1997 (Elton John)", "Shape of You (Ed Sheeran)", "Bohemian Rhapsody (Queen)"], "It has sold an estimated 50 million copies."),
    F("record", "What is the best-selling album of all time?", "Thriller (Michael Jackson)", ["Back in Black (AC/DC)", "The Dark Side of the Moon (Pink Floyd)", "Rumours (Fleetwood Mac)"]),
    F("record", "What is the UK's best-selling single of all time?", "Candle in the Wind 1997 (Elton John)", ["Do They Know It's Christmas? (Band Aid)", "Bohemian Rhapsody (Queen)", "Shape of You (Ed Sheeran)"]),
    F("record", "What is the UK's best-selling album of all time?", "Greatest Hits (Queen)", ["Gold: Greatest Hits (ABBA)", "Sgt. Pepper's Lonely Hearts Club Band (The Beatles)", "21 (Adele)"]),
    F("record", "Who are the best-selling music artists of all time?", "The Beatles", ["Elvis Presley", "Michael Jackson", "Madonna"]),
    F("record", "Who has won the most Grammy Awards?", "Beyoncé", ["Taylor Swift", "Michael Jackson", "Adele"]),
    F("record", "Who was the first artist to win the Grammy for Album of the Year four times?", "Taylor Swift", ["Adele", "Stevie Wonder", "Beyoncé"], "Her fourth was for Midnights in 2024."),
    F("record", "Which act has had the most number one singles in the UK?", "Elvis Presley", ["The Beatles", "Cliff Richard", "Madonna"]),
    F("record", "Which act has had the most number one singles in the US?", "The Beatles", ["Elvis Presley", "Madonna", "Michael Jackson"], "They had 20. Mariah Carey is next with 19."),
    F("record", "Which song spent 16 weeks in a row at number one in the UK, a record that still stands?", "(Everything I Do) I Do It for You (Bryan Adams)", ["One Dance (Drake)", "Shape of You (Ed Sheeran)", "Bohemian Rhapsody (Queen)"], "That was in 1991."),
    F("record", "Which song was the first ever UK number one, in 1952?", "Here in My Heart (Al Martino)", ["Heartbreak Hotel (Elvis Presley)", "Rock Around the Clock (Bill Haley)", "Love Me Do (The Beatles)"]),
    F("record", "Which song has been the UK Christmas number one twice, in 1975 and 1991?", "Bohemian Rhapsody (Queen)", ["Do They Know It's Christmas? (Band Aid)", "Last Christmas (Wham!)", "Mull of Kintyre (Wings)"]),
    F("record", "Which charity song was the UK Christmas number one in 1984?", "Do They Know It's Christmas? (Band Aid)", ["We Are the World (USA for Africa)", "Last Christmas (Wham!)", "Merry Xmas Everybody (Slade)"]),
    F("record", "Which song beat the X Factor winner to be the UK Christmas number one in 2009?", "Killing in the Name (Rage Against the Machine)", ["Fairytale of New York (The Pogues)", "Bohemian Rhapsody (Queen)", "Hallelujah (Alexandra Burke)"]),
    F("record", "Who had five UK Christmas number ones in a row, from 2018 to 2022?", "LadBaby", ["The Beatles", "Spice Girls", "Ed Sheeran"], "All five were charity songs about sausage rolls."),
    F("record", "Which song finally became the UK Christmas number one in 2023, 39 years after it came out?", "Last Christmas (Wham!)", ["All I Want for Christmas Is You (Mariah Carey)", "Fairytale of New York (The Pogues)", "Merry Christmas Everyone (Shakin' Stevens)"]),
    F("record", "Who had three UK Christmas number ones in a row from 1996 to 1998?", "Spice Girls", ["Westlife", "Take That", "Cliff Richard"]),
    F("record", "Which was the first video ever played on MTV, in 1981?", "Video Killed the Radio Star (The Buggles)", ["Thriller (Michael Jackson)", "Money for Nothing (Dire Straits)", "Take On Me (a-ha)"]),
    F("record", "Which Taylor Swift tour became the highest-earning concert tour ever?", "The Eras Tour", ["The Red Tour", "The 1989 World Tour", "The Reputation Stadium Tour"]),
    F("record", "Which Ed Sheeran tour was the highest-earning ever until the Eras Tour?", "The ÷ (Divide) Tour", ["The + (Plus) Tour", "The x (Multiply) Tour", "The Mathematics Tour"]),
    # history, festivals and events
    F("music", "In which year was Live Aid?", "1985", ["1975", "1980", "1990"]),
    F("music", "Live Aid was held at Wembley Stadium and which other stadium?", "JFK Stadium, Philadelphia", ["Madison Square Garden, New York", "The Rose Bowl, Pasadena", "Yankee Stadium, New York"]),
    F("music", "Who organised Band Aid and Live Aid with Midge Ure?", "Bob Geldof", ["Bono", "Elton John", "Paul McCartney"]),
    F("music", "In which year was the Woodstock festival?", "1969", ["1959", "1965", "1974"]),
    F("music", "Glastonbury Festival is held near which village?", "Pilton, Somerset", ["Glastonbury Tor itself", "Reading, Berkshire", "Knebworth, Hertfordshire"]),
    F("music", "Whose farm hosts the Glastonbury Festival?", "Michael Eavis's", ["Paul McCartney's", "Elton John's", "Richard Branson's"]),
    F("music", "Which city is home to the famous Abbey Road Studios?", "London", ["Liverpool", "Manchester", "New York"]),
    F("music", "Which city is known as 'Music City' and is the home of country music?", "Nashville", ["Memphis", "Austin", "New Orleans"]),
    F("music", "Elvis Presley's home, Graceland, is in which city?", "Memphis", ["Nashville", "Las Vegas", "Tupelo"]),
    F("music", "Motown Records started in which city?", "Detroit", ["Chicago", "Memphis", "New York"]),
    F("music", "In which city did The Beatles play hundreds of club gigs before they were famous?", "Hamburg", ["Berlin", "Amsterdam", "Paris"]),
    F("music", "From which club in Liverpool did The Beatles rise to fame?", "The Cavern Club", ["The Hacienda", "The Marquee", "The 100 Club"]),
    F("music", "Which TV talent show did One Direction come from?", "The X Factor", ["Britain's Got Talent", "Pop Idol", "The Voice"], "They were put together on the show in 2010 and finished third."),
    F("music", "Which TV talent show did Little Mix win in 2011?", "The X Factor", ["Britain's Got Talent", "The Voice", "Popstars"]),
    F("music", "Which singer became famous after Britain's Got Talent in 2009?", "Susan Boyle", ["Leona Lewis", "Olly Murs", "Ella Henderson"]),
    F("music", "Britpop's famous 1995 'battle' was between Oasis and which band?", "Blur", ["Pulp", "Suede", "The Verve"]),
    F("music", "What is the name of the yearly British music awards show?", "The BRIT Awards", ["The Grammys", "The Mercury Awards", "The Ivors"]),
    F("music", "Which K-pop group became the first to have a song debut at number one in the US, with 'Dynamite'?", "BTS", ["Blackpink", "EXO", "Stray Kids"]),
    F("music", "Which Swedish group won Eurovision with 'Waterloo' before becoming one of the best-selling acts ever?", "ABBA", ["Roxette", "Ace of Base", "Europe"]),
    # instruments and terms
    F("music", "How many strings does a standard guitar have?", "6", ["4", "5", "12"]),
    F("music", "How many strings does a standard bass guitar have?", "4", ["3", "5", "6"]),
    F("music", "How many keys does a standard piano have?", "88", ["66", "76", "100"]),
    F("music", "How many lines are on a musical stave?", "5", ["4", "6", "7"]),
    F("music", "In music, what does 'forte' mean?", "Loud", ["Quiet", "Fast", "Slow"]),
    F("music", "In music, what does 'piano' mean as an instruction?", "Quietly", ["Loudly", "Quickly", "Smoothly"]),
    F("music", "In music, what does 'tempo' mean?", "Speed", ["Volume", "Pitch", "Key"]),
    F("music", "What does BPM stand for in music?", "Beats per minute", ["Bass per measure", "Bars per melody", "Beats per measure"]),
    F("music", "What is a group of three musicians called?", "A trio", ["A duet", "A quartet", "A quintet"]),
    F("music", "What is a group of four musicians called?", "A quartet", ["A trio", "A quintet", "A sextet"]),
    F("music", "Which instrument has pedals, a soundboard and 47 strings?", "A concert harp", ["A grand piano", "A cello", "A sitar"]),
    F("music", "Which of these is a brass instrument?", "Trumpet", ["Clarinet", "Flute", "Oboe"]),
    F("music", "Which of these is a woodwind instrument?", "Clarinet", ["Trumpet", "Trombone", "Tuba"]),
    F("music", "Which of these string instruments is the biggest?", "Double bass", ["Cello", "Viola", "Violin"]),
    F("music", "What do you call the stick a conductor uses?", "A baton", ["A wand", "A bow", "A pick"]),
    F("music", "What is the small flat piece used to strum a guitar called?", "A plectrum (pick)", ["A capo", "A fret", "A bridge"]),
    F("music", "What does a capo do on a guitar?", "Raises the pitch of all the strings", ["Tunes the guitar", "Makes it louder", "Mutes the strings"]),
    F("music", "What are the metal strips across a guitar's neck called?", "Frets", ["Bridges", "Pegs", "Pickups"]),
    F("music", "The Great Highland bagpipe comes from which country?", "Scotland", ["Ireland", "Wales", "Spain"]),
    F("music", "Which country do the steel drums come from?", "Trinidad and Tobago", ["Jamaica", "Cuba", "Brazil"]),
    F("music", "Which country did reggae music come from?", "Jamaica", ["Barbados", "Trinidad and Tobago", "Cuba"]),
    F("music", "Which country did K-pop come from?", "South Korea", ["Japan", "China", "Thailand"]),
    F("music", "Which city is the birthplace of jazz?", "New Orleans", ["Chicago", "New York", "Memphis"]),
    F("music", "Grime music started in which city?", "London", ["Manchester", "Birmingham", "Bristol"]),
    F("music", "Which composer wrote 'The Four Seasons'?", "Vivaldi", ["Mozart", "Bach", "Beethoven"]),
    F("music", "Which composer kept writing music after going deaf?", "Beethoven", ["Mozart", "Chopin", "Handel"]),
    F("music", "Which composer wrote 'The Nutcracker'?", "Tchaikovsky", ["Mozart", "Strauss", "Vivaldi"]),
    F("music", "Which composer wrote 'The Magic Flute'?", "Mozart", ["Beethoven", "Verdi", "Wagner"]),
    F("music", "How old was Mozart when he wrote his first pieces of music?", "5", ["10", "15", "20"]),
    F("music", "Which singer is known as the 'Queen of Pop'?", "Madonna", ["Britney Spears", "Kylie Minogue", "Beyoncé"]),
    F("music", "Which singer is known as the 'King of Pop'?", "Michael Jackson", ["Elvis Presley", "Prince", "Justin Timberlake"]),
    F("music", "Who is known as 'The King of Rock and Roll'?", "Elvis Presley", ["Chuck Berry", "Little Richard", "Jerry Lee Lewis"]),
    F("music", "Who is known as 'The Boss'?", "Bruce Springsteen", ["Bon Jovi", "Bob Dylan", "Tom Petty"]),
    F("music", "Taylor Swift's fans are known as what?", "Swifties", ["Beliebers", "Little Monsters", "Arianators"]),
    F("music", "Lady Gaga's fans are known as what?", "Little Monsters", ["Swifties", "Beliebers", "The Beyhive"]),
    F("music", "Beyoncé's fans are known as what?", "The Beyhive", ["Little Monsters", "Swifties", "Barbz"]),
    F("music", "Justin Bieber's fans are known as what?", "Beliebers", ["Swifties", "Directioners", "Little Monsters"]),
    F("music", "One Direction's fans are known as what?", "Directioners", ["Beliebers", "Mixers", "Swifties"]),
    F("music", "Ed Sheeran's album titles are mostly what?", "Maths symbols", ["Colours", "Numbers in words", "Planet names"]),
    F("music", "Adele's albums '19', '21', '25' and '30' are named after what?", "Her age when she made them", ["Track counts", "Chart positions", "Her house numbers"]),
    F("music", "Which Beatles album cover shows the band walking across a zebra crossing?", "Abbey Road", ["Revolver", "Help!", "Let It Be"]),
    F("music", "Which Pink Floyd album cover shows a prism splitting light into a rainbow?", "The Dark Side of the Moon", ["The Wall", "Wish You Were Here", "Animals"]),
    F("music", "Which Nirvana album cover shows a baby swimming after a dollar bill?", "Nevermind", ["In Utero", "Bleach", "MTV Unplugged in New York"]),
    F("music", "Which instrument did Jimi Hendrix famously play?", "Guitar", ["Drums", "Piano", "Saxophone"]),
    F("music", "Which instrument did Ringo Starr play in The Beatles?", "Drums", ["Bass guitar", "Lead guitar", "Keyboards"]),
    F("music", "Which instrument is Lang Lang famous for playing?", "Piano", ["Violin", "Cello", "Guitar"]),
    F("music", "Which instrument is Kenny G famous for playing?", "Saxophone", ["Trumpet", "Clarinet", "Flute"]),
    # films and TV
    F("film", "Which film is 'My Heart Will Go On' from?", "Titanic", ["The Bodyguard", "Pearl Harbor", "Armageddon"], "Sung by Céline Dion."),
    F("film", "Which film is 'Let It Go' from?", "Frozen", ["Moana", "Tangled", "Encanto"]),
    F("film", "Which film is 'Shallow' from?", "A Star Is Born", ["The Greatest Showman", "Bohemian Rhapsody", "La La Land"]),
    F("film", "Which film is 'I Will Always Love You' by Whitney Houston from?", "The Bodyguard", ["Waiting to Exhale", "Titanic", "Sister Act"]),
    F("film", "Which film is 'Eye of the Tiger' famous for being in?", "Rocky III", ["Top Gun", "The Karate Kid", "Rambo"]),
    F("film", "Which film is 'Take My Breath Away' from?", "Top Gun", ["Dirty Dancing", "Ghost", "Flashdance"]),
    F("film", "Which film is '(I've Had) The Time of My Life' from?", "Dirty Dancing", ["Grease", "Footloose", "Flashdance"]),
    F("film", "Which film is 'Stayin' Alive' famous for being in?", "Saturday Night Fever", ["Grease", "Footloose", "Fame"]),
    F("film", "Which film is 'This Is Me' from?", "The Greatest Showman", ["Mamma Mia!", "Les Misérables", "A Star Is Born"]),
    F("film", "Which film is 'Happy' by Pharrell Williams from?", "Despicable Me 2", ["Minions", "Sing", "Trolls"]),
    F("film", "Which film is 'See You Again' from?", "Furious 7", ["Fast Five", "Hobbs & Shaw", "Baby Driver"]),
    F("film", "Which film is 'Lose Yourself' by Eminem from?", "8 Mile", ["Straight Outta Compton", "Hustle & Flow", "Get Rich or Die Tryin'"]),
    F("film", "Which film is 'What Was I Made For?' by Billie Eilish from?", "Barbie", ["Wonka", "Wicked", "Inside Out 2"]),
    F("film", "Which film is 'Circle of Life' from?", "The Lion King", ["The Jungle Book", "Tarzan", "Madagascar"]),
    F("film", "Which film is 'We Don't Talk About Bruno' from?", "Encanto", ["Coco", "Moana", "Frozen II"]),
    F("film", "Which musical film is built around ABBA songs?", "Mamma Mia!", ["Grease", "Rocketman", "Sing"]),
    F("film", "Which film tells the story of Queen and Freddie Mercury?", "Bohemian Rhapsody", ["Rocketman", "Elvis", "Walk the Line"]),
    F("film", "Which film tells the story of Elton John?", "Rocketman", ["Bohemian Rhapsody", "Yesterday", "Elvis"]),
    F("film", "Which TV show's theme tune is 'I'll Be There for You' by The Rembrandts?", "Friends", ["Seinfeld", "Frasier", "How I Met Your Mother"]),
    F("film", "Which TV show has a famous theme written by Ron Grainer and made with early electronic sounds by Delia Derbyshire?", "Doctor Who", ["Star Trek", "Blake's 7", "The X-Files"]),
]
BOND = [("Goldfinger", "Shirley Bassey"), ("Diamonds Are Forever", "Shirley Bassey"), ("Live and Let Die", "Paul McCartney and Wings"),
        ("The Spy Who Loved Me", "Carly Simon"), ("A View to a Kill", "Duran Duran"), ("The Living Daylights", "a-ha"), ("Licence to Kill", "Gladys Knight"),
        ("GoldenEye", "Tina Turner"), ("Tomorrow Never Dies", "Sheryl Crow"), ("The World Is Not Enough", "Garbage"), ("Die Another Day", "Madonna"),
        ("Casino Royale", "Chris Cornell"), ("Quantum of Solace", "Jack White and Alicia Keys"), ("Skyfall", "Adele"), ("Spectre", "Sam Smith"),
        ("No Time to Die", "Billie Eilish")]
singers = list(dict.fromkeys(s for _, s in BOND))
for film, singer in BOND:
    add("film", "bond:" + film, f"Who sang the theme for the Bond film {film}?", singer, rng.sample([s for s in singers if s != singer], 3), ks=["bond:" + film])
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ Eurovision (winners up to 2025)
EURO = [(1967, "United Kingdom", "Sandie Shaw", "Puppet on a String"), (1974, "Sweden", "ABBA", "Waterloo"), (1976, "United Kingdom", "Brotherhood of Man", "Save Your Kisses for Me"),
        (1980, "Ireland", "Johnny Logan", "What's Another Year"), (1981, "United Kingdom", "Bucks Fizz", "Making Your Mind Up"), (1982, "Germany", "Nicole", "Ein bisschen Frieden"),
        (1985, "Norway", "Bobbysocks!", "La det swinge"), (1987, "Ireland", "Johnny Logan", "Hold Me Now"), (1988, "Switzerland", "Céline Dion", "Ne partez pas sans moi"),
        (1990, "Italy", "Toto Cutugno", "Insieme: 1992"), (1994, "Ireland", "Paul Harrington and Charlie McGettigan", "Rock 'n' Roll Kids"),
        (1997, "United Kingdom", "Katrina and the Waves", "Love Shine a Light"), (1998, "Israel", "Dana International", "Diva"), (1999, "Sweden", "Charlotte Nilsson", "Take Me to Your Heaven"),
        (2000, "Denmark", "Olsen Brothers", "Fly on the Wings of Love"), (2003, "Turkey", "Sertab Erener", "Everyway That I Can"), (2004, "Ukraine", "Ruslana", "Wild Dances"),
        (2005, "Greece", "Helena Paparizou", "My Number One"), (2006, "Finland", "Lordi", "Hard Rock Hallelujah"), (2008, "Russia", "Dima Bilan", "Believe"),
        (2009, "Norway", "Alexander Rybak", "Fairytale"), (2010, "Germany", "Lena", "Satellite"), (2011, "Azerbaijan", "Ell and Nikki", "Running Scared"),
        (2012, "Sweden", "Loreen", "Euphoria"), (2013, "Denmark", "Emmelie de Forest", "Only Teardrops"), (2014, "Austria", "Conchita Wurst", "Rise Like a Phoenix"),
        (2015, "Sweden", "Måns Zelmerlöw", "Heroes"), (2016, "Ukraine", "Jamala", "1944"), (2017, "Portugal", "Salvador Sobral", "Amar pelos dois"),
        (2018, "Israel", "Netta", "Toy"), (2019, "Netherlands", "Duncan Laurence", "Arcade"), (2021, "Italy", "Måneskin", "Zitti e buoni"),
        (2022, "Ukraine", "Kalush Orchestra", "Stefania"), (2023, "Sweden", "Loreen", "Tattoo"), (2024, "Switzerland", "Nemo", "The Code"), (2025, "Austria", "JJ", "Wasted Love")]
ECOUNTRIES = sorted({c for _, c, _, _ in EURO} | {"France", "Spain", "Belgium", "Poland", "Croatia"})
for y, ctry, who, song in EURO:
    add("euro", f"euro-c:{y}", f"Which country won Eurovision in {y} with '{song}' by {who}?", ctry, rng.sample([c for c in ECOUNTRIES if c != ctry], 3), ks=[f"euro:{y}"])
    near = [e for e in EURO if e[0] != y and e[2] != who]
    near.sort(key=lambda e: abs(e[0] - y))
    add("euro", f"euro-w:{y}", f"Who won Eurovision in {y}?", who, rng.sample([e[2] for e in near[:8]], 3), f"They won for {ctry} with '{song}'.", ks=[f"euro:{y}"])
EFACTS = [
    F("euro", "How many times has the United Kingdom won Eurovision?", "5", ["3", "7", "9"], "1967, 1969, 1976, 1981 and 1997."),
    F("euro", "Which two countries share the record for the most Eurovision wins, with seven each?", "Ireland and Sweden", ["Ireland and the UK", "Sweden and Norway", "France and Luxembourg"]),
    F("euro", "Who is the only singer to have won Eurovision twice as the lead performer, other than Loreen?", "Johnny Logan", ["Dana International", "Céline Dion", "Alexander Rybak"]),
    F("euro", "Which Canadian superstar won Eurovision for Switzerland in 1988?", "Céline Dion", ["Shania Twain", "Alanis Morissette", "Avril Lavigne"]),
    F("euro", "Which heavy metal band in monster masks won Eurovision for Finland in 2006?", "Lordi", ["Nightwish", "HIM", "The Rasmus"]),
    F("euro", "Which band won Eurovision for Italy in 2021 and then became famous worldwide?", "Måneskin", ["Il Volo", "Lacuna Coil", "The Kolors"]),
    F("euro", "In 1969, how many countries tied for first place at Eurovision?", "4", ["2", "3", "5"], "The UK's Lulu was one of the four winners."),
    F("euro", "Which UK act won Eurovision in 1981, famous for ripping off their skirts on stage?", "Bucks Fizz", ["Brotherhood of Man", "Katrina and the Waves", "Sandie Shaw"]),
    F("euro", "Which singer won Eurovision for the UK in 1967, singing barefoot?", "Sandie Shaw", ["Lulu", "Cilla Black", "Dusty Springfield"]),
    F("euro", "Which country hosted Eurovision in 2023 on behalf of the winners, Ukraine?", "The United Kingdom", ["Sweden", "Italy", "Ireland"], "It was held in Liverpool."),
]
for c, q, a, o, x in EFACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ assemble exactly 1,000
total = sum(len(v) for v in Q.values())
print({k: len(v) for k, v in Q.items()}, total, file=sys.stderr)
bank = [q for v in Q.values() for q in v]
Q["song"] = Q["song"][:125]          # keep a balance between the chart and the hand-written songs
bank = [q for v in Q.values() for q in v]
if len(bank) > 1000:
    extra = len(bank) - 1000
    drop = set(id(q) for q in Q["usno1"][-extra:])
    bank = [q for q in bank if id(q) not in drop]
if len(bank) != 1000:
    raise SystemExit(f"bank has {len(bank)} questions")
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank), file=sys.stderr)
