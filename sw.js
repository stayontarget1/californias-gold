/* California's Gold — service worker. Caches the app shell + place data so the
   UI and all dots work offline. Map tiles are network-only (cross-origin). */
const CACHE = 'cg-v4';
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
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // tiles & cross-origin: straight to network

  e.respondWith(
    caches.match(req).then((hit) =>
      hit || fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }).catch(() => (req.mode === 'navigate' ? caches.match('./index.html') : undefined))
    )
  );
});
