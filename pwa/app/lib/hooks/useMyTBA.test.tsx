import { act, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  listFavorites,
  listSubscriptions,
  setModelPreferences,
} from '~/api/tba/mobile/sdk.gen';
import type {
  FavoriteCollection,
  SubscriptionCollection,
} from '~/api/tba/mobile/types.gen';
import { useMyTBA } from '~/lib/hooks/useMyTBA';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderHookWithClient } from '~/test/render';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

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
  return renderHookWithClient(() => useMyTBA(modelKey, TEAM));
}

function holdSave() {
  const save = deferred<Response>();
  const requests: Request[] = [];
  mockTbaApiWith(setModelPreferences, {}, ({ request }) => {
    requests.push(request);
    return save.promise;
  });
  return { ...save, requests };
}

async function renderLoaded(modelKey: string) {
  const rendered = renderMyTBA(modelKey);
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
    mockTbaApi(listFavorites, {}, FAVORITES);
    mockTbaApi(listSubscriptions, {}, SUBSCRIPTIONS);
    mockTbaApi(setModelPreferences, {}, { code: 200 });
  });

  test('reports nothing and fetches nothing when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const favoritesRequests = mockTbaApi(listFavorites, {}, FAVORITES);
    const subscriptionsRequests = mockTbaApi(
      listSubscriptions,
      {},
      SUBSCRIPTIONS,
    );

    const { result } = renderMyTBA('frc254');

    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
    expect(result.current.isPending).toBe(false);
    expect(favoritesRequests).toEqual([]);
    expect(subscriptionsRequests).toEqual([]);
  });

  test('refuses to save preferences when signed out', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const saveRequests = mockTbaApi(setModelPreferences, {}, { code: 200 });
    const { result, queryClient } = renderMyTBA('frc254');

    act(() => result.current.toggleFavorite());

    await waitFor(() => expect(result.current.isPending).toBe(false));
    expect(saveRequests).toEqual([]);
    // The optimistic write is not rolled back because there was no prior
    // cache entry to restore.
    expect(queryClient.getQueryData(['favorites', undefined])).toEqual({
      favorites: [{ model_key: 'frc254', model_type: TEAM }],
    });
  });

  test('reads favorite and notification state for the model', async () => {
    const favoritesRequests = mockTbaApi(listFavorites, {}, FAVORITES);
    const subscriptionsRequests = mockTbaApi(
      listSubscriptions,
      {},
      SUBSCRIPTIONS,
    );
    const { result } = await renderLoaded('frc254');

    expect(favoritesRequests[0].headers.get('Authorization')).toBe(
      'Bearer token-1',
    );
    expect(subscriptionsRequests[0].headers.get('Authorization')).toBe(
      'Bearer token-1',
    );
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
    mockTbaApi(listFavorites, {}, {});
    mockTbaApi(listSubscriptions, {}, {});
    const { result } = await renderLoaded('frc254');

    expect(result.current.isFavorite).toBe(false);
    expect(result.current.notifications).toEqual([]);
  });

  test('reports nothing when loading fails', async () => {
    mockTbaApiWith(
      listFavorites,
      {},
      () => new HttpResponse(null, { status: 500 }),
    );
    mockTbaApiWith(
      listSubscriptions,
      {},
      () => new HttpResponse(null, { status: 500 }),
    );
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
    const save = holdSave();
    const { result, queryClient } = await renderLoaded('frc1678');

    act(() => result.current.toggleFavorite());

    await waitFor(() => expect(result.current.isFavorite).toBe(true));
    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(save.requests).toHaveLength(1));
    expect(save.requests[0].headers.get('Authorization')).toBe(
      'Bearer token-1',
    );
    expect(await save.requests[0].json()).toEqual({
      model_key: 'frc1678',
      model_type: TEAM,
      device_key: null,
      notifications: [],
      favorite: true,
    });
    expect(queryClient.getQueryData(['subscriptions', 'user-1'])).toEqual(
      SUBSCRIPTIONS,
    );

    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');
    await act(async () => {
      save.resolve(HttpResponse.json({ code: 200 }));
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
    const save = holdSave();
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
      save.resolve(HttpResponse.json({ code: 200 }));
      await save.promise;
    });
  });

  test('clearing everything removes the model from both lists', async () => {
    const save = holdSave();
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
      save.resolve(HttpResponse.json({ code: 200 }));
      await save.promise;
    });
  });

  test('rolls back the optimistic update when saving fails', async () => {
    const save = holdSave();
    const { result, queryClient } = await renderLoaded('frc254');
    const setQueryData = vi.spyOn(queryClient, 'setQueryData');

    act(() => result.current.toggleFavorite());
    await waitFor(() => expect(result.current.isFavorite).toBe(false));

    await act(async () => {
      save.resolve(new HttpResponse(null, { status: 500 }));
      await save.promise;
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
