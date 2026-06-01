#!/usr/bin/env python3
"""Curated visitor-center coordinates for major road-accessible parks that the
Nominatim pass missed. Places the dot at the main visitor center and routes
Apple Maps directions to it. Boat/air-only parks are intentionally left
name-based (no drivable VC)."""
import json, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "national.json")

VC = {
    "Grand Canyon National Park": (36.0586, -112.1077),       # South Rim VC
    "Yellowstone National Park": (44.4605, -110.8278),        # Old Faithful VEC
    "Zion National Park": (37.2002, -112.9869),
    "Grand Teton National Park": (43.6589, -110.7172),        # Craig Thomas DVC
    "Glacier National Park": (48.5225, -113.9886),            # Apgar VC
    "Great Smoky Mountains National Park": (35.6863, -83.5370),  # Sugarlands VC
    "Mount Rainier National Park": (46.7857, -121.7351),      # Paradise / Jackson VC
    "Crater Lake National Park": (42.8966, -122.1340),        # Steel VC
    "Bryce Canyon National Park": (37.6403, -112.1696),
    "Acadia National Park": (44.4090, -68.2480),              # Hulls Cove VC
    "Everglades National Park": (25.3955, -80.5832),          # Coe VC
    "Badlands National Park": (43.7551, -101.9530),           # Ben Reifel VC
    "Carlsbad Caverns National Park": (32.1751, -104.4440),
    "Mesa Verde National Park": (37.3088, -108.4618),
    "Lassen Volcanic National Park": (40.4369, -121.5337),    # Kohm Yah-mah-nee VC
    "Saguaro National Park": (32.1797, -110.7368),            # Rincon Mtn VC
    "Shenandoah National Park": (38.5223, -78.4360),          # Byrd VC
    "Black Canyon of the Gunnison National Park": (38.5446, -107.6915),
    "Theodore Roosevelt National Park": (46.9149, -103.5235), # South Unit VC
    "Voyageurs National Park": (48.5840, -93.1606),           # Rainy Lake VC
    "Guadalupe Mountains National Park": (31.8976, -104.8281),# Pine Springs VC
    "Hawaiʻi Volcanoes National Park": (19.4304, -155.2570),  # Kīlauea VC
    "Haleakalā National Park": (20.7607, -156.2477),
    "Pinnacles National Park": (36.4944, -121.1466),          # East / Pinnacles VC
    "Denali National Park": (63.7295, -148.8869),
    "Kenai Fjords National Park": (60.1042, -149.4419),       # Seward VC
    "New River Gorge National Park": (38.0699, -81.0769),     # Canyon Rim VC
    "Redwood National and State Parks": (41.2901, -124.1010), # Kuchel VC
    "Cuyahoga Valley National Park": (41.2636, -81.5517),     # Boston Mill VC
    "Congaree National Park": (33.8294, -80.8246),            # Harry Hampton VC
    "Indiana Dunes National Park": (41.6306, -87.0269),
    "Biscayne National Park": (25.4644, -80.3360),            # Dante Fascell VC
    "Glacier Bay National Park": (58.4553, -135.8830),        # Bartlett Cove VC
    "Wrangell–St. Elias National Park": (61.9682, -145.5450), # Copper Center VC
    "Gateway Arch National Park": (38.6247, -90.1848),
}


def main():
    data = json.load(open(OUT, encoding="utf-8"))
    n = 0
    for p in data:
        if p["n"] in VC:
            lat, lng = VC[p["n"]]
            p["lat"], p["lng"] = lat, lng
            p["u"] = "https://maps.apple.com/?q=" + f"{lat},{lng}"
            n += 1
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    miss = [k for k in VC if k not in {p["n"] for p in data}]
    print(f"applied curated VC to {n} parks")
    if miss:
        print("WARN names not found:", miss)
    # final tally
    parks = [x for x in data if x["k"] == "park"]
    with_vc = sum(1 for x in parks if x["u"].split("?q=")[1][0].isdigit())
    print(f"parks now with coordinate directions: {with_vc}/{len(parks)}")


if __name__ == "__main__":
    main()
