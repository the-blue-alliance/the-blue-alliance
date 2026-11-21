import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { useFirebaseWebcasts } from '~/lib/gameday/useFirebaseWebcasts';

type Snapshot = { val: () => unknown };
type OnUpdate = (snapshot: Snapshot) => void;

const firebaseMocks = vi.hoisted(() => ({
  getDatabaseInstance: vi.fn<() => Promise<unknown>>(),
  onValue:
    vi.fn<
      (reference: string, onUpdate: (snapshot: Snapshot) => void) => () => void
    >(),
  ref: vi.fn<(database: unknown, path: string) => string>(),
  unsubscribeLiveEvents: vi.fn<() => void>(),
  unsubscribeSpecialWebcasts: vi.fn<() => void>(),
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

async function renderWebcasts() {
  const hook = renderHook(() => useFirebaseWebcasts(), {
    wrapper: createWrapper(),
  });
  await waitFor(() => expect(firebaseMocks.onValue).toHaveBeenCalledTimes(2));
  return hook;
}

function publish(path: 'live_events' | 'special_webcasts', value: unknown) {
  const subscription = firebaseMocks.onValue.mock.calls.find(
    ([reference]) => reference === path,
  );
  const onUpdate = subscription?.[1] as OnUpdate;
  act(() => onUpdate({ val: () => value }));
}

const twitch = { type: 'twitch', channel: 'firstinspires' } as const;

describe('useFirebaseWebcasts', () => {
  beforeEach(() => {
    firebaseMocks.getDatabaseInstance.mockResolvedValue({});
    firebaseMocks.ref.mockImplementation((_database, path) => path);
    firebaseMocks.onValue.mockImplementation((reference) =>
      reference === 'live_events'
        ? firebaseMocks.unsubscribeLiveEvents
        : firebaseMocks.unsubscribeSpecialWebcasts,
    );
  });

  test('subscribes to the live events and special webcasts nodes', async () => {
    await renderWebcasts();

    expect(firebaseMocks.ref).toHaveBeenCalledWith({}, 'live_events');
    expect(firebaseMocks.ref).toHaveBeenCalledWith({}, 'special_webcasts');
  });

  test('is loading until both nodes have answered', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', {
      '2024casj': {
        key: '2024casj',
        name: 'Silicon Valley',
        webcasts: [twitch],
      },
    });
    await waitFor(() =>
      expect(Object.keys(result.current.webcasts)).toEqual(['2024casj-0']),
    );

    expect(result.current.isLoading).toBe(true);
  });

  test('stops loading once both nodes have answered', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', null);
    publish('special_webcasts', null);

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.webcasts).toEqual({});
  });

  test('names a single event webcast after the event short name', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', {
      '2024casj': {
        key: '2024casj',
        name: 'Silicon Valley Regional',
        short_name: 'Silicon Valley',
        webcasts: [{ ...twitch, status: 'online', viewer_count: 12 }],
      },
    });
    publish('special_webcasts', null);

    await waitFor(() =>
      expect(result.current.webcasts).toEqual({
        '2024casj-0': {
          id: '2024casj-0',
          name: 'Silicon Valley',
          webcast: {
            type: 'twitch',
            channel: 'firstinspires',
            status: 'online',
            viewer_count: 12,
          },
          isSpecial: false,
        },
      }),
    );
  });

  test('falls back to the full event name without a short name', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', {
      '2024casj': {
        key: '2024casj',
        name: 'Silicon Valley Regional',
        webcasts: [twitch],
      },
    });
    publish('special_webcasts', null);

    await waitFor(() =>
      expect(result.current.webcasts['2024casj-0'].name).toBe(
        'Silicon Valley Regional',
      ),
    );
  });

  test('numbers the webcasts of a multi-stream event', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', {
      '2024cmptx': {
        key: '2024cmptx',
        name: 'Einstein',
        webcasts: [twitch, { type: 'youtube', channel: 'abc' }],
      },
    });
    publish('special_webcasts', null);

    await waitFor(() =>
      expect(
        Object.values(result.current.webcasts).map(({ id, name }) => [
          id,
          name,
        ]),
      ).toEqual([
        ['2024cmptx-0', 'Einstein 1'],
        ['2024cmptx-1', 'Einstein 2'],
      ]),
    );
  });

  test('skips events without webcasts', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', {
      '2024a': { key: '2024a', name: 'A', webcasts: [] },
      '2024b': { key: '2024b', name: 'B' },
    });
    publish('special_webcasts', null);

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.webcasts).toEqual({});
  });

  test('marks special webcasts and keys them by their key name', async () => {
    const { result } = await renderWebcasts();

    publish('live_events', null);
    publish('special_webcasts', {
      frn: { key_name: 'frn', name: 'FRN', type: 'twitch', channel: 'frn' },
    });

    await waitFor(() =>
      expect(result.current.webcasts).toEqual({
        'frn-0': {
          id: 'frn-0',
          name: 'FRN',
          webcast: { type: 'twitch', channel: 'frn' },
          isSpecial: true,
        },
      }),
    );
  });

  test('unsubscribes from both nodes on unmount', async () => {
    const { unmount } = await renderWebcasts();

    unmount();

    expect(firebaseMocks.unsubscribeLiveEvents).toHaveBeenCalledOnce();
    expect(firebaseMocks.unsubscribeSpecialWebcasts).toHaveBeenCalledOnce();
  });
});
