// ForecastIQ Service Worker — basic caching for offline support
const CACHE = 'forecastiq-v1';
const STATIC = [
    '/',
    '/css/styles.css',
    '/js/api.js',
    '/js/charts.js',
    '/js/extras.js',
    '/js/backtest.js',
    '/js/model_race.js',
    '/js/forecast.js',
    '/js/anomaly.js',
    '/js/scenario.js',
    '/js/app.js',
];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE).then(c => c.addAll(STATIC)).catch(() => {})
    );
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    // Only cache GET, not API calls
    if (e.request.method !== 'GET' || e.request.url.includes('/api/')) return;
    e.respondWith(
        caches.match(e.request).then(cached => cached || fetch(e.request))
    );
});
