/**
 * MCAT Mastery â€” Service Worker for Offline Mode
 * 
 * Caches all static assets (HTML, CSS, JS, fonts, lore JSON) 
 * and mission data for offline study sessions.
 * 
 * Strategy:
 * - Static assets: Cache-first (install time)
 * - API (Firestore): Network-first with cache fallback
 * - Mission data: Cache on first fetch, serve from cache if offline
 */

const CACHE_NAME   = 'mcat-mastery-v5';
const STATIC_CACHE = 'mcat-static-v5';
const DATA_CACHE   = 'mcat-data-v5';

// Static assets to pre-cache on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/main.css',
    '/css/planets.css',
    '/css/animations.css',
    '/css/screens.css',
    '/js/app.js',
    '/js/firebase.js',
    '/js/data/game-data.js',
    '/js/data/player.js',
    '/js/systems/tts.js',
    '/js/systems/fog.js',
    '/js/systems/energy.js',
    '/js/systems/streaks.js',
    '/js/systems/resonance.js',
    '/js/systems/creatures.js',
    '/js/systems/leaderboard.js',
    '/js/engines/game-engines.js',
    '/js/screens/dashboard.js',
    '/js/screens/planet-map.js',
    '/js/screens/mission.js',
    '/js/screens/character-select.js',
    '/js/screens/profile.js',
    '/js/screens/notebook.js',
    '/js/screens/shop.js',
    '/js/screens/calendar.js',
    '/js/screens/bridge.js',
    '/js/screens/settings.js',
    '/js/systems/mobile.js',
    '/manifest.json',
    '/icons/icon-192.png',
    '/icons/icon-512.png',
];

// Install â€” pre-cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(STATIC_CACHE).then(async (cache) => {
            console.log('[SW] Pre-caching static assets (network-first)');
            // Fetch each asset from network (bypass HTTP cache) to avoid stale content
            const requests = STATIC_ASSETS.map(url =>
                fetch(url, { cache: 'reload' })
                    .then(resp => resp.ok ? cache.put(url, resp) : Promise.resolve())
                    .catch(() => {/* offline â€” skip */})
            );
            return Promise.all(requests);
        }).then(() => self.skipWaiting())
    );
});

// Activate â€” clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(key => key !== STATIC_CACHE && key !== DATA_CACHE)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch â€” routing strategy
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Skip external URLs except Google Fonts & Firebase
    if (!url.origin.includes(self.location.origin) &&
        !url.hostname.includes('fonts.googleapis.com') &&
        !url.hostname.includes('fonts.gstatic.com')) {
        return;
    }
    
    // Google Fonts â€” cache-first
    if (url.hostname.includes('fonts.googleapis.com') || 
        url.hostname.includes('fonts.gstatic.com')) {
        event.respondWith(_cacheFirst(event.request, STATIC_CACHE));
        return;
    }
    
    // Firestore / API calls â€” network-first
    if (url.hostname.includes('firestore.googleapis.com') ||
        url.hostname.includes('firebase')) {
        event.respondWith(_networkFirst(event.request, DATA_CACHE));
        return;
    }
    
    // Static assets: HTML/JS/CSS use network-first so updates appear immediately
    const pathname = url.pathname;
    if (pathname.endsWith('.html') || pathname === '/' ||
        pathname.endsWith('.js') || pathname.endsWith('.css')) {
        event.respondWith(_networkFirst(event.request, STATIC_CACHE));
        return;
    }

    // Images, icons, other assets — cache-first
    event.respondWith(_cacheFirst(event.request, STATIC_CACHE));
});

// â”€â”€â”€ Caching Strategies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function _cacheFirst(request, cacheName) {
    const cached = await caches.match(request);
    if (cached) return cached;
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (e) {
        // If offline and not cached, return offline page
        return _offlineFallback();
    }
}

async function _networkFirst(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (e) {
        const cached = await caches.match(request);
        if (cached) return cached;
        return _offlineFallback();
    }
}

function _offlineFallback() {
    return new Response(
        `<html><body style="background:#0D1117;color:#E6EDF3;font-family:Nunito,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center">
            <div>
                <h1>ðŸ“¡ Connection Lost</h1>
                <p>You're offline, Commander. Your cached study data is still available.</p>
                <p>Reconnect to sync your progress.</p>
            </div>
        </body></html>`,
        { headers: { 'Content-Type': 'text/html' } }
    );
}

// â”€â”€â”€ Background Sync (for when we come back online) â”€â”€â”€â”€â”€

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-progress') {
        event.waitUntil(_syncPlayerProgress());
    }
});

async function _syncPlayerProgress() {
    // The main app will handle actual sync via Firebase
    // This just notifies the app that we're back online
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
        client.postMessage({ type: 'ONLINE_SYNC', timestamp: Date.now() });
    });
}

// â”€â”€â”€ Cache mission data for offline study â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

self.addEventListener('message', (event) => {
    if (event.data.type === 'CACHE_MISSION_DATA') {
        const { url, data } = event.data;
        caches.open(DATA_CACHE).then(cache => {
            const response = new Response(JSON.stringify(data), {
                headers: { 'Content-Type': 'application/json' }
            });
            cache.put(url, response);
        });
    }
    
    if (event.data.type === 'CLEAR_DATA_CACHE') {
        caches.delete(DATA_CACHE);
    }
});
