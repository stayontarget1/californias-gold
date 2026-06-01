#!/usr/bin/env python3
"""Parse the catalog markdown, geocode every place, emit places.json.

Strategy: US Census onelineaddress geocoder first (fast, no rate limit, great
for street addresses). Named POIs (parks, trailheads, ghost towns) that Census
can't match fall back to OpenStreetMap Nominatim (1 req/sec, polite UA).
Results are cached to geocache.json so re-runs are cheap.
"""
import glob, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE_PATH = os.path.join(HERE, "geocache.json")
OUT_PATH = os.path.join(HERE, "places.json")

ENTRY_RE = re.compile(
    r'^- \[(?P<name>.+?)\]\((?P<url>https://maps\.apple\.com/\?q=[^)]+)\)\s*'
    r'(?:\*\((?P<desc>.*)\)\*)?\s*$'
)

# Rough CA bounding box to sanity-check / bias results.
CA_BBOX = (-124.5, 32.3, -114.0, 42.1)  # west, south, east, north


def in_ca(lat, lon):
    w, s, e, n = CA_BBOX
    return s <= lat <= n and w <= lon <= e


def parse_catalog():
    places = []
    seen = set()
    for path in sorted(glob.glob(os.path.join(DATA, "*.md"))):
        region = category = None
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("# REGION:"):
                    region = line.split(":", 1)[1].strip()
                elif line.startswith("## "):
                    category = line[3:].strip()
                elif line.startswith("- ["):
                    m = ENTRY_RE.match(line)
                    if not m:
                        print("UNPARSED:", line, file=sys.stderr)
                        continue
                    name = m.group("name").strip()
                    url = m.group("url").strip()
                    desc = (m.group("desc") or "").strip()
                    q = url.split("?q=", 1)[1]
                    key = (name, q)
                    if key in seen:
                        continue
                    seen.add(key)
                    places.append({
                        "name": name,
                        "region": region,
                        "category": category,
                        "desc": desc,
                        "query": q,
                        "url": url,
                    })
    return places


def http_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def census_geocode(addr):
    base = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    qs = urllib.parse.urlencode({
        "address": addr,
        "benchmark": "Public_AR_Current",
        "format": "json",
    })
    try:
        data = http_json(base + "?" + qs, timeout=20)
    except Exception as e:
        print("  census err:", e, file=sys.stderr)
        return None
    matches = data.get("result", {}).get("addressMatches", [])
    if not matches:
        return None
    c = matches[0]["coordinates"]
    return (round(c["y"], 6), round(c["x"], 6))  # lat, lon


def nominatim_geocode(addr):
    base = "https://nominatim.openstreetmap.org/search"
    qs = urllib.parse.urlencode({
        "q": addr,
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    })
    try:
        data = http_json(base + "?" + qs,
                         headers={"User-Agent": "californias-gold-map/1.0 (personal map build)"},
                         timeout=25)
    except Exception as e:
        print("  nominatim err:", e, file=sys.stderr)
        return None
    if not data:
        return None
    return (round(float(data[0]["lat"]), 6), round(float(data[0]["lon"]), 6))


def main():
    places = parse_catalog()
    print(f"Parsed {len(places)} unique places")

    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            cache = json.load(f)

    fails = []
    for i, p in enumerate(places):
        q = p["query"]
        if q in cache and cache[q]:
            latlon = cache[q]
        else:
            addr = urllib.parse.unquote_plus(q)
            latlon = census_geocode(addr)
            src = "census"
            if not latlon or not in_ca(*latlon):
                # Census missed (or returned out-of-CA) -> Nominatim
                nl = nominatim_geocode(addr)
                time.sleep(1.05)  # Nominatim politeness
                if nl and in_ca(*nl):
                    latlon = nl
                    src = "nominatim"
                elif latlon and in_ca(*latlon):
                    src = "census"
                else:
                    latlon = nl or latlon
                    src = "nominatim?" if nl else "none"
            cache[q] = latlon
            if i % 25 == 0:
                with open(CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            print(f"[{i+1}/{len(places)}] {src:10} {p['name'][:40]}", flush=True)
        if latlon:
            p["lat"], p["lng"] = latlon
        else:
            fails.append(p["name"])

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f)

    good = [p for p in places if "lat" in p]
    out = []
    for p in good:
        out.append({
            "n": p["name"],
            "r": p["region"],
            "c": p["category"],
            "d": p["desc"],
            "u": p["url"],
            "lat": p["lat"],
            "lng": p["lng"],
        })
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"\nGeocoded {len(good)}/{len(places)} -> {OUT_PATH}")
    if fails:
        print(f"FAILED ({len(fails)}):")
        for n in fails:
            print("  -", n)


if __name__ == "__main__":
    main()
