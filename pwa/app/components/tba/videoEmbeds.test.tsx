import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { TwitchEmbed, YoutubeEmbed } from '~/components/tba/videoEmbeds';

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

  vi.stubGlobal('requestIdleCallback', requestIdleCallback);
  vi.stubGlobal('cancelIdleCallback', vi.fn());

  return {
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
      src: iframe.getAttribute('src'),
    }).toEqual({
      allowFullscreen: true,
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

describe('YoutubeEmbed click to play', () => {
  test('waits for a click before loading the player', () => {
    render(<YoutubeEmbed videoId="V4lDQSlvi7Q" title="Webcast" clickToPlay />);

    expect(screen.queryByTitle('Webcast')).toBeNull();
  });

  test('plays the video when clicked', () => {
    render(<YoutubeEmbed videoId="V4lDQSlvi7Q" title="Webcast" clickToPlay />);

    fireEvent.click(screen.getByRole('button', { name: 'Play Webcast' }));

    expect(screen.getByTitle('Webcast').getAttribute('src')).toBe(
      'https://www.youtube.com/embed/V4lDQSlvi7Q?autoplay=1',
    );
  });
});

describe('TwitchEmbed', () => {
  test('waits for a click before loading the player', () => {
    render(<TwitchEmbed channel="firstinspires" title="Webcast" />);

    expect(screen.queryByTitle('Webcast')).toBeNull();
  });

  test('plays the channel when clicked', () => {
    render(<TwitchEmbed channel="firstinspires" title="Webcast" />);

    fireEvent.click(screen.getByRole('button', { name: 'Play Webcast' }));

    expect(screen.getByTitle('Webcast').getAttribute('src')).toBe(
      'https://player.twitch.tv/?channel=firstinspires&parent=localhost',
    );
  });
});
