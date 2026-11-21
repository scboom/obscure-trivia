"""Build the Obscure Trivia site: a hub page plus one themed page per quiz, sharing one engine."""
import sys, os, json, shutil, datetime, html

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
        "desc": "A free Hearthstone Battlegrounds quiz: 20 random questions per game on minion tiers and stats, hero armor in Solo and Duos, Hero Powers, Buddies, quests, trinkets and anomalies. Play solo or co-op with a friend.",
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
                  "A free Hearthstone Battlegrounds quiz, 20 questions per game: minion tiers and stats, hero armor in Solo and Duos, Hero Powers, Buddies, quest rewards, trinkets, Tavern spells and anomalies. Play on your own, or co-op with a friend using a 5-letter code."),
    },
    {
        "id": "minecraft", "dir": "minecraft", "bank_src": "mc_questions.json",
        "title": "Minecraft Bedrock Quiz – Obscure Trivia",
        "desc": "A free Minecraft: Bedrock Edition quiz: 20 random questions per game on crafting recipes, blocks, tools, mobs, enchanting, brewing and biomes. Play solo or co-op with a friend.",
        "fonts": "family=Pixelify+Sans:wght@400;600;700&family=Noto+Sans:wght@400;600;700",
        "theme_color": "#1b1c1e",
        "favicon": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8' shape-rendering='crispEdges'%3E%3Crect width='8' height='8' fill='%23866043'/%3E%3Crect width='8' height='3' fill='%235f9f35'/%3E%3Crect y='3' width='2' height='1' fill='%235f9f35'/%3E%3Crect x='5' y='3' width='1' height='1' fill='%235f9f35'/%3E%3Crect x='3' y='5' width='1' height='1' fill='%23694b33'/%3E%3Crect x='6' y='6' width='1' height='1' fill='%23694b33'/%3E%3C/svg%3E",
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
  --f-display: "Pixelify Sans", ui-monospace, "Courier New", monospace; --f-body: "Noto Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --r: 0px; --r-panel: 0px; --r-pill: 0px; --r-key: 0px;
  color-scheme: dark;
}
body { image-rendering: pixelated; }
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
                  "A free Minecraft: Bedrock Edition quiz, 20 questions per game: crafting recipes, blocks and ores, tools, mobs, enchanting, brewing, biomes and villagers. Play on your own, or co-op with a friend using a 5-letter code."),
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

