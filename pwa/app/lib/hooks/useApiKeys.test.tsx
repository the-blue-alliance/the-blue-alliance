import { act, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  addApiReadKey,
  deleteApiReadKey,
  listApiKeys,
} from '~/api/tba/mobile/sdk.gen';
import type {
  ApiReadKeyMessage,
  ApiWriteKeyMessage,
} from '~/api/tba/mobile/types.gen';
import { useApiKeys } from '~/lib/hooks/useApiKeys';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderHookWithClient } from '~/test/render';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

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
  return renderHookWithClient(() => useApiKeys());
}

async function renderLoaded() {
  const hook = renderApiKeys();
  await waitFor(() => expect(hook.result.current.isLoading).toBe(false));
  return hook;
}

function failListApiKeys() {
  mockTbaApiWith(
    listApiKeys,
    {},
    () => new HttpResponse(null, { status: 500 }),
  );
}

describe('useApiKeys', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mockTbaApi(
      listApiKeys,
      {},
      { read_keys: [READ_KEY_A], write_keys: [WRITE_KEY] },
    );
  });

  test('does not load keys when signed out, and refuses writes', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const listRequests = mockTbaApi(listApiKeys, {}, {});
    const addRequests = mockTbaApi(addApiReadKey, {}, {});
    const deleteRequests = mockTbaApi(deleteApiReadKey, {}, {});
    const { result } = renderApiKeys();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(listRequests).toEqual([]);

    await expect(result.current.addReadKey('New key')).rejects.toThrow(
      'User not authenticated',
    );
    await expect(result.current.deleteReadKey('read-a')).rejects.toThrow(
      'User not authenticated',
    );
    expect(addRequests).toEqual([]);
    expect(deleteRequests).toEqual([]);
  });

  test('loads read and write keys with the user token', async () => {
    const requests = mockTbaApi(
      listApiKeys,
      {},
      { read_keys: [READ_KEY_A], write_keys: [WRITE_KEY] },
    );
    const { result } = await renderLoaded();

    expect(requests[0].headers.get('Authorization')).toBe('Bearer token-1');
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
  });

  test('falls back to empty lists when the response omits them', async () => {
    mockTbaApi(listApiKeys, {}, {});
    const { result } = await renderLoaded();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('returns empty lists when loading fails', async () => {
    failListApiKeys();
    const { result } = await renderLoaded();

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('appends an added key to the cache without refetching', async () => {
    const listRequests = mockTbaApi(
      listApiKeys,
      {},
      { read_keys: [READ_KEY_A], write_keys: [WRITE_KEY] },
    );
    const addRequests = mockTbaApi(addApiReadKey, {}, { read_key: READ_KEY_B });
    const { result } = await renderLoaded();

    let added: ApiReadKeyMessage | undefined;
    await act(async () => {
      added = await result.current.addReadKey('Stats');
    });

    expect(added).toEqual(READ_KEY_B);
    expect(addRequests[0].headers.get('Authorization')).toBe('Bearer token-1');
    expect(await addRequests[0].json()).toEqual({ description: 'Stats' });
    await waitFor(() =>
      expect(result.current.readKeys).toEqual([READ_KEY_A, READ_KEY_B]),
    );
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
    expect(listRequests).toHaveLength(1);
  });

  test('seeds an empty cache when adding before keys have loaded', async () => {
    failListApiKeys();
    mockTbaApi(addApiReadKey, {}, { read_key: READ_KEY_B });
    const { result } = await renderLoaded();

    await act(async () => {
      await result.current.addReadKey('Stats');
    });

    await waitFor(() => expect(result.current.readKeys).toEqual([READ_KEY_B]));
    expect(result.current.writeKeys).toEqual([]);
  });

  test('rejects when the backend does not return the new key', async () => {
    mockTbaApi(addApiReadKey, {}, {});
    const { result } = await renderLoaded();

    await act(async () => {
      await expect(result.current.addReadKey('Stats')).rejects.toThrow(
        'Failed to add key',
      );
    });
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
  });

  test('removes a deleted key from the cache', async () => {
    const requests = mockTbaApi(deleteApiReadKey, {}, { code: 200 });
    const { result } = await renderLoaded();

    let deleted: string | undefined;
    await act(async () => {
      deleted = await result.current.deleteReadKey('read-a');
    });

    expect(deleted).toBe('read-a');
    expect(requests[0].headers.get('Authorization')).toBe('Bearer token-1');
    expect(await requests[0].json()).toEqual({ key_id: 'read-a' });
    await waitFor(() => expect(result.current.readKeys).toEqual([]));
    expect(result.current.writeKeys).toEqual([WRITE_KEY]);
  });

  test('seeds an empty cache when deleting before keys have loaded', async () => {
    failListApiKeys();
    mockTbaApi(deleteApiReadKey, {}, { code: 200 });
    const { result } = await renderLoaded();

    await act(async () => {
      await result.current.deleteReadKey('read-a');
    });

    expect(result.current.readKeys).toEqual([]);
    expect(result.current.writeKeys).toEqual([]);
  });

  test('rejects when the body code reports a logical failure', async () => {
    mockTbaApi(deleteApiReadKey, {}, { code: 404 });
    const { result } = await renderLoaded();

    await act(async () => {
      await expect(result.current.deleteReadKey('read-a')).rejects.toThrow(
        'Failed to delete key',
      );
    });
    expect(result.current.readKeys).toEqual([READ_KEY_A]);
  });
});
