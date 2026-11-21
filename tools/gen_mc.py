"""Build the Minecraft: Bedrock Edition question bank (1,000 questions).

Data-driven parts come from PrismarineJS minecraft-data (Bedrock 1.26.60 blocks/items,
1.19.10 recipes, 1.19.1 enchantments, 1.21.60 biomes, 1.21.80 entities). Facts the data
does not cover (mob health, drops, breeding, villager jobs, food, a few world facts) are
hand-written below and limited to values that are the same in current Bedrock.
"""
import sys, json, re, random, collections

data = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
rng = random.Random(20261121)

BLK = {b["n"]: b for b in data["blocks"]}
ITM = {i["n"]: i for i in data["items"]}
OLD = data["oldItems"]
Q = collections.defaultdict(list)


RENAME = {"Stonebrick": "Stone Bricks", "Red Flower": "Poppy"}
DROP_IF = re.compile(r"Stone Block Slab|(^|· |\d× )Fence($| ·)")


def fixname(t):
    for k, v in RENAME.items():
        t = re.sub(r"\b" + k + r"\b", v, t)
    return re.sub(r"\ba ([AEIOU])", r"an \1", t)


def halves(points, unit):
    n = points / 2
    num = f"{n:g}"
    return f"{num} {unit}" if n == 1 else f"{num} {unit}s"


def add(cat, key, q, a, opts, tag=None, rich=False):
    if not opts:
        return False
    if cat == "health":
        a, opts = halves(int(a), "heart"), [halves(int(o), "heart") for o in opts]
    elif cat == "food":
        a, opts = halves(int(a), "drumstick"), [halves(int(o), "drumstick") for o in opts]
    q, a, opts = fixname(q), fixname(a), [fixname(o) for o in opts]
    if any(DROP_IF.search(x) for x in [q, a] + opts):
        return False
    opts = [o for o in dict.fromkeys(opts) if o != a]
    if len(opts) not in (1, 3):
        return False
    rec = {"c": cat, "k": key, "q": q, "a": a, "o": opts}
    if tag:
        rec["t"] = tag
    if rich:
        rec["r"] = 1
    Q[cat].append(rec)
    return True


def pick(pool, n, exclude=()):
    cand = [x for x in dict.fromkeys(pool) if x not in exclude]
    rng.shuffle(cand)
    return cand[:n] if len(cand) >= n else None


def near(v, lo, hi, n=3, spread=3):
    while True:
        cand = [x for x in range(max(lo, v - spread), min(hi, v + spread) + 1) if x != v]
        if len(cand) >= n or spread > 50:
            break
        spread += 1
    rng.shuffle(cand)
    return cand[:n]


def bdn(name):
    b = BLK.get(name)
    return b["d"] if b else None


def idn(name):
    i = ITM.get(name)
    return i["d"] if i else None


# ------------------------------------------------------------------ blocks: not a block
NON_BLOCK = """stick diamond emerald iron_ingot gold_ingot copper_ingot netherite_ingot netherite_scrap coal charcoal
raw_iron raw_gold raw_copper iron_nugget gold_nugget lapis_lazuli amethyst_shard echo_shard prismarine_shard
prismarine_crystals leather feather gunpowder bone blaze_rod blaze_powder ender_pearl slime_ball magma_cream ghast_tear
spider_eye rotten_flesh glowstone_dust flint clay_ball paper book compass clock apple bread cookie golden_apple
golden_carrot cooked_beef cooked_porkchop cooked_chicken pumpkin_pie sugar honeycomb ink_sac glow_ink_sac
nautilus_shell heart_of_the_sea totem_of_undying shulker_shell phantom_membrane nether_star dragon_breath
experience_bottle arrow bow crossbow trident shield saddle name_tag lead fishing_rod shears flint_and_steel bucket
diamond_sword iron_pickaxe golden_axe wooden_shovel stone_hoe diamond_helmet iron_chestplate leather_boots elytra
spyglass brush mace wind_charge breeze_rod rabbit_foot rabbit_hide snowball firework_rocket emerald""".split()
BLOCKS_OK = """stone cobblestone dirt grass_block sand gravel oak_log oak_planks glass obsidian bedrock netherrack end_stone
glowstone sea_lantern bookshelf crafting_table furnace chest tnt sponge ice packed_ice snow clay hardened_clay
diamond_block iron_block gold_block emerald_block coal_block lapis_block redstone_block diamond_ore iron_ore coal_ore
gold_ore emerald_ore deepslate tuff calcite basalt blackstone soul_sand magma prismarine hay_block pumpkin
melon_block cactus jukebox noteblock beacon anvil cauldron enchanting_table lectern barrel smoker blast_furnace loom
composter scaffolding honey_block slime dried_kelp_block mud moss_block sculk amethyst_block copper_block
ancient_debris crying_obsidian respawn_anchor lodestone target observer piston dispenser dropper hopper
redstone_lamp bell lantern quartz_block brick_block nether_brick mycelium podzol bone_block""".split()
non_blocks = [idn(n) for n in NON_BLOCK if n in ITM and n not in BLK and not ITM[n]["blk"] and idn(n)]
blocks_ok = [bdn(n) for n in BLOCKS_OK if n in BLK and bdn(n)]
block_names = {b["d"].lower() for b in data["blocks"]}
non_blocks = [x for x in dict.fromkeys(non_blocks) if x.lower() not in block_names]
for nb in non_blocks:
    for _ in range(2):
        add("notblock", "nb:" + nb, "Which of these is NOT a block in Minecraft: Bedrock Edition?", nb, pick(blocks_ok, 3))
for blk in blocks_ok:
    add("isblock", "bk:" + blk, "Only one of these can be placed as a block. Which one?", blk, pick(non_blocks, 3))

