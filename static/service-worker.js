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

// Install: 预缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: 清理旧版缓存
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

// Fetch: 缓存策略
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 跳过非 GET 请求
  if (event.request.method !== 'GET') return;

  // API / WebSocket / MCP: 不缓存，直接走网络
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/ws/') ||
      url.pathname.startsWith('/mcp/') ||
      url.pathname === '/health' ||
      url.pathname.startsWith('/register') ||
      url.pathname.startsWith('/login')) {
    return;
  }

  // 静态资源: Cache First
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        // 缓存新的静态资源
        if (response.ok && url.pathname.startsWith('/static/')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        // 离线降级: 返回 offline.html
        if (event.request.destination === 'document') {
          return caches.match('/static/offline.html');
        }
      });
    })
  );
});
