"""Build the Cars question bank (1,000 questions).

Power, top speed, price and founding-year questions compare published figures. Every figure
has an uncertainty margin (model years, markets and sources differ a little), and a question
is only made when the winner is clearly ahead of the runner-up by more than those margins.
The rest is hand-written and limited to settled facts.
Usage: gen_cars.py OUT.json
"""
import sys, json, random, itertools, collections

OUT = sys.argv[1]
rng = random.Random(20261122)
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


def comma(v):
    return f"{v:,.0f}"


# ------------------------------------------------------------------ stock power (maker's figures)
# (brand, model, year, value, unit, fuzz). Units: PS (metric horsepower, as European makers quote)
# or hp (as American makers quote). 1 hp = 1.0139 PS.
P = lambda *a: a
POWER = [
    # Audi
    P("Audi", "A1 30 TFSI", 2019, 110, "PS", .02), P("Audi", "A3 35 TFSI", 2020, 150, "PS", .02), P("Audi", "S3", 2020, 310, "PS", .02),
    P("Audi", "RS 3", 2021, 400, "PS", .02), P("Audi", "TT RS", 2019, 400, "PS", .02), P("Audi", "RS Q3", 2019, 400, "PS", .02),
    P("Audi", "RS 4 Avant", 2018, 450, "PS", .02), P("Audi", "RS 6 Avant", 2020, 600, "PS", .02), P("Audi", "RS 6 Avant performance", 2024, 630, "PS", .02),
    P("Audi", "R8 V10", 2015, 540, "PS", .02), P("Audi", "R8 V10 performance", 2019, 620, "PS", .02), P("Audi", "SQ7", 2019, 507, "PS", .02),
    P("Audi", "RS Q8", 2020, 600, "PS", .02), P("Audi", "Quattro", 1980, 200, "PS", .03), P("Audi", "Sport quattro", 1984, 306, "PS", .03),
    # BMW
    P("BMW", "118i", 2019, 136, "PS", .02), P("BMW", "M135i", 2019, 306, "PS", .02), P("BMW", "M340i", 2019, 374, "PS", .02),
    P("BMW", "Z4 M40i", 2019, 340, "PS", .02), P("BMW", "M2 Competition", 2018, 410, "PS", .02), P("BMW", "M2", 2023, 460, "PS", .02),
    P("BMW", "M3", 2021, 480, "PS", .02), P("BMW", "M3 Competition", 2021, 510, "PS", .02), P("BMW", "M3 (E30)", 1986, 200, "PS", .03),
    P("BMW", "M3 (E46)", 2000, 343, "PS", .02), P("BMW", "M3 (E92)", 2007, 420, "PS", .02), P("BMW", "M4 CSL", 2022, 550, "PS", .02),
    P("BMW", "M5 (E60)", 2005, 507, "PS", .02), P("BMW", "M5 (F90)", 2018, 600, "PS", .02), P("BMW", "M5 (G90)", 2024, 727, "PS", .02),
    P("BMW", "X5 M Competition", 2020, 625, "PS", .02), P("BMW", "XM", 2023, 653, "PS", .02), P("BMW", "i8", 2014, 362, "PS", .02),
    P("BMW", "i3", 2013, 170, "PS", .02), P("BMW", "M1", 1978, 277, "PS", .03),
    # Mercedes-Benz
    P("Mercedes-Benz", "A 180", 2018, 136, "PS", .02), P("Mercedes-Benz", "AMG A 35", 2019, 306, "PS", .02), P("Mercedes-Benz", "AMG A 45 S", 2019, 421, "PS", .02),
    P("Mercedes-Benz", "AMG C 63 S", 2015, 510, "PS", .02), P("Mercedes-Benz", "AMG C 63 S E Performance", 2023, 680, "PS", .02),
    P("Mercedes-Benz", "AMG E 63 S", 2017, 612, "PS", .02), P("Mercedes-Benz", "SLS AMG", 2010, 571, "PS", .02),
    P("Mercedes-Benz", "AMG GT Black Series", 2020, 730, "PS", .02), P("Mercedes-Benz", "AMG G 63", 2018, 585, "PS", .02),
    P("Mercedes-Benz", "AMG One", 2022, 1063, "PS", .02), P("Mercedes-Benz", "SLR McLaren", 2003, 626, "PS", .02), P("Mercedes-Benz", "300 SL Gullwing", 1954, 215, "PS", .05),
    # Volkswagen
    P("Volkswagen", "up! GTI", 2018, 116, "PS", .02), P("Volkswagen", "Polo GTI", 2018, 200, "PS", .03), P("Volkswagen", "Golf GTI (Mk1)", 1976, 110, "PS", .02),
    P("Volkswagen", "Golf GTI (Mk7)", 2013, 220, "PS", .02), P("Volkswagen", "Golf GTI (Mk8)", 2020, 245, "PS", .02), P("Volkswagen", "Golf GTI Clubsport", 2021, 300, "PS", .02),
    P("Volkswagen", "Golf R", 2021, 320, "PS", .02), P("Volkswagen", "Golf R32", 2002, 241, "PS", .02), P("Volkswagen", "Scirocco R", 2009, 265, "PS", .02),
    P("Volkswagen", "T-Roc R", 2019, 300, "PS", .02), P("Volkswagen", "Arteon R", 2020, 320, "PS", .02), P("Volkswagen", "Touareg R", 2020, 462, "PS", .02),
    P("Volkswagen", "Beetle 1200", 1961, 34, "PS", .03),
    # Ford
    P("Ford", "Model T", 1908, 20, "hp", .03), P("Ford", "Ka", 2008, 69, "PS", .03), P("Ford", "Fiesta 1.0 EcoBoost", 2017, 100, "PS", .02),
    P("Ford", "Fiesta ST", 2018, 200, "PS", .02), P("Ford", "Puma ST", 2020, 200, "PS", .02), P("Ford", "Focus ST", 2019, 280, "PS", .02),
    P("Ford", "Focus RS", 2016, 350, "PS", .02), P("Ford", "Sierra RS Cosworth", 1986, 204, "PS", .03), P("Ford", "Escort RS Cosworth", 1992, 227, "PS", .03),
    P("Ford", "Mustang GT", 2018, 450, "PS", .04), P("Ford", "Mustang Shelby GT500", 2020, 760, "hp", .02), P("Ford", "GT", 2017, 647, "hp", .03),
    P("Ford", "F-150 Raptor R", 2024, 720, "hp", .02), P("Ford", "Mustang Mach-E GT", 2021, 487, "PS", .03),
    # Porsche
    P("Porsche", "911 (the original)", 1964, 130, "PS", .03), P("Porsche", "Boxster", 1996, 204, "PS", .02), P("Porsche", "718 Cayman", 2016, 300, "PS", .02),
    P("Porsche", "911 Carrera", 2019, 385, "PS", .02), P("Porsche", "911 Carrera S", 2019, 450, "PS", .02), P("Porsche", "Macan GTS", 2021, 440, "PS", .02),
    P("Porsche", "911 GT3", 2021, 510, "PS", .02), P("Porsche", "911 GT3 RS", 2022, 525, "PS", .02), P("Porsche", "718 Cayman GT4 RS", 2021, 500, "PS", .02),
    P("Porsche", "Cayenne Turbo GT", 2021, 640, "PS", .02), P("Porsche", "911 Turbo S", 2020, 650, "PS", .02), P("Porsche", "Panamera Turbo S E-Hybrid", 2020, 700, "PS", .02),
    P("Porsche", "911 GT2 RS", 2017, 700, "PS", .02), P("Porsche", "Carrera GT", 2003, 612, "PS", .02), P("Porsche", "918 Spyder", 2013, 887, "PS", .02),
    P("Porsche", "959", 1986, 450, "PS", .03),
    # Ferrari
    P("Ferrari", "Testarossa", 1984, 390, "PS", .03), P("Ferrari", "F40", 1987, 478, "PS", .02), P("Ferrari", "F50", 1995, 520, "PS", .02),
    P("Ferrari", "Enzo", 2002, 660, "PS", .02), P("Ferrari", "458 Italia", 2009, 570, "PS", .02), P("Ferrari", "LaFerrari", 2013, 963, "PS", .02),
    P("Ferrari", "488 GTB", 2015, 670, "PS", .02), P("Ferrari", "812 Superfast", 2017, 800, "PS", .02), P("Ferrari", "F8 Tributo", 2019, 720, "PS", .02),
    P("Ferrari", "SF90 Stradale", 2019, 1000, "PS", .02), P("Ferrari", "Roma", 2020, 620, "PS", .02), P("Ferrari", "296 GTB", 2021, 830, "PS", .02),
    P("Ferrari", "Purosangue", 2022, 725, "PS", .02), P("Ferrari", "12Cilindri", 2024, 830, "PS", .02), P("Ferrari", "F80", 2024, 1200, "PS", .02),
    # Lamborghini
    P("Lamborghini", "Miura P400", 1966, 350, "PS", .03), P("Lamborghini", "Countach LP400", 1974, 375, "PS", .03), P("Lamborghini", "Diablo", 1990, 492, "PS", .03),
    P("Lamborghini", "Murciélago", 2001, 580, "PS", .02), P("Lamborghini", "Gallardo", 2003, 500, "PS", .02), P("Lamborghini", "Aventador LP 700-4", 2011, 700, "PS", .02),
    P("Lamborghini", "Huracán LP 610-4", 2014, 610, "PS", .02), P("Lamborghini", "Urus", 2018, 650, "PS", .02), P("Lamborghini", "Aventador SVJ", 2018, 770, "PS", .02),
    P("Lamborghini", "Huracán EVO", 2019, 640, "PS", .02), P("Lamborghini", "Revuelto", 2023, 1015, "PS", .02), P("Lamborghini", "Temerario", 2024, 920, "PS", .02),
    # McLaren
    P("McLaren", "F1", 1992, 627, "PS", .02), P("McLaren", "MP4-12C", 2011, 600, "PS", .02), P("McLaren", "P1", 2013, 916, "PS", .02),
    P("McLaren", "570S", 2015, 570, "PS", .02), P("McLaren", "720S", 2017, 720, "PS", .02), P("McLaren", "Senna", 2018, 800, "PS", .02),
    P("McLaren", "GT", 2019, 620, "PS", .02), P("McLaren", "Speedtail", 2020, 1070, "PS", .02), P("McLaren", "765LT", 2020, 765, "PS", .02),
    P("McLaren", "Artura", 2021, 680, "PS", .02), P("McLaren", "750S", 2023, 750, "PS", .02), P("McLaren", "W1", 2024, 1275, "PS", .02),
    # Bugatti
    P("Bugatti", "Veyron 16.4", 2005, 1001, "PS", .02), P("Bugatti", "Veyron Super Sport", 2010, 1200, "PS", .02), P("Bugatti", "Chiron", 2016, 1500, "PS", .02),
    P("Bugatti", "Chiron Super Sport 300+", 2019, 1600, "PS", .02), P("Bugatti", "Tourbillon", 2024, 1800, "PS", .02),
    # Japan and Korea
    P("Toyota", "Corolla 1.8 Hybrid", 2019, 122, "PS", .02), P("Toyota", "GR86", 2022, 234, "PS", .02), P("Toyota", "GR Yaris", 2020, 261, "PS", .02),
    P("Toyota", "GR Corolla", 2023, 300, "hp", .02), P("Toyota", "GR Supra 3.0", 2019, 340, "PS", .03), P("Lexus", "LC 500", 2017, 477, "PS", .02),
    P("Lexus", "LFA", 2010, 560, "PS", .02), P("Honda", "Civic Type R (FK8)", 2017, 320, "PS", .02), P("Honda", "Civic Type R (FL5)", 2022, 329, "PS", .03),
    P("Honda", "NSX", 1990, 280, "PS", .02), P("Honda", "NSX", 2016, 581, "PS", .02), P("Honda", "S2000", 1999, 240, "PS", .02),
    P("Nissan", "350Z", 2003, 280, "PS", .03), P("Nissan", "370Z", 2009, 328, "PS", .03), P("Nissan", "Skyline GT-R (R34)", 1999, 280, "PS", .03),
    P("Nissan", "GT-R", 2007, 480, "PS", .02), P("Nissan", "GT-R NISMO", 2017, 600, "PS", .02), P("Nissan", "Leaf", 2018, 150, "PS", .02),
    P("Subaru", "BRZ", 2012, 200, "PS", .02), P("Subaru", "WRX STI", 2014, 300, "PS", .02), P("Mitsubishi", "Lancer Evolution X", 2008, 295, "PS", .02),
    P("Mazda", "MX-5 2.0", 2019, 184, "PS", .02), P("Mazda", "RX-7", 1992, 255, "PS", .06), P("Mazda", "RX-8", 2003, 231, "PS", .03),
    P("Hyundai", "i20 N", 2021, 204, "PS", .02), P("Hyundai", "i30 N Performance", 2017, 275, "PS", .02), P("Hyundai", "Kona N", 2021, 280, "PS", .02),
    P("Kia", "Picanto 1.0", 2017, 67, "PS", .03), P("Kia", "Stinger GT", 2017, 370, "PS", .02), P("Kia", "EV6 GT", 2022, 585, "PS", .02),
    # France and Italy
    P("Renault", "Clio Williams", 1993, 150, "PS", .03), P("Renault", "Clio RS 200", 2013, 200, "PS", .02), P("Renault", "Mégane RS Trophy", 2019, 300, "PS", .02),
    P("Alpine", "A110", 2017, 252, "PS", .02), P("Alpine", "A110 S", 2022, 300, "PS", .02), P("Peugeot", "205 GTI 1.9", 1986, 130, "PS", .05),
    P("Peugeot", "208 GTi", 2013, 200, "PS", .02), P("Citroën", "2CV", 1949, 9, "PS", .05), P("Fiat", "500", 1957, 13, "PS", .05),
    P("Fiat", "500 1.2", 2007, 69, "PS", .02), P("Abarth", "595", 2016, 145, "PS", .02), P("Alfa Romeo", "Giulia Quadrifoglio", 2016, 510, "PS", .02),
    P("Alfa Romeo", "4C", 2013, 240, "PS", .02), P("Maserati", "MC20", 2020, 630, "PS", .02), P("Maserati", "GranTurismo Trofeo", 2023, 550, "PS", .02),
    P("Pagani", "Zonda C12", 1999, 394, "PS", .02), P("Pagani", "Huayra", 2012, 730, "PS", .02), P("Pagani", "Utopia", 2022, 864, "PS", .02),
    # Britain
    P("Jaguar", "E-Type", 1961, 265, "hp", .08), P("Jaguar", "XJ220", 1992, 542, "hp", .02), P("Jaguar", "F-Type SVR", 2016, 575, "PS", .02),
    P("Jaguar", "I-Pace", 2018, 400, "PS", .02), P("Land Rover", "Defender 90 V8", 2021, 525, "PS", .02), P("Land Rover", "Range Rover Sport SV", 2023, 635, "PS", .02),
    P("Mini", "Mini 850", 1959, 34, "PS", .05), P("Mini", "Cooper S", 2014, 192, "PS", .02), P("Mini", "John Cooper Works", 2018, 231, "PS", .02),
    P("Lotus", "Elise", 1996, 120, "PS", .03), P("Lotus", "Exige S", 2012, 350, "PS", .02), P("Lotus", "Emira V6", 2022, 405, "PS", .02),
    P("Lotus", "Evija", 2020, 2000, "PS", .03), P("Aston Martin", "DB5", 1963, 282, "hp", .08), P("Aston Martin", "Vantage", 2018, 510, "PS", .02),
    P("Aston Martin", "DB11 V12", 2016, 608, "PS", .02), P("Aston Martin", "Vantage", 2024, 665, "PS", .02), P("Aston Martin", "DBX707", 2022, 707, "PS", .02),
    P("Aston Martin", "DBS Superleggera", 2018, 725, "PS", .02), P("Aston Martin", "Valkyrie", 2021, 1160, "PS", .02),
    P("Rolls-Royce", "Phantom", 2017, 571, "PS", .02), P("Rolls-Royce", "Spectre", 2023, 585, "PS", .02), P("Rolls-Royce", "Wraith", 2013, 632, "PS", .02),
    P("Bentley", "Continental GT V8", 2019, 550, "PS", .02), P("Bentley", "Bentayga W12", 2015, 608, "PS", .02), P("Bentley", "Continental GT Speed", 2021, 659, "PS", .02),
    P("Vauxhall", "Corsa VXR", 2015, 205, "PS", .02), P("Vauxhall", "Astra VXR", 2012, 280, "PS", .02),
    # elsewhere
    P("Škoda", "Octavia vRS", 2020, 245, "PS", .02), P("Cupra", "Formentor VZ5", 2021, 390, "PS", .02), P("Seat", "Leon Cupra R", 2017, 310, "PS", .02),
    P("Dacia", "Sandero TCe 90", 2021, 91, "PS", .03), P("Polestar", "Polestar 1", 2019, 609, "PS", .02), P("Koenigsegg", "Regera", 2016, 1500, "PS", .02),
    P("Rimac", "Nevera", 2021, 1914, "PS", .02), P("Tesla", "Roadster", 2008, 248, "hp", .02), P("Tesla", "Model S Plaid", 2021, 1020, "hp", .02),
    P("Chevrolet", "Corvette Stingray", 2020, 495, "hp", .02), P("Chevrolet", "Corvette Z06", 2023, 670, "hp", .02), P("Chevrolet", "Corvette ZR1", 2025, 1064, "hp", .02),
    P("Chevrolet", "Camaro ZL1", 2017, 650, "hp", .02), P("Dodge", "Challenger SRT Hellcat", 2015, 707, "hp", .02), P("Dodge", "Viper", 2013, 640, "hp", .02),
    P("DeLorean", "DMC-12", 1981, 130, "hp", .03), P("Hennessey", "Venom F5", 2021, 1817, "hp", .02), P("Peel", "P50", 1962, 4.5, "hp", .1),
]
CARS = []
for b, m, y, v, u, f in POWER:
    ps = v if u == "PS" else v * 1.01387
    other = f"{comma(v / 1.01387)} hp" if u == "PS" else f"{comma(ps)} PS"
    CARS.append({"id": f"{b}|{m}|{y}", "brand": b, "year": y, "short": f"{m} ({y})", "long": f"{b} {m} ({y})",
                 "ps": ps, "fuzz": f, "disp": f"{comma(v) if v >= 10 else v} {u} ({other})"})