# ------------------------------------------------------------------ light levels (values checked against the data)
LIGHT = [("torch", "a Torch", 14), ("soul_torch", "a Soul Torch", 10), ("redstone_torch", "a Redstone Torch", 7),
         ("lantern", "a Lantern", 15), ("soul_lantern", "a Soul Lantern", 10), ("glowstone", "Glowstone", 15),
         ("sea_lantern", "a Sea Lantern", 15), ("shroomlight", "a Shroomlight", 15), ("lit_pumpkin", "a Jack o'Lantern", 15),
         ("beacon", "a Beacon", 15), ("conduit", "a Conduit", 15), ("campfire", "a Campfire", 15),
         ("soul_campfire", "a Soul Campfire", 10), ("end_rod", "an End Rod", 14), ("magma", "a Magma Block", 3),
         ("crying_obsidian", "Crying Obsidian", 10), ("glow_lichen", "Glow Lichen", 7), ("amethyst_cluster", "an Amethyst Cluster", 5),
         ("sculk_catalyst", "a Sculk Catalyst", 6), ("ender_chest", "an Ender Chest", 7), ("dragon_egg", "the Dragon Egg", 1),
         ("brown_mushroom", "a Brown Mushroom", 1), ("lit_furnace", "a Furnace while it's smelting", 13),
         ("ochre_froglight", "a Froglight", 15), ("lit_redstone_lamp", "a powered Redstone Lamp", 15),
         ("large_amethyst_bud", "a Large Amethyst Bud", 4), ("medium_amethyst_bud", "a Medium Amethyst Bud", 2),
         ("small_amethyst_bud", "a Small Amethyst Bud", 1), ("lava", "Lava", 15), ("fire", "Fire", 15)]
LIGHT = [x for x in LIGHT if x[0] in BLK and BLK[x[0]]["l"] == x[2]]
for n, label, lv in LIGHT:
    add("light", "l:" + n, f"What light level does {label} give off?", str(lv), [str(x) for x in near(lv, 0, 15, spread=4)])
DARK = [bdn(n) for n in "stone dirt oak_planks glass obsidian sand cobblestone bookshelf crafting_table chest iron_block diamond_block hay_block pumpkin cactus anvil lectern barrel netherrack soul_sand basalt blackstone end_stone".split()
        if n in BLK and BLK[n]["l"] == 0]
GLOW = [(n, label) for n, label, lv in LIGHT if lv >= 7 and n not in ("lit_furnace", "lit_redstone_lamp", "lava", "fire")]
for n, label in GLOW:
    add("lightwhich", "lw:" + n, "Which of these blocks gives off light?", bdn(n), pick(DARK, 3))

# ------------------------------------------------------------------ pickaxe tier
TIER = ["Wooden Pickaxe", "Stone Pickaxe", "Iron Pickaxe", "Diamond Pickaxe"]
TIER_BLOCKS = """diamond_ore deepslate_diamond_ore iron_ore deepslate_iron_ore gold_ore deepslate_gold_ore redstone_ore
deepslate_redstone_ore lapis_ore deepslate_lapis_ore emerald_ore deepslate_emerald_ore copper_ore deepslate_copper_ore
coal_ore deepslate_coal_ore nether_gold_ore quartz_ore obsidian crying_obsidian ancient_debris netherite_block
respawn_anchor diamond_block iron_block gold_block emerald_block lapis_block copper_block raw_iron_block raw_gold_block
raw_copper_block stone cobblestone end_stone netherrack deepslate blackstone basalt sandstone bricks
prismarine amethyst_block""".split()
for n in TIER_BLOCKS:
    b = BLK.get(n)
    if not b or b["tier"] is None or not b["pickOnly"] or b["tier"] > 3:
        continue
    add("tier", "t:" + n, f"What's the weakest pickaxe that can mine {b['d']} and actually get its drop?", TIER[b["tier"]],
        [t for t in TIER if t != TIER[b["tier"]]])

# ------------------------------------------------------------------ blast resistance / hardness
COMMON = [b for b in data["blocks"] if b["n"] in set(BLOCKS_OK + TIER_BLOCKS + "glass oak_planks wool white_wool dirt sand gravel ice leaves oak_leaves".split())
          and b["h"] is not None and b["h"] >= 0 and b["r"] is not None]
for _ in range(400):
    four = rng.sample(COMMON, 4)
    rs = sorted(four, key=lambda b: -b["r"])
    if rs[0]["r"] >= 1.5 * rs[1]["r"] and len({b["r"] for b in four}) == 4:
        add("blast", "br:" + rs[0]["n"] + str(_), "Which of these blocks has the highest blast resistance?", rs[0]["d"], [b["d"] for b in rs[1:]])
    hs = sorted(four, key=lambda b: b["h"])
    if hs[1]["h"] >= max(0.5, 2 * hs[0]["h"]) and len({b["h"] for b in four}) == 4:
        add("hardness", "hd:" + hs[0]["n"] + str(_), "Which of these blocks is the quickest to break by hand?", hs[0]["d"], [b["d"] for b in hs[1:]])

# ------------------------------------------------------------------ stack sizes (only where data matches known values)
STACK = {1: "bed oak_boat minecart saddle water_bucket lava_bucket milk_bucket potion totem_of_undying enchanted_book writable_book diamond_sword iron_pickaxe bow trident elytra mushroom_stew rabbit_stew beetroot_soup spyglass shield shears fishing_rod flint_and_steel music_disc_cat",
         16: "ender_pearl snowball egg oak_sign bucket honey_bottle banner written_book",
         64: "diamond iron_ingot bread cookie arrow ender_eye experience_bottle name_tag lead compass clock book paper stick torch cobblestone glass firework_rocket golden_apple"}
for size, names in STACK.items():
    for n in names.split():
        it = ITM.get(n)
        if not it or it["ss"] != size:
            continue
        add("stack", "st:" + n, f"What's the max stack size of {it['d']}?",
            str(size), [x for x in ("1", "16", "32", "64") if x != str(size)])

