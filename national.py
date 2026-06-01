#!/usr/bin/env python3
"""Build national.json: every current US National Monument and National Park,
with name + coordinates from Wikidata. Dedupes the 'National Park and Preserve'
variants and repeated items. Each gets an Apple Maps link (name-based, like the
gold catalog) and a kind: 'monument' (purple) or 'park' (green)."""
import json, re, urllib.parse, urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
# instance of <class>, has coordinates, not dissolved/abolished (P576)
QTMPL = ("SELECT ?itemLabel ?lat ?lon WHERE {{ "
         "?item wdt:P31 wd:{cls}; p:P625/psv:P625 ?n. "
         "?n wikibase:geoLatitude ?lat; wikibase:geoLongitude ?lon. "
         "FILTER NOT EXISTS {{ ?item wdt:P576 ?diss }} "
         "SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"en\". }} }}")
CLASS = {"monument": "Q893775", "park": "Q34918903"}

# Official national parks missing from Wikidata's Q34918903 typing.
MANUAL_PARKS = [
    ("Lake Clark National Park", 60.9672, -153.4178),
    ("New River Gorge National Park", 38.0686, -81.0817),
    ("Virgin Islands National Park", 18.3380, -64.7490),
]


def query(cls):
    url = ENDPOINT + "?" + urllib.parse.urlencode({
        "query": QTMPL.format(cls=cls), "format": "json"})
    req = urllib.request.Request(url, headers={
        "Accept": "application/sparql-results+json",
        "User-Agent": "californias-gold-map/1.0 (personal map build)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    rows = []
    for b in data["results"]["bindings"]:
        name = b["itemLabel"]["value"]
        if re.match(r"^Q\d+$", name):      # no English label -> skip
            continue
        rows.append((name, round(float(b["lat"]["value"]), 5),
                     round(float(b["lon"]["value"]), 5)))
    return rows


def park_key(name):
    # collapse "... National Park and Preserve" -> "... National Park"
    return name.replace(" National Park and Preserve", " National Park").strip()


def apple_link(name):
    return "https://maps.apple.com/?q=" + urllib.parse.quote_plus(name)


def dedupe(rows, key_fn):
    seen_key, seen_coord, out = set(), set(), []
    for name, lat, lon in rows:
        k = key_fn(name)
        ck = (round(lat, 3), round(lon, 3))
        if k in seen_key or ck in seen_coord:
            continue
        seen_key.add(k); seen_coord.add(ck)
        out.append((key_fn(name) if key_fn is park_key else name, lat, lon))
    return out


def main():
    out = []
    parks = dedupe(query(CLASS["park"]), park_key)
    have = {park_key(n) for n, _, _ in parks}
    for name, lat, lon in MANUAL_PARKS:
        if park_key(name) not in have:
            parks.append((name, lat, lon))
    for name, lat, lon in sorted(parks):
        out.append({"n": name, "k": "park", "u": apple_link(name),
                    "lat": lat, "lng": lon})
    monuments = dedupe(query(CLASS["monument"]), lambda n: n)
    for name, lat, lon in sorted(monuments):
        out.append({"n": name, "k": "monument", "u": apple_link(name),
                    "lat": lat, "lng": lon})

    json.dump(out, open("national.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"parks: {len(parks)}  monuments: {len(monuments)}  total: {len(out)}")
    print("\nPARKS:")
    for p in [x for x in out if x["k"] == "park"]:
        print("  ", p["n"])


if __name__ == "__main__":
    main()