assert len({c["id"] for c in CARS}) == len(CARS)
PLURAL = {"Audi": "Audis", "BMW": "BMWs", "Mercedes-Benz": "Mercedes-Benz models", "Volkswagen": "Volkswagens", "Ford": "Fords",
          "Porsche": "Porsches", "Ferrari": "Ferraris", "Lamborghini": "Lamborghinis", "McLaren": "McLarens", "Aston Martin": "Aston Martins"}


def clear_winner(items, key, fuzz, most=True, gap=1.04, min_diff=0):
    """The top (or bottom) item if it beats every other one by more than both margins."""
    s = sorted(items, key=key, reverse=most)
    a, b = s[0], s[1]
    hi, lo = (key(a), key(b)) if most else (key(b), key(a))
    if hi - lo < min_diff:
        return None
    big, small = (a, b) if most else (b, a)
    if hi / lo < (1 + fuzz(big)) * (1 + fuzz(small)) * gap:
        return None
    return a


def power_q(cars, brand=None):
    most = rng.random() > 0.18
    win = clear_winner(cars, lambda c: c["ps"], lambda c: c["fuzz"], most, gap=1.03, min_diff=15)
    if not win:
        return False
    # the newest car being the most powerful (or the oldest the least) is allowed about 1 time in 4,
    # the same as a random guess, so the years don't point to the answer either way
    years = [c["year"] for c in cars]
    obvious = (most and win["year"] >= max(years)) or (not most and win["year"] <= min(years))
    if obvious and OBVIOUS[0] >= 0.25 * (len(Q["power"]) + 1):
        return False
    label = (lambda c: c["short"]) if brand else (lambda c: c["long"])
    who = f"Which of these {PLURAL[brand]}" if brand else "Which of these cars"
    q = f"{who} has the {'most' if most else 'least'} stock horsepower?"
    x = "Maker's figures: " + " · ".join(f"{label(c)} {c['disp']}" for c in sorted(cars, key=lambda c: -c["ps"])) + "."
    key = "power:" + "|".join(sorted(c["id"] for c in cars)) + (":most" if most else ":least")
    ok = add("power", key, q, label(win), [label(c) for c in cars if c is not win], x, ks=[c["id"] for c in cars])
    if ok and obvious:
        OBVIOUS[0] += 1
    return ok


OBVIOUS = [0]
by_brand = collections.defaultdict(list)
for c in CARS:
    by_brand[c["brand"]].append(c)
tries = 0
while len(Q["power"]) < 60 and tries < 400000:
    tries += 1
    b = rng.choice(list(PLURAL))
    power_q(rng.sample(by_brand[b], 4), b)