# ------------------------------------------------------------------ recipes
GENERIC = {"planks": "Any Planks", "log": "Any Log", "wooden_slab": "Any Wooden Slab"}
WOOD_VARIANTS = re.compile(r"^(oak|spruce|birch|jungle|acacia|dark_oak|mangrove|cherry|bamboo|crimson|warped|pale_oak)_(planks|log|slab)$")
SKIP_OUT = {"lodestone", "crafting_table"} - {"crafting_table"}  # lodestone's recipe changed after the recipe data was taken


def ing_name(i):
    if i.get("metadata") not in (None, 0):
        return None
    n = i["name"]
    if n in GENERIC:
        return GENERIC[n]
    if WOOD_VARIANTS.match(n):
        return "WOOD"
    return idn(n) or bdn(n)


crafting = collections.defaultdict(list)   # output display -> list of normalized multisets
smelt = []
for r in data["recipes"]:
    out = r["o"][0]
    if out.get("metadata") not in (None, 0) or out["name"] in SKIP_OUT:
        continue
    od = idn(out["name"]) or bdn(out["name"])
    if not od:
        continue
    ings = [(ing_name(i), i["count"]) for i in r["i"]]
    if any(n is None for n, _ in ings):
        continue
    if r["t"].startswith("crafting"):
        ms = tuple(sorted(collections.Counter({n: c for n, c in ings}).items()))
        if sum(c for _, c in ms) > 9:
            continue
        crafting[(od, out["name"], out["count"])].append(ms)
    elif r["t"] == "furnace" and len(ings) == 1 and ings[0][0] != "WOOD":
        smelt.append((ings[0][0], od))

# collapse wood variants: keep the generic "Any Planks" recipe, drop per-wood duplicates
recipes = {}
for (od, oname, cnt), lst in crafting.items():
    clean = [ms for ms in lst if not any(n == "WOOD" for n, _ in ms)]
    if not clean:
        continue
    recipes[(od, oname, cnt)] = clean

INTERESTING = re.compile(r"(pickaxe|sword|axe|shovel|hoe|helmet|chestplate|leggings|boots|bow|crossbow|arrow|shield|bucket|compass|clock|map|"
                         r"table|furnace|smoker|chest|barrel|hopper|piston|observer|dispenser|dropper|repeater|comparator|lever|button|"
                         r"rail|minecart|boat|torch|lantern|lamp|beacon|anvil|cauldron|brewing|jukebox|note|tnt|bed|book|bookshelf|"
                         r"cake|bread|pie|cookie|stew|soup|golden|apple|carrot|ladder|fence|door|sign|scaffolding|campfire|bell|"
                         r"lectern|composter|loom|grindstone|stonecutter|target|spyglass|lightning|candle|lead|fishing|shears|flint|"
                         r"eye|glass|sticky|slime|honey|daylight|crafter|conduit|end_crystal|respawn|recovery|ender|netherite|"
                         r"magma|snow|clay|brick|paper|sugar|stick|bowl|painting|item_frame|armor_stand|banner|firework|tripwire|trapped)")
COLORS = r"^(White|Orange|Magenta|Light Blue|Yellow|Lime|Pink|Gray|Light Gray|Cyan|Purple|Blue|Brown|Green|Red|Black) "
items_by_display = {}
for (od, oname, cnt), lst in recipes.items():
    if not INTERESTING.search(oname) or re.search(r"(stairs|slab|wall|_fence_gate|dye|carpet|concrete|terracotta|stained|wool|banner_pattern)", oname) \
            or re.match(COLORS, od):
        continue
    items_by_display[od] = (oname, cnt, lst)

all_ings = sorted({n for (_, _, lst) in items_by_display.values() for ms in lst for n, _ in ms})
SWAP = {"Diamond": ["Emerald", "Iron Ingot", "Gold Ingot"], "Iron Ingot": ["Gold Ingot", "Copper Ingot", "Diamond"],
        "Gold Ingot": ["Iron Ingot", "Copper Ingot", "Gold Nugget"], "Obsidian": ["Crying Obsidian", "Cobblestone", "Blackstone"],
        "Book": ["Paper", "Book and Quill", "Leather"], "Stick": ["Any Planks", "Blaze Rod", "Bone"], "Any Planks": ["Stick", "Any Log", "Cobblestone"],
        "Cobblestone": ["Stone", "Any Planks", "Blackstone"], "String": ["Leather", "Feather", "Paper"], "Redstone Dust": ["Glowstone Dust", "Gunpowder", "Sugar"],
        "Milk Bucket": ["Water Bucket", "Bucket", "Egg"], "Sugar": ["Wheat", "Egg", "Honey Bottle"], "Egg": ["Sugar", "Feather", "Wheat"],
        "Wheat": ["Sugar", "Hay Bale", "Wheat Seeds"], "Glass": ["Sand", "Glass Pane", "Quartz Block"], "Leather": ["Rabbit Hide", "String", "Paper"]}


COMMON_INGS = ["Stick", "Any Planks", "Iron Ingot", "Gold Ingot", "Diamond", "String", "Leather", "Cobblestone", "Redstone Dust", "Paper",
               "Glass", "Sand", "Slimeball", "Copper Ingot", "Coal", "Flint", "Feather", "Wheat", "Sugar", "Egg", "Gunpowder", "Book"]


def fmt(ms):
    return " · ".join(f"{c}× {n}" for n, c in sorted(ms, key=lambda x: (-x[1], x[0])))


def mutate(ms):
    ms = dict(ms)
    keys = list(ms)
    k = rng.choice(keys)
    roll = rng.random()
    if roll < 0.45:
        ms[k] = max(1, ms[k] + rng.choice([-2, -1, 1, 2]))
    elif roll < 0.8:
        alts = [a for a in SWAP.get(k, []) if a not in ms] or [a for a in rng.sample(COMMON_INGS, len(COMMON_INGS)) if a not in ms]
        if not alts:
            return None
        ms[rng.choice(alts[:4])] = ms.pop(k)
    elif len(keys) >= 2:
        a, b = rng.sample(keys, 2)
        ms[a], ms[b] = ms[b], ms[a]
    else:
        ms[k] = ms[k] + 1
    if sum(ms.values()) > 9:
        return None
    return tuple(sorted(ms.items()))