for qz in QUIZZES:
    d = os.path.join(OUT, qz["dir"])
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(SRC, qz["bank_src"]), os.path.join(d, "questions.json"))
    url = SITE + qz["dir"] + "/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": qz["title"].split(" – ")[0], "url": url, "applicationCategory": "GameApplication",
         "operatingSystem": "Any", "description": qz["desc"], "isPartOf": {"@type": "WebSite", "name": "Obscure Trivia", "url": SITE},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Obscure Trivia", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": qz["title"].split(" – ")[0], "item": url}]}]}
    page = head(qz["title"], qz["desc"], url, qz["fonts"], qz["theme_color"], qz["favicon"],
                extra_head=f'<link rel="stylesheet" href="../assets/quiz.css">\n<style>{qz["theme"]}</style>', ld=ld)
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
<script src="../assets/quiz.js"></script>
</body>
</html>
"""
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

# ------------------------------------------------------------------ hub
hub_desc = "Obscure Trivia: free quizzes for the details only real players know. 20 random questions per game on Hearthstone Battlegrounds and Minecraft: Bedrock Edition, solo or co-op with a friend."
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
.wrap { max-width: 880px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
.top { display: flex; align-items: center; gap: 12px; }
.mark { width: 34px; height: 34px; border-radius: 9px; background: var(--ink); color: var(--bg); display: grid; place-items: center; font-family: var(--f-display); font-weight: 800; font-size: 1.3rem; transform: rotate(-6deg); }
.brand { font-family: var(--f-display); font-weight: 800; font-size: 1.35rem; letter-spacing: -0.01em; margin: 0; }
.hero { display: flex; flex-direction: column; gap: 12px; }
.hero h2 { font-family: var(--f-display); font-weight: 800; font-size: clamp(2.1rem, 7vw, 3.4rem); line-height: 1.02; letter-spacing: -0.025em; margin: 0; text-wrap: balance; max-width: 16ch; }
.hero p { margin: 0; color: var(--muted); max-width: 56ch; font-size: 1.05rem; }
.eyebrow { font-size: 0.74rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); }
.shelf { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
@media (max-width: 640px) { .shelf { grid-template-columns: 1fr; } }
.quiz { position: relative; display: flex; flex-direction: column; justify-content: flex-end; gap: 10px; min-height: 260px; padding: 22px; text-decoration: none; overflow: hidden; min-width: 0;
  transition: transform .15s ease, box-shadow .15s ease; }
.quiz:hover { transform: translateY(-3px); }
.quiz h3 { margin: 0; line-height: 1.05; text-wrap: balance; }
.quiz p { margin: 0; font-size: 0.95rem; max-width: 36ch; }
.quiz .meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.quiz .pill { font-size: 0.78rem; font-weight: 700; padding: 4px 10px; }
.quiz .play { margin-left: auto; font-weight: 800; }
/* tavern tile: oak planks, a gold coin and a serif title */
.hs { border-radius: 16px; color: var(--hs-ink);
  background: linear-gradient(180deg, rgba(20,12,7,0.15) 0%, rgba(20,12,7,0.85) 78%), url(__WOOD__) center / cover;
  box-shadow: 0 12px 30px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(232,180,80,0.35); }
.hs:hover { box-shadow: 0 16px 36px rgba(0,0,0,0.55), inset 0 0 0 2px var(--hs-gold); }
.hs h3 { font-family: "Bree Serif", Georgia, serif; font-weight: 400; font-size: clamp(1.7rem, 4.6vw, 2.2rem); }
.hs p { color: #e3cfb2; }
.hs .pill { border-radius: 999px; background: rgba(232,180,80,0.16); border: 1px solid rgba(232,180,80,0.45); color: #f6d58f; }
.hs .play { color: var(--hs-gold); }
.hs .coin { position: absolute; top: 20px; right: 20px; width: 54px; height: 54px; border-radius: 50%; display: grid; place-items: center;
  background: radial-gradient(circle at 35% 30%, #fff3c4 0 12%, #e8b450 38%, #a8721f 100%); color: #2a1b08; font-family: "Bree Serif", Georgia, serif; font-size: 1.6rem;
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.25), 0 4px 10px rgba(0,0,0,0.5); }
/* block tile: pixel grass-and-dirt, square corners, a pixel title */
.mc { border-radius: 0; color: var(--mc-ink); image-rendering: pixelated;
  background: linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,0.78) 82%), url(__GRASS__) 0 0 / 56px 56px;
  box-shadow: inset 0 0 0 3px #0f0f10, inset 0 0 0 5px rgba(255,255,255,0.18), 0 10px 0 rgba(0,0,0,0.35); }
.mc:hover { box-shadow: inset 0 0 0 3px #0f0f10, inset 0 0 0 5px var(--mc-green), 0 12px 0 rgba(0,0,0,0.35); }
.mc h3 { font-family: "Pixelify Sans", ui-monospace, monospace; font-weight: 700; font-size: clamp(1.8rem, 5vw, 2.4rem); text-shadow: 3px 3px 0 #1f1f1f; }
.mc p { color: #e6e6e6; text-shadow: 1px 1px 0 #000; }
.mc .pill { background: #313233; border: 2px solid #0f0f10; color: #fff; box-shadow: inset 0 -3px 0 rgba(0,0,0,0.3); }
.mc .play { color: var(--mc-green); text-shadow: 2px 2px 0 #000; font-family: "Pixelify Sans", ui-monospace, monospace; font-size: 1.1rem; }
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
hub = head("Obscure Trivia – Hearthstone & Minecraft Quizzes", hub_desc, SITE,
           "family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Inter:wght@400;500;700&family=Bree+Serif&family=Pixelify+Sans:wght@700",
           "#121117", hub_fav, extra_head=f"<style>{hub_css}</style>", ld=hub_ld)
hub += """<div class="wrap">
  <header class="top"><span class="mark" aria-hidden="true">?</span><h1 class="brand">Obscure Trivia</h1></header>
  <section class="hero">
    <span class="eyebrow">Free game quizzes</span>
    <h2>Trivia for the details only real players know.</h2>
    <p>Each quiz pulls 20 random questions from a bank of 1,000. Play on your own, or send a friend a 5-letter code and answer the same questions together.</p>
  </section>
  <section class="shelf" aria-label="Quizzes">
""" + "".join(f"""    <a class="quiz {q['tile']['cls']}" href="{q['dir']}/">
      {q['tile']['art']}
      <h3>{E(q['tile']['title'])}</h3>
      <p>{E(q['tile']['blurb'])}</p>
      <div class="meta"><span class="pill">{QUESTIONS_PER_GAME} questions</span><span class="pill">Solo &amp; co-op</span><span class="play">Play →</span></div>
    </a>
""" for q in QUIZZES) + """  </section>
  <section class="joinbox">
    <h3>Got a code from a friend?</h3>
    <p>Type it in and you'll go straight to the right quiz.</p>
    <form class="row" id="join" autocomplete="off">
      <input class="input" id="code" maxlength="5" placeholder="CODE" aria-label="Game code">
      <button class="btn" type="submit">Join game</button>
    </form>
    <p class="err" id="err" role="alert"></p>
  </section>
  <p class="foot">More quizzes on the way. Fan-made, not affiliated with Blizzard, Mojang or Microsoft.</p>
</div>
<script>
(() => {
  const routes = """ + json.dumps({q["config"]["letter"]: q["dir"] + "/" for q in QUIZZES}) + """;
  const ALPH = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
  document.getElementById("join").addEventListener("submit", e => {
    e.preventDefault();
    const c = String(document.getElementById("code").value || "").toUpperCase().replace(/[^A-Z0-9]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1");
    const err = document.getElementById("err");
    if (c.length !== 5 || ![...c].every(ch => ALPH.includes(ch))) { err.textContent = "Codes are 5 letters or numbers, like M7QX2."; return; }
    const r = routes[c[0]];
    if (!r) { err.textContent = """ + json.dumps("That code doesn't match a quiz. " + " and ".join(q["tile"]["title"] + " codes start with " + q["config"]["letter"] for q in QUIZZES) + ".") + """; return; }
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
