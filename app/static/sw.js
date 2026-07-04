const CACHE_NAME = 'pcem-cache-v2.11';

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
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
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

self.addEventListener('push', function(event) {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body,
            icon: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
            badge: '/static/img/badge.png',
            data: {
                url: data.url || '/',
                id: data.id
            },
            actions: [
                {
                    action: 'mark-read',
                    title: 'Marquer comme lu'
                }
            ]
        };

        if (data.image) {
            options.image = data.image;
            options.icon = data.image;
        }

        if (!data.quiet) {
            options.vibrate = [200, 100, 200, 100, 200];
            options.requireInteraction = true;
        } else {
            options.silent = true;
        }
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    const notifId = event.notification.data && event.notification.data.id;
    const fetchPromise = notifId ? fetch(`/api/push/notifications/${notifId}/read`, {
        method: 'POST',
        credentials: 'same-origin'
    }) : Promise.resolve();
    
    if (event.action === 'mark-read') {
        event.waitUntil(fetchPromise);
    } else {
        if (event.notification.data && event.notification.data.url) {
            event.waitUntil(
                fetchPromise.then(() => clients.openWindow(event.notification.data.url))
            );
        } else {
            event.waitUntil(fetchPromise);
        }
    }
});
