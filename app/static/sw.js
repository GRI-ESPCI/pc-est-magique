const CACHE_NAME = 'pcem-cache-v2';

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async (cache) => {
            const urlsToCache = [
                '/static/site.webmanifest',
                '/static/img/gri_192.png',
                '/static/img/gri_512.png'
            ];
            for (const url of urlsToCache) {
                try {
                    await cache.add(url);
                } catch (e) {
                    console.warn('Failed to cache', url, e);
                }
            }
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Only intercept GET requests
    if (event.request.method !== 'GET') return;

    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