tries = 0
while len(Q["power"]) < 90 and tries < 400000:
    tries += 1
    cs = rng.sample(CARS, 4)
    if len({c["brand"] for c in cs}) < 4 or max(c["ps"] for c in cs) / min(c["ps"] for c in cs) > 2.6:
        continue
    power_q(cs)

# ------------------------------------------------------------------ founding years
# (brand, year, fuzz in years, how to show it). Fuzz covers brands that began as something else.
FOUNDED = [("Peugeot", 1810, 80, "1810 (as a family firm; cars from 1889)"), ("Opel", 1862, 37, "1862 (cars from 1899)"),
           ("Škoda", 1895, 0, "1895 (as Laurin & Klement)"), ("Renault", 1899, 0, "1899"), ("Fiat", 1899, 0, "1899"), ("Dodge", 1900, 14, "1900 (cars from 1914)"),
           ("Cadillac", 1902, 0, "1902"), ("Ford", 1903, 0, "1903"), ("Buick", 1903, 0, "1903"), ("Rolls-Royce", 1906, 2, "1906"), ("Lancia", 1906, 0, "1906"),
           ("Audi", 1909, 1, "1909"), ("Bugatti", 1909, 0, "1909"), ("Suzuki", 1909, 46, "1909 (cars from 1955)"), ("Alfa Romeo", 1910, 0, "1910"),
           ("Morgan", 1910, 0, "1910"), ("Chevrolet", 1911, 0, "1911"), ("Aston Martin", 1913, 0, "1913"), ("Maserati", 1914, 0, "1914"),
           ("BMW", 1916, 1, "1916"), ("Lincoln", 1917, 0, "1917"), ("Citroën", 1919, 0, "1919"), ("Bentley", 1919, 0, "1919"),
           ("Mazda", 1920, 11, "1920 (cars from 1931)"), ("Jaguar", 1922, 23, "1922 (as Swallow Sidecar)"), ("MG", 1924, 0, "1924"),
           ("Chrysler", 1925, 0, "1925"), ("Mercedes-Benz", 1926, 43, "1926 (Benz & Cie began in 1883)"), ("Volvo", 1927, 0, "1927"),
           ("Porsche", 1931, 0, "1931"), ("Nissan", 1933, 0, "1933"), ("Toyota", 1937, 0, "1937"), ("Volkswagen", 1937, 0, "1937"),
           ("Ferrari", 1939, 8, "1939 (first Ferrari car 1947)"), ("Jeep", 1941, 2, "1941"), ("Kia", 1944, 30, "1944 (cars from 1974)"),
           ("Tata Motors", 1945, 0, "1945"), ("Honda", 1948, 0, "1948"), ("Land Rover", 1948, 0, "1948"), ("Abarth", 1949, 0, "1949"),
           ("Seat", 1950, 0, "1950"), ("Lotus", 1952, 4, "1952"), ("Subaru", 1953, 1, "1953"), ("Alpine", 1955, 0, "1955"), ("Mini", 1959, 0, "1959"),
           ("Lamborghini", 1963, 0, "1963"), ("McLaren", 1963, 22, "1963 (as a racing team)"), ("Dacia", 1966, 0, "1966"), ("Hyundai", 1967, 0, "1967"),
           ("DeLorean", 1975, 0, "1975"), ("Lexus", 1989, 0, "1989"), ("Pagani", 1992, 0, "1992"), ("Koenigsegg", 1994, 0, "1994"),
           ("Tesla", 2003, 0, "2003"), ("Rimac", 2009, 0, "2009"), ("Genesis", 2015, 0, "2015"), ("Cupra", 2018, 0, "2018")]
FD = {b: (y, f, s) for b, y, f, s in FOUNDED}
tries = 0
while len(Q["founded"]) < 100 and tries < 200000:
    tries += 1
    bs = rng.sample(list(FD), 4)
    first = rng.random() > 0.25
    s = sorted(bs, key=lambda b: FD[b][0], reverse=not first)
    a, b = s[0], s[1]
    if abs(FD[a][0] - FD[b][0]) <= FD[a][1] + FD[b][1] + 3:
        continue
    if max(FD[x][0] for x in bs) - min(FD[x][0] for x in bs) > 90:
        continue
    q = "Which of these car makers was founded first?" if first else "Which of these car makers was founded most recently?"
    x = " · ".join(f"{x}: {FD[x][2]}" for x in sorted(bs, key=lambda x: FD[x][0])) + "."
    add("founded", "founded:" + "|".join(sorted(bs)) + str(first), q, a, [x for x in bs if x != a], x, ks=["brand:" + x for x in bs])

DEC = [b for b, (y, f, _) in FD.items() if f == 0 and 1890 <= y <= 2019]
rng.shuffle(DEC)
for b in DEC[:32]:
    d = FD[b][0] // 10 * 10
    near = sorted({d - 20, d - 10, d + 10, d + 20} - {d}, key=lambda x: (abs(x - d), rng.random()))
    near = [x for x in near if 1880 <= x <= 2020][:3]
    if len(near) < 3:
        continue
    add("decade", "decade:" + b, f"In which decade was {b} founded?", f"{d}s", [f"{x}s" for x in near], f"{b} was founded in {FD[b][0]}.", ks=["brand:" + b])

# ------------------------------------------------------------------ prices when new (UK, rough launch prices)
PRICES = [("Bugatti Tourbillon (2024)", 3.2e6, .1), ("Aston Martin Valkyrie (2021)", 2.5e6, .15), ("Mercedes-AMG One (2022)", 2.3e6, .1),
          ("Bugatti Chiron (2016)", 2.4e6, .15), ("Rimac Nevera (2021)", 2.0e6, .1), ("Ferrari LaFerrari (2013)", 1.0e6, .15),
          ("Bugatti Veyron (2005)", 850000, .1), ("McLaren P1 (2013)", 866000, .02), ("McLaren Senna (2018)", 750000, .03),
          ("Porsche 918 Spyder (2013)", 711000, .03), ("McLaren F1 (1992)", 540000, .03), ("Ferrari Enzo (2002)", 450000, .15),
          ("Ferrari SF90 Stradale (2019)", 375000, .05), ("Rolls-Royce Phantom (2017)", 360000, .1), ("Lamborghini Aventador S (2017)", 270000, .1),
          ("Rolls-Royce Cullinan (2018)", 250000, .1), ("Porsche 911 GT3 RS (2022)", 180000, .05), ("Ferrari Roma (2020)", 170000, .05),
          ("Lamborghini Urus (2018)", 165000, .05), ("Bentley Continental GT (2018)", 160000, .1), ("Range Rover (2022)", 95000, .1),
          ("Porsche 911 Carrera (2019)", 83000, .05), ("BMW M3 Competition (2021)", 75000, .05), ("Tesla Model 3 (2024)", 40000, .1),
          ("Volkswagen Golf GTI (2020)", 34000, .1), ("Toyota GR Yaris (2020)", 30000, .1), ("Ford Fiesta (2019)", 17000, .15),
          ("Dacia Sandero (2021)", 12000, .1)]


def money(v):
    if v >= 1e6:
        return f"about £{v / 1e6:.1f} million".replace(".0 million", " million")
    return f"about £{comma(round(v, -3))}"


tries = 0
while len(Q["price"]) < 42 and tries < 100000:
    tries += 1
    cs = rng.sample(PRICES, 4)
    s = sorted(cs, key=lambda c: -c[1])
    if s[0][1] / s[1][1] < (1 + s[0][2]) * (1 + s[1][2]) * 1.05 or s[0][1] / s[3][1] > 40:
        continue
    x = "Rough UK prices when new: " + " · ".join(f"{n} {money(v)}" for n, v, _ in s) + "."
    add("price", "price:" + "|".join(sorted(c[0] for c in cs)), "Which of these cost the most to buy new (at the time)?", s[0][0],
        [c[0] for c in s[1:]], x, ks=["price:" + c[0] for c in cs])

AUCTION = [("Mercedes-Benz 300 SLR Uhlenhaut Coupé (1955)", 143e6, "€135 million (about $143 million) in 2022"),
           ("Ferrari 250 GTO (1962)", 48.4e6, "$48.4 million in 2018"), ("Ferrari 335 S Spider Scaglietti (1957)", 35.7e6, "€32.1 million (about $35.7 million) in 2016"),
           ("Mercedes-Benz W196 R (1954)", 29.6e6, "$29.6 million in 2013"), ("Ferrari 275 GTB/4*S N.A.R.T. Spider (1967)", 27.5e6, "$27.5 million in 2013"),
           ("Aston Martin DBR1 (1956)", 22.55e6, "$22.55 million in 2017"), ("Jaguar D-Type (1955)", 21.78e6, "$21.78 million in 2016"),
           ("McLaren F1 (1995)", 20.47e6, "$20.47 million in 2021"), ("Porsche 917K (1970)", 14.08e6, "$14.08 million in 2017"),
           ("Ford GT40 (1968)", 11e6, "$11 million in 2012"), ("Aston Martin DB5 (1965, a Bond promotional car)", 6.39e6, "$6.39 million in 2019")]
tries = 0
while len(Q["auction"]) < 16 and tries < 100000:
    tries += 1
    cs = rng.sample(AUCTION, 4)
    s = sorted(cs, key=lambda c: -c[1])
    if s[0][1] / s[1][1] < 1.08:
        continue
    x = "Auction prices: " + " · ".join(f"{n}: {t}" for n, _, t in s) + "."
    add("auction", "auction:" + "|".join(sorted(c[0] for c in cs)), "Which of these sold for the most money at auction?", s[0][0],
        [c[0] for c in s[1:]], x, ks=["auction:" + c[0] for c in cs])

