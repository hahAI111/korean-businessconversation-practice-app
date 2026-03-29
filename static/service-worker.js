const CACHE_NAME = 'kbc-cache-v3';
const STATIC_ASSETS = [
  '/static/index.html',
  '/static/chat.html',
  '/static/vocab.html',
  '/static/progress.html',
  '/static/style.css?v=3',
  '/static/app.js?v=3',
  '/static/manifest.json',
  '/static/offline.html',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Install: precache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: caching strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // API / WebSocket / MCP: no cache, network only
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/ws/') ||
      url.pathname.startsWith('/mcp/') ||
      url.pathname === '/health' ||
      url.pathname.startsWith('/register') ||
      url.pathname.startsWith('/login')) {
    return;
  }

  // Static resources: Cache First
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // Cache new static resources
        if (response.ok && url.pathname.startsWith('/static/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        // Offline fallback: return offline.html
        if (event.request.destination === 'document') {
          return caches.match('/static/offline.html');
        }
      });
    })
  );
});
