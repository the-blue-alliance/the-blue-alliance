import { act, waitFor } from '@testing-library/react';
import { HttpResponse } from 'msw';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  acceptModerationSuggestion,
  getModerationQueue,
  listModerationSuggestions,
  rejectModerationSuggestions,
} from '~/api/tba/moderation/sdk.gen';
import {
  type AcceptResponse,
  type RejectRequest,
  ReviewResult,
  SuggestionType,
} from '~/api/tba/moderation/types.gen';
import {
  type ReviewSubmissionResult,
  useModerationQueue,
  useModerationSuggestions,
  useReviewSubmission,
} from '~/lib/hooks/useModeration';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';
import { renderHookWithClient } from '~/test/render';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };
const TYPE = SuggestionType.OFFSEASON_EVENT;

function renderQueue() {
  return renderHookWithClient(() => useModerationQueue());
}

function mockAccept(key: string, status: number, body: object) {
  const requests: Request[] = [];
  mockTbaApiWith(
    acceptModerationSuggestion,
    { path: { suggestion_key: key } },
    ({ request }) => {
      requests.push(request);
      return HttpResponse.json(body, { status });
    },
  );
  return requests;
}

describe('useModerationQueue', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('stays idle when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const requests = mockTbaApi(
      getModerationQueue,
      {},
      { counts: {}, type_names: {} },
    );

    const { result } = renderQueue();

    expect(result.current.fetchStatus).toBe('idle');
    expect(requests).toEqual([]);
  });

  test('returns the queue for moderators', async () => {
    const queue = {
      counts: { [TYPE]: 3 },
      type_names: { [TYPE]: 'Offseason Events' },
    };
    const requests = mockTbaApi(getModerationQueue, {}, queue);

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(queue);
    expect(requests[0].headers.get('Authorization')).toBe('Bearer token-1');
  });

  test('returns null for accounts without review permissions', async () => {
    mockTbaApiWith(getModerationQueue, {}, () =>
      HttpResponse.json({ Error: 'Forbidden' }, { status: 403 }),
    );

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });

  test('surfaces a 403 that asks for a verified email', async () => {
    const error = { Error: 'Moderators need a verified email' };
    mockTbaApiWith(getModerationQueue, {}, () =>
      HttpResponse.json(error, { status: 403 }),
    );

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toEqual(error);
  });

  test('reports an error when the server fails', async () => {
    mockTbaApiWith(
      getModerationQueue,
      {},
      () => new HttpResponse(null, { status: 500 }),
    );

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useModerationSuggestions', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('stays idle when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const requests = mockTbaApi(
      listModerationSuggestions,
      { path: { suggestion_type: TYPE } },
      { suggestions: [], total: 0 },
    );

    const { result } = renderHookWithClient(() =>
      useModerationSuggestions(TYPE),
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(requests).toEqual([]);
  });

  test('lists pending suggestions of the given type', async () => {
    const suggestions = { suggestions: [], total: 0 };
    const requests = mockTbaApi(
      listModerationSuggestions,
      { path: { suggestion_type: TYPE } },
      suggestions,
    );

    const { result } = renderHookWithClient(() =>
      useModerationSuggestions(TYPE),
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(suggestions);
    expect(requests[0].headers.get('Authorization')).toBe('Bearer token-1');
  });
});

