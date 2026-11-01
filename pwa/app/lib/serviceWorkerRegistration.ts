import { createLogger } from '~/lib/utils';

const logger = createLogger('serviceWorkerRegistration');

let updateReady = false;

/**
 * Whether a newer service worker took over this tab after it loaded. The tab
 * keeps running the code it loaded, so it is now behind the cached version.
 */
export function isServiceWorkerUpdateReady(): boolean {
  return updateReady;
}

// Register service worker for precaching
export default async function registerServiceWorker() {
  if ('serviceWorker' in navigator && import.meta.env.PROD) {
    // A new deploy's service worker takes over open tabs right away
    // (skipWaiting and clientsClaim in scripts/generate-sw.ts). The first
    // install also takes over this tab, which is not an update.
    let controlled = Boolean(navigator.serviceWorker.controller);
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (controlled) {
        updateReady = true;
      }
      controlled = true;
    });

    try {
      const { Workbox } = await import('workbox-window');
      const wb = new Workbox('/sw.js');

      wb.addEventListener('installed', (event) => {
        if (!event.isUpdate) {
          logger.info('Service Worker installed for first time');
        } else {
          logger.info('Service Worker updated');
        }
      });

      // Register service worker
      await wb.register();
      logger.info('Service Worker registered successfully');
    } catch (error) {
      logger.error({ error }, 'Service Worker registration failed');
    }
  }
}
