import React, { useEffect, useState } from 'react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import useOfflineStore from '../stores/useOfflineStore';
import { offlineSyncManager } from '../utils/offlineSync';

export default function OfflineIndicator() {
  const { isOnline } = useNetworkStatus();
  const { offlineQueue, isSyncing, syncErrors } = useOfflineStore();
  const [showNotification, setShowNotification] = useState(false);

  useEffect(() => {
    if (!isOnline) {
      setShowNotification(true);
    } else if (offlineQueue.length > 0) {
      setShowNotification(true);
    } else {
      // Hide notification after 3 seconds when back online
      const timer = setTimeout(() => setShowNotification(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, offlineQueue.length]);

  const handleManualSync = async () => {
    try {
      await offlineSyncManager.manualSync();
    } catch (error) {
      console.error('Manual sync failed:', error);
    }
  };

  if (!showNotification) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      {!isOnline && (
        <div className="bg-yellow-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
            />
          </svg>
          <div className="flex-1">
            <p className="font-semibold">You're offline</p>
            <p className="text-sm">
              {offlineQueue.length > 0
                ? `${offlineQueue.length} action(s) queued for sync`
                : 'Changes will be saved locally'}
            </p>
          </div>
        </div>
      )}

      {isOnline && isSyncing && (
        <div className="bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <svg
            className="animate-spin w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <div className="flex-1">
            <p className="font-semibold">Syncing...</p>
            <p className="text-sm">
              Syncing {offlineQueue.length} queued action(s)
            </p>
          </div>
        </div>
      )}

      {isOnline && !isSyncing && offlineQueue.length > 0 && (
        <div className="bg-orange-500 text-white px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center gap-3 mb-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div className="flex-1">
              <p className="font-semibold">Sync pending</p>
              <p className="text-sm">
                {offlineQueue.length} action(s) waiting to sync
              </p>
            </div>
          </div>
          <button
            onClick={handleManualSync}
            className="w-full bg-white text-orange-600 px-3 py-1 rounded text-sm font-medium hover:bg-orange-50 transition-colors"
          >
            Sync Now
          </button>
        </div>
      )}

      {isOnline && !isSyncing && offlineQueue.length === 0 && syncErrors.length === 0 && (
        <div className="bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="flex-1">
            <p className="font-semibold">Back online</p>
            <p className="text-sm">All changes synced</p>
          </div>
        </div>
      )}

      {syncErrors.length > 0 && (
        <div className="bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg mt-2">
          <div className="flex items-center gap-3 mb-2">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="font-semibold">Sync errors</p>
              <p className="text-sm">
                {syncErrors.length} action(s) failed to sync
              </p>
            </div>
          </div>
          <button
            onClick={handleManualSync}
            className="w-full bg-white text-red-600 px-3 py-1 rounded text-sm font-medium hover:bg-red-50 transition-colors"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
}
