import { act, renderHook } from '@testing-library/react';
import { renderToString } from 'react-dom/server';
import { describe, expect, test, vi } from 'vitest';

import { useIsHydrated, useMediaQuery } from '~/lib/hooks';

type ChangeListener = (event: MediaQueryListEvent) => void;

function stubMatchMedia(matches: boolean) {
  const listeners = new Set<ChangeListener>();
  const mediaQueryList = {
    matches,
    addEventListener: vi.fn<(type: string, listener: ChangeListener) => void>(
      (_type: string, listener: ChangeListener) => {
        listeners.add(listener);
      },
    ),
    removeEventListener: vi.fn<
      (type: string, listener: ChangeListener) => void
    >((_type: string, listener: ChangeListener) => {
      listeners.delete(listener);
    }),
  };
  const matchMedia = vi.fn<(query: string) => typeof mediaQueryList>(
    (_query: string) => mediaQueryList,
  );
  vi.stubGlobal('matchMedia', matchMedia);
  return {
    matchMedia,
    mediaQueryList,
    listeners,
    emit(nextMatches: boolean) {
      for (const listener of listeners) {
        listener({ matches: nextMatches } as MediaQueryListEvent);
      }
    },
  };
}

function HydrationProbe() {
  return <span>{String(useIsHydrated())}</span>;
}

function MediaQueryProbe() {
  return <span>{String(useMediaQuery('(min-width: 768px)'))}</span>;
}

describe('useIsHydrated', () => {
  test('is false during server rendering', () => {
    expect(renderToString(<HydrationProbe />)).toBe('<span>false</span>');
  });

  test('becomes true once mounted on the client', () => {
    const { result } = renderHook(() => useIsHydrated());

    expect(result.current).toBe(true);
  });
});

describe('useMediaQuery', () => {
  test('is false during server rendering', () => {
    stubMatchMedia(true);

    expect(renderToString(<MediaQueryProbe />)).toBe('<span>false</span>');
  });

  test('reports the current match after mounting', () => {
    const media = stubMatchMedia(true);

    const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

    expect(media.matchMedia).toHaveBeenCalledWith('(min-width: 768px)');
    expect(result.current).toBe(true);
  });

  test('follows change events', () => {
    const media = stubMatchMedia(false);
    const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));
    expect(result.current).toBe(false);

    act(() => media.emit(true));
    expect(result.current).toBe(true);

    act(() => media.emit(false));
    expect(result.current).toBe(false);
  });

  test('removes its listener on unmount and when the query changes', () => {
    const media = stubMatchMedia(false);
    const { rerender, unmount } = renderHook(
      ({ query }) => useMediaQuery(query),
      { initialProps: { query: '(min-width: 768px)' } },
    );

    rerender({ query: '(min-width: 1024px)' });
    expect(media.matchMedia).toHaveBeenLastCalledWith('(min-width: 1024px)');
    expect(media.mediaQueryList.removeEventListener).toHaveBeenCalledTimes(1);
    expect(media.listeners.size).toBe(1);

    unmount();
    expect(media.mediaQueryList.removeEventListener).toHaveBeenCalledTimes(2);
    expect(media.listeners.size).toBe(0);
  });
});