for od, (oname, cnt, lst) in items_by_display.items():
    valid = set(lst)
    main = sorted(lst, key=lambda ms: sum(c for _, c in ms))[0]
    ds = set()
    for _ in range(60):
        m = mutate(main)
        if m and m not in valid:
            ds.add(m)
        if len(ds) >= 3:
            break
    if len(ds) >= 3:
        add("recipe", "r:" + oname, f"What's the crafting recipe for {od}?", fmt(main), [fmt(m) for m in list(ds)[:3]], rich=True)

# reverse: which item does this recipe make (ingredient multiset must be unique)
owner = collections.defaultdict(set)
for od, (oname, cnt, lst) in items_by_display.items():
    for ms in lst:
        owner[ms].add(od)
for (od2, oname2, cnt2), lst2 in recipes.items():
    for ms in lst2:
        owner[ms].add(od2)
outs = list(items_by_display)
for od, (oname, cnt, lst) in items_by_display.items():
    ms = lst[0]
    if len(owner[ms]) != 1:
        continue
    ds = pick(outs, 3, exclude={od})
    if ds:
        add("recipewhat", "r:" + oname, f"What do you get by crafting these together?\n{fmt(ms)}", od, ds, rich=True)
    if cnt > 1:
        add("recipecount", "r:" + oname, f"Crafting {od}: how many do you get from one craft?", str(cnt), [str(x) for x in near(cnt, 1, 16, spread=4)])

# smelting
smelt = [(i, o) for i, o in smelt if i != o and " " in (i + " " + o) and not re.match(COLORS, o) and not re.match(COLORS, i)
         and i not in ("Stonebrick",) and o not in ("Stonebrick",)]
smelt_outs = sorted({o for _, o in smelt})
seen_in = set()
for i, o in smelt:
    if i in seen_in or i in ("Any Log",):
        continue
    seen_in.add(i)
    if len([1 for i2, o2 in smelt if i2 == i]) > 1:
        continue
    ds = pick(smelt_outs, 3, exclude={o})
    if ds:
        add("smelt", "s:" + i, f"What do you get when you smelt {i} in a furnace?", o, ds)

# ------------------------------------------------------------------ enchanting
EN = {e["name"]: e for e in data["ench"]}
pretty = lambda n: {"binding_curse": "Curse of Binding", "vanishing_curse": "Curse of Vanishing"}.get(n, EN[n]["displayName"] if n in EN else n.replace("_", " ").title())
MACE = {"density": ("Density", 5), "breach": ("Breach", 4), "wind_burst": ("Wind Burst", 3)}
levels = {n: e["maxLevel"] for n, e in EN.items()}
levels.update({k: v[1] for k, v in MACE.items()})
names = {n: pretty(n) for n in EN}
names.update({k: v[0] for k, v in MACE.items()})
for n, lv in levels.items():
    add("enchlevel", "e:" + n, f"What's the highest level {names[n]} can normally reach?", "Level " + "I II III IV V".split()[lv - 1],
        ["Level " + x for x in "I II III IV V".split() if x != "I II III IV V".split()[lv - 1]][:3] if lv > 1 else ["Level II", "Level III", "Level V"])
TREASURE = ["mending", "frost_walker", "soul_speed", "swift_sneak", "binding_curse", "vanishing_curse", "wind_burst"]
TABLE = ["protection", "fire_protection", "blast_protection", "projectile_protection", "feather_falling", "respiration", "aqua_affinity",
         "depth_strider", "thorns", "sharpness", "smite", "bane_of_arthropods", "knockback", "fire_aspect", "looting", "efficiency",
         "silk_touch", "unbreaking", "fortune", "power", "punch", "flame", "infinity", "luck_of_the_sea", "lure", "impaling", "riptide",
         "loyalty", "channeling", "multishot", "piercing", "quick_charge"]
for t in TREASURE:
    for _ in range(3):
        add("treasure", "tr:" + t + str(_), "Which of these enchantments can you NOT get from an enchanting table?", names[t], [names[x] for x in rng.sample(TABLE, 3)])
for _ in range(10):
    t = rng.choice(TABLE)
    add("treasure2", "tb:" + t + str(_), "Which of these enchantments CAN you get from an enchanting table?", names[t], [names[x] for x in rng.sample(TREASURE, 3)])
for c in ("binding_curse", "vanishing_curse"):
    for _ in range(3):
        add("curse", "cu:" + c + str(_), "Which of these enchantments is a curse?", names[c], [names[x] for x in rng.sample(TABLE + ["mending", "swift_sneak"], 3)])
SLOT = {"depth_strider": "Boots", "frost_walker": "Boots", "soul_speed": "Boots", "feather_falling": "Boots", "respiration": "Helmet",
        "aqua_affinity": "Helmet", "swift_sneak": "Leggings", "power": "Bow", "punch": "Bow", "flame": "Bow", "infinity": "Bow",
        "multishot": "Crossbow", "piercing": "Crossbow", "quick_charge": "Crossbow", "impaling": "Trident", "riptide": "Trident",
        "loyalty": "Trident", "channeling": "Trident", "luck_of_the_sea": "Fishing Rod", "lure": "Fishing Rod",
        "density": "Mace", "breach": "Mace", "wind_burst": "Mace", "fortune": "Pickaxe", "silk_touch": "Pickaxe"}
GEAR = ["Helmet", "Chestplate", "Leggings", "Boots", "Bow", "Crossbow", "Trident", "Fishing Rod", "Mace", "Sword", "Pickaxe"]
EXCL_GEAR = {"fortune": {"Sword", "Mace", "Trident", "Bow", "Crossbow"}, "silk_touch": {"Sword", "Mace", "Trident", "Bow", "Crossbow"}}
for n, slot in SLOT.items():
    bad = [g for g in GEAR if g != slot and g not in ({"Pickaxe", "Sword"} if n in ("fortune", "silk_touch") else set())]
    if n in ("fortune", "silk_touch"):
        bad = ["Sword", "Bow", "Helmet", "Boots", "Crossbow", "Trident"]
    add("enchslot", "es:" + n, f"Which of these can you put {names[n]} on?", slot, pick(bad, 3))