describe('useReviewSubmission', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  function renderSubmission() {
    const hook = renderHookWithClient(() => useReviewSubmission(TYPE));
    const invalidate = vi.spyOn(hook.queryClient, 'invalidateQueries');
    return { ...hook, invalidate };
  }

  test('rejects the submission when signed out', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const requests = mockAccept('a', 200, {
      result: ReviewResult.ACCEPTED,
      suggestion_key: 'a',
    });
    const { result } = renderSubmission();

    await act(async () => {
      await expect(
        result.current.mutateAsync({ accepts: [], rejects: [] }),
      ).rejects.toThrow('User not authenticated');
    });
    expect(requests).toEqual([]);
  });

  test('sorts accept outcomes and invalidates moderation queries', async () => {
    const acceptA = mockAccept('a', 200, {
      result: ReviewResult.ACCEPTED,
      suggestion_key: 'a',
    } satisfies AcceptResponse);
    mockAccept('b', 409, { result: ReviewResult.ALREADY_REVIEWED });
    mockAccept('c', 400, {
      result: ReviewResult.INVALID,
      message: 'Missing city',
    });
    mockAccept('d', 404, { result: ReviewResult.NOT_FOUND });
    mockAccept('e', 500, {});
    const rejectRequests = mockTbaApi(
      rejectModerationSuggestions,
      {},
      { results: [] },
    );
    const { result, invalidate } = renderSubmission();

    let outcome: ReviewSubmissionResult | undefined;
    await act(async () => {
      outcome = await result.current.mutateAsync({
        accepts: ['a', 'b', 'c', 'd', 'e'].map((key) => ({
          key,
          overrides: {},
        })),
        rejects: [],
      });
    });

    expect(acceptA[0].headers.get('Authorization')).toBe('Bearer token-1');
    expect(await acceptA[0].json()).toEqual({});
    expect(outcome).toEqual({
      accepted: ['a'],
      rejected: [],
      alreadyReviewed: ['b'],
      failed: [
        { key: 'c', message: 'Missing city' },
        { key: 'd', message: ReviewResult.NOT_FOUND },
        { key: 'e', message: 'request failed' },
      ],
    });
    expect(rejectRequests).toEqual([]);
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['moderation', 'suggestions', TYPE],
    });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['moderation', 'queue'],
    });
  });

  test('batches rejects by message and sorts their outcomes', async () => {
    const bodies: RejectRequest[] = [];
    mockTbaApiWith(rejectModerationSuggestions, {}, async ({ request }) => {
      const body = (await request.json()) as RejectRequest;
      bodies.push(body);
      return HttpResponse.json(
        body.user_message
          ? {
              results: [
                {
                  suggestion_key: 'r3',
                  result: ReviewResult.FORBIDDEN,
                  message: 'Not allowed',
                },
                { suggestion_key: 'r4', result: ReviewResult.NOT_FOUND },
              ],
            }
          : {
              results: [
                { suggestion_key: 'r1', result: ReviewResult.REJECTED },
                {
                  suggestion_key: 'r2',
                  result: ReviewResult.ALREADY_REVIEWED,
                },
              ],
            },
      );
    });
    const { result } = renderSubmission();

    let outcome: ReviewSubmissionResult | undefined;
    await act(async () => {
      outcome = await result.current.mutateAsync({
        accepts: [],
        rejects: [
          { key: 'r1' },
          { key: 'r2' },
          { key: 'r3', userMessage: 'Sorry' },
          { key: 'r4', userMessage: 'Sorry' },
        ],
      });
    });

    expect(bodies).toEqual([
      { suggestion_keys: ['r1', 'r2'] },
      { suggestion_keys: ['r3', 'r4'], user_message: 'Sorry' },
    ]);
    expect(outcome).toEqual({
      accepted: [],
      rejected: ['r1'],
      alreadyReviewed: ['r2'],
      failed: [
        { key: 'r3', message: 'Not allowed' },
        { key: 'r4', message: ReviewResult.NOT_FOUND },
      ],
    });
  });

  test('rejects whose request fails outright are reported as failed', async () => {
    mockTbaApiWith(rejectModerationSuggestions, {}, () =>
      HttpResponse.json({ Error: 'Internal Server Error' }, { status: 500 }),
    );
    const { result } = renderSubmission();

    let outcome: ReviewSubmissionResult | undefined;
    await act(async () => {
      outcome = await result.current.mutateAsync({
        accepts: [],
        rejects: [{ key: 'r1' }],
      });
    });

    expect(outcome).toEqual({
      accepted: [],
      rejected: [],
      alreadyReviewed: [],
      failed: [{ key: 'r1', message: expect.any(String) }],
    });
  });
});
