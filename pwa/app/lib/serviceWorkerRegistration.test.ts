import { beforeEach, describe, expect, test, vi } from 'vitest';

import registerServiceWorker from '~/lib/serviceWorkerRegistration';

type InstalledListener = (event: { isUpdate?: boolean }) => void;

const mocks = vi.hoisted(() => ({
  logger: {
    info: vi.fn<(message: string) => void>(),
    error: vi.fn<(bindings: object, message: string) => void>(),
  },
  register: vi.fn<() => Promise<unknown>>(),
  scriptUrls: [] as string[],
  listeners: new Map<string, InstalledListener>(),
}));

vi.mock('~/lib/logger', () => ({
  createLogger: () => mocks.logger,
}));

vi.mock('workbox-window', () => ({
  Workbox: class {
    constructor(scriptUrl: string) {
      mocks.scriptUrls.push(scriptUrl);
    }
    addEventListener(type: string, listener: InstalledListener) {
      mocks.listeners.set(type, listener);
    }
    register() {
      return mocks.register();
    }
  },
}));

describe('registerServiceWorker', () => {
  beforeEach(() => {
    mocks.scriptUrls.length = 0;
    mocks.listeners.clear();
    mocks.register.mockResolvedValue(undefined);
    vi.stubEnv('PROD', true);
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: {},
    });
  });

  test('does nothing outside production', async () => {
    vi.stubEnv('PROD', false);

    await registerServiceWorker();

    expect(mocks.register).not.toHaveBeenCalled();
  });

  test('does nothing when the browser has no service worker support', async () => {
    Reflect.deleteProperty(navigator, 'serviceWorker');

    await registerServiceWorker();

    expect(mocks.register).not.toHaveBeenCalled();
  });

  test('registers the precaching service worker', async () => {
    await registerServiceWorker();

    expect(mocks.scriptUrls).toEqual(['/sw.js']);
    expect(mocks.register).toHaveBeenCalledOnce();
  });

  test('logs the first install', async () => {
    await registerServiceWorker();

    mocks.listeners.get('installed')?.({ isUpdate: false });

    expect(mocks.logger.info).toHaveBeenCalledWith(
      'Service Worker installed for first time',
    );
  });

  test('logs an update to an existing install', async () => {
    await registerServiceWorker();

    mocks.listeners.get('installed')?.({ isUpdate: true });

    expect(mocks.logger.info).toHaveBeenCalledWith('Service Worker updated');
  });

  test('logs a failed registration instead of throwing', async () => {
    const error = new Error('offline');
    mocks.register.mockRejectedValue(error);

    await registerServiceWorker();

    expect(mocks.logger.error).toHaveBeenCalledWith(
      { error },
      'Service Worker registration failed',
    );
  });
});