PAIRS = [("sharpness", "smite"), ("sharpness", "bane_of_arthropods"), ("smite", "bane_of_arthropods"), ("protection", "blast_protection"),
         ("protection", "fire_protection"), ("protection", "projectile_protection"), ("silk_touch", "fortune"), ("infinity", "mending"),
         ("depth_strider", "frost_walker"), ("riptide", "loyalty"), ("riptide", "channeling"), ("multishot", "piercing")]
for a, b in PAIRS:
    for x, y in ((a, b), (b, a)):
        okay = [n for n in TABLE + ["mending"] if n not in EN.get(x, {}).get("exclude", []) and n != x and n != y]
        if y not in EN.get(x, {}).get("exclude", []):
            continue
        add("enchclash", "ex:" + x + y, f"Which enchantment can't be on the same item as {names[x]}?", names[y], [names[n] for n in pick(okay, 3)])

# ------------------------------------------------------------------ biomes
BIOME = {"hell": "Nether Wastes", "crimson_forest": "Crimson Forest", "warped_forest": "Warped Forest", "soulsand_valley": "Soul Sand Valley",
         "basalt_deltas": "Basalt Deltas", "the_end": "The End", "plains": "Plains", "sunflower_plains": "Sunflower Plains", "forest": "Forest",
         "flower_forest": "Flower Forest", "birch_forest": "Birch Forest", "roofed_forest": "Dark Forest", "taiga": "Taiga",
         "cold_taiga": "Snowy Taiga", "ice_plains": "Snowy Plains", "ice_plains_spikes": "Ice Spikes", "desert": "Desert", "savanna": "Savanna",
         "mesa": "Badlands", "jungle": "Jungle", "bamboo_jungle": "Bamboo Jungle", "swampland": "Swamp", "mangrove_swamp": "Mangrove Swamp",
         "mushroom_island": "Mushroom Fields", "beach": "Beach", "river": "River", "ocean": "Ocean", "warm_ocean": "Warm Ocean",
         "frozen_ocean": "Frozen Ocean", "meadow": "Meadow", "grove": "Grove", "snowy_slopes": "Snowy Slopes", "jagged_peaks": "Jagged Peaks",
         "cherry_grove": "Cherry Grove", "deep_dark": "Deep Dark", "lush_caves": "Lush Caves", "dripstone_caves": "Dripstone Caves",
         "pale_garden": "Pale Garden", "stone_beach": "Stony Shore"}
bio = {b["n"]: b for b in data["biomes"] if b["n"] in BIOME}
nether = [BIOME[n] for n, b in bio.items() if b["dim"] == "nether"]
over = [BIOME[n] for n, b in bio.items() if b["dim"] == "overworld"]
for nb in nether:
    for _ in range(3):
        add("biome", "bn:" + nb + str(_), "Which of these biomes is in the Nether?", nb, pick(over, 3))
dry = [BIOME[n] for n, b in bio.items() if b["dim"] == "overworld" and not b["rain"]]
wet = [BIOME[n] for n, b in bio.items() if b["dim"] == "overworld" and b["rain"] and n not in ("deep_dark", "lush_caves", "dripstone_caves")]
for d in dry:
    for _ in range(2):
        add("biome", "bd:" + d + str(_), "In which of these biomes does it never rain?", d, pick(wet, 3))
caves = ["Deep Dark", "Lush Caves", "Dripstone Caves"]
for c in caves:
    for _ in range(2):
        add("biome", "bc:" + c + str(_), "Which of these is an underground cave biome?", c, pick([o for o in over if o not in caves], 3))
HOME = [("Mooshrooms", "Mushroom Fields", {"Mushroom Fields"}), ("the Warden", "Deep Dark", {"Deep Dark"}), ("Axolotls", "Lush Caves", {"Lush Caves"}),
        ("the Creaking", "Pale Garden", {"Pale Garden"}), ("Pandas", "Bamboo Jungle", {"Bamboo Jungle", "Jungle"}),
        ("Parrots", "Jungle", {"Jungle", "Bamboo Jungle"}), ("Ocelots", "Jungle", {"Jungle", "Bamboo Jungle"}),
        ("Hoglins", "Crimson Forest", set(nether))]
for mob, home, bad in HOME:
    add("biome", "bh:" + mob, f"In which biome do {mob} naturally spawn?", home, pick([o for o in over if o not in bad and o not in caves] + ([] if home == "Crimson Forest" else []), 3))

# ------------------------------------------------------------------ mobs (hand-written, same in current Bedrock)
HEALTH = {"Ender Dragon": 200, "Wither": 600, "Warden": 500, "Elder Guardian": 80, "Ravager": 100, "Iron Golem": 100, "Evoker": 24,
          "Vindicator": 24, "Pillager": 24, "Witch": 26, "Enderman": 40, "Hoglin": 40, "Zoglin": 40, "Piglin Brute": 50, "Shulker": 30,
          "Guardian": 30, "Blaze": 20, "Creeper": 20, "Zombie": 20, "Skeleton": 20, "Spider": 16, "Cave Spider": 12, "Ghast": 10,
          "Phantom": 20, "Breeze": 30, "Silverfish": 8, "Endermite": 8, "Vex": 14, "Piglin": 16, "Strider": 20, "Polar Bear": 30,
          "Turtle": 30, "Camel": 32, "Sniffer": 14, "Snow Golem": 4, "Chicken": 4, "Cow": 10, "Pig": 10, "Sheep": 8, "Rabbit": 3,
          "Bat": 6, "Villager": 20, "Axolotl": 14, "Allay": 20, "Fox": 10, "Bee": 10, "Goat": 10, "Frog": 10, "Armadillo": 12,
          "Bogged": 16, "Dolphin": 10, "Squid": 10, "Panda": 20, "Wandering Trader": 20, "Wither Skeleton": 20}
