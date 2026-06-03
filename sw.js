/* CALIDEX — service worker.
   - App shell + place data are precached so the UI and all dots work offline.
   - Map tiles are runtime-cached as you view them (cache-first, capped), so any
     area you've already panned over also works offline. */
const CACHE = 'cg-v5';
const TILE_CACHE = 'cg-tiles-v1';
const TILE_MAX = 1200; // ~ how many map tiles to keep offline
const SHELL = [
  './', './index.html',
  './vendor/leaflet.js', './vendor/leaflet.css',
  './places.json', './national.json',
  './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './favicon.ico'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE && k !== TILE_CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

async function trim(cache, max) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

async function tileFirst(req) {
  const cache = await caches.open(TILE_CACHE);
  const hit = await cache.match(req);
  if (hit) return hit;
  try {
    const res = await fetch(req);
    if (res && (res.ok || res.type === 'opaque')) {
      cache.put(req, res.clone()).then(() => trim(cache, TILE_MAX)).catch(() => {});
    }
    return res;
  } catch (err) {
    return hit || Response.error();
  }
}

async function shellFirst(req) {
  const hit = await caches.match(req);
  if (hit) return hit;
  try {
    const res = await fetch(req);
    const copy = res.clone();
    caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
    return res;
  } catch (err) {
    return req.mode === 'navigate' ? caches.match('./index.html') : Response.error();
  }
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.hostname.endsWith('basemaps.cartocdn.com')) {
    e.respondWith(tileFirst(req));
  } else if (url.origin === location.origin) {
    e.respondWith(shellFirst(req));
  }
});
