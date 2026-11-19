// Grateful Water Station - Rider Service Worker
const CACHE_NAME = 'gws-rider-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/static/accounts/css/styles.css',
  '/static/accounts/css/home.css',
  '/static/accounts/js/home.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith('http')) return;

  // API requests - network first, then cache
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/rider/update-location/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone and cache successful responses
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          return caches.match(request);
        })
    );
    return;
  }

  // Static assets - cache first, then network
  if (request.destination === 'style' || 
      request.destination === 'script' || 
      request.destination === 'font' ||
      request.destination === 'image') {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) {
          // Return cached version but fetch update in background
          fetch(request).then((response) => {
            if (response.status === 200) {
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(request, response);
              });
            }
          }).catch(() => {});
          return cached;
        }
        
        // Not in cache, fetch from network
        return fetch(request).then((response) => {
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // HTML pages - network first with offline fallback
  if (request.mode === 'navigate' || request.destination === 'document') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful page loads
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Try to serve from cache
          return caches.match(request).then((cached) => {
            if (cached) {
              return cached;
            }
            // If not in cache, return a simple offline page
            return new Response(
              `<!DOCTYPE html>
<html>
<head>
  <title>Offline - GWS Rider</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f4f8fc; }
    .offline-container { text-align: center; padding: 2rem; }
    .offline-icon { font-size: 4rem; margin-bottom: 1rem; }
    h1 { color: #1a8ad4; margin-bottom: 0.5rem; }
    p { color: #64748b; }
    .retry-btn { background: #1a8ad4; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 1rem; cursor: pointer; margin-top: 1rem; }
  </style>
</head>
<body>
  <div class="offline-container">
    <div class="offline-icon">📴</div>
    <h1>You're Offline</h1>
    <p>Please check your internet connection and try again.</p>
    <button class="retry-btn" onclick="window.location.reload()">Retry</button>
  </div>
</body>
</html>`,
              {
                headers: { 'Content-Type': 'text/html' },
                status: 503,
                statusText: 'Service Unavailable'
              }
            );
          });
        })
    );
    return;
  }

  // Default: try cache, then network
  event.respondWith(
    caches.match(request).then((cached) => {
      return cached || fetch(request);
    })
  );
});

// Background sync for delivery updates
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-deliveries') {
    event.waitUntil(syncDeliveries());
  }
});

async function syncDeliveries() {
  // Get pending deliveries from IndexedDB and sync when online
  // This would need to be implemented with IndexedDB
  console.log('[SW] Syncing pending deliveries...');
}

// Push notifications support
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'New delivery assigned',
      icon: '/static/accounts/icons/icon-192x192.png',
      badge: '/static/accounts/icons/icon-72x72.png',
      tag: data.tag || 'delivery',
      requireInteraction: true,
      actions: [
        {
          action: 'view',
          title: 'View'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'GWS Rider', options)
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/accounts/rider/dashboard/')
    );
  }
});
