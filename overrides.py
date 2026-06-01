#!/usr/bin/env python3
"""Apply curated coordinates for the iconic named features that the geocoders
missed or mismatched (same-name collisions). Coordinates are approximate visual
placements; each place's Apple Maps directions link uses its real address."""
import json, os
import geocode

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "places.json")

# name -> (lat, lng)
OVERRIDES = {
    "Chantry Flat / Sturtevant Falls": (34.1958, -118.0227),
    "The Beverly Hills Sign & Electric Fountain": (34.0672, -118.4004),
    "Angel's Gate Lighthouse": (33.7156, -118.2517),
    "Pioneer Boulevard Little India": (33.8686, -118.0808),
    "Big Rock Creek Recreation Area": (34.3897, -117.8472),
    "Mammoth Earthquake Fault": (37.6470, -119.0130),
    "Alabama Hills BLM / Movie Road": (36.6060, -118.1150),
    "Whoa Nellie Deli at Tioga Gas Mart": (37.9578, -119.1186),
    "Oasis of Murals (29 Palms Mural Project)": (34.1356, -116.0540),
    "Hicksville Trailer Palace": (34.0833, -116.3000),
    "Lost Horse Mine Trail": (33.9479, -116.1640),
    "MazAmar Art Pottery": (34.1593, -116.4936),
    "Saddleback Inn at Lake Arrowhead": (34.2480, -117.1890),
    "Spreckels Organ Pavilion": (32.7197, -117.1525),
    # fix same-name collisions from the CA-wide viewbox pass:
    "Hidden Valley": (34.0114, -116.1680),   # Joshua Tree NP, not Santa Monica Mtns
    "Skull Rock": (33.9931, -116.0710),       # Joshua Tree NP, not Topanga
    "Topaz Lake": (38.6790, -119.5180),       # CA/NV border, Coleville
}


def main():
    placed = json.load(open(OUT, encoding="utf-8"))
    by_name = {p["n"]: p for p in placed}
    allp = {p["name"]: p for p in geocode.parse_catalog()}

    updated = added = 0
    for name, (lat, lng) in OVERRIDES.items():
        if name in by_name:
            by_name[name]["lat"] = lat
            by_name[name]["lng"] = lng
            updated += 1
        elif name in allp:
            p = allp[name]
            placed.append({"n": p["name"], "r": p["region"], "c": p["category"],
                           "d": p["desc"], "u": p["url"], "lat": lat, "lng": lng})
            added += 1
        else:
            print("WARN: override name not found in catalog:", name)

    json.dump(placed, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"updated {updated}, added {added}, total now {len(placed)}")

    # report any catalog places still missing from places.json
    have = {p["n"] for p in placed}
    missing = [n for n in allp if n not in have]
    print(f"still missing ({len(missing)}):")
    for n in missing:
        print("  -", n)


if __name__ == "__main__":
    main()
