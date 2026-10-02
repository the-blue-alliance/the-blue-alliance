import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { YoutubeEmbed } from '~/components/tba/videoEmbeds';

function setDocumentReadyState(state: DocumentReadyState) {
  vi.spyOn(document, 'readyState', 'get').mockReturnValue(state);
}

function stubIdleCallback() {
  let callback: IdleRequestCallback | undefined;
  const requestIdleCallback = vi.fn<typeof window.requestIdleCallback>(
    (scheduledCallback: IdleRequestCallback) => {
      callback = scheduledCallback;
      return 42;
    },
  );
  const cancelIdleCallback = vi.fn<typeof window.cancelIdleCallback>();

  vi.stubGlobal('requestIdleCallback', requestIdleCallback);
  vi.stubGlobal('cancelIdleCallback', cancelIdleCallback);

  return {
    cancelIdleCallback,
    requestIdleCallback,
    runCallback: () => {
      if (!callback) {
        throw new Error('No idle callback was scheduled');
      }
      callback({ didTimeout: false, timeRemaining: () => 50 });
    },
  };
}

afterEach(() => {
  vi.useRealTimers();
});

describe('YoutubeEmbed', () => {
  test('renders the video immediately by default', () => {
    render(<YoutubeEmbed videoId="dQw4w9WgXcQ" title="Qualification 1" />);

    const iframe = screen.getByTitle('Qualification 1') as HTMLIFrameElement;
    expect({
      allowFullscreen: iframe.allowFullscreen,
      loading: iframe.getAttribute('loading'),
      src: iframe.getAttribute('src'),
    }).toEqual({
      allowFullscreen: true,
      loading: 'lazy',
      src: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
    });
  });

  test('converts a YouTube timestamp to an embed start time', () => {
    render(<YoutubeEmbed videoId="dQw4w9WgXcQ?t=90" title="Qualification 1" />);

    expect(screen.getByTitle('Qualification 1').getAttribute('src')).toBe(
      'https://www.youtube.com/embed/dQw4w9WgXcQ?start=90',
    );
  });

  test('shows an accessible placeholder while loading is deferred', () => {
    setDocumentReadyState('loading');

    render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    expect(screen.getByText('Loading Qualification 1')).toBeTruthy();
  });

  test('does not schedule idle work before the window load event', () => {
    setDocumentReadyState('loading');
    const { requestIdleCallback } = stubIdleCallback();

    render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    expect(requestIdleCallback).not.toHaveBeenCalled();
  });

  test('loads the deferred video through an idle callback after window load', () => {
    setDocumentReadyState('loading');
    const { runCallback } = stubIdleCallback();
    render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    act(() => {
      window.dispatchEvent(new Event('load'));
    });
    act(runCallback);

    expect(screen.getByTitle('Qualification 1')).toBeTruthy();
  });

  test('sets a two-second deadline when scheduling idle work', () => {
    setDocumentReadyState('complete');
    const { requestIdleCallback } = stubIdleCallback();

    render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    expect(requestIdleCallback).toHaveBeenCalledWith(expect.any(Function), {
      timeout: 2_000,
    });
  });

  test('loads the deferred video after the fallback timeout', () => {
    vi.useFakeTimers();
    setDocumentReadyState('complete');
    vi.stubGlobal('requestIdleCallback', undefined);

    render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );
    act(() => {
      vi.advanceTimersByTime(1_000);
    });

    expect(screen.getByTitle('Qualification 1')).toBeTruthy();
  });

  test('cancels scheduled idle work when unmounted', () => {
    setDocumentReadyState('complete');
    const { cancelIdleCallback } = stubIdleCallback();
    const { unmount } = render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    unmount();

    expect(cancelIdleCallback).toHaveBeenCalledWith(42);
  });

  test('clears the fallback timeout when unmounted', () => {
    vi.useFakeTimers();
    setDocumentReadyState('complete');
    vi.stubGlobal('requestIdleCallback', undefined);
    const clearTimeout = vi.spyOn(window, 'clearTimeout');
    const { unmount } = render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    unmount();

    expect(clearTimeout).toHaveBeenCalledOnce();
  });

  test('removes the pending load listener when unmounted', () => {
    setDocumentReadyState('loading');
    const { requestIdleCallback } = stubIdleCallback();
    const { unmount } = render(
      <YoutubeEmbed
        videoId="dQw4w9WgXcQ"
        title="Qualification 1"
        deferUntilIdle
      />,
    );

    unmount();
    window.dispatchEvent(new Event('load'));

    expect(requestIdleCallback).not.toHaveBeenCalled();
  });
});