# ------------------------------------------------------------------ top speeds (maker's figures, km/h)
SPEEDS = [("Bugatti Chiron Super Sport 300+ (2019)", 490, .01), ("Koenigsegg Agera RS (2017)", 447, .01), ("Bugatti Chiron (2016)", 420, .01),
          ("Rimac Nevera (2021)", 412, .01), ("Bugatti Veyron (2005)", 407, .01), ("McLaren Speedtail (2020)", 403, .01),
          ("McLaren F1 (1992)", 386, .01), ("Mercedes-AMG One (2022)", 352, .02), ("Ferrari LaFerrari (2013)", 350, .03),
          ("Lamborghini Aventador SVJ (2018)", 350, .02), ("Ford GT (2017)", 348, .02), ("Porsche 918 Spyder (2013)", 345, .02),
          ("Jaguar XJ220 (1992)", 341, .02), ("Ferrari SF90 Stradale (2019)", 340, .02), ("Bentley Continental GT Speed (2021)", 335, .02),
          ("Porsche 911 Turbo S (2020)", 330, .02), ("Ferrari F40 (1987)", 324, .02), ("Tesla Model S Plaid (2021)", 322, .02),
          ("Nissan GT-R (2017)", 315, .02), ("Lamborghini Urus (2018)", 305, .02), ("Range Rover Sport SV (2023)", 290, .02),
          ("Honda Civic Type R (2022)", 275, .02), ("Rolls-Royce Phantom (2017)", 250, .01), ("Toyota GR Yaris (2020)", 230, .02),
          ("Mini Cooper S (2014)", 235, .02), ("DeLorean DMC-12 (1981)", 177, .03), ("Fiat 500 1.2 (2007)", 160, .02),
          ("Nissan Leaf (2018)", 144, .02), ("Mini 850 (1959)", 116, .03), ("Tata Nano (2008)", 105, .03), ("Ford Model T (1908)", 72, .05),
          ("Citroën 2CV (1949)", 64, .05), ("Peel P50 (1962)", 61, .05)]


def kmh(v):
    return f"{v} km/h ({round(v * 0.621371)} mph)"


tries = 0
while len(Q["speed"]) < 58 and tries < 100000:
    tries += 1
    cs = rng.sample(SPEEDS, 4)
    s = sorted(cs, key=lambda c: -c[1])
    if s[0][1] / s[1][1] < (1 + s[0][2]) * (1 + s[1][2]) * 1.03 or s[0][1] / s[3][1] > 3:
        continue
    x = "Top speeds: " + " · ".join(f"{n} {kmh(v)}" for n, v, _ in s) + "."
    add("speed", "speed:" + "|".join(sorted(c[0] for c in cs)), "Which of these has the highest top speed?", s[0][0],
        [c[0] for c in s[1:]], x, ks=["speed:" + c[0] for c in cs])

# ------------------------------------------------------------------ makers: models, countries, owners
BRANDS = {  # brand: (country, tier, owner or None)
    "Ford": ("USA", "mass", None), "Chevrolet": ("USA", "mass", "General Motors"), "Cadillac": ("USA", "premium", "General Motors"),
    "Dodge": ("USA", "mass", "Stellantis"), "Jeep": ("USA", "mass", "Stellantis"), "Chrysler": ("USA", "mass", "Stellantis"),
    "Tesla": ("USA", "premium", None), "Lincoln": ("USA", "premium", "Ford"),
    "Toyota": ("Japan", "mass", None), "Lexus": ("Japan", "premium", "Toyota"), "Honda": ("Japan", "mass", None), "Nissan": ("Japan", "mass", None),
    "Mazda": ("Japan", "mass", None), "Subaru": ("Japan", "mass", None), "Mitsubishi": ("Japan", "mass", None), "Suzuki": ("Japan", "mass", None),
    "Daihatsu": ("Japan", "mass", "Toyota"), "Hyundai": ("South Korea", "mass", None), "Kia": ("South Korea", "mass", "Hyundai Motor Group"),
    "Genesis": ("South Korea", "premium", "Hyundai Motor Group"),
    "Volkswagen": ("Germany", "mass", None), "Audi": ("Germany", "premium", "Volkswagen Group"), "Porsche": ("Germany", "super", "Volkswagen Group"),
    "BMW": ("Germany", "premium", None), "Mercedes-Benz": ("Germany", "premium", None), "Opel": ("Germany", "mass", "Stellantis"),
    "Renault": ("France", "mass", None), "Peugeot": ("France", "mass", "Stellantis"), "Citroën": ("France", "mass", "Stellantis"),
    "Alpine": ("France", "premium", "Renault Group"), "Bugatti": ("France", "super", None), "Dacia": ("Romania", "mass", "Renault Group"),
    "Fiat": ("Italy", "mass", "Stellantis"), "Alfa Romeo": ("Italy", "premium", "Stellantis"), "Maserati": ("Italy", "super", "Stellantis"),
    "Lancia": ("Italy", "mass", "Stellantis"), "Abarth": ("Italy", "mass", "Stellantis"), "Ferrari": ("Italy", "super", None),
    "Lamborghini": ("Italy", "super", "Volkswagen Group"), "Pagani": ("Italy", "super", None),
    "Škoda": ("Czech Republic", "mass", "Volkswagen Group"), "Seat": ("Spain", "mass", "Volkswagen Group"), "Cupra": ("Spain", "premium", "Volkswagen Group"),
    "Volvo": ("Sweden", "premium", "Geely"), "Polestar": ("Sweden", "premium", "Geely"), "Koenigsegg": ("Sweden", "super", None), "Saab": ("Sweden", "premium", None),
    "Jaguar": ("UK", "premium", "Tata Motors"), "Land Rover": ("UK", "premium", "Tata Motors"), "Aston Martin": ("UK", "super", None),
    "Bentley": ("UK", "super", "Volkswagen Group"), "Rolls-Royce": ("UK", "super", "BMW Group"), "McLaren": ("UK", "super", None),
    "Lotus": ("UK", "super", "Geely"), "Mini": ("UK", "mass", "BMW Group"), "Vauxhall": ("UK", "mass", "Stellantis"), "Morgan": ("UK", "super", None),
    "Rimac": ("Croatia", "super", None), "Lada": ("Russia", "mass", None), "Tata": ("India", "mass", None), "Mahindra": ("India", "mass", None),
    "Proton": ("Malaysia", "mass", None), "Holden": ("Australia", "mass", None), "BYD": ("China", "mass", None), "Geely": ("China", "mass", None),
    "MG": (None, "mass", "SAIC"),
}
COUNTRY_NAME = {"USA": "The USA", "UK": "The UK", "Czech Republic": "The Czech Republic"}
MODELS = {  # brand: [(model, still made?)]
    "Ford": "Fiesta- Focus- Mondeo- Kuga Puma Mustang Ranger Transit Capri Cortina- Escort- |Model T- F-150 Bronco Explorer Ka- GT40-",
    "Toyota": "Corolla Yaris Prius Supra Celica- Hilux |Land Cruiser Aygo RAV4 C-HR Camry Avensis-",
    "Honda": "Civic Jazz Accord CR-V HR-V NSX- S2000- Prelude",
    "Nissan": "Micra Qashqai Juke Leaf Skyline- GT-R- X-Trail Navara- Note- 350Z-",
    "Mazda": "MX-5 RX-7- RX-8- CX-5",
    "Subaru": "Impreza Forester Outback Legacy- BRZ WRX",
    "Mitsubishi": "Lancer- Outlander Shogun- L200",
    "Suzuki": "Swift Jimny Vitara Ignis Alto",
    "Hyundai": "i10 i30 Tucson |Santa Fe Kona |Ioniq 5",
    "Kia": "Picanto Rio- Ceed Sportage Niro Stinger- EV6 Sorento",
    "Renault": "Clio Mégane Captur Zoe- Twingo Espace Scénic Kangoo Laguna-",
    "Peugeot": "205- 208 3008 406-",
    "Citroën": "2CV- C3 Berlingo Saxo- |Xsara Picasso-",
    "Fiat": "Panda Punto- Multipla- Uno- Tipo",
    "Volkswagen": "Golf Polo Passat Tiguan Touareg Beetle- Scirocco- up!- Arteon- ID.3 T-Roc Corrado-",
    "Škoda": "Octavia Fabia Superb Kodiaq Karoq Enyaq Yeti-",
    "Seat": "Ibiza Arona Ateca Tarraco",
    "Cupra": "Formentor Born",
    "Dacia": "Sandero Duster Logan- Jogger Spring",
    "Chevrolet": "Corvette Camaro- Silverado Impala- Tahoe",
    "Dodge": "Viper- Challenger- Charger Durango",
    "Jeep": "Wrangler Cherokee Renegade Compass",
    "Tesla": "|Model S |Model 3 |Model X |Model Y Cybertruck",
    "Mini": "Countryman Clubman-",
    "Audi": "TT- R8- Q7 A4-",
    "BMW": "Z4 i3- i8- X5 M3",
    "Mercedes-Benz": "G-Class SLK- Sprinter A-Class S-Class",
    "Volvo": "XC90 XC40 V70- P1800- Amazon-",
    "Jaguar": "E-Type- XJ- F-Type- I-Pace- XK- F-Pace",
    "Land Rover": "Defender Discovery Freelander-",
    "Lexus": "LFA-",
    "Alfa Romeo": "Giulia Stelvio Giulietta- Tonale 4C-",
    "Porsche": "911 Cayenne Macan Panamera Taycan Boxster- Cayman- |Carrera GT- 959-",
    "Cadillac": "Escalade Eldorado-",
    "Ferrari": "Testarossa- Enzo- F40- Roma- Purosangue |458 Italia- |SF90 Stradale-",
    "Lamborghini": "Countach- Diablo- Murciélago- Aventador- Huracán- Urus Miura- Gallardo- Revuelto",
    "McLaren": "P1- Senna- Speedtail- Artura 720S-",
    "Bugatti": "Veyron- Chiron- Divo- Tourbillon |Type 35-",
    "Pagani": "Zonda- Huayra- Utopia",
    "Koenigsegg": "Agera- Regera- Jesko Gemera",
    "Aston Martin": "DB5- Vantage Valkyrie- DBX Vanquish",
    "Bentley": "Bentayga Mulsanne- |Flying Spur |Continental GT",
    "Rolls-Royce": "Phantom Ghost Cullinan Wraith- Spectre |Silver Shadow- |Silver Ghost-",
    "Maserati": "Ghibli- Levante- Quattroporte- MC20-",
    "Lotus": "Elise- Exige- Evora- Esprit- Evija Emira",
    "Rimac": "Nevera",
}


def parse_models(s):
    out, words = [], s.split(" ")
    i = 0
    while i < len(words):
        w = words[i]
        if w.startswith("|"):            # "|Land Cruiser" joins the next word
            w = w[1:] + " " + words[i + 1]
            i += 1
        i += 1
        out.append((w.rstrip("-"), not w.endswith("-")))
    return out


TIER = collections.defaultdict(list)
for b, (_, t, _) in BRANDS.items():
    if b in MODELS:
        TIER[t].append(b)
model_items = []
for b, s in MODELS.items():
    for m, current in parse_models(s):
        model_items.append((b, m, current))
