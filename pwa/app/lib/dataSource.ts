// Dev-only switch for pointing the read API client at the local dev stack
// instead of production. Persisted in localStorage; applied at client
// configuration time in __root.tsx, so changing it requires a reload.

export type DataSource = 'prod' | 'local';

const STORAGE_KEY = 'tba-data-source';

export const LOCAL_API_BASE_URL = 'http://localhost:8080/api/v3';

// The deterministic read key the local dev stack auto-creates via
// /local/bootstrap (DEV_AUTH_KEY in backend/web/local/blueprint.py)
export const LOCAL_API_AUTH_KEY = 'tba-dev-key';

interface StorageLike {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

function defaultStorage(): StorageLike | undefined {
  return typeof window === 'undefined' ? undefined : window.localStorage;
}

/** The selected data source. Always 'prod' outside dev builds and on the server. */
export function getDataSource(
  storage: StorageLike | undefined = defaultStorage(),
): DataSource {
  if (!import.meta.env.DEV || !storage) return 'prod';
  return storage.getItem(STORAGE_KEY) === 'local' ? 'local' : 'prod';
}

export function setDataSource(
  source: DataSource,
  storage: StorageLike | undefined = defaultStorage(),
): void {
  storage?.setItem(STORAGE_KEY, source);
}

/** Whether reads should hit the local dev stack (dev builds only). */
export function isLocalDataSource(): boolean {
  return import.meta.env.DEV && getDataSource() === 'local';
}
