import { registerSW } from 'virtual:pwa-register';

export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    const updateSW = registerSW({
      onNeedRefresh() {
        if (confirm('New content available. Reload to update?')) {
          updateSW(true);
        }
      },
      onOfflineReady() {
        console.log('App ready to work offline');
        // Notify user that app is ready for offline use
        if (window.showOfflineNotification) {
          window.showOfflineNotification();
        }
      },
      onRegistered(registration) {
        console.log('Service Worker registered:', registration);
        
        // Check for updates every hour
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);
      },
      onRegisterError(error) {
        console.error('Service Worker registration failed:', error);
      },
    });

    return updateSW;
  }
  
  return null;
}

// Queue offline actions
export async function queueOfflineAction(action) {
  const db = await openDB();
  const tx = db.transaction('offline-actions', 'readwrite');
  const store = tx.objectStore('offline-actions');
  
  await store.add({
    ...action,
    timestamp: Date.now(),
  });
  
  // Request background sync
  if ('sync' in navigator.serviceWorker.registration) {
    await navigator.serviceWorker.registration.sync.register('sync-offline-actions');
  }
}

// Get pending offline actions
export async function getPendingActions() {
  const db = await openDB();
  const tx = db.transaction('offline-actions', 'readonly');
  const store = tx.objectStore('offline-actions');
  return store.getAll();
}

// Clear synced actions
export async function clearSyncedActions() {
  const db = await openDB();
  const tx = db.transaction('offline-actions', 'readwrite');
  const store = tx.objectStore('offline-actions');
  await store.clear();
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
