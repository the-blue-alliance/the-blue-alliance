import { beforeEach, describe, expect, test, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  state: { isServer: false },
  getApps: vi.fn<() => unknown[]>(),
  initializeApp: vi.fn<(config: unknown) => unknown>(),
  initializeAuth: vi.fn<(app: unknown, deps: unknown) => unknown>(),
  connectAuthEmulator:
    vi.fn<(auth: unknown, url: string, options: unknown) => void>(),
  getDatabase: vi.fn<(app: unknown) => unknown>(),
  initializeAnalytics: vi.fn<(app: unknown, options: unknown) => unknown>(),
}));

vi.mock('@tanstack/react-query', () => ({
  get isServer() {
    return mocks.state.isServer;
  },
}));

vi.mock('firebase/app', () => ({
  getApps: mocks.getApps,
  initializeApp: mocks.initializeApp,
}));

vi.mock('firebase/auth', () => ({
  browserLocalPersistence: 'browserLocalPersistence',
  browserPopupRedirectResolver: 'browserPopupRedirectResolver',
  indexedDBLocalPersistence: 'indexedDBLocalPersistence',
  connectAuthEmulator: mocks.connectAuthEmulator,
  initializeAuth: mocks.initializeAuth,
}));

vi.mock('firebase/database', () => ({ getDatabase: mocks.getDatabase }));

vi.mock('firebase/analytics', () => ({
  initializeAnalytics: mocks.initializeAnalytics,
}));

const NEW_APP = { name: 'new-app' };
const EXISTING_APP = { name: 'existing-app' };
const AUTH = { name: 'auth' };

async function loadConfig() {
  vi.resetModules();
  return import('~/firebase/firebaseConfig');
}

describe('firebaseConfig', () => {
  beforeEach(() => {
    mocks.state.isServer = false;
    mocks.getApps.mockReturnValue([]);
    mocks.initializeApp.mockReturnValue(NEW_APP);
    mocks.initializeAuth.mockReturnValue(AUTH);
    mocks.getDatabase.mockReturnValue({ name: 'database' });
    mocks.initializeAnalytics.mockReturnValue({ name: 'analytics' });
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_HOST', '');
  });

  test('initializes a new app and browser auth', async () => {
    const { auth } = await loadConfig();

    expect(mocks.initializeApp).toHaveBeenCalledTimes(1);
    expect(mocks.initializeAuth).toHaveBeenCalledWith(NEW_APP, {
      persistence: ['indexedDBLocalPersistence', 'browserLocalPersistence'],
      popupRedirectResolver: 'browserPopupRedirectResolver',
    });
    expect(auth).toBe(AUTH);
    expect(mocks.connectAuthEmulator).not.toHaveBeenCalled();
  });

  test('reuses an app that is already initialized', async () => {
    mocks.getApps.mockReturnValue([EXISTING_APP]);

    await loadConfig();

    expect(mocks.initializeApp).not.toHaveBeenCalled();
    expect(mocks.initializeAuth).toHaveBeenCalledWith(
      EXISTING_APP,
      expect.anything(),
    );
  });

  test('connects to the auth emulator when configured', async () => {
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_HOST', 'http://localhost:9099');

    await loadConfig();

    expect(mocks.connectAuthEmulator).toHaveBeenCalledWith(
      AUTH,
      'http://localhost:9099',
      { disableWarnings: true },
    );
  });

  test('skips auth on the server', async () => {
    mocks.state.isServer = true;
    vi.stubEnv('VITE_FIREBASE_AUTH_EMULATOR_HOST', 'http://localhost:9099');

    const { auth, getAnalyticsInstance } = await loadConfig();

    expect(auth).toBeNull();
    expect(mocks.initializeAuth).not.toHaveBeenCalled();
    expect(mocks.connectAuthEmulator).not.toHaveBeenCalled();
    await expect(getAnalyticsInstance()).resolves.toBeNull();
    expect(mocks.initializeAnalytics).not.toHaveBeenCalled();
  });

  test('returns no analytics without a window', async () => {
    const { getAnalyticsInstance } = await loadConfig();
    vi.stubGlobal('window', undefined);

    await expect(getAnalyticsInstance()).resolves.toBeNull();
    expect(mocks.initializeAnalytics).not.toHaveBeenCalled();
  });

  test('creates the database once and caches it', async () => {
    const { getDatabaseInstance } = await loadConfig();

    const first = await getDatabaseInstance();
    const second = await getDatabaseInstance();

    expect(first).toEqual({ name: 'database' });
    expect(second).toBe(first);
    expect(mocks.getDatabase).toHaveBeenCalledTimes(1);
    expect(mocks.getDatabase).toHaveBeenCalledWith(NEW_APP);
  });

  test('creates analytics once, without automatic page views', async () => {
    const { getAnalyticsInstance } = await loadConfig();

    const first = await getAnalyticsInstance();
    const second = await getAnalyticsInstance();

    expect(first).toEqual({ name: 'analytics' });
    expect(second).toBe(first);
    expect(mocks.initializeAnalytics).toHaveBeenCalledTimes(1);
    expect(mocks.initializeAnalytics).toHaveBeenCalledWith(NEW_APP, {
      config: { send_page_view: false },
    });
  });
});
