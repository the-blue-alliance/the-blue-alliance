import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type {
  FavoriteCollection,
  SubscriptionCollection,
} from '~/api/tba/mobile/types.gen';
import { useMyTBA } from '~/lib/hooks/useMyTBA';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
  listFavorites: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
  listSubscriptions: vi.fn<(options: unknown) => Promise<{ data?: unknown }>>(),
  setModelPreferences: vi.fn<(options: unknown) => Promise<unknown>>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/api/tba/mobile/sdk.gen', () => ({
  listFavorites: mocks.listFavorites,
  listSubscriptions: mocks.listSubscriptions,
  setModelPreferences: mocks.setModelPreferences,
}));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };
const TEAM = 1;

const FAVORITES: FavoriteCollection = {
  favorites: [
    { model_key: 'frc254', model_type: TEAM },
    { model_key: 'frc604', model_type: TEAM },
  ],
};
const SUBSCRIPTIONS: SubscriptionCollection = {
  subscriptions: [
    {
      model_key: 'frc254',
      model_type: TEAM,
      notifications: ['match_score', 'awards_posted'],
    },
    { model_key: 'frc604', model_type: TEAM, notifications: ['match_score'] },
  ],
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function renderMyTBA(modelKey: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  const hook = renderHook(() => useMyTBA(modelKey, TEAM), { wrapper: Wrapper });
  return { ...hook, queryClient };
}

async function renderLoaded(modelKey: string) {
  const rendered = renderMyTBA(modelKey);
  await waitFor(() => {
    expect(mocks.listFavorites).toHaveBeenCalled();
    expect(mocks.listSubscriptions).toHaveBeenCalled();
  });
  await waitFor(() =>
    expect(
      rendered.queryClient.getQueryData(['subscriptions', 'user-1']),
    ).toBeDefined(),
  );
  await waitFor(() =>
    expect(
      rendered.queryClient.getQueryData(['favorites', 'user-1']),
    ).toBeDefined(),
  );
  return rendered;
}

describe('useMyTBA', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
    mocks.listFavorites.mockResolvedValue({ data: FAVORITES });
    mocks.listSubscriptions.mockResolvedValue({ data: SUBSCRIPTIONS });
    mocks.setModelPreferences.mockResolvedValue({ data: { code: 200 } });
  });

  test('reports nothing and fetches nothing when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = renderMyTBA('frc254');

    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
    expect(result.current.isPending).toBe(false);
    expect(mocks.listFavorites).not.toHaveBeenCalled();
    expect(mocks.listSubscriptions).not.toHaveBeenCalled();
  });

  test('refuses to save preferences when signed out', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const { result, queryClient } = renderMyTBA('frc254');

    act(() => result.current.toggleFavorite());

    await waitFor(() => expect(result.current.isPending).toBe(false));
    expect(mocks.setModelPreferences).not.toHaveBeenCalled();
    // The optimistic write is not rolled back because there was no prior
    // cache entry to restore.
    expect(queryClient.getQueryData(['favorites', undefined])).toEqual({
      favorites: [{ model_key: 'frc254', model_type: TEAM }],
    });
  });

  test('reads favorite and notification state for the model', async () => {
    const { result } = await renderLoaded('frc254');

    expect(mocks.listFavorites).toHaveBeenCalledWith({ auth: 'token-1' });
    expect(mocks.listSubscriptions).toHaveBeenCalledWith({ auth: 'token-1' });
    expect(result.current.isFavorite).toBe(true);
    expect(result.current.notifications).toEqual([
      'match_score',
      'awards_posted',
    ]);
  });

  test('treats models missing from the lists as unfavorited', async () => {
    const { result } = await renderLoaded('frc1678');

    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
  });

  test('treats collections without lists as empty', async () => {
    mocks.listFavorites.mockResolvedValue({ data: {} });
    mocks.listSubscriptions.mockResolvedValue({ data: {} });
    const { result } = await renderLoaded('frc254');

    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
  });

  test('reports nothing when loading fails', async () => {
    mocks.listFavorites.mockResolvedValue({ data: undefined });
    mocks.listSubscriptions.mockResolvedValue({ data: undefined });
    const { result, queryClient } = renderMyTBA('frc254');

    await waitFor(() =>
      expect(
        queryClient.getQueryState(['subscriptions', 'user-1'])?.status,
      ).toBe('error'),
    );
    await waitFor(() =>
      expect(queryClient.getQueryState(['favorites', 'user-1'])?.status).toBe(
        'error',
      ),
    );
    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
  });

  test('toggleFavorite optimistically favorites and keeps notifications', async () => {
    const save = deferred<unknown>();
    mocks.setModelPreferences.mockReturnValue(save.promise);
    const { result, queryClient } = await renderLoaded('frc1678');

    act(() => result.current.toggleFavorite());

    await waitFor(() => expect(result.current.isFavorite).toBe(true));
    expect(result.current.isPending).toBe(true);
    expect(mocks.setModelPreferences).toHaveBeenCalledWith({
      auth: 'token-1',
      body: {
        model_key: 'frc1678',
        model_type: TEAM,
        device_key: null,
        notifications: [],
        favorite: true,
      },
    });
    expect(queryClient.getQueryData(['subscriptions', 'user-1'])).toEqual(
      SUBSCRIPTIONS,
    );

    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');
    await act(async () => {
      save.resolve({ data: { code: 200 } });
      await save.promise;
    });

    await waitFor(() => expect(result.current.isPending).toBe(false));
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['favorites', 'user-1'],
    });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['subscriptions', 'user-1'],
    });
  });

  test('setPreferences optimistically replaces the model entries', async () => {
    const save = deferred<unknown>();
    mocks.setModelPreferences.mockReturnValue(save.promise);
    const { result, queryClient } = await renderLoaded('frc254');

    act(() => result.current.setPreferences(true, ['upcoming_match']));

    await waitFor(() =>
      expect(result.current.notifications).toEqual(['upcoming_match']),
    );
    expect(queryClient.getQueryData(['favorites', 'user-1'])).toEqual({
      favorites: [
        { model_key: 'frc604', model_type: TEAM },
        { model_key: 'frc254', model_type: TEAM },
      ],
    });
    expect(queryClient.getQueryData(['subscriptions', 'user-1'])).toEqual({
      subscriptions: [
        {
          model_key: 'frc604',
          model_type: TEAM,
          notifications: ['match_score'],
        },
        {
          model_key: 'frc254',
          model_type: TEAM,
          notifications: ['upcoming_match'],
        },
      ],
    });

    await act(async () => {
      save.resolve({ data: { code: 200 } });
      await save.promise;
    });
  });

  test('clearing everything removes the model from both lists', async () => {
    const save = deferred<unknown>();
    mocks.setModelPreferences.mockReturnValue(save.promise);
    const { result, queryClient } = await renderLoaded('frc254');

    act(() => result.current.setPreferences(false, []));

    await waitFor(() => expect(result.current.isFavorite).toBe(false));
    expect(result.current.notifications).toEqual([]);
    expect(queryClient.getQueryData(['favorites', 'user-1'])).toEqual({
      favorites: [{ model_key: 'frc604', model_type: TEAM }],
    });
    expect(queryClient.getQueryData(['subscriptions', 'user-1'])).toEqual({
      subscriptions: [
        {
          model_key: 'frc604',
          model_type: TEAM,
          notifications: ['match_score'],
        },
      ],
    });

    await act(async () => {
      save.resolve({ data: { code: 200 } });
      await save.promise;
    });
  });

  test('rolls back the optimistic update when saving fails', async () => {
    const save = deferred<unknown>();
    mocks.setModelPreferences.mockReturnValue(save.promise);
    const { result, queryClient } = await renderLoaded('frc254');
    const setQueryData = vi.spyOn(queryClient, 'setQueryData');

    act(() => result.current.toggleFavorite());
    await waitFor(() => expect(result.current.isFavorite).toBe(false));

    await act(async () => {
      save.reject(new Error('network down'));
      await save.promise.catch(() => undefined);
    });

    await waitFor(() => expect(result.current.isPending).toBe(false));
    expect(setQueryData).toHaveBeenCalledWith(
      ['favorites', 'user-1'],
      FAVORITES,
    );
    expect(setQueryData).toHaveBeenCalledWith(
      ['subscriptions', 'user-1'],
      SUBSCRIPTIONS,
    );
    await waitFor(() => expect(result.current.isFavorite).toBe(true));
  });
});
