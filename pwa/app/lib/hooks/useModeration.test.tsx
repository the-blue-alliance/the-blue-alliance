import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { ReviewResult, SuggestionType } from '~/api/tba/moderation/types.gen';
import {
  type ReviewSubmissionResult,
  useModerationQueue,
  useModerationSuggestions,
  useReviewSubmission,
} from '~/lib/hooks/useModeration';

interface SdkResponse {
  data?: unknown;
  error?: unknown;
  response?: { status: number };
}

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => { user: unknown }>(),
  getModerationQueue: vi.fn<(options: unknown) => Promise<SdkResponse>>(),
  listModerationSuggestions:
    vi.fn<(options: unknown) => Promise<SdkResponse>>(),
  acceptModerationSuggestion:
    vi.fn<(options: unknown) => Promise<SdkResponse>>(),
  rejectModerationSuggestions:
    vi.fn<(options: unknown) => Promise<SdkResponse>>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/api/tba/moderation/sdk.gen', () => ({
  getModerationQueue: mocks.getModerationQueue,
  listModerationSuggestions: mocks.listModerationSuggestions,
  acceptModerationSuggestion: mocks.acceptModerationSuggestion,
  rejectModerationSuggestions: mocks.rejectModerationSuggestions,
}));

const USER = { uid: 'user-1', getIdToken: () => Promise.resolve('token-1') };
const TYPE = SuggestionType.OFFSEASON_EVENT;

function createClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function wrapperFor(queryClient: QueryClient) {
  return function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

function renderQueue() {
  return renderHook(() => useModerationQueue(), {
    wrapper: wrapperFor(createClient()),
  });
}

describe('useModerationQueue', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('stays idle when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = renderQueue();

    expect(result.current.fetchStatus).toBe('idle');
    expect(mocks.getModerationQueue).not.toHaveBeenCalled();
  });

  test('returns the queue for moderators', async () => {
    const queue = { total_pending: 3 };
    mocks.getModerationQueue.mockResolvedValue({ data: queue });

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(queue);
    expect(mocks.getModerationQueue).toHaveBeenCalledWith({ auth: 'token-1' });
  });

  test('returns null for accounts without review permissions', async () => {
    mocks.getModerationQueue.mockResolvedValue({
      error: { Error: 'Forbidden' },
      response: { status: 403 },
    });

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeNull();
  });

  test('surfaces a 403 that asks for a verified email', async () => {
    const error = { Error: 'Moderators need a verified email' };
    mocks.getModerationQueue.mockResolvedValue({
      error,
      response: { status: 403 },
    });

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBe(error);
  });

  test('falls back to a generic error when the SDK has none', async () => {
    mocks.getModerationQueue.mockResolvedValue({ response: { status: 500 } });

    const { result } = renderQueue();

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toEqual(
      new Error('Failed to load moderation queue'),
    );
  });
});

describe('useModerationSuggestions', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  test('stays idle when signed out', () => {
    mocks.useAuth.mockReturnValue({ user: null });

    const { result } = renderHook(() => useModerationSuggestions(TYPE), {
      wrapper: wrapperFor(createClient()),
    });

    expect(result.current.fetchStatus).toBe('idle');
    expect(mocks.listModerationSuggestions).not.toHaveBeenCalled();
  });

  test('lists pending suggestions of the given type', async () => {
    const suggestions = { suggestions: [] };
    mocks.listModerationSuggestions.mockResolvedValue({ data: suggestions });

    const { result } = renderHook(() => useModerationSuggestions(TYPE), {
      wrapper: wrapperFor(createClient()),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe(suggestions);
    expect(mocks.listModerationSuggestions).toHaveBeenCalledWith({
      auth: 'token-1',
      path: { suggestion_type: TYPE },
      throwOnError: true,
    });
  });
});

describe('useReviewSubmission', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ user: USER });
  });

  function renderSubmission() {
    const queryClient = createClient();
    const invalidate = vi.spyOn(queryClient, 'invalidateQueries');
    const hook = renderHook(() => useReviewSubmission(TYPE), {
      wrapper: wrapperFor(queryClient),
    });
    return { ...hook, invalidate };
  }

  test('rejects the submission when signed out', async () => {
    mocks.useAuth.mockReturnValue({ user: null });
    const { result } = renderSubmission();

    await act(async () => {
      await expect(
        result.current.mutateAsync({ accepts: [], rejects: [] }),
      ).rejects.toThrow('User not authenticated');
    });
    expect(mocks.acceptModerationSuggestion).not.toHaveBeenCalled();
  });

  test('sorts accept outcomes and invalidates moderation queries', async () => {
    mocks.acceptModerationSuggestion
      .mockResolvedValueOnce({ data: { result: ReviewResult.ACCEPTED } })
      .mockResolvedValueOnce({
        error: { result: ReviewResult.ALREADY_REVIEWED },
      })
      .mockResolvedValueOnce({
        error: { result: ReviewResult.INVALID, message: 'Missing city' },
      })
      .mockResolvedValueOnce({ error: { result: ReviewResult.NOT_FOUND } })
      .mockResolvedValueOnce({});
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

    expect(mocks.acceptModerationSuggestion).toHaveBeenNthCalledWith(1, {
      auth: 'token-1',
      path: { suggestion_key: 'a' },
      body: {},
    });
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
    expect(mocks.rejectModerationSuggestions).not.toHaveBeenCalled();
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['moderation', 'suggestions', TYPE],
    });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ['moderation', 'queue'],
    });
  });

  test('batches rejects by message and sorts their outcomes', async () => {
    mocks.rejectModerationSuggestions
      .mockResolvedValueOnce({
        data: {
          results: [
            { suggestion_key: 'r1', result: ReviewResult.REJECTED },
            { suggestion_key: 'r2', result: ReviewResult.ALREADY_REVIEWED },
          ],
        },
      })
      .mockResolvedValueOnce({
        data: {
          results: [
            {
              suggestion_key: 'r3',
              result: ReviewResult.FORBIDDEN,
              message: 'Not allowed',
            },
            { suggestion_key: 'r4', result: ReviewResult.NOT_FOUND },
          ],
        },
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

    expect(mocks.rejectModerationSuggestions).toHaveBeenNthCalledWith(1, {
      auth: 'token-1',
      body: { suggestion_keys: ['r1', 'r2'], user_message: undefined },
    });
    expect(mocks.rejectModerationSuggestions).toHaveBeenNthCalledWith(2, {
      auth: 'token-1',
      body: { suggestion_keys: ['r3', 'r4'], user_message: 'Sorry' },
    });
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

  test('Bug #62: rejects whose request fails outright are reported as failed', async () => {
    // Wrong today: when the reject call returns no `data` (for example a
    // 500), its keys land in none of rejected/alreadyReviewed/failed, so the
    // moderator is never told the reject didn't happen.
    // Correct: those keys appear in `failed`, as failed accepts do.
    mocks.rejectModerationSuggestions.mockResolvedValue({
      error: { Error: 'Internal Server Error' },
      response: { status: 500 },
    });
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
