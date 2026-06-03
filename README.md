# CALIDEX — a California map

*(formerly "California's Gold"; the repo/URL keeps the `californias-gold` name.)*

An interactive map of vintage Americana across Southern California: programmatic
architecture, neon signs, motor courts, soda fountains, and old-school
institutions worth pulling over for. Each gold dot opens its name, a short note,
and a one-tap **Apple Maps directions** link.

Built from a personal Notion catalog organized by region. Live at
**https://stayontarget1.github.io/californias-gold/**

## How it works

- `data/*.md` — the catalog, one file per region (name, category, Apple Maps
  query, and a short description per place).
- `geocode.py` — parses the catalog and geocodes every place to lat/lng using
  the US Census geocoder (street addresses) with an OpenStreetMap Nominatim
  fallback (named spots like trailheads and ghost towns). Writes `places.json`.
- `index.html` — a single static page. Leaflet (vendored locally, no CDN) draws
  the dots on a dark CARTO basemap. No analytics, no trackers.

To rebuild the data after editing the catalog:

```sh
python3 geocode.py   # regenerates places.json
```

## Credits

Map tiles &copy; OpenStreetMap contributors &copy; CARTO. Geocoding by the US
Census Bureau and OpenStreetMap Nominatim.