for mob, hp in HEALTH.items():
    spread = max(4, hp // 4)
    cand = sorted({hp + d for d in (-spread * 2, -spread, spread, spread * 2, -2, 2, 4, -4, hp, -hp // 2) if hp + d > 0 and hp + d != hp})
    ds = pick([str(c) for c in cand], 3)
    add("health", "mh:" + mob, f"How many hearts of health does {'the ' if mob in ('Ender Dragon', 'Wither', 'Warden') else 'a '}{mob} have?", str(hp), ds)
HOSTILE = "Zombie Creeper Skeleton Witch Stray Husk Wither Skeleton Guardian Vindicator Pillager Ravager Evoker Vex Drowned Blaze Ghast Magma Cube Slime Phantom Shulker Silverfish Endermite Hoglin Zoglin Piglin Brute Warden Breeze Bogged".split(" ")
HOSTILE = ["Zombie", "Creeper", "Skeleton", "Witch", "Stray", "Husk", "Wither Skeleton", "Guardian", "Vindicator", "Pillager", "Ravager",
           "Evoker", "Vex", "Drowned", "Blaze", "Ghast", "Magma Cube", "Slime", "Phantom", "Shulker", "Silverfish", "Endermite", "Hoglin",
           "Zoglin", "Piglin Brute", "Warden", "Breeze", "Bogged"]
PASSIVE = ["Chicken", "Cow", "Pig", "Sheep", "Mooshroom", "Rabbit", "Horse", "Donkey", "Mule", "Squid", "Glow Squid", "Bat", "Villager",
           "Wandering Trader", "Cod", "Salmon", "Tropical Fish", "Turtle", "Parrot", "Cat", "Ocelot", "Strider", "Sniffer", "Camel", "Frog",
           "Allay", "Armadillo", "Snow Golem"]
NEUTRAL = ["Enderman", "Bee", "Iron Golem", "Wolf", "Polar Bear", "Zombified Piglin", "Llama", "Dolphin", "Panda", "Goat"]
for m in HOSTILE:
    add("hostile", "ho:" + m, "Which of these mobs is hostile and will attack you on sight?", m, pick(PASSIVE, 3))
for m in PASSIVE[:20]:
    add("hostile", "pa:" + m, "Which of these mobs will never attack you?", m, pick(HOSTILE, 3))
for m in NEUTRAL:
    add("hostile", "ne:" + m, "Which of these mobs is neutral, only attacking if you provoke it?", m, pick(HOSTILE[:14] + PASSIVE[:10], 3))
DROPS = {"Creeper": {"Gunpowder"}, "Skeleton": {"Bone", "Arrow", "Bow"}, "Zombie": {"Rotten Flesh", "Iron Ingot", "Carrot", "Potato"},
         "Spider": {"String", "Spider Eye"}, "Enderman": {"Ender Pearl"}, "Blaze": {"Blaze Rod"}, "Ghast": {"Ghast Tear", "Gunpowder"},
         "Slime": {"Slimeball"}, "Magma Cube": {"Magma Cream"}, "Witch": {"Glass Bottle", "Glowstone Dust", "Gunpowder", "Redstone Dust", "Spider Eye", "Sugar", "Stick"},
         "Evoker": {"Totem of Undying", "Emerald"}, "Shulker": {"Shulker Shell"}, "Phantom": {"Phantom Membrane"},
         "Drowned": {"Rotten Flesh", "Copper Ingot", "Trident", "Nautilus Shell"}, "Wither": {"Nether Star"},
         "Guardian": {"Prismarine Shard", "Prismarine Crystals", "Raw Cod"}, "Elder Guardian": {"Wet Sponge", "Prismarine Shard", "Prismarine Crystals", "Raw Cod"},
         "Squid": {"Ink Sac"}, "Glow Squid": {"Glow Ink Sac"}, "Chicken": {"Feather", "Raw Chicken"}, "Cow": {"Leather", "Raw Beef"},
         "Sheep": {"Wool", "Raw Mutton"}, "Pig": {"Raw Porkchop"}, "Rabbit": {"Rabbit Hide", "Raw Rabbit", "Rabbit's Foot"},
         "Breeze": {"Breeze Rod"}, "Wither Skeleton": {"Coal", "Bone", "Wither Skeleton Skull"}, "Iron Golem": {"Iron Ingot", "Poppy"},
         "Snow Golem": {"Snowball"}}
for mob, drops in DROPS.items():
    for item in sorted(drops):
        holders = [m for m, d in DROPS.items() if item in d]
        if mob != holders[0]:
            continue
        others = [m for m in DROPS if item not in DROPS[m]]
        add("drops", "dr:" + item, f"Which mob can drop {item}?", mob, pick(others, 3))
BREED = [("Cows", "Wheat", {"Wheat"}), ("Sheep", "Wheat", {"Wheat"}), ("Pigs", "Carrot", {"Carrot", "Potato", "Beetroot"}),
         ("Chickens", "Wheat Seeds", {"Wheat Seeds", "Melon Seeds", "Pumpkin Seeds", "Beetroot Seeds", "Torchflower Seeds", "Pitcher Pod"}),
         ("Turtles", "Seagrass", {"Seagrass"}), ("Pandas", "Bamboo", {"Bamboo"}), ("Foxes", "Sweet Berries", {"Sweet Berries", "Glow Berries"}),
         ("Llamas", "Hay Bale", {"Hay Bale"}), ("Goats", "Wheat", {"Wheat"}), ("Frogs", "Slimeball", {"Slimeball"}),
         ("Axolotls", "Bucket of Tropical Fish", {"Bucket of Tropical Fish"}), ("Striders", "Warped Fungus", {"Warped Fungus"}),
         ("Hoglins", "Crimson Fungus", {"Crimson Fungus"}), ("Sniffers", "Torchflower Seeds", {"Torchflower Seeds"}),
         ("Camels", "Cactus", {"Cactus"}), ("Armadillos", "Spider Eye", {"Spider Eye"}), ("Cats", "Raw Cod", {"Raw Cod", "Raw Salmon"}),
         ("Horses", "Golden Apple", {"Golden Apple", "Golden Carrot", "Enchanted Golden Apple"})]
FOODS = ["Wheat", "Carrot", "Potato", "Beetroot", "Wheat Seeds", "Seagrass", "Bamboo", "Sweet Berries", "Hay Bale", "Slimeball", "Warped Fungus",
         "Crimson Fungus", "Torchflower Seeds", "Cactus", "Spider Eye", "Raw Cod", "Raw Salmon", "Golden Apple", "Apple", "Bread", "Sugar", "Kelp"]
for mob, food, ok in BREED:
    add("breed", "bf:" + mob, f"What do you feed {mob} to make them breed?", food, pick([f for f in FOODS if f not in ok], 3))
TAME = [("a Wolf", "Bone", {"Bone"}), ("a Parrot", "Wheat Seeds", {"Wheat Seeds", "Melon Seeds", "Pumpkin Seeds", "Beetroot Seeds", "Torchflower Seeds", "Pitcher Pod"}),
        ("a Cat", "Raw Cod", {"Raw Cod", "Raw Salmon"})]
for mob, food, ok in TAME:
    add("breed", "tm:" + mob, f"What do you use to tame {mob}?", food, pick([f for f in FOODS + ["Rotten Flesh", "Cookie"] if f not in ok], 3))
JOBS = [("Composter", "Farmer"), ("Lectern", "Librarian"), ("Smithing Table", "Toolsmith"), ("Barrel", "Fisherman"), ("Blast Furnace", "Armorer"),
        ("Brewing Stand", "Cleric"), ("Cartography Table", "Cartographer"), ("Cauldron", "Leatherworker"), ("Fletching Table", "Fletcher"),
        ("Grindstone", "Weaponsmith"), ("Loom", "Shepherd"), ("Smoker", "Butcher"), ("Stonecutter", "Mason")]
for ws, job in JOBS:
    add("villager", "vj:" + job, f"Which job does a Villager take when it claims a {ws}?", job, pick([j for _, j in JOBS if j != job], 3))
    add("villager", "vw:" + job, f"Which block turns a Villager into a {job}?", ws, pick([w for w, _ in JOBS if w != ws], 3))
FOOD = {"Steak": 8, "Cooked Porkchop": 8, "Bread": 5, "Golden Carrot": 6, "Apple": 4, "Baked Potato": 5, "Cooked Chicken": 6, "Cooked Mutton": 6,
        "Cooked Salmon": 6, "Cooked Cod": 5, "Carrot": 3, "Potato": 1, "Beetroot": 1, "Melon Slice": 2, "Cookie": 2, "Pumpkin Pie": 8,
        "Rabbit Stew": 10, "Mushroom Stew": 6, "Beetroot Soup": 6, "Honey Bottle": 6, "Sweet Berries": 2, "Glow Berries": 2, "Dried Kelp": 1,
        "Rotten Flesh": 4, "Spider Eye": 2, "Chorus Fruit": 4, "Golden Apple": 4, "Raw Beef": 3, "Raw Porkchop": 3, "Raw Chicken": 2,
        "Raw Mutton": 2, "Raw Rabbit": 3, "Cooked Rabbit": 5, "Raw Cod": 2, "Raw Salmon": 2, "Tropical Fish": 1, "Pufferfish": 1}
for f, v in FOOD.items():
    add("food", "fd:" + f, f"How many drumsticks of hunger does eating {f} fill?", str(v), [str(x) for x in near(v, 1, 12, spread=3)])

# ------------------------------------------------------------------ world and game facts
FACTS = [
    ("How many blocks of Obsidian does the smallest Nether portal frame need (corners left out)?", "10", ["8", "12", "14"]),
    ("How many blocks of Obsidian does the smallest Nether portal frame need if you fill in the corners?", "14", ["10", "12", "16"]),
    ("Walking 1 block in the Nether moves you how far in the Overworld?", "8 blocks", ["4 blocks", "16 blocks", "2 blocks"]),
    ("How many Eyes of Ender does it take to fill an End Portal?", "12", ["8", "10", "16"]),
    ("How long is one full day-and-night cycle in real time?", "20 minutes", ["10 minutes", "30 minutes", "24 minutes"]),
    ("What's the lowest Y level of the Overworld?", "-64", ["0", "-32", "-128"]),
    ("What's the highest Y level you can place a block at in the Overworld?", "319", ["255", "256", "383"]),
    ("What's the strongest redstone signal strength?", "15", ["10", "16", "20"]),
    ("What's the longest delay a Redstone Repeater can be set to?", "4 ticks", ["2 ticks", "3 ticks", "8 ticks"]),
    ("How many slots does a Hopper have?", "5", ["3", "4", "9"]),
    ("How many slots does a single Chest have?", "27", ["18", "36", "54"]),
    ("How many slots does a Double Chest have?", "54", ["27", "48", "64"]),
    ("How many slots does a Shulker Box have?", "27", ["9", "18", "36"]),
    ("How many items can one piece of Coal smelt?", "8", ["4", "6", "16"]),
    ("How many items can one Lava Bucket smelt?", "100", ["64", "50", "80"]),
    ("How many items can one Blaze Rod smelt?", "12", ["8", "16", "10"]),
    ("How many items can one Block of Dried Kelp smelt?", "20", ["9", "16", "32"]),
    ("How many layers can a full Beacon pyramid have?", "4", ["3", "5", "6"]),
    ("How many blocks does a full four-layer Beacon pyramid take?", "164", ["81", "128", "200"]),
    ("How many Bookshelves do you need around an Enchanting Table for level 30 enchantments?", "15", ["12", "16", "20"]),
    ("What's the highest level an Enchanting Table can offer?", "30", ["20", "40", "50"]),
    ("What do you get by smelting Ancient Debris?", "Netherite Scrap", ["Netherite Ingot", "Iron Ingot", "Gold Nugget"]),
    ("How many Netherite Scrap go into one Netherite Ingot?", "4", ["2", "8", "9"]),
    ("Which mob do you get a Totem of Undying from?", "Evoker", ["Vindicator", "Witch", "Pillager"]),
    ("Where do you find Elytra?", "In End City ships", ["In Bastion Remnants", "In Ancient Cities", "In Woodland Mansions"]),
    ("What do you need to charge a Respawn Anchor?", "Glowstone", ["Redstone Dust", "Blaze Powder", "Ender Pearls"]),
    ("How many charges can a Respawn Anchor hold?", "4", ["3", "5", "8"]),
    ("What turns a Creeper into a Charged Creeper?", "Being struck by lightning", ["Standing in lava", "A full moon", "Being hit by a Blaze"]),
    ("What happens when flowing water meets a Lava source block?", "It turns into Obsidian", ["It turns into Cobblestone", "It turns into Stone", "Nothing"]),
    ("How many days can you go without sleeping before Phantoms start spawning?", "3", ["1", "5", "7"]),
    ("How far do you have to fall before you take fall damage?", "More than 3 blocks", ["More than 1 block", "More than 5 blocks", "More than 10 blocks"]),
    ("How many slots are in the hotbar?", "9", ["8", "10", "12"]),
    ("How many inventory slots does a player have, not counting armor and the off-hand?", "36", ["27", "40", "45"]),
    ("How many drumsticks make up a full hunger bar?", "10", ["8", "12", "20"]),
    ("What do you need to brew any potion first?", "Nether Wart", ["Blaze Powder", "Sugar", "Glowstone Dust"]),
    ("What fuels a Brewing Stand?", "Blaze Powder", ["Coal", "Redstone Dust", "Lava"]),
    ("What do you add to a potion to turn it into a Splash Potion?", "Gunpowder", ["Dragon's Breath", "Redstone Dust", "Glowstone Dust"]),
    ("What do you add to a Splash Potion to make it a Lingering Potion?", "Dragon's Breath", ["Gunpowder", "Ghast Tear", "Fermented Spider Eye"]),
    ("What makes a potion last longer?", "Redstone Dust", ["Glowstone Dust", "Sugar", "Gunpowder"]),
    ("What makes a potion stronger (level II)?", "Glowstone Dust", ["Redstone Dust", "Blaze Powder", "Magma Cream"]),
    ("Which item gives the Night Vision potion its effect?", "Golden Carrot", ["Glistering Melon Slice", "Spider Eye", "Sugar"]),
    ("Which item brews a Potion of Fire Resistance?", "Magma Cream", ["Blaze Powder", "Ghast Tear", "Golden Carrot"]),
    ("Which item brews a Potion of Regeneration?", "Ghast Tear", ["Magma Cream", "Sugar", "Rabbit's Foot"]),
    ("Which item brews a Potion of Swiftness?", "Sugar", ["Rabbit's Foot", "Feather", "Golden Carrot"]),
    ("Which item brews a Potion of Leaping?", "Rabbit's Foot", ["Feather", "Sugar", "Slimeball"]),
    ("Which item brews a Potion of Water Breathing?", "Pufferfish", ["Raw Cod", "Turtle Shell", "Kelp"]),
    ("Which item brews a Potion of Slow Falling?", "Phantom Membrane", ["Feather", "Elytra", "String"]),
    ("Which item turns a potion into its 'opposite', like Swiftness into Slowness?", "Fermented Spider Eye", ["Spider Eye", "Rotten Flesh", "Poisonous Potato"]),
    ("Which blocks can you build a Conduit's frame from?", "Prismarine blocks and Sea Lanterns", ["Obsidian and Crying Obsidian", "Ice and Packed Ice", "Sponges and Wet Sponges"]),
    ("What does a Sponge become after soaking up water?", "Wet Sponge", ["Soggy Sponge", "Sponge Block", "Clay"]),
    ("Which item lets you ride a Strider and steer it?", "Warped Fungus on a Stick", ["Carrot on a Stick", "Lead", "Crimson Fungus"]),
    ("Which item lets you steer a Pig you're riding?", "Carrot on a Stick", ["Lead", "Warped Fungus on a Stick", "Golden Carrot"]),
    ("Ominous Vaults are found in which structure?", "Trial Chambers", ["Ancient Cities", "Bastion Remnants", "Strongholds"]),
    ("Which structure is the Warden found in?", "Ancient City", ["Stronghold", "Trial Chambers", "Woodland Mansion"]),
]
for i, (q, a, o) in enumerate(FACTS):
    add("fact", "f:" + str(i), q, a, o)

# ------------------------------------------------------------------ quotas -> exactly 1,000
QUOTA = {"notblock": 57, "isblock": 30, "light": 28, "lightwhich": 18, "tier": 40, "blast": 25, "hardness": 20, "stack": 45,
         "recipe": 175, "recipewhat": 70, "recipecount": 35, "smelt": 40,
         "enchlevel": 41, "treasure": 21, "treasure2": 10, "curse": 6, "enchslot": 25, "enchclash": 20,
         "biome": 35, "health": 55, "hostile": 50, "drops": 22, "breed": 21, "villager": 26, "food": 37, "fact": 55}
avail = {k: len(v) for k, v in Q.items()}
print("available", avail)
final, short = [], 0
for cat, n in QUOTA.items():
    items = Q.get(cat, [])
    rng.shuffle(items)
    must = [x for x in items if any(s in x["q"] for s in ("Cake", "Enchanting Table"))]
    rest = [x for x in items if x not in must]
    take = (must + rest)[:n]
    short += n - len(take)
    final += take
# top up from the biggest data categories if any quota was short
spare = [x for c in ("recipe", "notblock", "blast", "hostile") for x in Q[c] if x not in final]
rng.shuffle(spare)
final += spare[:max(0, 1000 - len(final))]
final = final[:1000]
print("final", len(final), collections.Counter(x["c"] for x in final))
with open(OUT, "w") as f:
    f.write("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in final) + "\n]\n")
