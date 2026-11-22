"""Build the Obscure Trivia site: a hub page plus one themed page per quiz, sharing one engine."""
import sys, os, json, shutil, datetime, html, hashlib

SRC, OUT = sys.argv[1], sys.argv[2]
SITE = os.environ.get("SITE_URL", "https://scboom.github.io/obscure-trivia/")
QUESTIONS_PER_GAME = 20   # what every quiz tile advertises
VERIFY = "WFhPSjzH6ULlMofAm5JW4QaXPHvu2l7NRQUrSs7A3Ho"
TEX = json.load(open(os.path.join(SRC, "textures.json")))
E = html.escape

QUIZZES = [
    {
        "id": "hearthstone", "dir": "hearthstone", "bank_src": "hs_questions.json",
        "title": "Hearthstone Battlegrounds Quiz – Obscure Trivia",
        "desc": "A free Hearthstone Battlegrounds quiz: 20 random questions per game on minion tiers and stats, hero armor in Solo and Duos, Hero Powers, Buddies, quests, trinkets and anomalies. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Bree+Serif&family=Figtree:wght@400;500;600;700",
        "theme_color": "#1d1512",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23e8b450' stroke='%23a8721f' stroke-width='4'/%3E%3Ctext x='32' y='44' font-size='34' text-anchor='middle' font-family='Georgia,serif' fill='%232a1b08'%3E%3F%3C/text%3E%3C/svg%3E",
        "config": {
            "id": "hearthstone", "letter": "H", "short": "Battlegrounds", "icon": "?",
            "eyebrow": "Hearthstone Battlegrounds quiz", "headline": "How well do you really know Bob's Tavern?",
            "topics": "minion tiers and stats, hero armor in Solo and Duos, Hero Powers, Buddies, quest rewards, trinkets, Tavern spells and anomalies",
            "foot": "Card data from the Hearthstone client files, build of 3 November 2026. Fan-made quiz, not affiliated with Blizzard.",
            "seed": "tavern-trivia-v1:", "topic": "tavern-trivia/v1/", "recentKey": "tt-recent-v1", "sessionKey": "tt-game",
            "bank": "questions.json", "hub": "../", "others": {"M": "../minecraft/"},
            "groups": {"tier": "Minion", "stats": "Minion", "type": "Minion", "effect": "Minion", "whois": "Minion", "golden": "Minion",
                       "oldstats": "Minion", "oldeffect": "Minion", "duos": "Minion", "armor": "Hero", "duoarmor": "Hero", "health": "Hero",
                       "hpname": "Hero", "hpwho": "Hero", "hpeffect": "Hero", "hpcost": "Hero", "buddy": "Hero", "buddywho": "Hero",
                       "quest": "Quest", "questwho": "Quest", "trinket": "Trinket", "trinketcost": "Trinket", "trinketkind": "Trinket",
                       "spell": "Tavern spell", "spellcost": "Tavern spell", "spelltier": "Tavern spell", "anomaly": "Anomaly", "anomalywho": "Anomaly"},
            "caps": {"Minion": 9, "Hero": 7, "Quest": 3, "Trinket": 3, "Tavern spell": 3, "Anomaly": 3},
            "verdicts": [[18, "Tavern legend."], [14, "Top four, easily."], [10, "Solid lobby. Bob approves."], [6, "You held on to your Armor."], [0, "Bob says: keep practising."]],
        },
        "theme": """
:root {
  --bg: #1d1512;
  --bg-art: repeating-linear-gradient(90deg, rgba(255,255,255,0.012) 0 2px, transparent 2px 9px), radial-gradient(ellipse at 50% -10%, #3a2618 0%, transparent 60%);
  --panel: #2a1f1a; --panel-fill: linear-gradient(180deg, #2a1f1a 0%, #251b16 100%); --panel-2: #37291f;
  --panel-shadow: 0 10px 30px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
  --line: #4a382c; --line-hover: #6a5140; --ink: #f4eadf; --muted: #b8a391; --faint: #8a7666; --placeholder: #7d6a5b;
  --accent: #e8b450; --accent-ink: #2a1b08; --accent-text: #e8b450; --accent-hover: #f0c063; --accent-edge: #f5cf7f; --accent-shadow: 0 2px 0 #9b6a1c;
  --chip-bg: rgba(232,180,80,0.1); --chip-line: rgba(232,180,80,0.25); --chip-ink: #f2cf8a;
  --pal: #6fc6d8; --pal-ink: #062026; --pal-bg: rgba(111,198,216,0.1); --pal-line: rgba(111,198,216,0.3);
  --good: #86d16f; --good-ink: #10200a; --good-bg: rgba(134,209,111,0.12); --bad: #e9725f; --bad-ink: #2a0b06; --bad-bg: rgba(233,114,95,0.12);
  --inset: #1a1210; --opt: #231a15; --tile: #221914;
  --card-bg: #f1e4cc; --card-ink: #2b1f14; --card-line: #c9b48f; --card-inner: #e6d5b5; --card-strong: #1a120b;
  --f-display: "Bree Serif", Georgia, "Times New Roman", serif; --f-body: "Figtree", system-ui, -apple-system, "Segoe UI", sans-serif;
  --r: 10px; --r-panel: 14px; --r-pill: 999px; --r-key: 7px;
  color-scheme: dark;
}
.coin {
  width: 30px; height: 30px; border-radius: 50%; flex: none;
  background: radial-gradient(circle at 35% 30%, #fff3c4 0 12%, var(--accent) 38%, #a8721f 100%);
  box-shadow: inset 0 -2px 0 rgba(0,0,0,0.25), 0 1px 0 rgba(0,0,0,0.4);
  display: grid; place-items: center; color: var(--accent-ink); font-family: var(--f-display); font-size: 0.9rem;
}
""",
        "tile": {"cls": "hs", "title": "Hearthstone Battlegrounds", "art": '<span class="coin" aria-hidden="true">?</span>',
                 "blurb": "Minion tiers and stats, hero armor in Solo and Duos, Hero Powers, quests, trinkets and anomalies."},
        "intro": ("Hearthstone Battlegrounds quiz", "How well do you really know Bob's Tavern?",
                  "A free Hearthstone Battlegrounds quiz, 20 questions per game: minion tiers and stats, hero armor in Solo and Duos, Hero Powers, Buddies, quest rewards, trinkets, Tavern spells and anomalies. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
    {
        "id": "minecraft", "dir": "minecraft", "bank_src": "mc_questions.json",
        "title": "Minecraft Bedrock Quiz – Obscure Trivia",
        "desc": "A free Minecraft: Bedrock Edition quiz: 20 random questions per game on crafting recipes, blocks, tools, mobs, enchanting, brewing and biomes. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Noto+Sans:wght@400;600;700",
        "theme_color": "#1b1c1e",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8' shape-rendering='crispEdges'%3E%3Crect width='8' height='8' fill='%23866043'/%3E%3Crect width='8' height='3' fill='%235f9f35'/%3E%3Crect y='3' width='2' height='1' fill='%235f9f35'/%3E%3Crect x='5' y='3' width='1' height='1' fill='%235f9f35'/%3E%3Crect x='3' y='5' width='1' height='1' fill='%23694b33'/%3E%3Crect x='6' y='6' width='1' height='1' fill='%23694b33'/%3E%3C/svg%3E",
        "extra": [("fonts/Monocraft.woff2", "Monocraft.woff2"), ("fonts/Monocraft-OFL.txt", "Monocraft-OFL.txt")],
        "config": {
            "id": "minecraft", "letter": "M", "short": "Minecraft", "icon": "",
            "eyebrow": "Minecraft: Bedrock Edition quiz", "headline": "Think you know every block, mob and recipe?",
            "topics": "crafting recipes, blocks and ores, tools, mobs, enchanting, brewing, biomes and villagers, all for the current Bedrock Edition",
            "foot": "All questions are about the current Minecraft: Bedrock Edition. Block, item and recipe data comes from the Bedrock game files (late 2026). Fan-made quiz, not affiliated with Mojang or Microsoft.",
            "seed": "obscure-trivia-minecraft-v1:", "topic": "obscure-trivia/minecraft/v1/", "recentKey": "ot-recent-minecraft-v1", "sessionKey": "ot-game-minecraft",
            "bank": "questions.json", "hub": "../", "others": {"H": "../hearthstone/"},
            "groups": {"recipe": "Crafting", "recipewhat": "Crafting", "recipecount": "Crafting", "smelt": "Crafting",
                       "notblock": "Blocks", "isblock": "Blocks", "light": "Blocks", "lightwhich": "Blocks", "tier": "Blocks", "blast": "Blocks", "hardness": "Blocks",
                       "stack": "Items", "food": "Items", "health": "Mobs", "hostile": "Mobs", "drops": "Mobs", "breed": "Mobs", "villager": "Mobs",
                       "enchlevel": "Enchanting", "treasure": "Enchanting", "treasure2": "Enchanting", "curse": "Enchanting", "enchslot": "Enchanting",
                       "enchclash": "Enchanting", "biome": "World", "fact": "World"},
            "caps": {"Crafting": 7, "Blocks": 5, "Items": 3, "Mobs": 5, "Enchanting": 4, "World": 4},
            "verdicts": [[19, "Netherite tier."], [16, "Diamond tier."], [12, "Iron tier. Solid gear."], [8, "Stone tier. Keep mining."], [0, "Wooden pickaxe energy. Try again!"]],
        },
        "theme": """
:root {
  --bg: #17181a;
  --bg-art: linear-gradient(rgba(12,12,14,0.62), rgba(12,12,14,0.78)), url(%(deep)s) 0 0 / 64px 64px;
  --panel: #313233; --panel-fill: #313233; --panel-2: #48494a;
  --panel-shadow: inset 0 3px 0 rgba(255,255,255,0.07), inset 0 -3px 0 rgba(0,0,0,0.25), 0 6px 0 rgba(0,0,0,0.35);
  --line: #0f0f10; --line-hover: #8c8d90; --ink: #ffffff; --muted: #b9babd; --faint: #8c8d90; --placeholder: #77787b;
  --accent: #3c8527; --accent-ink: #ffffff; --accent-text: #7ad155; --accent-hover: #4a9a32; --accent-edge: #1e4d12;
  --accent-shadow: inset 0 -4px 0 #1d4d13, inset 0 3px 0 rgba(255,255,255,0.22);
  --chip-bg: rgba(108,195,73,0.12); --chip-line: rgba(108,195,73,0.4); --chip-ink: #95e06f;
  --pal: #5fb7ee; --pal-ink: #04223a; --pal-bg: rgba(95,183,238,0.12); --pal-line: rgba(95,183,238,0.4);
  --good: #6cc349; --good-ink: #0d2a05; --good-bg: rgba(108,195,73,0.16); --bad: #ef5a45; --bad-ink: #2b0702; --bad-bg: rgba(239,90,69,0.16);
  --inset: #1e1e1f; --opt: #3a3b3c; --tile: #262728;
  --card-bg: #c6c6c6; --card-ink: #3a3a3a; --card-line: #000000; --card-inner: #8b8b8b; --card-strong: #1a1a1a;
  --f-display: "Monocraft", ui-monospace, "Courier New", monospace; --f-body: "Noto Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --r: 0px; --r-panel: 0px; --r-pill: 0px; --r-key: 0px;
  color-scheme: dark;
}
@font-face { font-family: "Monocraft"; src: url("Monocraft.woff2") format("woff2"); font-display: swap; }
body { image-rendering: pixelated; }
.qtext { font-size: clamp(1.1rem, 3.9vw, 1.4rem); line-height: 1.35; }
.opt .lbl.big { font-size: 1.05rem; }
.board { border-width: 2px; }
.btn { border-width: 2px; border-color: #0f0f10; box-shadow: inset 0 -4px 0 rgba(0,0,0,0.3), inset 0 3px 0 rgba(255,255,255,0.12); }
.btn:active { transform: translateY(2px); box-shadow: inset 0 -2px 0 rgba(0,0,0,0.3); }
.btn.gold { border-color: #0f0f10; }
.opt { border-width: 2px; }
.opt .key { border-width: 2px; }
.pip { border-radius: 0; }
.chip, .tag { border-radius: 0; }
.coin {
  width: 30px; height: 30px; flex: none; display: block;
  background: url(%(grass_side)s) 0 0 / 100%% 100%%; image-rendering: pixelated;
  box-shadow: inset 0 0 0 2px rgba(0,0,0,0.35), 0 2px 0 rgba(0,0,0,0.45);
}
.qtext { letter-spacing: 0.01em; }
.cardtext { box-shadow: inset 2px 2px 0 #ffffff, inset -2px -2px 0 #555555; border-width: 2px; font-weight: 600; }
""" % {"deep": TEX["deep"], "grass_side": TEX["grass_side"]},
        "tile": {"cls": "mc", "title": "Minecraft", "art": "",
                 "blurb": "Bedrock Edition: crafting recipes, blocks, tools, mobs, enchanting, brewing and biomes."},
        "intro": ("Minecraft: Bedrock Edition quiz", "Think you know every block, mob and recipe?",
                  "A free Minecraft: Bedrock Edition quiz, 20 questions per game: crafting recipes, blocks and ores, tools, mobs, enchanting, brewing, biomes and villagers. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
    {
        "id": "world", "dir": "general-knowledge", "bank_src": "world_questions.json",
        "title": "General Knowledge Quiz – Obscure Trivia",
        "desc": "A free general knowledge quiz: 20 random questions per game on space, animals, the human body, countries and flags, geography, history, science and culture. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Outfit:wght@500;600;700;800&family=Atkinson+Hyperlegible:wght@400;700",
        "theme_color": "#050a18",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='29' fill='%232f7fd0'/%3E%3Cpath d='M18 18c6-4 12-2 14 3s-3 8 1 12 9 1 10 7-6 10-10 9' fill='none' stroke='%2366b45a' stroke-width='7' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='32' r='29' fill='none' stroke='%23bfe3ff' stroke-width='3'/%3E%3C/svg%3E",
        "extra": [("world/earth-bg.jpg", "earth-bg.jpg"), ("world/earth-tile.jpg", "earth-tile.jpg"), ("world/flags", "flags")],
        "config": {
            "id": "world", "letter": "W", "short": "General Knowledge", "icon": "",
            "eyebrow": "General knowledge quiz", "headline": "How much do you know about our world?",
            "topics": "space, animals, the human body, countries and flags, geography, history and inventions, science, food, sport and culture",
            "foot": "Country facts from the open mledoze/countries dataset (ODbL) and flags from flag-icons (MIT). The Earth picture is drawn from Natural Earth map data. Fan-made quiz.",
            "seed": "obscure-trivia-world-v1:", "topic": "obscure-trivia/world/v1/", "recentKey": "ot-recent-world-v1", "sessionKey": "ot-game-world",
            "bank": "questions.json", "hub": "../",
            "groups": {"space": "Space", "animals": "Animals", "body": "Human body", "geo": "Geography", "history": "History", "science": "Science",
                       "culture": "Culture", "capital": "Countries", "capitalwho": "Countries", "currency": "Countries", "currencywho": "Countries",
                       "language": "Countries", "continent": "Countries", "landlocked": "Countries", "bigger": "Countries", "flag": "Countries"},
            "caps": {"Countries": 7, "Space": 2, "Animals": 3, "Human body": 2, "Geography": 3, "History": 2, "Science": 2, "Culture": 3},
            "verdicts": [[19, "Walking encyclopedia."], [16, "World class!"], [12, "Well travelled."], [8, "Tourist. Keep exploring!"], [0, "Time to pack your bags and explore!"]],
        },
        "theme": """
:root {
  --bg: #050a18; --bg-art: none;
  --panel: rgba(12, 22, 48, 0.78); --panel-fill: linear-gradient(180deg, rgba(16, 30, 64, 0.82), rgba(9, 18, 42, 0.86)); --panel-2: rgba(38, 60, 110, 0.75);
  --panel-shadow: 0 18px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  --line: rgba(150, 190, 255, 0.2); --line-hover: rgba(160, 210, 255, 0.55); --ink: #f2f7ff; --muted: #a9bbd8; --faint: #8296b8; --placeholder: #7186a8;
  --accent: #7dd3fc; --accent-ink: #04213a; --accent-text: #8edbff; --accent-hover: #a5e2ff; --accent-edge: #bfeaff; --accent-shadow: 0 6px 18px rgba(125, 211, 252, 0.28);
  --chip-bg: rgba(125, 211, 252, 0.1); --chip-line: rgba(125, 211, 252, 0.32); --chip-ink: #b9e8ff;
  --pal: #ff9b7a; --pal-ink: #3a1206; --pal-bg: rgba(255, 155, 122, 0.12); --pal-line: rgba(255, 155, 122, 0.4);
  --good: #5ee0a0; --good-ink: #03261a; --good-bg: rgba(94, 224, 160, 0.14); --bad: #ff7a85; --bad-ink: #3a060c; --bad-bg: rgba(255, 122, 133, 0.14);
  --inset: rgba(4, 10, 26, 0.7); --opt: rgba(20, 36, 74, 0.7); --tile: rgba(14, 26, 56, 0.75);
  --card-bg: #eef6ff; --card-ink: #0b1a33; --card-line: #bcd6f5; --card-inner: #dcebfd; --card-strong: #06122a;
  --f-display: "Outfit", "Segoe UI", system-ui, sans-serif; --f-body: "Atkinson Hyperlegible", "Segoe UI", system-ui, sans-serif;
  --r: 14px; --r-panel: 22px; --r-pill: 999px; --r-key: 10px;
  color-scheme: dark;
}
body::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: linear-gradient(180deg, rgba(5, 10, 24, 0.15) 0%, rgba(5, 10, 24, 0.35) 55%, rgba(5, 10, 24, 0.55) 100%), url(earth-bg.jpg) center bottom / cover no-repeat, #050a18; }
.board { backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
h1, h2, h3 { font-weight: 700; letter-spacing: -0.01em; }
.qtext { font-weight: 600; letter-spacing: -0.005em; }
.opt .lbl.big { font-weight: 600; }
.code-big { font-weight: 800; }
.coin {
  width: 30px; height: 30px; border-radius: 50%; flex: none; display: block;
  background: radial-gradient(circle at 70% 70%, transparent 46%, rgba(2, 8, 30, 0.55) 70%), radial-gradient(circle at 34% 38%, #6fbf5c 0 16%, transparent 17%),
    radial-gradient(circle at 62% 62%, #6fbf5c 0 13%, transparent 14%), radial-gradient(circle at 30% 30%, #8fd0ff, #2f7fd0 55%, #123f8a);
  box-shadow: 0 0 0 1px rgba(191, 227, 255, 0.5), 0 0 14px rgba(125, 211, 252, 0.45);
}
""",
        "tile": {"cls": "gk", "title": "General Knowledge", "art": "",
                 "blurb": "Space, animals, the human body, countries and flags, history, science and culture."},
        "intro": ("General knowledge quiz", "How much do you know about our world?",
                  "A free general knowledge quiz, 20 questions per game: space, animals, the human body, countries and flags, geography, history, science and culture. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
    {
        "id": "football", "dir": "football", "bank_src": "football_questions.json",
        "title": "Football Quiz – Obscure Trivia",
        "desc": "A free football quiz: 20 random questions per game on the Premier League, the World Cup, the Champions League, players, stadiums, nicknames and rules. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Oswald:wght@500;600;700&family=Barlow:wght@400;500;600;700",
        "theme_color": "#0d2a17",
        "favicon": "BALL",
        "extra": [],
        "config": {
            "id": "football", "letter": "F", "short": "Football", "icon": "",
            "eyebrow": "Football quiz", "headline": "Think you know your football?",
            "topics": "the Premier League, the World Cup, the Champions League and the Euros, legendary players, stadiums, nicknames, derbies and the rules",
            "foot": "Premier League and World Cup results from the openfootball project (public domain). Fan-made quiz, not affiliated with the Premier League, FIFA or UEFA.",
            "seed": "obscure-trivia-football-v1:", "topic": "obscure-trivia/football/v1/", "recentKey": "ot-recent-football-v1", "sessionKey": "ot-game-football",
            "bank": "questions.json", "hub": "../",
            "groups": {"plchamp": "Premier League", "plsecond": "Premier League", "plthird": "Premier League", "plfourth": "Premier League", "plpoints": "Premier League",
                       "plbottom": "Premier League", "pllowest": "Premier League", "pldown": "Premier League", "plup": "Premier League", "plhigher": "Premier League",
                       "plstreak": "Premier League", "plseasons": "Premier League", "plfirst": "Premier League", "plfounder": "Premier League", "plever": "Premier League",
                       "pltitles": "Premier League", "plrecord": "Premier League",
                       "wcwin": "World Cup", "wcfinal": "World Cup", "wchost": "World Cup", "wccount": "World Cup", "wclast": "World Cup", "wcpens": "World Cup", "wc": "World Cup",
                       "ucl": "Europe", "euro": "Europe", "player": "Players", "stadium": "Grounds", "city": "Grounds", "nickname": "Clubs", "derby": "Clubs",
                       "rules": "Rules", "fa": "English football"},
            "caps": {"Premier League": 7, "World Cup": 3, "Players": 3, "Europe": 2, "Grounds": 2, "Clubs": 2, "Rules": 2, "English football": 2},
            "verdicts": [[19, "Ballon d'Or material."], [16, "World class."], [12, "Premier League quality."], [8, "Championship level. Keep training!"], [0, "Sunday league. Back to training!"]],
        },
        "theme": """
:root {
  --bg: #0b2414;
  --bg-art: none;
  --panel: rgba(8, 24, 14, 0.86); --panel-fill: linear-gradient(180deg, rgba(10, 30, 18, 0.9), rgba(6, 20, 12, 0.92)); --panel-2: rgba(30, 70, 42, 0.85);
  --panel-shadow: 0 16px 34px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  --line: rgba(255, 255, 255, 0.22); --line-hover: rgba(255, 255, 255, 0.6); --ink: #ffffff; --muted: #bfd6c6; --faint: #95b39f; --placeholder: #7f9d89;
  --accent: #ffd84a; --accent-ink: #1d1600; --accent-text: #ffe066; --accent-hover: #ffe27a; --accent-edge: #fff0a8; --accent-shadow: 0 3px 0 #b8911a;
  --chip-bg: rgba(255, 255, 255, 0.08); --chip-line: rgba(255, 255, 255, 0.3); --chip-ink: #ffffff;
  --pal: #5ab4ff; --pal-ink: #03203a; --pal-bg: rgba(90, 180, 255, 0.12); --pal-line: rgba(90, 180, 255, 0.4);
  --good: #6ee07a; --good-ink: #062b0b; --good-bg: rgba(110, 224, 122, 0.15); --bad: #ff6b6b; --bad-ink: #3a0606; --bad-bg: rgba(255, 107, 107, 0.16);
  --inset: rgba(0, 0, 0, 0.35); --opt: rgba(16, 44, 26, 0.85); --tile: rgba(12, 34, 20, 0.88);
  --card-bg: #f4f7f2; --card-ink: #0f2416; --card-line: #c9d9cc; --card-inner: #e5eee6; --card-strong: #061409;
  --f-display: "Oswald", "Arial Narrow", Impact, sans-serif; --f-body: "Barlow", "Segoe UI", system-ui, sans-serif;
  --r: 8px; --r-panel: 12px; --r-pill: 999px; --r-key: 6px;
  color-scheme: dark;
}
/* a floodlit pitch: mowing stripes, chalk centre circle, dark edges */
body::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(255, 255, 230, 0.16), transparent 55%),
    radial-gradient(circle at 50% 46%, transparent 0 118px, rgba(255, 255, 255, 0.16) 119px 122px, transparent 123px),
    linear-gradient(180deg, transparent calc(46% - 1.5px), rgba(255, 255, 255, 0.16) calc(46% - 1.5px) calc(46% + 1.5px), transparent calc(46% + 1.5px)),
    radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0, 0, 0, 0.55) 100%),
    repeating-linear-gradient(180deg, #1d6a35 0 70px, #22783c 70px 140px); }
h1, h2, h3, .qtext, .code-big, .bigmsg, .verdict { text-transform: uppercase; letter-spacing: 0.02em; }
h1, h2, h3 { font-weight: 700; }
.qtext { font-weight: 600; text-transform: none; letter-spacing: 0; }
.opt .lbl.big { font-family: var(--f-body); font-weight: 600; font-size: 1.1rem; }
.coin {
  width: 30px; height: 30px; border-radius: 50%; flex: none; display: block;
  background: url("BALL") center / 100% 100%; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
}
""".replace("BALL", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='29' fill='%23fff' stroke='%23111' stroke-width='3'/%3E%3Cpath d='M32 20l10 7-4 12H26l-4-12z' fill='%23111'/%3E%3Cpath d='M32 20V8M42 27l11-4M38 39l7 10M26 39l-7 10M22 27l-11-4' stroke='%23111' stroke-width='3'/%3E%3C/svg%3E"),
        "tile": {"cls": "fb", "title": "Football", "art": "",
                 "blurb": "The Premier League, the World Cup, the Champions League, legendary players, stadiums, nicknames and rules."},
        "intro": ("Football quiz", "Think you know your football?",
                  "A free football quiz, 20 questions per game: the Premier League, the World Cup, the Champions League, legendary players, stadiums, nicknames and the rules. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
    {
        "id": "cars", "dir": "cars", "bank_src": "cars_questions.json",
        "title": "Car Quiz – Obscure Trivia",
        "desc": "A free car quiz: 20 random questions per game on horsepower, top speeds, prices, car makers, badges, engines and famous film cars. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Chakra+Petch:ital,wght@0,600;0,700;1,700&family=Titillium+Web:wght@400;600;700",
        "theme_color": "#0d0e10",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='29' fill='%2316171b' stroke='%23e10600' stroke-width='3'/%3E%3Cpath d='M14 42a20 20 0 1 1 36 0' fill='none' stroke='%23f3f4f6' stroke-width='5' stroke-dasharray='2 5.3'/%3E%3Cpath d='M32 36L45 21' stroke='%23e10600' stroke-width='4' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='36' r='4.5' fill='%23f3f4f6'/%3E%3C/svg%3E",
        "extra": [],
        "config": {
            "id": "cars", "letter": "C", "short": "Cars", "icon": "",
            "eyebrow": "Car quiz", "headline": "From hatchbacks to hypercars: how well do you know cars?",
            "topics": "horsepower, top speeds, prices, car makers and who owns them, founding dates, engines, badges, famous film cars and the rules of the road",
            "foot": "Horsepower and top speeds are the makers' own figures, and prices are rough UK prices when new. A question only compares cars when one is clearly ahead, because figures vary a little between model years and countries. Fan-made quiz, not affiliated with any car maker.",
            "seed": "obscure-trivia-cars-v1:", "topic": "obscure-trivia/cars/v1/", "recentKey": "ot-recent-cars-v1", "sessionKey": "ot-game-cars",
            "bank": "questions.json", "hub": "../",
            "groups": {"power": "Power", "model": "Makers", "country": "Makers", "owner": "Makers", "notby": "Makers", "decade": "History", "founded": "History", "hist": "History", "price": "Prices", "auction": "Prices", "pricefact": "Prices", "speed": "Speed", "speedfact": "Speed", "cyl": "Tech", "ev": "Tech", "tech": "Tech", "logo": "Badges", "name": "Badges", "screen": "Film & TV", "drive": "On the road", "road": "On the road"},
            "caps": {"Power": 2, "Makers": 3, "History": 5, "Prices": 2, "Speed": 2, "Tech": 2, "Badges": 2, "Film & TV": 2, "On the road": 1},
            "verdicts": [[19, "Pole position."], [16, "Podium finish."], [12, "Points finish."], [8, "Still on the grid. Keep practising."], [0, "Stalled on the line. Try again!"]],
        },
        "theme": """
:root {
  --bg: #0d0e10;
  --bg-art: linear-gradient(45deg, #121316 25%, transparent 25%, transparent 75%, #121316 75%) 0 0 / 10px 10px,
    linear-gradient(45deg, #121316 25%, transparent 25%, transparent 75%, #121316 75%) 5px 5px / 10px 10px,
    linear-gradient(#18191d, #141518);
  --panel: #17181c; --panel-fill: linear-gradient(180deg, rgba(30, 31, 36, 0.97), rgba(20, 21, 25, 0.97)); --panel-2: #24262c;
  --panel-shadow: 0 14px 34px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  --line: #33353c; --line-hover: #6b6f7a; --ink: #f3f4f6; --muted: #a6abb6; --faint: #81868f; --placeholder: #6f747d;
  --accent: #e10600; --accent-ink: #ffffff; --accent-text: #ff5a4d; --accent-hover: #f5170f; --accent-edge: #ff6a5c; --accent-shadow: 0 3px 0 #7a0300;
  --chip-bg: rgba(255, 255, 255, 0.06); --chip-line: rgba(255, 255, 255, 0.2); --chip-ink: #e5e7eb;
  --pal: #38bdf8; --pal-ink: #03202e; --pal-bg: rgba(56, 189, 248, 0.12); --pal-line: rgba(56, 189, 248, 0.4);
  --good: #34d399; --good-ink: #022c1d; --good-bg: rgba(52, 211, 153, 0.13); --bad: #f87171; --bad-ink: #300808; --bad-bg: rgba(248, 113, 113, 0.14);
  --inset: #0b0c0e; --opt: #1b1c21; --tile: #15161a;
  --card-bg: #f3f4f6; --card-ink: #111214; --card-line: #c9ccd2; --card-inner: #e4e6ea; --card-strong: #000000;
  --f-display: "Chakra Petch", "Arial Narrow", system-ui, sans-serif; --f-body: "Titillium Web", system-ui, -apple-system, "Segoe UI", sans-serif;
  --r: 6px; --r-panel: 10px; --r-pill: 999px; --r-key: 4px;
  color-scheme: dark;
}
/* carbon fibre under a red glow, like brake lights at the top of the screen */
body::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: radial-gradient(ellipse at 50% -15%, rgba(225, 6, 0, 0.32), transparent 55%), radial-gradient(ellipse at 50% 50%, transparent 45%, rgba(0, 0, 0, 0.6) 100%); }
h1, h2, h3, .bigmsg, .verdict, .code-big { font-weight: 700; font-style: italic; letter-spacing: 0.01em; }
.hero h2 { text-transform: uppercase; }
.qtext { font-weight: 700; }
.opt .lbl.big { font-family: var(--f-display); font-weight: 600; font-size: 1.12rem; }
.opt .key { font-family: var(--f-display); }
.opt:hover:not([disabled]) { border-color: var(--accent); }
/* a red and white stripe on each panel */
.board { position: relative; }
.board::before { content: ""; position: absolute; top: -1px; left: 22px; width: 64px; height: 4px; border-radius: 0 0 2px 2px;
  background: linear-gradient(90deg, var(--accent) 0 58%, transparent 58% 70%, #f3f4f6 70% 100%); }
.btn.gold { font-family: var(--f-display); font-style: italic; letter-spacing: 0.02em; }
.coin { width: 32px; height: 32px; flex: none; display: block; background: url("GAUGE") center / 100% 100%; }
""".replace("GAUGE", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='29' fill='%2316171b' stroke='%23e10600' stroke-width='3'/%3E%3Cpath d='M14 42a20 20 0 1 1 36 0' fill='none' stroke='%23f3f4f6' stroke-width='5' stroke-dasharray='2 5.3'/%3E%3Cpath d='M32 36L45 21' stroke='%23e10600' stroke-width='4' stroke-linecap='round'/%3E%3Ccircle cx='32' cy='36' r='4.5' fill='%23f3f4f6'/%3E%3C/svg%3E"),
        "tile": {"cls": "cr", "title": "Cars", "art": "",
                 "blurb": "Horsepower, top speeds, prices, badges, car makers and their history, and famous film cars."},
        "intro": ("Car quiz", "From hatchbacks to hypercars: how well do you know cars?",
                  "A free car quiz, 20 questions per game: horsepower, top speeds, prices, car makers and their owners, founding dates, engines, badges, famous film cars and the rules of the road. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
    {
        "id": "bigger", "dir": "this-or-that", "bank_src": "bigger_questions.json", "section": "games",
        "aliases": ["B"], "old_dirs": ["which-is-bigger"],   # it was called Which Is Bigger? at first
        "title": "This or That – Higher or Lower Game – Obscure Trivia",
        "desc": "This or That is a free head-to-head numbers game: two things go up against each other and you pick the right one. 20 questions per game on heights, areas, populations, speeds, weights, dates, space, science, sport and food. Play solo or in party mode with up to 6 players.",
        "fonts": "family=Lilita+One&family=Rubik:wght@400;500;600;700",
        "theme_color": "#fff3dc",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='2' y='2' width='60' height='60' rx='16' fill='%231b1b2f'/%3E%3Crect x='13' y='30' width='15' height='22' rx='3' fill='%23ff6b57'/%3E%3Crect x='36' y='12' width='15' height='40' rx='3' fill='%233d7bff'/%3E%3C/svg%3E",
        "extra": [],
        "config": {
            "id": "bigger", "letter": "T", "short": "This or That", "icon": "",
            "eyebrow": "Head-to-head numbers game", "headline": "Two things go head to head. Which one is bigger?",
            "topics": "heights, areas, populations, lengths, weights, speeds, dates, space, science, sport and food",
            "foot": "Country populations come from the World Bank (2025), country areas from the world-countries dataset and Premier League seasons from openfootball. Everything else uses well-known published figures, and two things are only paired when the gap between them is clearly bigger than any disagreement between sources.",
            "seed": "obscure-trivia-bigger-v1:", "topic": "obscure-trivia/bigger/v1/", "recentKey": "ot-recent-bigger-v1", "sessionKey": "ot-game-bigger",
            "bank": "questions.json", "hub": "../",
            "groups": {"height": "Height", "area": "Area", "population": "Population", "length": "Length", "weight": "Weight", "speed": "Speed", "lifespan": "Lifespan", "dates": "Dates", "numbers": "Numbers", "diameter": "Space", "spin": "Space", "gravity": "Space", "heat": "Heat", "protons": "Science", "density": "Science", "melting": "Science", "stadium": "Sport", "ball": "Sport", "plseasons": "Sport", "calories": "Food", "chilli": "Food", "caffeine": "Food", "distance": "Distance"},
            "caps": {"Height": 2, "Area": 2, "Population": 2, "Length": 2, "Weight": 2, "Speed": 2, "Lifespan": 1, "Dates": 3, "Numbers": 3, "Space": 2, "Heat": 2, "Science": 2, "Sport": 2, "Food": 2, "Distance": 1},
            "verdicts": [[19, "Human measuring tape."], [16, "Brilliant sense of scale."], [12, "Bigger brain than most."], [8, "Size isn't everything."], [0, "Was it the other one?"]],
        },
        "theme": """
:root {
  --bg: #fff3dc;
  --bg-art: radial-gradient(circle, rgba(27, 27, 47, 0.09) 1.2px, transparent 1.7px) 0 0 / 18px 18px;
  --panel: #fffdf7; --panel-fill: #fffdf7; --panel-2: #fff0cc;
  --panel-shadow: 6px 6px 0 #1b1b2f;
  --line: #1b1b2f; --line-hover: #1b1b2f; --ink: #1b1b2f; --muted: #57546b; --faint: #75728a; --placeholder: #9895aa;
  --accent: #ffcd29; --accent-ink: #1b1b2f; --accent-text: #c2410c; --accent-hover: #ffd94f; --accent-edge: #1b1b2f; --accent-shadow: 3px 3px 0 #1b1b2f;
  --chip-bg: #fff0cc; --chip-line: #1b1b2f; --chip-ink: #1b1b2f;
  --pal: #2563eb; --pal-ink: #ffffff; --pal-bg: rgba(37, 99, 235, 0.1); --pal-line: #2563eb;
  --good: #15803d; --good-ink: #ffffff; --good-bg: #d7f5de; --bad: #dc2626; --bad-ink: #ffffff; --bad-bg: #fde3e3;
  --inset: #ffffff; --opt: #ffffff; --tile: #fff8e8;
  --card-bg: #ffffff; --card-ink: #1b1b2f; --card-line: #1b1b2f; --card-inner: #fff0cc; --card-strong: #000000;
  --f-display: "Lilita One", "Arial Rounded MT Bold", system-ui, sans-serif; --f-body: "Rubik", system-ui, -apple-system, "Segoe UI", sans-serif;
  --r: 14px; --r-panel: 18px; --r-pill: 999px; --r-key: 8px;
  --side-a: #ff6b57; --side-a-bg: #ffe2dc; --side-b: #3d7bff; --side-b-bg: #dfe9ff;
  color-scheme: light;
}
/* a warm side and a cool side, like a versus screen */
body::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background: radial-gradient(circle, rgba(27, 27, 47, 0.1) 1.2px, transparent 1.7px) 0 0 / 18px 18px,
    linear-gradient(115deg, #ffdcd2 0 50%, #d9e6ff 50% 100%); }
.c2 { --pc: #7c3aed; --pc-ink: #ffffff; } .c3 { --pc: #db2777; --pc-ink: #ffffff; }
.c4 { --pc: #c2410c; --pc-ink: #ffffff; } .c5 { --pc: #047857; --pc-ink: #ffffff; }
.board { border-width: 2.5px; }
.btn { border-width: 2.5px; border-color: var(--line); background: #ffffff; box-shadow: 3px 3px 0 var(--line); }
.btn:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--line); }
.btn.skip { box-shadow: none; }
.input { border-width: 2.5px; }
.chip { border-width: 1.5px; font-weight: 600; }
.pip { background: #eadcb8; }
.timer { background: #eadcb8; }
.divider::before, .divider::after { background: #d9c79c; }
.opt { border-width: 2.5px; box-shadow: 4px 4px 0 var(--line); transition: transform .1s ease, box-shadow .1s ease, background .12s ease; }
.opt:hover:not([disabled]) { background: var(--opt); transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--line); }
.opt .key { border: 2px solid var(--line); background: #ffffff; color: var(--ink); }
.opt.card.side-a { background: var(--side-a-bg); }
.opt.card.side-b { background: var(--side-b-bg); }
.opt.card.side-a:hover:not([disabled]) { background: var(--side-a-bg); }
.opt.card.side-b:hover:not([disabled]) { background: var(--side-b-bg); }
.opt.card.side-a .key { background: var(--side-a); color: #ffffff; }
.opt.card.side-b .key { background: var(--side-b); color: #ffffff; }
.opt.card.right { background: var(--good-bg); border-color: var(--good); box-shadow: 4px 4px 0 var(--good); }
.opt.card.wrong { background: var(--bad-bg); border-color: var(--bad); box-shadow: 4px 4px 0 var(--bad); }
.opt.card.faded { opacity: 0.6; }
.opt.card .val { color: var(--ink); }
.opt.card.right .val { color: var(--good); }
.opts.duel .vs { background: var(--ink); color: var(--accent); width: 54px; height: 54px; font-size: 1.2rem; transform: rotate(-8deg);
  box-shadow: 3px 3px 0 var(--accent-text); }
.why { background: #ffffff; border: 2px dashed var(--line); }
.feed-btn, .feed-panel { border-width: 2px; border-color: var(--line); }
.feed-btn { background: #ffffff; color: var(--ink); }
.coin { width: 32px; height: 32px; flex: none; display: block; background: url("BARS") center / 100% 100%; }
""".replace("BARS", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='2' y='2' width='60' height='60' rx='16' fill='%231b1b2f'/%3E%3Crect x='13' y='30' width='15' height='22' rx='3' fill='%23ff6b57'/%3E%3Crect x='36' y='12' width='15' height='40' rx='3' fill='%233d7bff'/%3E%3C/svg%3E"),
        "tile": {"cls": "wb", "title": "This or That", "art": '<span class="vs-badge" aria-hidden="true">VS</span>',
                 "blurb": "Two things go head to head. Taller, heavier, faster, older: can you pick the right one?"},
        "intro": ("Head-to-head numbers game", "Two things go head to head. Which one is bigger?",
                  "A free head-to-head numbers game, 20 questions per game: heights, areas, populations, lengths, weights, speeds, dates, space, science, sport and food. Play on your own, or start a party of up to 6 players with a 5-letter code."),
    },
]

BASE_CSS = """:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
.top-links { gap: 8px; }
.top-links a { text-decoration: none; color: inherit; }
"""


def head(title, desc, url, fonts, theme_color, favicon, extra_head="", image="social.png", ld=None):
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld)}</script>' if ld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta name="google-site-verification" content="{VERIFY}">
<meta property="og:site_name" content="Obscure Trivia">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{url}{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="{theme_color}">
<link rel="icon" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
{ld_tag}
{extra_head}
</head>
<body>
"""


os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
shutil.copy(os.path.join(SRC, "quiz.css"), os.path.join(OUT, "assets", "quiz.css"))
with open(os.path.join(OUT, "assets", "quiz.css"), "a", encoding="utf-8") as f:
    f.write("\n" + BASE_CSS)
shutil.copy(os.path.join(SRC, "engine.js"), os.path.join(OUT, "assets", "quiz.js"))

def stamp(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:10]
V_CSS, V_JS = stamp(os.path.join(OUT, "assets", "quiz.css")), stamp(os.path.join(OUT, "assets", "quiz.js"))
for qz in QUIZZES:
    qz["config"]["others"] = {l: "../" + o["dir"] + "/" for o in QUIZZES if o is not qz for l in [o["config"]["letter"]] + o.get("aliases", [])}
    # every quiz a host can move their party to (this one included)
    qz["config"]["catalog"] = [{"letter": o["config"]["letter"], "name": o["tile"]["title"], "url": "./" if o is qz else "../" + o["dir"] + "/"} for o in QUIZZES]
for qz in QUIZZES:
    d = os.path.join(OUT, qz["dir"])
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(SRC, qz["bank_src"]), os.path.join(d, "questions.json"))
    for src, dst in qz.get("extra", []):
        sp, dp = os.path.join(SRC, src), os.path.join(d, dst)
        if os.path.isdir(sp):
            shutil.rmtree(dp, ignore_errors=True); shutil.copytree(sp, dp)
        else:
            shutil.copy(sp, dp)
    url = SITE + qz["dir"] + "/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": qz["title"].split(" – ")[0], "url": url, "applicationCategory": "GameApplication",
         "operatingSystem": "Any", "description": qz["desc"], "isPartOf": {"@type": "WebSite", "name": "Obscure Trivia", "url": SITE},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Obscure Trivia", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": qz["title"].split(" – ")[0], "item": url}]}]}
    page = head(qz["title"], qz["desc"], url, qz["fonts"], qz["theme_color"], qz["favicon"],
                extra_head=f'<link rel="stylesheet" href="../assets/quiz.css?v={V_CSS}">\n<style>{qz["theme"]}</style>', ld=ld)
    eb, h2, p = qz["intro"]
    cfg = qz["config"]
    page += f"""<div class="wrap" id="app">
  <header class="top"><div class="brand"><span class="coin" aria-hidden="true">{E(cfg['icon'])}</span><h1>{E(cfg['short'])}</h1></div><a class="btn copy" href="../">All quizzes</a></header>
  <section class="hero">
    <span class="eyebrow">{E(eb)}</span>
    <h2>{E(h2)}</h2>
    <p>{E(p)}</p>
  </section>
  <div class="loading">Loading the questions…</div>
  <noscript><p class="center muted">This quiz needs JavaScript turned on.</p></noscript>
</div>
<script>window.QUIZ = {json.dumps(cfg)};</script>
<script src="../assets/quiz.js?v={V_JS}"></script>
</body>
</html>
"""
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
    for old in qz.get("old_dirs", []):
        od = os.path.join(OUT, old)
        os.makedirs(od, exist_ok=True)
        name = qz["title"].split(" – ")[0]
        open(os.path.join(od, "index.html"), "w", encoding="utf-8").write(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(name)} – Obscure Trivia</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url=../{qz['dir']}/">
<script>location.replace("../{qz['dir']}/" + location.search + location.hash);</script>
<style>body{{margin:0;padding:40px 16px;font:16px/1.5 system-ui,sans-serif;background:{qz['theme_color']};color:#1b1b2f;text-align:center}}</style>
</head>
<body><p>This game is now called <a href="../{qz['dir']}/">{E(name)}</a>.</p></body>
</html>
""")

# ------------------------------------------------------------------ hub
def mc_sheep():
    """A big, simple pixel sheep (side view, facing right) for the Minecraft tile."""
    W, H = 22, 18
    px = {}
    def put(x, y, c): px[(x, y)] = c
    def box(x0, x1, y0, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(x, y, c)
    WOOL, SHADE, DEEP, SKIN, SKIN2 = "#f5f5f5", "#e0e0e0", "#c9c9c9", "#e8c7b2", "#c9a38c"
    box(1, 15, 2, 11, WOOL)                                   # body
    box(1, 15, 10, 11, SHADE); box(1, 1, 3, 11, SHADE)
    for x, y in [(4, 4), (8, 3), (11, 5), (6, 7), (13, 8), (3, 9), (9, 9), (12, 3), (5, 5), (10, 7)]:
        put(x, y, SHADE)
    for x, y in [(2, 10), (7, 11), (12, 10), (14, 11)]:
        put(x, y, DEEP)
    for lx in (2, 5, 10, 13):                                 # legs: wool at the top, skin below
        box(lx, lx + 1, 12, 12, SHADE)
        box(lx, lx + 1, 13, 16, SKIN)
        box(lx, lx, 13, 16, SKIN2)
    box(14, 20, 0, 1, WOOL); box(14, 16, 2, 7, WOOL); box(14, 14, 1, 7, SHADE)   # head wool
    box(17, 20, 2, 7, SKIN); box(17, 17, 2, 7, SKIN2); box(17, 20, 7, 7, SKIN2)  # face
    put(18, 3, "#ffffff"); put(19, 3, "#1b1b1b")             # eye
    put(20, 5, "#d98b8b")                                    # nose
    groups = {}
    for (x, y), c in px.items():
        groups.setdefault(c, []).append((x, y))
    paths = "".join(f'<path fill="{c}" d="{"".join(f"M{x} {y}h1v1h-1z" for x, y in sorted(v))}"/>' for c, v in groups.items())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">'
            f'<rect x="0" y="17" width="17" height="1" fill="#000" fill-opacity=".22"/>{paths}</svg>\n')


open(os.path.join(OUT, "minecraft", "sheep.svg"), "w").write(mc_sheep())
SECTIONS = [("quizzes", "Quizzes", "Pick a topic and answer 20 questions."),
            ("games", "Other games", "Something a bit different, with the same party codes, timer and top scores.")]
hub_desc = "Obscure Trivia: free quizzes for the details only real players know. 20 random questions per game on Hearthstone Battlegrounds, Minecraft: Bedrock Edition, general knowledge, football and cars, plus the This or That head-to-head game. Play solo or in party mode with up to 6 players."
hub_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Obscure Trivia", "alternateName": ["Tavern Trivia", "Obscure Trivia quizzes"], "url": SITE}
hub_fav = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect x='4' y='4' width='56' height='56' rx='14' fill='%23f2efe6'/%3E%3Ctext x='32' y='46' font-size='40' font-weight='800' text-anchor='middle' font-family='Arial,sans-serif' fill='%2315141a'%3E%3F%3C/text%3E%3C/svg%3E"
hub_css = """
/* Layout: a single column; brand bar, a short headline, the quiz shelf (one textured tile per quiz), and a join-by-code box. */
:root {
  --bg: #121117; --panel: #1c1b23; --line: #2e2c39; --ink: #f2efe6; --muted: #a7a3b5; --faint: #7a7689;
  --hs-ink: #f6e7cf; --hs-gold: #e8b450; --mc-ink: #ffffff; --mc-green: #7ad155; --focus: #f2efe6;
  --f-display: "Bricolage Grotesque", "Arial Black", system-ui, sans-serif; --f-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  color-scheme: dark;
  padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px);
}
* { box-sizing: border-box; }
body { margin: 0; background: radial-gradient(ellipse at 20% -10%, #2a2636 0%, transparent 55%), var(--bg); color: var(--ink); font-family: var(--f-body); font-size: 16px; line-height: 1.5;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 22px 48px; }
.wrap { max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
.top { display: flex; align-items: center; gap: 12px; }
.mark { width: 34px; height: 34px; border-radius: 9px; background: var(--ink); color: var(--bg); display: grid; place-items: center; font-family: var(--f-display); font-weight: 800; font-size: 1.3rem; transform: rotate(-6deg); }
.brand { font-family: var(--f-display); font-weight: 800; font-size: 1.35rem; letter-spacing: -0.01em; margin: 0; }
.hero { display: flex; flex-direction: column; gap: 12px; }
.hero h2 { font-family: var(--f-display); font-weight: 800; font-size: clamp(2.1rem, 7vw, 3.4rem); line-height: 1.02; letter-spacing: -0.025em; margin: 0; text-wrap: balance; max-width: 16ch; }
.hero p { margin: 0; color: var(--muted); max-width: 56ch; font-size: 1.05rem; }
.eyebrow { font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.shelf { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
@media (max-width: 900px) { .shelf { grid-template-columns: 1fr 1fr; } .shelf .quiz:last-child:nth-child(odd) { grid-column: 1 / -1; } }
@media (max-width: 620px) { .shelf { grid-template-columns: 1fr; } }
/* globe tile: a lit Earth in space, clean sans titles */
.gk { border-radius: 22px; color: #f2f7ff;
  background: linear-gradient(180deg, rgba(5,10,24,0) 25%, rgba(5,10,24,0.82) 80%), url(general-knowledge/earth-tile.jpg) 62% 40% / cover;
  box-shadow: 0 12px 30px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(150,190,255,0.3); }
.gk:hover { box-shadow: 0 16px 36px rgba(0,0,0,0.55), 0 0 0 2px #7dd3fc, inset 0 0 0 1px rgba(150,190,255,0.3); }
.gk h3 { font-family: "Outfit", system-ui, sans-serif; font-weight: 800; font-size: clamp(1.7rem, 4.4vw, 2.2rem); letter-spacing: -0.015em; }
.gk p { color: #cfe0f5; font-family: "Atkinson Hyperlegible", system-ui, sans-serif; }
.gk .pill { border-radius: 999px; background: rgba(125,211,252,0.16); border: 1px solid rgba(125,211,252,0.45); color: #c4ecff; }
.gk .play { color: #8edbff; }
/* pitch tile: mowing stripes, a chalk centre circle and condensed sports type */
.fb { border-radius: 14px; color: #fff;
  background: linear-gradient(180deg, rgba(0,0,0,0) 25%, rgba(4,18,9,0.85) 82%),
    radial-gradient(circle at 70% 38%, transparent 0 46px, rgba(255,255,255,0.55) 47px 49px, transparent 50px),
    linear-gradient(90deg, transparent calc(70% - 1px), rgba(255,255,255,0.55) calc(70% - 1px) calc(70% + 1px), transparent calc(70% + 1px)),
    repeating-linear-gradient(90deg, #1d6a35 0 34px, #22783c 34px 68px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.45), inset 0 0 0 3px rgba(255,255,255,0.55); }
.fb:hover { box-shadow: 0 16px 36px rgba(0,0,0,0.55), inset 0 0 0 3px #ffd84a; }
.fb h3 { font-family: "Oswald", "Arial Narrow", sans-serif; font-weight: 700; font-size: clamp(1.9rem, 5vw, 2.5rem); text-transform: uppercase; letter-spacing: 0.02em; }
.fb p { color: #dcebdf; font-family: "Barlow", system-ui, sans-serif; }
.fb .pill { border-radius: 999px; background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.45); color: #fff; }
.fb .play { color: #ffd84a; }
.quiz { position: relative; display: flex; flex-direction: column; justify-content: flex-end; gap: 10px; min-height: 260px; padding: 22px; text-decoration: none; overflow: hidden; min-width: 0;
  transition: transform .15s ease, box-shadow .15s ease; }
.quiz:hover { transform: translateY(-3px); }
.quiz h3 { margin: 0; line-height: 1.05; text-wrap: balance; }
.quiz p { margin: 0; font-size: 0.95rem; max-width: 36ch; }
.quiz .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.quiz .pill { font-size: 0.78rem; font-weight: 700; padding: 4px 10px; }
.quiz .play { margin-left: auto; font-weight: 800; }
@font-face { font-family: "Monocraft"; src: url("minecraft/Monocraft.woff2") format("woff2"); font-display: swap; }
/* tavern tile: oak planks, a gold coin and a serif title */
.hs { border-radius: 16px; color: var(--hs-ink);
  background: radial-gradient(circle at 86% 22%, rgba(255, 196, 96, 0.5) 0, rgba(255, 150, 50, 0.18) 20%, transparent 46%),
    radial-gradient(ellipse at 10% 110%, rgba(255, 120, 40, 0.22), transparent 55%),
    repeating-linear-gradient(180deg, transparent 0 51px, rgba(0, 0, 0, 0.22) 51px 53px, rgba(255, 210, 150, 0.04) 53px 54px),
    linear-gradient(180deg, #4b2e19 0%, #301d10 55%, #1b100a 100%);
  box-shadow: 0 12px 30px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(232,180,80,0.5), inset 0 0 0 5px rgba(20, 12, 7, 0.35); }
.hs:hover { box-shadow: 0 16px 36px rgba(0,0,0,0.55), inset 0 0 0 2px var(--hs-gold); }
.hs h3 { font-family: "Bree Serif", Georgia, serif; font-weight: 400; font-size: clamp(1.7rem, 4.6vw, 2.2rem); }
.hs p { color: #e3cfb2; }
.hs .pill { border-radius: 999px; background: rgba(232,180,80,0.16); border: 1px solid rgba(232,180,80,0.45); color: #f6d58f; }
.hs .play { color: var(--hs-gold); }
.hs .coin { position: absolute; top: 22px; right: 26px; width: 64px; height: 64px; border-radius: 50%; display: grid; place-items: center;
  background: radial-gradient(circle at 35% 30%, #fff6d2 0 12%, #f0be5c 40%, #a8721f 100%); color: #2a1b08; font-family: "Bree Serif", Georgia, serif; font-size: 1.9rem;
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.25), inset 0 0 0 3px rgba(255, 240, 200, 0.35), 0 0 0 5px rgba(232, 180, 80, 0.16), 0 0 34px rgba(255, 180, 80, 0.55); }
/* block tile: pixel grass-and-dirt, square corners, a pixel title */
.mc { border-radius: 0; color: var(--mc-ink); image-rendering: pixelated;
  background: linear-gradient(180deg, rgba(0,0,0,0) 52%, rgba(14,34,8,0.6) 100%),
    url(minecraft/sheep.svg) right 30px top 18px / auto 50% no-repeat,
    repeating-conic-gradient(rgba(255,255,255,0.05) 0 25%, rgba(0,0,0,0) 0 50%) 0 0 / 26px 26px,
    linear-gradient(180deg, #70b540 0%, #5b9d32 60%, #4a8627 100%);
  box-shadow: inset 0 0 0 3px #0f0f10, inset 0 0 0 5px rgba(255,255,255,0.18), 0 10px 0 rgba(0,0,0,0.35); }
@media (max-width: 620px) { .mc { min-height: 340px; background-size: auto, auto 40%, 26px 26px, auto; } }
.mc:hover { box-shadow: inset 0 0 0 3px #0f0f10, inset 0 0 0 5px var(--mc-green), 0 12px 0 rgba(0,0,0,0.35); }
.mc h3 { font-family: "Monocraft", ui-monospace, monospace; font-weight: 400; font-size: clamp(1.8rem, 5vw, 2.4rem); text-shadow: 3px 3px 0 #1f1f1f; }
.mc p { color: #e6e6e6; text-shadow: 1px 1px 0 #000; }
.mc .pill { background: #313233; border: 2px solid #0f0f10; color: #fff; box-shadow: inset 0 -3px 0 rgba(0,0,0,0.3); }
.mc .play { color: var(--mc-green); text-shadow: 2px 2px 0 #000; font-family: "Monocraft", ui-monospace, monospace; font-size: 1.1rem; }
/* car tile: carbon fibre, a red and white racing stripe and slanted motorsport type */
.cr { border-radius: 12px; color: #fff;
  background: linear-gradient(180deg, rgba(10, 10, 12, 0) 22%, rgba(10, 10, 12, 0.92) 80%),
    radial-gradient(ellipse at 25% 0%, rgba(225, 6, 0, 0.35), transparent 60%),
    linear-gradient(100deg, transparent 0 64%, #e10600 64% 71%, transparent 71% 73.5%, #f3f4f6 73.5% 76%, transparent 76%),
    linear-gradient(45deg, #111215 25%, transparent 25%, transparent 75%, #111215 75%) 0 0 / 12px 12px,
    linear-gradient(45deg, #111215 25%, transparent 25%, transparent 75%, #111215 75%) 6px 6px / 12px 12px,
    linear-gradient(#202227, #18191d);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45), inset 0 0 0 1px rgba(255, 255, 255, 0.14); }
.cr:hover { box-shadow: 0 16px 36px rgba(0, 0, 0, 0.55), inset 0 0 0 2px #e10600; }
.cr h3 { font-family: "Chakra Petch", "Arial Narrow", sans-serif; font-weight: 700; font-style: italic; font-size: clamp(2rem, 5.4vw, 2.6rem); text-transform: uppercase; letter-spacing: 0.02em; }
.cr p { color: #d4d7dd; font-family: "Titillium Web", system-ui, sans-serif; }
.cr .pill { border-radius: 999px; background: rgba(0, 0, 0, 0.45); border: 1px solid rgba(255, 90, 77, 0.6); color: #fff; }
.cr .play { color: #ff5a4d; }
/* two sections: the quizzes, then other games */
.sect { display: flex; flex-direction: column; gap: 14px; }
.sect-head { display: flex; align-items: baseline; justify-content: space-between; gap: 4px 16px; flex-wrap: wrap; padding-bottom: 10px; border-bottom: 1px solid var(--line); }
.sect-head h2 { margin: 0; font-family: var(--f-display); font-weight: 800; font-size: 1.55rem; letter-spacing: -0.015em; }
.sect-head p { margin: 0; color: var(--muted); font-size: 0.95rem; }
.shelf.games .quiz:last-child:nth-child(odd) { grid-column: auto; }
@media (max-width: 620px) { .shelf.games .quiz:last-child:nth-child(odd) { grid-column: 1 / -1; } }
/* versus tile: a warm side, a cool side, a VS badge and chunky rounded type */
.wb { border-radius: 18px; color: #1b1b2f; border: 3px solid #1b1b2f;
  background: linear-gradient(180deg, rgba(255,246,226,0) 28%, rgba(255,246,226,0.97) 64%),
    radial-gradient(circle, rgba(27,27,47,0.14) 1.2px, transparent 1.7px) 0 0 / 16px 16px,
    linear-gradient(115deg, #ff8a78 0 50%, #6d9bff 50% 100%);
  box-shadow: 6px 6px 0 #000; }
.wb:hover { box-shadow: 9px 9px 0 #000; }
.wb h3 { font-family: "Lilita One", "Arial Rounded MT Bold", sans-serif; font-weight: 400; font-size: clamp(1.9rem, 5vw, 2.4rem); }
.wb p { color: #44415a; font-family: "Rubik", system-ui, sans-serif; }
.wb .pill { border-radius: 999px; background: #fff; border: 2px solid #1b1b2f; color: #1b1b2f; }
.wb .play { color: #c2410c; }
.wb .vs-badge { position: absolute; top: 26px; left: 50%; width: 64px; height: 64px; margin-left: -32px; border-radius: 50%; display: grid; place-items: center;
  background: #1b1b2f; color: #ffcd29; font-family: "Lilita One", sans-serif; font-size: 1.45rem; transform: rotate(-8deg); box-shadow: 4px 4px 0 #c2410c; }
:focus-visible.wb { outline-offset: 5px; }
.joinbox { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.joinbox h3 { margin: 0; font-family: var(--f-display); font-weight: 800; font-size: 1.25rem; }
.joinbox p { margin: 0; color: var(--muted); font-size: 0.95rem; }
.row { display: flex; gap: 10px; flex-wrap: wrap; }
.input { flex: 1 1 160px; min-width: 0; background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 11px 12px; color: var(--ink); font: inherit;
  text-transform: uppercase; letter-spacing: 0.3em; text-align: center; font-weight: 700; }
.input::placeholder { color: var(--faint); }
.btn { border-radius: 10px; border: 0; padding: 12px 20px; font: inherit; font-weight: 800; background: var(--ink); color: var(--bg); cursor: pointer; }
.err { color: #f08a7c; font-size: 0.9rem; min-height: 1.3em; margin: 0; }
.foot { color: var(--faint); font-size: 0.82rem; text-align: center; margin: 0; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
""".replace("__WOOD__", TEX["wood"]).replace("__GRASS__", TEX["grass_side"])
hub = head("Obscure Trivia – Hearthstone, Minecraft, General Knowledge, Football & Car Quizzes", hub_desc, SITE,
           "family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Inter:wght@400;500;700&family=Bree+Serif&family=Outfit:wght@800&family=Atkinson+Hyperlegible&family=Oswald:wght@700&family=Barlow&family=Lilita+One&family=Rubik:wght@400;500&family=Chakra+Petch:ital,wght@1,700&family=Titillium+Web:wght@400;600",
           "#121117", hub_fav, extra_head=f"<style>{hub_css}</style>", ld=hub_ld)
hub += """<div class="wrap">
  <header class="top"><span class="mark" aria-hidden="true">?</span><h1 class="brand">Obscure Trivia</h1></header>
  <section class="hero">
    <span class="eyebrow">Free game quizzes</span>
    <h2>Trivia for the details only real players know.</h2>
    <p>Each quiz pulls 20 random questions from a bank of 1,000. Play on your own, or start a party of up to 6 players with a 5-letter code and see who wins.</p>
  </section>
""" + "".join(f"""  <section class="sect" aria-labelledby="h-{sid}">
    <div class="sect-head"><h2 id="h-{sid}">{E(stitle)}</h2><p>{E(sblurb)}</p></div>
    <div class="shelf {sid}">
""" + "".join(f"""      <a class="quiz {q['tile']['cls']}" href="{q['dir']}/">
        {q['tile']['art']}
        <h3>{E(q['tile']['title'])}</h3>
        <p>{E(q['tile']['blurb'])}</p>
        <div class="meta"><span class="pill">{QUESTIONS_PER_GAME} questions</span><span class="pill">Solo &amp; party</span><span class="play">Play →</span></div>
      </a>
""" for q in QUIZZES if q.get("section", "quizzes") == sid) + """    </div>
  </section>
""" for sid, stitle, sblurb in SECTIONS) + """
  <section class="joinbox">
    <h3>Got a code from a friend?</h3>
    <p>Type it in and you'll go straight to the right quiz.</p>
    <form class="row" id="join" autocomplete="off">
      <input class="input" id="code" maxlength="5" placeholder="CODE" aria-label="Game code">
      <button class="btn" type="submit">Join game</button>
    </form>
    <p class="err" id="err" role="alert"></p>
  </section>
  <p class="foot">More quizzes on the way. Fan-made, not affiliated with Blizzard, Mojang, Microsoft, the Premier League, FIFA, UEFA or any car maker.</p>
</div>
<script>
(() => {
  const routes = """ + json.dumps({l: q["dir"] + "/" for q in QUIZZES for l in [q["config"]["letter"]] + q.get("aliases", [])}) + """;
  const ALPH = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
  document.getElementById("join").addEventListener("submit", e => {
    e.preventDefault();
    const c = String(document.getElementById("code").value || "").toUpperCase().replace(/[^A-Z0-9]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1");
    const err = document.getElementById("err");
    if (c.length !== 5 || ![...c].every(ch => ALPH.includes(ch))) { err.textContent = "Codes are 5 letters or numbers, like M7QX2."; return; }
    const r = routes[c[0]];
    if (!r) { err.textContent = """ + json.dumps("That code doesn't match a game. Codes start with " + ", ".join(q["config"]["letter"] + " (" + q["tile"]["title"].rstrip("?") + ")" for q in QUIZZES[:-1]) + " or " + QUIZZES[-1]["config"]["letter"] + " (" + QUIZZES[-1]["tile"]["title"].rstrip("?") + ").") + """; return; }
    location.href = r + "?join=" + c;
  });
})();
</script>
</body>
</html>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(hub)

today = datetime.date.today().isoformat()
urls = [SITE] + [SITE + q["dir"] + "/" for q in QUIZZES]
open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(OUT, ".nojekyll"), "w").write("")
print("built", OUT, os.listdir(OUT))
