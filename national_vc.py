#!/usr/bin/env python3
"""Improve national.json directions: for each park/monument, find its visitor
center via Nominatim, validate it's near the site, and if so move the dot there
and point Apple Maps directions at it (coordinate-based). Otherwise leave the
name-based link (Apple resolves well-known park names fine)."""
import json, math, os, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "national.json")
CACHE = "/tmp/vc_cache.json"
NEAR_DEG = 1.2  # visitor center must be within ~80 mi of the site


def nominatim(q):
    qs = urllib.parse.urlencode({"q": q, "format": "json", "limit": 3,
                                 "countrycodes": "us", "addressdetails": 0})
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?" + qs,
        headers={"User-Agent": "californias-gold-map/1.0 (personal map build)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        print("  err", e); return []


def main():
    data = json.load(open(OUT, encoding="utf-8"))
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    moved = 0
    for i, p in enumerate(data):
        if p["k"] not in ("park", "monument"):
            continue
        name = p["n"]
        if name in cache:
            vc = cache[name]
        else:
            vc = None
            for cand in [name + " Visitor Center", name + " visitor center"]:
                for row in nominatim(cand):
                    lat, lon = float(row["lat"]), float(row["lon"])
                    if abs(lat - p["lat"]) <= NEAR_DEG and abs(lon - p["lng"]) <= NEAR_DEG:
                        vc = [round(lat, 5), round(lon, 5)]; break
                time.sleep(1.05)
                if vc:
                    break
            cache[name] = vc
            if i % 10 == 0:
                json.dump(cache, open(CACHE, "w"))
            print(f"[{i+1}/{len(data)}] {'VC ' if vc else '-- '}{name[:46]}", flush=True)
        if vc:
            p["lat"], p["lng"] = vc
            p["u"] = "https://maps.apple.com/?q=" + f"{vc[0]},{vc[1]}"
            moved += 1
    json.dump(cache, open(CACHE, "w"))
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\nvisitor centers applied: {moved}/{len(data)}")


if __name__ == "__main__":
    main()
