#!/usr/bin/env python3
"""Render the gold-California app icon (matches the attached favicon) from real
California GeoJSON geometry, at the sizes a PWA + favicons need."""
import json, math, os, urllib.request
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "icons")
os.makedirs(ICONS, exist_ok=True)

GOLD = (251, 192, 45)   # vivid gold, matches the attached icon
INK = (12, 14, 17)      # app background (#0c0e11)
SS = 4                  # supersample factor for smooth edges
CONTENT = 0.78          # fraction of canvas the shape fills (maskable safe zone)

SRC = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"


def ca_ring():
    cache = "/tmp/us-states.json"
    if not os.path.exists(cache):
        urllib.request.urlretrieve(SRC, cache)
    d = json.load(open(cache))
    ca = next(f for f in d["features"] if f["properties"].get("name") == "California")
    return ca["geometry"]["coordinates"][0]  # single 93-pt ring


def projected(ring):
    midlat = sum(p[1] for p in ring) / len(ring)
    k = math.cos(math.radians(midlat))
    return [(lng * k, -lat) for lng, lat in ring]  # x east, y north-up


def render(size, ring_proj):
    n = size * SS
    img = Image.new("RGB", (n, n), INK)
    dr = ImageDraw.Draw(img)
    xs = [p[0] for p in ring_proj]; ys = [p[1] for p in ring_proj]
    w = max(xs) - min(xs); h = max(ys) - min(ys)
    scale = CONTENT * n / max(w, h)
    ox = (n - w * scale) / 2 - min(xs) * scale
    oy = (n - h * scale) / 2 - min(ys) * scale
    poly = [(x * scale + ox, y * scale + oy) for x, y in ring_proj]
    dr.polygon(poly, fill=GOLD)
    return img.resize((size, size), Image.LANCZOS)


def main():
    ring = projected(ca_ring())
    base = render(512, ring)
    for s in (512, 192, 180, 32, 16):
        render(s, ring).save(os.path.join(ICONS, f"icon-{s}.png"))
    # favicon.ico (multi-size) + a maskable alias (same art, safe zone already built in)
    render(64, ring).save(os.path.join(HERE, "favicon.ico"),
                          sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    base.save(os.path.join(ICONS, "maskable-512.png"))
    print("wrote icons:", sorted(os.listdir(ICONS)), "+ favicon.ico")


if __name__ == "__main__":
    main()
