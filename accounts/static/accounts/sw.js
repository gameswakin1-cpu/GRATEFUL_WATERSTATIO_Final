// Grateful Water Station - Service Worker
const CACHE_NAME = 'gws-customer-v1';
const STATIC_ASSETS = [
    '/static/accounts/css/styles.css',
    '/static/accounts/images/for login image.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .catch((err) => console.log('Cache install failed:', err))
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Skip API calls and non-same-origin requests
    if (!event.request.url.startsWith(self.location.origin) && 
        !event.request.url.includes('cdnjs.cloudflare.com') &&
        !event.request.url.includes('unpkg.com') &&
        !event.request.url.includes('cartocdn.com') &&
        !event.request.url.includes('openstreetmap.org')) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            // Return cached version if available
            if (cachedResponse) {
                // Fetch new version in background
                fetch(event.request)
                    .then((networkResponse) => {
                        if (networkResponse && networkResponse.status === 200) {
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, networkResponse.clone());
                            });
                        }
                    })
                    .catch(() => {});
                return cachedResponse;
            }

            // Otherwise fetch from network
            return fetch(event.request)
                .then((networkResponse) => {
                    if (!networkResponse || networkResponse.status !== 200) {
                        return networkResponse;
                    }

                    // Cache successful responses
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });

                    return networkResponse;
                })
                .catch(() => {
                    // Return offline fallback if available
                    if (event.request.destination === 'document') {
                        return caches.match('/static/accounts/offline.html');
                    }
                });
        })
    );
});

// Push notification support (for future order updates)
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'New update from Grateful Water Station',
        icon: '/static/accounts/icons/icon-192x192.png',
        badge: '/static/accounts/icons/icon-72x72.png',
        tag: 'gws-notification',
        requireInteraction: true,
        actions: [
            { action: 'open', title: 'View Order' },
            { action: 'close', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('Grateful Water Station', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.openWindow('/accounts/customer/orders/')
        );
    }
});
