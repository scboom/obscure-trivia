# Obscure Trivia

Free game quizzes for the details only real players know: https://scboom.github.io/obscure-trivia/

Each quiz and game has its own themed page, a bank of 1,000 questions, 20 random questions per game, solo play, a 10-minute time limit, party mode for 2 to 6 players with a 5-letter code (host starts the quiz; answers revealed together at the end, skipped only if every player votes, then a ranking), a small "Top scores" tab with the 3 most recent top scores, and a "Recent quizzes" list of your last 5 games.

| Quiz | Page | Codes start with |
| --- | --- | --- |
| Hearthstone Battlegrounds | `hearthstone/` | `H` |
| Minecraft: Bedrock Edition | `minecraft/` | `M` |
| General Knowledge | `general-knowledge/` | `W` |
| Football | `football/` | `F` |

Other games (same features, in their own section on the hub):

| Game | Page | Codes start with |
| --- | --- | --- |
| Which Is Bigger? (two things head to head: pick the bigger one) | `which-is-bigger/` | `B` |

## How it's built

- `index.html` is the hub. Each quiz folder has its page and `questions.json`.
- `assets/quiz.js` and `assets/quiz.css` are the shared quiz engine and layout; each quiz page sets its own theme and settings.
- `tools/` holds the generators: `gen.py` (Hearthstone, from the game's card data), `gen_mc.py` (Minecraft, from Bedrock game data plus hand-checked facts), `gen_world.py` (General Knowledge: country data from mledoze/countries, ODbL, flags from flag-icons, MIT, plus hand-written fun facts), `earth.js` (draws the Earth pictures from Natural Earth map data), `pl_parse.py` + `gen_football.py` (Football: Premier League and World Cup results from openfootball, public domain, plus hand-written questions), `gen_bigger.py` (Which Is Bigger?: country populations from the World Bank via datasets/population, CC BY 4.0, country areas from world-countries, Premier League seasons from openfootball, plus hand-entered published figures, each with an uncertainty margin so only clear-cut pairs are used) and `build_site.py`, which builds the pages.

Fan-made. Not affiliated with Blizzard Entertainment, Mojang or Microsoft.
