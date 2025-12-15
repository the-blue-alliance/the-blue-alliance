import { createLogger } from '~/lib/utils';

const logger = createLogger('serviceWorkerRegistration');

// Register service worker for precaching
export default async function registerServiceWorker() {
  if ('serviceWorker' in navigator && import.meta.env.PROD) {
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