names = collections.Counter(m for _, m, _ in model_items)
assert all(v == 1 for v in names.values()), [n for n, v in names.items() if v > 1]
rng.shuffle(model_items)
for b, m, current in model_items:
    tier = BRANDS[b][1]
    pool = [x for x in TIER[tier] if x != b]
    if len(pool) < 3:
        pool += [x for x in TIER["premium"] if x != b]
    label = "the original McLaren F1" if m == "F1" else m
    q = f"Which brand {'makes' if current else 'made'} the {label}?"
    add("model", "model:" + m, q, b, rng.sample(pool, 3), ks=["model:" + m])

def article(b):
    return ("an " if b[0] in "AEIOU" else "a ") + b


by_maker = collections.defaultdict(list)
for b, m, current in model_items:
    by_maker[b].append(m)
odd_brands = [b for b, ms in by_maker.items() if len(ms) >= 4]
tries = 0
while len(Q["notby"]) < 70 and tries < 20000:
    tries += 1
    b = rng.choice(odd_brands)
    ms = rng.sample(by_maker[b], 3)
    other = rng.choice([x for x in TIER[BRANDS[b][1]] if x != b])
    odd = rng.choice(by_maker[other])
    add("notby", "notby:" + b + ":" + "|".join(sorted(ms + [odd])), f"Which of these is not {article(b)}?", odd, ms,
        f"The {odd} is {article(other)}.", ks=["model:" + m for m in ms + [odd]])

COUNTRIES = ["The USA", "Japan", "Germany", "France", "Italy", "The UK", "Sweden", "South Korea", "Spain", "The Czech Republic", "China", "India"]
cbrands = [b for b, v in BRANDS.items() if v[0]]
rng.shuffle(cbrands)
for b in cbrands:
    c = COUNTRY_NAME.get(BRANDS[b][0], BRANDS[b][0])
    near = {"Croatia": ["Italy", "Germany", "Sweden"], "Romania": ["France", "The Czech Republic", "Spain"], "Russia": ["The Czech Republic", "Germany", "China"],
            "Malaysia": ["Japan", "South Korea", "China"], "Australia": ["The UK", "The USA", "Japan"]}.get(c)
    opts = near or rng.sample([x for x in COUNTRIES if x != c], 3)
    add("country", "country:" + b, f"Which country does the car maker {b} come from?", c, opts, ks=["brand:" + b])

GROUPS = ["Volkswagen Group", "BMW Group", "Mercedes-Benz Group", "Stellantis", "Toyota", "Hyundai Motor Group", "Geely", "Tata Motors",
          "Renault Group", "General Motors", "Ford", "SAIC"]
for b, (_, _, owner) in sorted(BRANDS.items()):
    if owner:
        add("owner", "owner:" + b, f"Which company owns {b}?", owner, rng.sample([g for g in GROUPS if g != owner], 3),
            "As of 2026." if b in ("Lotus", "Polestar", "Porsche") else None, ks=["brand:" + b])

# ------------------------------------------------------------------ engines: cylinders
CYL = [("Bugatti Chiron", 16, "a W16"), ("Bugatti Veyron", 16, "a W16"), ("Bugatti Tourbillon", 16, "a V16"), ("Lamborghini Aventador", 12, "a V12"),
       ("Lamborghini Revuelto", 12, "a V12 (plus three electric motors)"), ("Ferrari 812 Superfast", 12, "a V12"), ("Ferrari Purosangue", 12, "a V12"),
       ("Rolls-Royce Phantom (2017)", 12, "a twin-turbo V12"), ("Aston Martin Valkyrie", 12, "a V12"), ("McLaren F1", 12, "a BMW-built V12"),
       ("Pagani Huayra", 12, "an AMG V12"), ("Lamborghini Huracán", 10, "a V10"), ("Audi R8 V10", 10, "a V10"), ("Lexus LFA", 10, "a V10"),
       ("Dodge Viper", 10, "an 8.4-litre V10"), ("BMW M5 (E60)", 10, "a V10"), ("Ferrari F8 Tributo", 8, "a twin-turbo V8"), ("McLaren 720S", 8, "a twin-turbo V8"),
       ("Ford Mustang GT", 8, "a 5.0-litre V8"), ("Chevrolet Corvette (C8)", 8, "a V8"), ("Mercedes-AMG C 63 (2015)", 8, "a twin-turbo V8"),
       ("Porsche 911 Carrera (2019)", 6, "a flat-six"), ("BMW M3 (2021)", 6, "a straight-six"), ("Nissan GT-R", 6, "a twin-turbo V6"),
       ("Ferrari 296 GTB", 6, "a V6 hybrid"), ("McLaren Artura", 6, "a V6 hybrid"), ("Audi RS 3", 5, "a five-cylinder"), ("Audi TT RS", 5, "a five-cylinder"),
       ("Ford Focus RS (2009)", 5, "a five-cylinder"), ("Volkswagen Golf GTI (2020)", 4, "a four-cylinder"), ("Mercedes-AMG C 63 (2023)", 4, "a four-cylinder hybrid"),
       ("Porsche 718 Cayman (2016)", 4, "a flat-four turbo"), ("Honda Civic Type R", 4, "a four-cylinder"), ("Mazda MX-5 (2019)", 4, "a four-cylinder"),
       ("Toyota GR Yaris", 3, "a three-cylinder"), ("Ford Fiesta 1.0 EcoBoost", 3, "a three-cylinder"), ("BMW i8", 3, "a three-cylinder hybrid"), ("Fiat 500 TwinAir", 2, "a two-cylinder"), ("Citroën 2CV", 2, "a two-cylinder"),
       ("Fiat 500 (1957)", 2, "a two-cylinder")]
NUMS = [2, 3, 4, 5, 6, 8, 10, 12, 16]
for car, n, how in CYL:
    i = NUMS.index(n)
    near = [x for x in NUMS if x != n]
    near.sort(key=lambda x: (abs(NUMS.index(x) - i), rng.random()))
    add("cyl", "cyl:" + car, f"How many cylinders are in the engine of the {car}?", str(n), [str(x) for x in near[:3]],
        f"It has {how} engine.", ks=["cyl:" + car.split()[0]])

# ------------------------------------------------------------------ fully electric or not
EVS = ["Nissan Leaf", "Tesla Model 3", "Renault Zoe", "Kia EV6", "Hyundai Ioniq 5", "Polestar 2", "Volkswagen ID.3", "Jaguar I-Pace",
       "Porsche Taycan", "MG4", "Rimac Nevera", "Lotus Evija", "Rolls-Royce Spectre", "Tesla Cybertruck", "Ford Mustang Mach-E"]
NOT_EV = ["Toyota Prius", "Mazda MX-5", "Toyota GR Yaris", "Honda Civic Type R", "Volkswagen Golf GTI", "Porsche 911 Carrera", "Ford Fiesta ST",
          "Subaru BRZ", "Dacia Duster", "Toyota Corolla", "Nissan Qashqai", "Kia Sportage", "Suzuki Swift", "Lamborghini Huracán",
          "Ferrari F8 Tributo", "Bugatti Chiron", "Volvo XC90", "BMW M3"]
for i in range(14):
    ev = EVS[i % len(EVS)]
    add("ev", "ev:" + ev, "Which of these is fully electric?", ev, rng.sample(NOT_EV, 3), f"The {ev} runs on batteries alone.", ks=["ev:" + ev])
for i in range(10):
    ne = NOT_EV[(i * 5) % len(NOT_EV)]
    add("ev", "notev:" + ne, "Which of these is NOT fully electric?", ne, rng.sample(EVS, 3),
        "The Toyota Prius is a hybrid: it has a petrol engine as well as an electric motor." if ne == "Toyota Prius" else f"The {ne} has a petrol engine.", ks=["ev:" + ne])

# ------------------------------------------------------------------ which side of the road
LEFT = ["The UK", "Ireland", "Japan", "Australia", "New Zealand", "India", "South Africa", "Kenya", "Thailand", "Malaysia", "Singapore",
        "Indonesia", "Pakistan", "Sri Lanka", "Jamaica", "Cyprus", "Malta", "Bangladesh"]
RIGHT = ["France", "Germany", "The USA", "Canada", "Spain", "Italy", "Brazil", "Mexico", "China", "Russia", "Egypt", "Nigeria", "Argentina",
         "Saudi Arabia", "South Korea", "Sweden", "Portugal", "Turkey", "The Philippines", "Vietnam", "Iceland", "Poland", "Greece", "Norway"]
for i in range(12):
    a = LEFT[(i * 7) % len(LEFT)]
    add("drive", "left:" + a, "In which of these countries do people drive on the left?", a, rng.sample(RIGHT, 3), ks=["drive:" + a])
for i in range(8):
    a = RIGHT[(i * 5) % len(RIGHT)]
    add("drive", "right:" + a, "In which of these countries do people drive on the right?", a, rng.sample(LEFT, 3), ks=["drive:" + a])

