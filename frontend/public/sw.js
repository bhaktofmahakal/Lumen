/* eslint-disable no-restricted-globals */
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate, NetworkFirst, CacheFirst } from 'workbox-strategies';
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { ExpirationPlugin } from 'workbox-expiration';

// Precache static assets injected by build process
precacheAndRoute(self.__WB_MANIFEST || []);

// Cache API responses with network-first strategy
const apiCachePlugin = new ExpirationPlugin({
  maxEntries: 100,
  maxAgeSeconds: 60 * 60, // 1 hour
});

// Background sync for failed requests
const bgSyncPlugin = new BackgroundSyncPlugin('api-queue', {
  maxRetentionTime: 24 * 60, // Retry for up to 24 hours
});

// API routes - Network first with background sync
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      apiCachePlugin,
      bgSyncPlugin,
      {
        cacheWillUpdate: async ({ response }) => {
          // Only cache successful responses
          if (response && response.status === 200) {
            return response;
          }
          return null;
        },
      },
    ],
  })
);

// Document uploads - Queue for background sync
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/documents/upload'),
  new NetworkFirst({
    cacheName: 'upload-cache',
    plugins: [bgSyncPlugin],
  }),
  'POST'
);

// Chat messages - Queue for background sync
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/chat/'),
  new NetworkFirst({
    cacheName: 'chat-cache',
    plugins: [bgSyncPlugin],
  }),
  'POST'
);

// Static assets - Cache first
registerRoute(
  ({ request }) => request.destination === 'style' ||
                   request.destination === 'script' ||
                   request.destination === 'worker',
  new CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 60,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
);

// Images - Cache first with expiration
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
);

// Fonts - Cache first
registerRoute(
  ({ request }) => request.destination === 'font',
  new CacheFirst({
    cacheName: 'fonts',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 20,
        maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
      }),
    ],
  })
);

// Documents (PDFs) - Stale while revalidate
registerRoute(
  ({ url }) => url.pathname.match(/\.(pdf|doc|docx)$/),
  new StaleWhileRevalidate({
    cacheName: 'documents',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
      }),
    ],
  })
);

// Handle background sync events
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-actions') {
    event.waitUntil(syncOfflineActions());
  }
});

async function syncOfflineActions() {
  // Get queued actions from IndexedDB
  const db = await openDB();
  const actions = await db.getAll('offline-actions');
  
  for (const action of actions) {
    try {
      await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body,
      });
      
      // Remove from queue on success
      await db.delete('offline-actions', action.id);
    } catch (error) {
      console.error('Failed to sync action:', error);
      // Keep in queue for next sync
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('offline-sync-db', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline-actions')) {
        db.createObjectStore('offline-actions', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(self.clients.claim());
});

// Message event for manual cache updates
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
