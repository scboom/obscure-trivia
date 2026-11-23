# Obscure Trivia

Free game quizzes for the details only real players know: https://scboom.github.io/obscure-trivia/

Each quiz and game has its own themed page, a bank of 1,000 questions, 20 random questions per game, solo play, a 10-minute time limit, party mode for 2 to 6 players with a 5-letter code (host starts the quiz; answers revealed together at the end, skipped only if every player votes, then a ranking; afterwards the host can "Play again" or "Change quiz" and the whole party moves with them), a small "Top scores" tab with the 3 best scores of the last 7 days (every player in a party counts, and one person can hold all three; ties go to the faster time), and a "Recent quizzes" list of your last 5 games.

| Quiz | Page | Codes start with |
| --- | --- | --- |
| Hearthstone Battlegrounds | `hearthstone/` | `H` |
| Minecraft: Bedrock Edition | `minecraft/` | `M` |
| OG Fortnite (Battle Royale, Chapter 1 only: Pre-Season to Season X) | `fortnite/` | `N` |
| Clash Royale (every card's Elixir cost, rarity and arena, card descriptions, stats, Evolutions, Heroes, Champions, arenas and mechanics) | `clash-royale/` | `R` |
| General Knowledge | `general-knowledge/` | `W` |
| Football | `football/` | `F` |
| Cars | `cars/` | `C` |
| Music | `music/` | `S` |

Other games (same features, in their own section on the hub):

| Game | Page | Codes start with |
| --- | --- | --- |
| This or That (two things head to head: pick the right one) | `this-or-that/` | `T` (old `B` codes still work) |

## How it's built

- `index.html` is the hub. Each quiz folder has its page and `questions.json`.
- `assets/quiz.js` and `assets/quiz.css` are the shared quiz engine and layout; each quiz page sets its own theme and settings.
- `tools/` holds the generators: `gen.py` (Hearthstone, from the game's card data), `gen_mc.py` (Minecraft, from Bedrock game data plus hand-checked facts), `gen_world.py` (General Knowledge: country data from mledoze/countries, ODbL, flags from flag-icons, MIT, plus hand-written fun facts), `earth.js` (draws the Earth pictures from Natural Earth map data), `pl_parse.py` + `gen_football.py` (Football: Premier League and World Cup results from openfootball, public domain, plus hand-written questions), `gen_cars.py` (Cars: makers' horsepower, top speed and rough UK price figures, each with a margin so only clear-cut comparisons are asked, plus hand-written questions), `gen_music.py` (Music: US chart questions worked out from every Billboard Hot 100 since 1958, from utdata/rwd-billboard-data, plus hand-written songs, albums, artists, records, Eurovision winners and film songs; no lyrics), `fn_extract.py` + `gen_fortnite.py` (OG Fortnite, Chapter 1 only, from the Pre-Season to Season X, with nothing later in the questions, wrong answers or explanations: outfits and the season they arrived in, from Fortnite-API's cosmetics list; seasons, named locations and live events, from the Fortnite Wiki (CC BY-SA); plus hand-written questions on the big moments of each season, items, Battle Passes, the map and history, checked against the wiki; map questions count the main Battle Royale island only), `cr_extract.py` + `gen_royale.py` (Clash Royale: card costs, rarities, types, unlock arenas, release dates, in-game descriptions, stat tables, Evolutions, Heroes and Champion abilities from the Clash Royale Wiki (CC BY-SA), as of November 2026; a stat is only asked about when it matches the latest change in that card's History, and hitpoint and damage comparisons need a clear 25% gap; plus hand-written mechanics and game facts checked against the same wiki), `gen_bigger.py` (This or That, first called Which Is Bigger?: country populations from the World Bank via datasets/population, CC BY 4.0, country areas from world-countries, Premier League seasons from openfootball, plus hand-entered published figures, each with an uncertainty margin so only clear-cut pairs are used) and `build_site.py`, which builds the pages.

The Battlegrounds emblem's crown shape comes from HearthSim's hs-icons (CC0).
The Clash Royale tile's crown and Elixir drop are original artwork (`tools/src/cr-crown.svg`).
The Fortnite tile's Peely picture comes from Fortnite-API's cosmetics images (© Epic Games).
The Minecraft tile's sheep is rendered from Mojang's own sheep model and texture (Mojang/bedrock-samples, © Mojang AB) by `tools/render-sheep/`.

Fan-made. Not affiliated with Blizzard Entertainment, Mojang, Microsoft, Epic Games or Supercell, or with any football club, car maker or record label.
