"""Original procedural textures for the quiz themes (no game assets used)."""
import sys, io, json, base64, random, math
from PIL import Image, ImageDraw, ImageFilter

out = sys.argv[1]
rng = random.Random(7)

def uri(img):
    b = io.BytesIO(); img.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()

def noise(w, h, palette, weights=None, seed=1):
    r = random.Random(seed)
    img = Image.new("RGB", (w, h))
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), r.choices(palette, weights)[0])
    return img

stone = noise(16, 16, [(112, 112, 114), (122, 122, 124), (99, 99, 102), (131, 131, 133), (88, 88, 91)], [5, 5, 3, 2, 1], 3)
deep = noise(16, 16, [(38, 39, 42), (44, 45, 48), (33, 34, 37), (50, 51, 55), (29, 30, 33)], [5, 5, 3, 2, 2], 4)
dirt = noise(16, 16, [(134, 96, 67), (121, 85, 58), (150, 108, 74), (105, 75, 51), (168, 123, 86)], [5, 4, 3, 2, 1], 5)
grass_top = noise(16, 16, [(95, 159, 53), (86, 145, 47), (106, 172, 60), (77, 131, 42), (118, 184, 68)], [5, 4, 3, 2, 1], 6)
side = dirt.copy()
r = random.Random(9)
for x in range(16):
    depth = 3 + (1 if r.random() < 0.45 else 0) + (1 if r.random() < 0.15 else 0)
    for y in range(depth):
        side.putpixel((x, y), r.choice([(95, 159, 53), (86, 145, 47), (106, 172, 60), (77, 131, 42)]))

# warm wooden planks for the tavern tile: 4 boards with grain and dark seams
W, H = 256, 128
wood = Image.new("RGB", (W, H))
px = wood.load()
for b in range(4):
    base = [(118, 74, 40), (108, 66, 35), (126, 81, 44), (101, 62, 33)][b]
    off = rng.random() * 10
    for y in range(b * 32, b * 32 + 32):
        for x in range(W):
            g = math.sin((x / 23.0) + off + math.sin(y / 3.0 + off) * 0.9) * 0.5 + math.sin(x / 7.0 + y * 0.4 + off) * 0.25
            k = 1 + g * 0.12 + (rng.random() - 0.5) * 0.06
            if y % 32 in (0, 31):
                k *= 0.55
            px[x, y] = tuple(max(0, min(255, int(c * k))) for c in base)
    for nx in (rng.randint(20, 100), rng.randint(140, 230)):           # nail heads
        for dy in (8, 23):
            ImageDraw.Draw(wood).ellipse([nx - 2, b * 32 + dy - 2, nx + 2, b * 32 + dy + 2], fill=(58, 40, 26))
wood = wood.filter(ImageFilter.SMOOTH)

json.dump({"stone": uri(stone), "deep": uri(deep), "dirt": uri(dirt), "grass_top": uri(grass_top), "grass_side": uri(side), "wood": uri(wood)},
          open(out, "w"))
print({k: len(v) for k, v in json.load(open(out)).items()})