# ------------------------------------------------------------------ hand-written questions
F = lambda c, q, a, o, x=None: (c, q, a, o, x)
FACTS = [
    # history
    F("hist", "Who built the first practical petrol-powered car, in 1885 to 1886?", "Karl Benz", ["Henry Ford", "Ferdinand Porsche", "Enzo Ferrari"]),
    F("hist", "Which car was the first to be built on a moving assembly line?", "Ford Model T", ["Volkswagen Beetle", "Austin Seven", "Rolls-Royce Silver Ghost"], "Ford started the moving assembly line in 1913."),
    F("hist", "Roughly how many Ford Model Ts were built?", "About 15 million", ["About 1.5 million", "About 150,000", "About 50 million"]),
    F("hist", "Which car is the best-selling of all time, counting every generation?", "Toyota Corolla", ["Volkswagen Golf", "Ford Fiesta", "Honda Civic"], "More than 50 million Corollas have been sold."),
    F("hist", "Which car is the best-selling single design ever, with over 21 million built?", "Volkswagen Beetle", ["Ford Model T", "Mini", "Citroën 2CV"]),
    F("hist", "Who designed the original Volkswagen Beetle?", "Ferdinand Porsche", ["Enzo Ferrari", "Alec Issigonis", "Henry Ford"]),
    F("hist", "Who designed the original Mini?", "Alec Issigonis", ["Colin Chapman", "Ferdinand Porsche", "Ian Callum"]),
    F("hist", "In which year did the original Mini go on sale?", "1959", ["1949", "1969", "1979"]),
    F("hist", "Who founded Lotus?", "Colin Chapman", ["Bruce McLaren", "Alec Issigonis", "Frank Williams"]),
    F("hist", "Before making sports cars, Ferruccio Lamborghini made his money building what?", "Tractors", ["Motorbikes", "Aeroplanes", "Washing machines"]),
    F("hist", "Peugeot was making which of these long before it built cars?", "Pepper and coffee mills", ["Sewing machines", "Cork", "Weaving looms"]),
    F("hist", "Opel started out making what?", "Sewing machines", ["Pepper mills", "Cork", "Tractors"]),
    F("hist", "Mazda began as a company making what?", "Cork", ["Sewing machines", "Pepper mills", "Tractors"], "It was called Toyo Cork Kogyo."),
    F("hist", "The company that started Toyota first made what?", "Automatic weaving looms", ["Cork", "Sewing machines", "Tractors"], "Toyoda Automatic Loom Works started the car business in the 1930s."),
    F("hist", "Saab built what before it built cars?", "Aeroplanes", ["Tractors", "Sewing machines", "Ships"]),
    F("hist", "BMW first made what?", "Aircraft engines", ["Tractors", "Sewing machines", "Bicycles"]),
    F("hist", "Honda got started by fitting small engines to what?", "Bicycles", ["Lawnmowers", "Boats", "Tractors"]),
    F("hist", "Which team did Enzo Ferrari race for before starting Ferrari?", "Alfa Romeo", ["Maserati", "Fiat", "Lancia"]),
    F("hist", "According to the famous story, which car maker was started by a tractor maker who was annoyed with his Ferrari?", "Lamborghini", ["Maserati", "De Tomaso", "Pagani"]),
    F("hist", "In which year was the first Le Mans 24 Hours race?", "1923", ["1903", "1953", "1963"]),
    F("hist", "Which car maker has won the Le Mans 24 Hours the most times?", "Porsche", ["Ferrari", "Audi", "Toyota"]),
    F("hist", "In which country is the Le Mans 24 Hours held?", "France", ["Belgium", "Germany", "Italy"]),
    F("hist", "What is the Nürburgring Nordschleife's nickname?", "The Green Hell", ["The Iron Ring", "The Black Forest", "The Long Mile"], "Racing driver Jackie Stewart called it that."),
    F("hist", "In which country is the Nürburgring?", "Germany", ["Austria", "Belgium", "Switzerland"]),
    F("hist", "Which country makes the most cars?", "China", ["The USA", "Japan", "Germany"]),
    F("hist", "Which car maker sold the most cars in the world in 2024?", "Toyota", ["Volkswagen", "Hyundai", "Ford"]),
    F("hist", "An engineer at which car maker invented the modern three-point seat belt in 1959?", "Volvo", ["Mercedes-Benz", "Saab", "Ford"], "Nils Bohlin of Volvo designed it, and Volvo let every car maker use it for free."),
    F("hist", "In which year did wearing a front seat belt become the law for UK drivers?", "1983", ["1963", "1973", "1993"]),
    F("hist", "In which year did driving tests become compulsory in the UK?", "1935", ["1905", "1955", "1965"]),
    F("hist", "In which year did the MOT test start in the UK?", "1960", ["1930", "1975", "1990"]),
    F("hist", "What was the UK's first stretch of motorway, opened in 1958?", "The Preston Bypass", ["The M1 near London", "The M25", "The M4 into Wales"], "It's now part of the M6."),
    F("hist", "In which year did the M25 around London fully open?", "1986", ["1966", "1976", "1996"]),
    F("hist", "In 1896 Walter Arnold got the world's first speeding ticket. How fast was he going?", "8 mph", ["18 mph", "28 mph", "48 mph"], "The limit was 2 mph."),
    F("hist", "What did Britain's 1865 'Red Flag Act' make cars have?", "A person walking in front waving a red flag", ["A red flag on the roof", "Red paint on the front", "A red light at night"]),
    F("hist", "Who said customers could have a car in 'any colour so long as it is black'?", "Henry Ford", ["Ferdinand Porsche", "Enzo Ferrari", "Karl Benz"]),
    F("hist", "Which was the first car to go faster than 300 mph?", "Bugatti Chiron Super Sport 300+", ["Koenigsegg Agera RS", "McLaren F1", "SSC Tuatara"], "A prototype hit 304.77 mph in 2019."),
    F("hist", "What is the world land speed record, set by Thrust SSC in 1997?", "763 mph", ["463 mph", "663 mph", "863 mph"]),
    F("hist", "Who drove Thrust SSC to the land speed record?", "Andy Green", ["Donald Campbell", "Lewis Hamilton", "Jeremy Clarkson"]),
    F("hist", "Thrust SSC was the first car to break what?", "The sound barrier", ["1,000 mph", "The speed of light", "The 24-hour distance record"]),
    F("hist", "Tesla's first car, the Roadster, was based on which car?", "Lotus Elise", ["Mazda MX-5", "Porsche Boxster", "Toyota MR2"]),
    F("hist", "The Ford GT40 was built to beat which team at Le Mans?", "Ferrari", ["Porsche", "Jaguar", "Mercedes-Benz"]),
    F("hist", "In which year did the Ford GT40 first win Le Mans?", "1966", ["1956", "1976", "1986"]),
    F("hist", "Which car was the UK's best-seller every year from 2009 to 2020?", "Ford Fiesta", ["Vauxhall Corsa", "Ford Focus", "Volkswagen Golf"]),
    F("hist", "In which year did Ford stop making the Fiesta?", "2023", ["2013", "2018", "2020"]),
    F("hist", "East Germany's Trabant had a body made of what?", "Hard plastic mixed with cotton", ["Aluminium", "Fibreglass", "Wood"]),
    F("hist", "Morgan still builds car frames out of which material?", "Ash wood", ["Bamboo", "Carbon fibre only", "Cast iron"]),
    F("hist", "Which is the smallest production car ever made?", "Peel P50", ["Smart ForTwo", "Fiat 500", "Mini"], "It's 1.37 m long and was built on the Isle of Man."),
    F("hist", "What is the most expensive car ever sold?", "Mercedes-Benz 300 SLR Uhlenhaut Coupé", ["Ferrari 250 GTO", "McLaren F1", "Bugatti Chiron"], "It sold for €135 million in 2022."),
    # prices and speeds
    F("pricefact", "How much did the original Mini cost in 1959?", "About £500", ["About £50", "About £5,000", "About £15,000"], "It was £497."),
    F("pricefact", "The Tata Nano was launched in 2008 as the world's cheapest car. What did it cost in India?", "About 100,000 rupees", ["About 10,000 rupees", "About 1 million rupees", "About 5 million rupees"], "That's 1 lakh, about £1,250 at the time."),
    F("pricefact", "About how much did a McLaren F1 cost new in the UK?", "£540,000", ["£54,000", "£154,000", "£5.4 million"]),
    F("speedfact", "The Bugatti Chiron's top speed is limited to what?", "261 mph (420 km/h)", ["201 mph (324 km/h)", "231 mph (372 km/h)", "301 mph (484 km/h)"]),
    F("speedfact", "What was the McLaren F1's top speed?", "240 mph (386 km/h)", ["190 mph (306 km/h)", "210 mph (338 km/h)", "260 mph (418 km/h)"]),
    F("speedfact", "Many fast German cars are limited to what top speed?", "155 mph (250 km/h)", ["125 mph (201 km/h)", "186 mph (300 km/h)", "200 mph (322 km/h)"]),
    F("speedfact", "What is the Peel P50's top speed?", "38 mph (61 km/h)", ["18 mph (29 km/h)", "58 mph (93 km/h)", "78 mph (126 km/h)"]),
    F("speedfact", "What is the Tesla Model S Plaid's top speed?", "200 mph (322 km/h)", ["155 mph (250 km/h)", "180 mph (290 km/h)", "230 mph (370 km/h)"]),
    # tech
    F("tech", "Where is the engine in a Porsche 911?", "Behind the rear wheels", ["In the front", "Just behind the seats", "Under the seats"]),
    F("tech", "Where was the engine in the original Volkswagen Beetle?", "At the back", ["At the front", "Under the front seats", "In the middle of the roof"]),
    F("tech", "How did the original Mini fit four seats into such a small car?", "Its engine was turned sideways", ["Its engine was in the boot", "It had no gearbox", "Its wheels were inside the car"]),
    F("tech", "What kind of engine did the Mazda RX-7 and RX-8 use?", "A rotary (Wankel) engine", ["A V12", "A diesel engine", "A W16"]),
    F("tech", "Who invented the rotary engine used by Mazda?", "Felix Wankel", ["Rudolf Diesel", "Karl Benz", "Nikolaus Otto"]),
    F("tech", "Which kind of engine lights its fuel by squeezing it, with no spark plugs?", "Diesel", ["Petrol", "Rotary", "Electric"]),
    F("tech", "What spins a turbocharger?", "Exhaust gases", ["A belt from the engine", "The battery", "Air from the radiator"]),
    F("tech", "What drives a supercharger?", "A belt or gears from the engine", ["Exhaust gases", "The wheels", "A solar panel"]),
    F("tech", "What does ABS stand for?", "Anti-lock braking system", ["Automatic brake sensor", "Air bag system", "Assisted braking speed"]),
    F("tech", "What does ESC stand for?", "Electronic stability control", ["Engine speed control", "Emergency stop clutch", "Electric steering column"]),
    F("tech", "What does DSG stand for, in Volkswagen gearboxes?", "Direct-shift gearbox", ["Double-speed gears", "Drive sport gear", "Digital shift guide"]),
    F("tech", "What does PS stand for in car power figures?", "Pferdestärke (German for horsepower)", ["Power speed", "Piston size", "Pounds per second"]),
    F("tech", "What does rpm stand for?", "Revolutions per minute", ["Rotations per mile", "Revs per metre", "Rate of power made"]),
    F("tech", "What does PHEV stand for?", "Plug-in hybrid electric vehicle", ["Petrol hybrid engine vehicle", "Power hybrid electric van", "Plug-in high-efficiency vehicle"]),
    F("tech", "What does LPG stand for?", "Liquefied petroleum gas", ["Low-pressure gas", "Light petrol gas", "Liquid power gel"]),
    F("tech", "In a rear-wheel-drive car, which wheels does the engine turn?", "The back wheels", ["The front wheels", "All four wheels", "Whichever has most grip"]),
    F("tech", "What does Audi call its four-wheel-drive system?", "quattro", ["xDrive", "4MATIC", "4MOTION"], "Quattro is Italian for four."),
    F("tech", "What does BMW call its four-wheel-drive system?", "xDrive", ["quattro", "4MATIC", "4MOTION"]),
    F("tech", "What does Mercedes-Benz call its four-wheel-drive system?", "4MATIC", ["quattro", "xDrive", "4MOTION"]),
    F("tech", "What does Volkswagen call its four-wheel-drive system?", "4MOTION", ["quattro", "xDrive", "4MATIC"]),
    F("tech", "What does torque measure?", "Twisting force", ["Top speed", "Fuel use", "Weight"]),
    F("tech", "What does a catalytic converter do?", "Cuts harmful gases in the exhaust", ["Makes the engine louder", "Cools the brakes", "Charges the battery"]),
    F("tech", "What does regenerative braking do?", "Turns the car's movement back into electricity", ["Pumps the brakes for you", "Recycles old brake pads", "Uses the engine to stop"]),
    F("tech", "What does an electric car's kWh figure tell you?", "How much energy the battery holds", ["Its top speed", "How heavy the battery is", "How fast it charges"]),
    F("tech", "What does the red line on a rev counter show?", "The engine's maximum safe revs", ["The speed limit", "When to fill up", "The engine's temperature"]),
    F("tech", "What does a clutch do?", "Connects and disconnects the engine from the gearbox", ["Stops the wheels", "Cools the engine", "Steers the car"]),
    F("tech", "Which car maker uses 'boxer' (flat) engines in almost all of its cars?", "Subaru", ["Mazda", "Honda", "Toyota"]),
    F("tech", "How many turbochargers does the Bugatti Chiron's engine have?", "Four", ["Two", "Six", "Eight"]),
    F("tech", "What powers a Toyota Prius?", "A petrol engine and an electric motor", ["Batteries only", "A diesel engine", "Hydrogen only"]),
    F("tech", "In Formula 1, what does DRS stand for?", "Drag reduction system", ["Driver radio system", "Dynamic ride suspension", "Direct race start"]),
    F("tech", "What does GT stand for?", "Gran Turismo (grand tourer)", ["Great torque", "Gear train", "Grand turbo"]),
    F("tech", "What does GTI stand for?", "Grand Touring Injection", ["Great Torque Inside", "Gear Train Ignition", "Grand Turbo Intake"]),
    F("tech", "What does RS stand for on fast Audis and Porsches?", "RennSport (German for racing sport)", ["Road Sport", "Rally Special", "Rapid Speed"]),
    F("tech", "What does SUV stand for?", "Sport utility vehicle", ["Super urban vehicle", "Small utility van", "Speed and utility vehicle"]),
    F("tech", "What does a car's differential do?", "Lets the wheels on each side turn at different speeds", ["Changes gear", "Measures fuel", "Cools the gearbox"]),
    F("tech", "What is understeer?", "The front tyres slide and the car turns less than you steer", ["The back tyres slide out", "The car leans in corners", "The steering goes light at speed"]),
    F("tech", "What is oversteer?", "The back of the car slides out", ["The front tyres slide wide", "The engine revs too high", "The car turns too slowly"]),
    F("tech", "What are 'slick' tyres?", "Tyres with no tread", ["Tyres for snow", "Tyres filled with foam", "Tyres for wet roads"]),
    F("tech", "What does mpg measure?", "Miles per gallon of fuel", ["Miles per gear", "Maximum power gain", "Metres per go"]),
    # badges and names
    F("logo", "Which car maker's badge shows a prancing horse on a yellow shield?", "Ferrari", ["Lamborghini", "Maserati", "Alfa Romeo"]),
    F("logo", "Which car maker's badge shows a charging bull?", "Lamborghini", ["Ferrari", "Maserati", "Pagani"]),
    F("logo", "Which car maker's badge is four interlocking rings?", "Audi", ["Volkswagen", "BMW", "Mercedes-Benz"]),
    F("logo", "What do Audi's four rings stand for?", "Four car companies that joined together", ["The founder's four children", "Four wheels", "Four Le Mans wins"], "Audi, DKW, Horch and Wanderer formed Auto Union in 1932."),
    F("logo", "Which car maker's badge is a trident?", "Maserati", ["Ferrari", "Alfa Romeo", "Lancia"]),
    F("logo", "Maserati's trident comes from a statue in Bologna of which god?", "Neptune", ["Zeus", "Mars", "Apollo"]),
    F("logo", "Which car maker's badge shows a lion standing on its back legs?", "Peugeot", ["Renault", "Citroën", "Opel"]),
    F("logo", "Which car maker's badge is a three-pointed star?", "Mercedes-Benz", ["BMW", "Audi", "Volkswagen"]),
    F("logo", "The Mercedes star's three points stand for land, sea and what?", "Air", ["Fire", "Space", "Speed"]),
    F("logo", "Which car maker's badge shows six stars?", "Subaru", ["Mitsubishi", "Mazda", "Toyota"]),
    F("logo", "Subaru's six stars are part of which star cluster?", "The Pleiades", ["Orion's Belt", "The Plough", "Cassiopeia"], "Subaru is the Japanese name for the Pleiades."),
    F("logo", "Which car maker's badge is three red diamonds?", "Mitsubishi", ["Subaru", "Toyota", "Mazda"]),
    F("logo", "Which car maker's badge shows a leaping big cat?", "Jaguar", ["Peugeot", "Lotus", "Porsche"]),
    F("logo", "Which car maker's badge shows a scorpion?", "Abarth", ["Alfa Romeo", "Lancia", "Fiat"]),
    F("logo", "Which car maker's badge shows a snake swallowing a person?", "Alfa Romeo", ["Maserati", "Lancia", "Fiat"]),
    F("logo", "Which car maker's badge is known as 'the bowtie'?", "Chevrolet", ["Cadillac", "Ford", "Dodge"]),
    F("logo", "Which car maker's badge is two chevrons, one above the other?", "Citroën", ["Renault", "Peugeot", "Opel"]),
    F("logo", "Citroën's chevrons come from André Citroën's first business, making what?", "Gears", ["Hats", "Bicycles", "Tyres"]),
    F("logo", "Which car maker's badge is a diamond shape?", "Renault", ["Peugeot", "Citroën", "Opel"]),
    F("logo", "Which car maker's badge is a blue and white roundel?", "BMW", ["Volkswagen", "Audi", "Mercedes-Benz"]),
    F("logo", "BMW's blue and white come from the flag of which German state?", "Bavaria", ["Saxony", "Berlin", "Hamburg"]),
    F("logo", "Which car maker's badge has wings with a big letter B in the middle?", "Bentley", ["Aston Martin", "Mini", "Bugatti"]),
    F("logo", "The 'Spirit of Ecstasy' figure on the bonnet belongs to which car maker?", "Rolls-Royce", ["Bentley", "Jaguar", "Aston Martin"]),
    F("logo", "Which car maker's badge shows a griffin?", "Vauxhall", ["Opel", "Ford", "Jaguar"]),
    F("logo", "Which car maker's badge is a lightning bolt?", "Opel", ["Vauxhall", "Tesla", "Ford"]),
    F("logo", "Which car maker's badge is three overlapping ovals?", "Toyota", ["Honda", "Nissan", "Hyundai"]),
    F("logo", "Which car maker's badge is a slanted letter H in an oval?", "Hyundai", ["Honda", "Kia", "Genesis"]),
    F("logo", "Which car maker's badge is a letter T shaped like part of an electric motor?", "Tesla", ["Toyota", "Lotus", "Polestar"]),
    F("logo", "Which car maker's badge is a circle with an arrow pointing up and to the right?", "Volvo", ["Saab", "Polestar", "Kia"]),
    F("logo", "Which car maker's badge is a winged arrow?", "Škoda", ["Seat", "Dacia", "Opel"]),
    F("logo", "Which car maker's badge has a black horse in the middle of a crest with antlers?", "Porsche", ["Ferrari", "Lamborghini", "Maserati"]),
    F("logo", "Porsche's crest uses the coat of arms of which city?", "Stuttgart", ["Munich", "Berlin", "Frankfurt"]),
    F("logo", "Which car maker's badge is nicknamed 'the Blue Oval'?", "Ford", ["Chevrolet", "Opel", "Hyundai"]),
    F("logo", "Ferrari's prancing horse first appeared on the plane of which First World War pilot?", "Francesco Baracca", ["The Red Baron", "Charles Lindbergh", "Douglas Bader"]),
    F("logo", "Lamborghini names most of its cars after what?", "Famous fighting bulls", ["Italian cities", "Winds", "Racing drivers"]),
    F("logo", "Many Maserati models are named after what?", "Winds", ["Bulls", "Gods", "Cities"], "Ghibli, Levante, Mistral and Bora are all winds."),
    F("name", "What does 'Volkswagen' mean?", "People's car", ["Fast car", "Wolf's car", "Family wagon"]),
    F("name", "'Audi' is Latin for what?", "Listen", ["Gold", "Speed", "Four"], "It's a play on the founder's name, Horch, which means 'hark' in German."),
    F("name", "'Volvo' is Latin for what?", "I roll", ["I fly", "Safe", "Strong"]),
    F("name", "What does 'Hyundai' mean in Korean?", "Modern", ["Fast", "Star", "Strong"]),
    F("name", "What does BMW stand for?", "Bayerische Motoren Werke (Bavarian Motor Works)", ["British Motor Works", "Berlin Motor Wagons", "Bavarian Military Wheels"]),
    F("name", "What does FIAT stand for?", "Fabbrica Italiana Automobili Torino", ["Ferrari Italian Auto Team", "First Italian Automobile Trade", "Fast Italian Auto Technology"]),
    F("name", "What does SEAT stand for?", "Sociedad Española de Automóviles de Turismo", ["Spanish Engineering And Technology", "Sport España Auto Team", "Sociedad Europea de Autos y Trenes"]),
    F("name", "What does MG stand for?", "Morris Garages", ["Motor Group", "Midland Garages", "Mini Grand"]),
    F("name", "What does Saab stand for?", "Svenska Aeroplan Aktiebolaget (Swedish Aeroplane Company)", ["Swedish Automobile Association Board", "Scandinavian Auto And Bus", "Stockholm Auto Assembly Base"]),
    F("name", "What does AMG stand for?", "Aufrecht, Melcher, Großaspach", ["Advanced Mercedes Group", "Automobile Motor Germany", "Auto Mercedes GmbH"], "The founders' names and Aufrecht's home town."),
    F("name", "What did 'ALFA' in Alfa Romeo originally stand for?", "Anonima Lombarda Fabbrica Automobili", ["Automobili Leggeri Fabbricati in Alessandria", "Associazione Lombarda Fabbricanti Auto", "Auto Lusso Fatte in Ancona"]),
    F("name", "Which car maker is named after a famous inventor?", "Tesla", ["Lincoln", "Chevrolet", "Dodge"], "Nikola Tesla worked on electric motors and power."),
    F("name", "Lincoln cars are named after whom?", "Abraham Lincoln", ["The founder, Henry Lincoln", "The city of Lincoln", "Lincoln Ford, Henry Ford's son"]),
    F("name", "Louis Chevrolet, who gave Chevrolet its name, was what?", "A racing driver", ["A banker", "A football player", "A train driver"]),
    F("name", "Aston Martin's name comes from Lionel Martin and what?", "Aston Hill, a hill-climb race", ["His wife, Aston", "Aston Villa", "Aston University"]),
    F("name", "Mazda's name comes partly from Ahura Mazda, a god of what?", "Wisdom", ["War", "The sea", "Speed"]),
    F("name", "How was the Toyota founder's family name spelt?", "Toyoda", ["Toyata", "Toyado", "Tayoda"]),
    F("name", "What does 'Mitsubishi' mean?", "Three diamonds", ["Rising sun", "Three rivers", "Strong engine"]),
    F("name", "What does 'Murciélago' mean in Spanish?", "Bat", ["Bull", "Storm", "Lion"], "It was also the name of a famous fighting bull."),
    F("name", "What does 'Testarossa' mean in Italian?", "Red head", ["Fast red", "Red horse", "Red track"], "Its engine had red cam covers."),
    F("name", "What does 'Huracán' mean in Spanish?", "Hurricane", ["Hunter", "Thunder", "Horn"]),
    F("name", "Pagani's founder, Horacio Pagani, comes from which country?", "Argentina", ["Italy", "Spain", "Brazil"]),
    # film and TV
    F("screen", "Which car did James Bond drive in Goldfinger (1964)?", "Aston Martin DB5", ["Jaguar E-Type", "Lotus Esprit", "BMW Z3"]),
    F("screen", "Which Bond car turned into a submarine in The Spy Who Loved Me (1977)?", "Lotus Esprit", ["Aston Martin DB5", "AMC Hornet", "Toyota 2000GT"]),
    F("screen", "Which BMW did James Bond drive in GoldenEye (1995)?", "BMW Z3", ["BMW Z8", "BMW M3", "BMW i8"]),
    F("screen", "Which car was turned into a time machine in Back to the Future?", "DeLorean DMC-12", ["Ford Mustang", "Chevrolet Corvette", "Pontiac Firebird"]),
    F("screen", "What kind of car was KITT in the 1982 TV series Knight Rider?", "Pontiac Firebird Trans Am", ["Chevrolet Camaro", "Ford Mustang", "Dodge Charger"]),
    F("screen", "What kind of car is Herbie, the Love Bug?", "Volkswagen Beetle", ["Mini", "Fiat 500", "Citroën 2CV"]),
    F("screen", "What is Herbie the Love Bug's racing number?", "53", ["95", "13", "7"]),
    F("screen", "What kind of car does Mr Bean drive?", "Mini", ["Fiat 500", "Reliant Robin", "Volkswagen Beetle"]),
    F("screen", "What colour is Mr Bean's Mini?", "Lime green with a black bonnet", ["Red with a white roof", "Yellow", "Blue with a white stripe"]),
    F("screen", "The Ghostbusters' car, Ecto-1, was built from what?", "A 1959 Cadillac", ["A 1959 Chevrolet Impala", "A Lincoln Continental", "A Ford Thunderbird"]),
    F("screen", "In the 2007 Transformers film, Bumblebee turns into which car?", "Chevrolet Camaro", ["Ford Mustang", "Dodge Charger", "Volkswagen Beetle"]),
    F("screen", "In the original 1980s Transformers cartoon, Bumblebee was which car?", "Volkswagen Beetle", ["Chevrolet Camaro", "Mini", "Fiat 500"]),
    F("screen", "Which cars made the famous getaway in The Italian Job (1969)?", "Minis", ["Fiat 500s", "Volkswagen Beetles", "Ford Escorts"]),
    F("screen", "What colours were the three Minis in The Italian Job (1969)?", "Red, white and blue", ["Black, white and gold", "Red, green and white", "Yellow, blue and black"]),
    F("screen", "In The Fast and the Furious (2001), which car is Brian's orange car in the final race?", "Toyota Supra", ["Mazda RX-7", "Honda NSX", "Nissan 350Z"]),
    F("screen", "Which car is Dom Toretto's famous black muscle car in the Fast & Furious films?", "Dodge Charger", ["Chevrolet Camaro", "Ford Mustang", "Plymouth Barracuda"]),
    F("screen", "In Tokyo Drift, what is Han's orange and black car?", "Mazda RX-7", ["Nissan Silvia", "Toyota Supra", "Mitsubishi Lancer Evolution"]),
    F("screen", "In Gone in 60 Seconds (2000), what kind of car is 'Eleanor'?", "Ford Mustang", ["Chevrolet Camaro", "Dodge Charger", "Pontiac GTO"]),
    F("screen", "Which car did Steve McQueen drive in the famous chase in Bullitt (1968)?", "Ford Mustang GT", ["Dodge Charger", "Chevrolet Camaro", "Pontiac GTO"]),
    F("screen", "What kind of car is the General Lee in The Dukes of Hazzard?", "Dodge Charger", ["Pontiac Trans Am", "Chevrolet Camaro", "Ford Mustang"]),
    F("screen", "Which car did the Bandit drive in Smokey and the Bandit (1977)?", "Pontiac Trans Am", ["Chevrolet Camaro", "Ford Mustang", "Dodge Charger"]),
    F("screen", "Which red sports car do the friends borrow in Ferris Bueller's Day Off?", "Ferrari 250 GT California", ["Ferrari Testarossa", "Lamborghini Countach", "Porsche 911"]),
    F("screen", "Which white car did Crockett drive in later series of Miami Vice?", "Ferrari Testarossa", ["Lamborghini Countach", "Porsche 928", "Chevrolet Corvette"]),
    F("screen", "What kind of van did The A-Team drive?", "GMC Vandura", ["Ford Econoline", "Volkswagen Transporter", "Dodge Ram Van"]),
    F("screen", "In Only Fools and Horses, what is the Trotters' yellow three-wheeler?", "Reliant Regal", ["Reliant Robin", "Bond Bug", "Peel P50"], "It's often called a Robin, but it's a Reliant Regal Supervan."),
    F("screen", "In Thunderbirds, Lady Penelope's pink car FAB 1 is which make?", "Rolls-Royce", ["Bentley", "Jaguar", "Cadillac"]),
    F("screen", "What is Lightning McQueen's racing number in Cars?", "95", ["53", "43", "86"]),
    F("screen", "In Cars, Sally Carrera is which car?", "Porsche 911", ["Chevrolet Corvette", "Mazda MX-5", "Ferrari 308"]),
    F("screen", "In Cars, Doc Hudson is which car?", "Hudson Hornet", ["Ford Model T", "Chevrolet Bel Air", "Buick Roadmaster"]),
    F("screen", "What is Scooby-Doo's van called?", "The Mystery Machine", ["The Spooky Van", "The Clue Cruiser", "The Ghost Wagon"]),
    F("screen", "What is the name of Top Gear's anonymous racing driver?", "The Stig", ["The Doc", "The Ace", "The Mask"]),
    F("screen", "The Batmobile in the 1966 Batman TV series was built from which concept car?", "Lincoln Futura", ["Cadillac Eldorado", "Chevrolet Corvette", "Ford Thunderbird"]),
    F("screen", "In the 2007 Transformers film, which truck is Optimus Prime?", "Peterbilt 379", ["Kenworth W900", "Mack Anthem", "Freightliner Cascadia"]),
    F("screen", "What kind of car is Christine, the killer car in the 1983 film?", "Plymouth Fury", ["Dodge Charger", "Cadillac Eldorado", "Ford Thunderbird"]),
    # road rules
    F("road", "What is the speed limit for cars on a UK motorway?", "70 mph", ["60 mph", "75 mph", "80 mph"]),
    F("road", "What is the usual speed limit on a road with street lights in England?", "30 mph", ["20 mph", "25 mph", "40 mph"]),
    F("road", "Since 2023, what is the usual limit on built-up roads in Wales?", "20 mph", ["15 mph", "25 mph", "30 mph"]),
    F("road", "What is the national speed limit for cars on a UK single-carriageway road?", "60 mph", ["50 mph", "55 mph", "70 mph"]),
    F("road", "In England, Scotland and Wales, how old is a car when it needs its first MOT?", "3 years", ["1 year", "5 years", "10 years"]),
    F("road", "What colour is the number plate on the back of a UK car?", "Yellow", ["White", "Black", "Blue"]),
    F("road", "What does a green strip on the left of a UK number plate mean?", "The car is fully electric", ["The car is brand new", "The driver is a learner", "The car is a hybrid"]),
    F("road", "How old do you normally have to be to drive a car on UK roads?", "17", ["16", "18", "21"]),
    F("road", "Which country is famous for stretches of motorway with no speed limit?", "Germany", ["Italy", "France", "Spain"]),
    F("road", "In the Highway Code, what is the typical stopping distance at 70 mph?", "96 metres", ["46 metres", "66 metres", "126 metres"]),
    F("road", "In the Highway Code, what is the typical stopping distance at 30 mph?", "23 metres", ["12 metres", "36 metres", "53 metres"]),
    F("road", "In which year did Sweden switch from driving on the left to the right?", "1967", ["1927", "1947", "1987"]),
    F("road", "On a UK motorway, what colour are the reflective studs between the lanes?", "White", ["Red", "Amber", "Green"]),
    F("road", "Who invented 'cat's eyes' road studs?", "Percy Shaw", ["Isambard Kingdom Brunel", "John Logie Baird", "James Dyson"]),
    F("road", "What does an 'L' plate on a car mean?", "A learner driver", ["A large vehicle", "A left-hand-drive car", "A lorry"]),
]
for c, q, a, o, x in FACTS:
    add(c, "fact:" + q, q, a, o, x)

# ------------------------------------------------------------------ assemble exactly 1,000
total = sum(len(v) for v in Q.values())
print({k: len(v) for k, v in Q.items()}, total)
bank = [q for v in Q.values() for q in v]
if total > 1000:   # trim the biggest pool (which brand makes which model)
    extra = total - 1000
    drop = set(id(q) for q in Q["model"][-extra:])
    bank = [q for q in bank if id(q) not in drop]
assert len(bank) == 1000, len(bank)
for q in bank:
    assert len(q["o"]) == 3 and q["a"] not in q["o"], q
json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wrote", len(bank))
