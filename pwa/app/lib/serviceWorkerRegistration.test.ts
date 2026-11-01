import { beforeEach, describe, expect, test, vi } from 'vitest';

import registerServiceWorker, {
  isServiceWorkerUpdateReady,
} from '~/lib/serviceWorkerRegistration';

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

function stubServiceWorkerContainer(controller: object | null) {
  const container = Object.assign(new EventTarget(), { controller });
  Object.defineProperty(navigator, 'serviceWorker', {
    configurable: true,
    value: container,
  });
  return container;
}

describe('registerServiceWorker', () => {
  beforeEach(() => {
    mocks.scriptUrls.length = 0;
    mocks.listeners.clear();
    mocks.register.mockResolvedValue(undefined);
    vi.stubEnv('PROD', true);
    stubServiceWorkerContainer(null);
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

describe('isServiceWorkerUpdateReady', () => {
  // The update flag is module state, so load a fresh copy for each test.
  async function loadFreshModule() {
    vi.resetModules();
    return import('~/lib/serviceWorkerRegistration');
  }

  beforeEach(() => {
    mocks.register.mockResolvedValue(undefined);
    vi.stubEnv('PROD', true);
  });

  test('is false before any new service worker takes over', () => {
    expect(isServiceWorkerUpdateReady()).toBe(false);
  });

  test('is true once a new service worker takes over a controlled tab', async () => {
    const container = stubServiceWorkerContainer({ state: 'activated' });
    const module = await loadFreshModule();
    await module.default();

    container.dispatchEvent(new Event('controllerchange'));

    expect(module.isServiceWorkerUpdateReady()).toBe(true);
  });

  test('is false after the first install takes over the tab', async () => {
    const container = stubServiceWorkerContainer(null);
    const module = await loadFreshModule();
    await module.default();

    container.dispatchEvent(new Event('controllerchange'));

    expect(module.isServiceWorkerUpdateReady()).toBe(false);
  });

  test('is true once a deploy takes over after the first install', async () => {
    const container = stubServiceWorkerContainer(null);
    const module = await loadFreshModule();
    await module.default();
    container.dispatchEvent(new Event('controllerchange'));

    container.dispatchEvent(new Event('controllerchange'));

    expect(module.isServiceWorkerUpdateReady()).toBe(true);
  });
});
