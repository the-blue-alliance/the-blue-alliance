import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { type Event, WebcastStatus } from '~/api/tba/read';
import type { WebcastWithMeta } from '~/lib/gameday/types';
import { useOnlineEventWebcasts } from '~/lib/gameday/useOnlineEventWebcasts';

const webcastMocks = vi.hoisted(() => ({
  useFirebaseWebcasts:
    vi.fn<
      () => { webcasts: Record<string, WebcastWithMeta>; isLoading: boolean }
    >(),
}));

vi.mock('~/lib/gameday/useFirebaseWebcasts', () => ({
  useFirebaseWebcasts: webcastMocks.useFirebaseWebcasts,
}));

function webcast(
  id: string,
  status: WebcastStatus,
  isSpecial = false,
): WebcastWithMeta {
  return {
    id,
    name: id,
    isSpecial,
    webcast: { type: 'twitch', channel: id, status },
  };
}

const event = { key: '2024casj' } as Event;

describe('useOnlineEventWebcasts', () => {
  beforeEach(() => {
    webcastMocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: {},
      isLoading: false,
    });
  });

  test('reports an event with an online webcast as live', () => {
    webcastMocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: { '2024casj-0': webcast('2024casj-0', WebcastStatus.ONLINE) },
      isLoading: false,
    });

    const { result } = renderHook(() => useOnlineEventWebcasts());

    expect(result.current(event)).toBe(true);
  });

  test('reports an event whose webcasts are offline as not live', () => {
    webcastMocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: { '2024casj-0': webcast('2024casj-0', WebcastStatus.OFFLINE) },
      isLoading: false,
    });

    const { result } = renderHook(() => useOnlineEventWebcasts());

    expect(result.current(event)).toBe(false);
  });

  test('reports an event without webcasts as not live', () => {
    const { result } = renderHook(() => useOnlineEventWebcasts());

    expect(result.current(event)).toBe(false);
  });

  test('ignores special webcasts that are not tied to an event', () => {
    webcastMocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: {
        '2024casj-0': webcast('2024casj-0', WebcastStatus.ONLINE, true),
      },
      isLoading: false,
    });

    const { result } = renderHook(() => useOnlineEventWebcasts());

    expect(result.current(event)).toBe(false);
  });

  test('reports nothing as live while Firebase is still loading', () => {
    webcastMocks.useFirebaseWebcasts.mockReturnValue({
      webcasts: { '2024casj-0': webcast('2024casj-0', WebcastStatus.ONLINE) },
      isLoading: true,
    });

    const { result } = renderHook(() => useOnlineEventWebcasts());

    expect(result.current(event)).toBe(false);
  });
});
