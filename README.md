# Obscure Trivia

Free game quizzes for the details only real players know: https://scboom.github.io/obscure-trivia/

Each quiz has its own themed page, a bank of 1,000 questions, 20 random questions per game, solo play, party mode for 2 to 6 players with a 5-letter code (host starts the quiz; answers revealed together at the end, then a ranking), and a "Recent quizzes" list of your last 5 games.

| Quiz | Page | Codes start with |
| --- | --- | --- |
| Hearthstone Battlegrounds | `hearthstone/` | `H` |
| Minecraft: Bedrock Edition | `minecraft/` | `M` |
| General Knowledge | `general-knowledge/` | `W` |

## How it's built

- `index.html` is the hub. Each quiz folder has its page and `questions.json`.
- `assets/quiz.js` and `assets/quiz.css` are the shared quiz engine and layout; each quiz page sets its own theme and settings.
- `tools/` holds the generators: `gen.py` (Hearthstone, from the game's card data), `gen_mc.py` (Minecraft, from Bedrock game data plus hand-checked facts), `gen_world.py` (General Knowledge: country data from mledoze/countries, ODbL, flags from flag-icons, MIT, plus hand-written fun facts), `earth.js` (draws the Earth pictures from Natural Earth map data) and `build_site.py`, which builds the pages.

Fan-made. Not affiliated with Blizzard Entertainment, Mojang or Microsoft.
