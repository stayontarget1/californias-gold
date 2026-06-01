#!/usr/bin/env python3
"""Second pass: geocode the places that failed the first run.

These are named natural/POI features (trailheads, ghost towns, monuments).
Query Nominatim with several candidate strings, biased to a California viewbox,
and accept the first result inside the CA bounding box. Merge into places.json.
"""
import json, os, re, time, urllib.parse, urllib.request
import geocode  # reuse parser + helpers

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "places.json")
CA_BBOX = geocode.CA_BBOX  # west, south, east, north


def nominatim(q):
    base = "https://nominatim.openstreetmap.org/search"
    w, s, e, n = CA_BBOX
    qs = urllib.parse.urlencode({
        "q": q, "format": "json", "limit": 5,
        "viewbox": f"{w},{n},{e},{s}",  # x1,y1,x2,y2
        "bounded": 1,
    })
    req = urllib.request.Request(base + "?" + qs,
        headers={"User-Agent": "californias-gold-map/1.0 (personal map build)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as ex:
        print("  err:", ex)
        return None
    for row in data:
        lat, lon = round(float(row["lat"]), 6), round(float(row["lng" if False else "lon"]), 6)
        if geocode.in_ca(lat, lon):
            return (lat, lon)
    return None


def clean_name(name):
    n = re.sub(r"\([^)]*\)", "", name)      # drop parentheticals
    n = re.split(r"\s*/\s*", n)[0]            # take part before " / "
    return n.strip(" –-—\"")


# region -> anchor words to append for disambiguation
ANCHOR = {
    "Joshua Tree Area": "Joshua Tree National Park, California",
    "395 / Eastern Sierra": "California",
    "Antelope Valley": "Los Angeles County, California",
}


def candidates(p):
    orig = urllib.parse.unquote_plus(p["query"])
    cn = clean_name(p["name"])
    anchor = ANCHOR.get(p["region"], "California")
    out = [orig, f"{cn}, {anchor}", f"{cn}, California"]
    # also try cleaned name + the locality token from the query (last words before CA)
    toks = orig.replace("+", " ").rsplit(" CA", 1)[0].split()
    if len(toks) >= 2:
        out.append(f"{cn}, {' '.join(toks[-2:])}, California")
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


def main():
    placed = json.load(open(OUT_PATH, encoding="utf-8"))
    have = {(p["n"], p["u"]) for p in placed}
    allp = geocode.parse_catalog()
    missing = [p for p in allp if (p["name"], p["url"]) not in have]
    print(f"{len(missing)} missing")

    fixed = 0
    for p in missing:
        latlon = None
        for c in candidates(p):
            latlon = nominatim(c)
            time.sleep(1.05)
            if latlon:
                tag = c
                break
        if latlon:
            placed.append({"n": p["name"], "r": p["region"], "c": p["category"],
                           "d": p["desc"], "u": p["url"], "lat": latlon[0], "lng": latlon[1]})
            fixed += 1
            print(f"OK  {p['name'][:38]:38} -> {latlon}  [{tag[:40]}]")
        else:
            print(f"XX  {p['name']}  (still unmatched)")

    json.dump(placed, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\nFixed {fixed}/{len(missing)}; total now {len(placed)}")


if __name__ == "__main__":
    main()
