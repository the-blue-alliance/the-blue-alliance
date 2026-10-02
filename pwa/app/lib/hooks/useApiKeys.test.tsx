import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type {
  ApiReadKeyMessage,
  ApiWriteKeyMessage,
} from '~/api/tba/mobile/types.gen';
import { useApiKeys } from '~/lib/hooks/useApiKeys';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
  listApiKeys: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
  addApiReadKey: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
  deleteApiReadKey: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/api/tba/mobile/sdk.gen', () => ({
  listApiKeys: mocks.listApiKeys,
  addApiReadKey: mocks.addApiReadKey,
  deleteApiReadKey: mocks.deleteApiReadKey,
}));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };

const READ_KEY_A: ApiReadKeyMessage = {
  key: 'read-a',
  description: 'Scouting',
};
const READ_KEY_B: ApiReadKeyMessage = { key: 'read-b', description: 'Stats' };
const WRITE_KEY: ApiWriteKeyMessage = {
  auth_id: 'auth-1',
  secret: 'secret',
  description: 'Event sync',
  event_keys: ['2026casj'],
  auth_types: ['event matches'],
};

function renderApiKeys() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  return renderHook(() => useApiKeys(), { wrapper: Wrapper });
}

async function renderLoaded() {
  const hook = renderApiKeys();
  await waitFor(() => expect(hook.result.current.isLoading).toBe(false));
  return hook;
}

describe('useApiKeys', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mocks.listApiKeys.mockResolvedValue({
      data: { read_keys: [READ_KEY_A], write_keys: [WRITE_KEY] },
    });
  });

  test('does not load keys when signed out, and refuses writes', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const { result } = renderApiKeys();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(mocks.listApiKeys).not.toHaveBeenCalled();

    await expect(result.current.addReadKey('New key')).rejects.toThrow(
      'User not authenticated',
    );
    await expect(result.current.deleteReadKey('read-a')).rejects.toThrow(
      'User not authenticated',
    );
    expect(mocks.addApiReadKey).not.toHaveBeenCalled();
    expect(mocks.deleteApiReadKey).not.toHaveBeenCalled();
  });

  test('loads read and write keys with the user token', async () => {
    const { result } = await renderLoaded();

    expect(mocks.listApiKeys).toHaveBeenCalledWith({ auth: 'token-1' });
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
  });

  test('falls back to empty lists when the response omits them', async () => {
    mocks.listApiKeys.mockResolvedValue({ data: {} });
    const { result } = await renderLoaded();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('returns empty lists when loading fails', async () => {
    mocks.listApiKeys.mockResolvedValue({ data: undefined });
    const { result } = await renderLoaded();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('appends an added key to the cache without refetching', async () => {
    mocks.addApiReadKey.mockResolvedValue({ data: { read_key: READ_KEY_B } });
    const { result } = await renderLoaded();

    let added: ApiReadKeyMessage | undefined;
    await act(async () => {
      added = await result.current.addReadKey('Stats');
    });

    expect(added).toEqual(READ_KEY_B);
    expect(mocks.addApiReadKey).toHaveBeenCalledWith({
      auth: 'token-1',
      body: { description: 'Stats' },
    });
    await waitFor(() =>
      expect(result.current.readKeys).toEqual([READ_KEY_A, READ_KEY_B]),
    );
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
    expect(mocks.listApiKeys).toHaveBeenCalledTimes(1);
  });

  test('seeds an empty cache when adding before keys have loaded', async () => {
    mocks.listApiKeys.mockResolvedValue({ data: undefined });
    mocks.addApiReadKey.mockResolvedValue({ data: { read_key: READ_KEY_B } });
    const { result } = await renderLoaded();

    await act(async () => {
      await result.current.addReadKey('Stats');
    });

    await waitFor(() => expect(result.current.readKeys).toEqual([READ_KEY_B]));
    expect(result.current.writeKeys).toEqual([]);
  });

  test('rejects when the backend does not return the new key', async () => {
    mocks.addApiReadKey.mockResolvedValue({ data: {} });
    const { result } = await renderLoaded();

    await act(async () => {
      await expect(result.current.addReadKey('Stats')).rejects.toThrow(
        'Failed to add key',
      );
    });
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
  });

  test('removes a deleted key from the cache', async () => {
    mocks.deleteApiReadKey.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    let deleted: string | undefined;
    await act(async () => {
      deleted = await result.current.deleteReadKey('read-a');
    });

    expect(deleted).toBe('read-a');
    expect(mocks.deleteApiReadKey).toHaveBeenCalledWith({
      auth: 'token-1',
      body: { key_id: 'read-a' },
    });
    await waitFor(() => expect(result.current.readKeys).toEqual([]));
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
  });

  test('seeds an empty cache when deleting before keys have loaded', async () => {
    mocks.listApiKeys.mockResolvedValue({ data: undefined });
    mocks.deleteApiReadKey.mockResolvedValue({ data: { code: 200 } });
    const { result } = await renderLoaded();

    await act(async () => {
      await result.current.deleteReadKey('read-a');
    });

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('rejects when the body code reports a logical failure', async () => {
    mocks.deleteApiReadKey.mockResolvedValue({ data: { code: 404 } });
    const { result } = await renderLoaded();

    await act(async () => {
      await expect(result.current.deleteReadKey('read-a')).rejects.toThrow(
        'Failed to delete key',
      );
    });
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
  });
});
