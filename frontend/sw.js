const CACHE_NAME = 'ealpr-cache-v5';
const urlsToCache = [
  '/',
  '/frontend/index.css',
  '/frontend/app.js'
];

// Install Event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
            .catch(err => console.error('Cache install error:', err))
    );
});

// Fetch Event
self.addEventListener('fetch', (event) => {
    // We only want to cache GET requests for our UI, NOT API POST requests doing inference.
    if (event.request.method !== 'GET') return;
    if (event.request.url.includes('/api/')) return;
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response; // Return from cache
                }
                return fetch(event.request).then(
                  (response) => {
                    // Don't cache bad responses or opaque responses for now
                    if(!response || response.status !== 200 || response.type !== 'basic') {
                      return response;
                    }
                    var responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                      .then((cache) => {
                        cache.put(event.request, responseToCache);
                      });
                    return response;
                  }
                );
            })
    );
});

// Activate Event - Clean up old caches
self.addEventListener('activate', (event) => {
    const cacheAllowlist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheAllowlist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
