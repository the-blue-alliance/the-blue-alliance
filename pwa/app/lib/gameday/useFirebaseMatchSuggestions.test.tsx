import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { MatchSuggestions } from '~/api/firebase';
import { useFirebaseMatchSuggestions } from '~/lib/gameday/useFirebaseMatchSuggestions';

const firebaseMocks = vi.hoisted(() => ({
  getDatabaseInstance: vi.fn<() => Promise<unknown>>(),
  onValue:
    vi.fn<
      (
        reference: unknown,
        onUpdate: (snapshot: { val: () => unknown }) => void,
        onError: (error: Error) => void,
      ) => () => void
    >(),
  ref: vi.fn<(database: unknown, path: string) => unknown>(),
  unsubscribe: vi.fn<() => void>(),
}));

vi.mock('~/firebase/firebaseConfig', () => ({
  getDatabaseInstance: firebaseMocks.getDatabaseInstance,
}));

vi.mock('firebase/database', () => ({
  onValue: firebaseMocks.onValue,
  ref: firebaseMocks.ref,
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: PropsWithChildren) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useFirebaseMatchSuggestions', () => {
  beforeEach(() => {
    firebaseMocks.getDatabaseInstance.mockResolvedValue({});
    firebaseMocks.ref.mockReturnValue({});
    firebaseMocks.onValue.mockReturnValue(firebaseMocks.unsubscribe);
  });

  test('subscribes to the match suggestions node', async () => {
    renderHook(() => useFirebaseMatchSuggestions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(firebaseMocks.ref).toHaveBeenCalledWith({}, 'match_suggestions');
    });
  });

  test('publishes Firebase updates to consumers', async () => {
    const { result } = renderHook(() => useFirebaseMatchSuggestions(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(firebaseMocks.onValue).toHaveBeenCalled());
    const onUpdate = firebaseMocks.onValue.mock.calls[0][1] as (snapshot: {
      val: () => MatchSuggestions;
    }) => void;
    const feed: MatchSuggestions = { updated_at: 1_776_959_400 };

    act(() => onUpdate({ val: () => feed }));

    await waitFor(() => expect(result.current.data).toEqual(feed));
  });

  test('treats a missing Firebase node as an empty feed', async () => {
    const { result } = renderHook(() => useFirebaseMatchSuggestions(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(firebaseMocks.onValue).toHaveBeenCalled());
    const onUpdate = firebaseMocks.onValue.mock.calls[0][1] as (snapshot: {
      val: () => null;
    }) => void;

    act(() => onUpdate({ val: () => null }));

    await waitFor(() => expect(result.current.data).toBeNull());
  });

  test('exposes subscription errors', async () => {
    const { result } = renderHook(() => useFirebaseMatchSuggestions(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(firebaseMocks.onValue).toHaveBeenCalled());
    const onError = firebaseMocks.onValue.mock.calls[0][2] as (
      error: Error,
    ) => void;

    act(() => onError(new Error('Permission denied')));

    await waitFor(() =>
      expect(result.current.error?.message).toBe('Permission denied'),
    );
  });

  test('unsubscribes when the panel unmounts', async () => {
    const { unmount } = renderHook(() => useFirebaseMatchSuggestions(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(firebaseMocks.onValue).toHaveBeenCalled());

    unmount();

    expect(firebaseMocks.unsubscribe).toHaveBeenCalledOnce();
  });
});
