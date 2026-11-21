import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import type { Media } from '~/api/tba/read';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';

class FakeIntersectionObserver {
  observe() {}
  disconnect() {}
}

beforeEach(() => {
  vi.stubGlobal('IntersectionObserver', FakeIntersectionObserver);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function imgur(key: string): Media {
  return {
    type: 'imgur',
    foreign_key: key,
    team_keys: ['frc254'],
    direct_url: `https://i.imgur.com/${key}.jpg`,
    view_url: `https://imgur.com/${key}`,
  } as Media;
}

const fiveRobots = ['aaaaaaa', 'bbbbbbb', 'ccccccc', 'ddddddd', 'eeeeeee'].map(
  imgur,
);

function images() {
  return Array.from(document.querySelectorAll('img'));
}

function loadedSlides() {
  return Array.from(
    document.querySelectorAll('[aria-roledescription="slide"]'),
  ).map((slide) => slide.querySelector('img') !== null);
}

function currentDot() {
  return document
    .querySelector('[aria-current="true"]')
    ?.getAttribute('aria-label');
}

describe('TeamRobotPicsCarousel', () => {
  test('loads only the first two images initially', () => {
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    expect(loadedSlides()).toEqual([true, true, false, false, false]);
  });

  test('loads the first image eagerly at the default priority', () => {
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    expect([
      images()[0].getAttribute('loading'),
      images()[0].getAttribute('fetchpriority'),
    ]).toEqual(['eager', 'auto']);
  });

  test('shows the medium imgur thumbnail for the first image', () => {
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    expect(images()[0].getAttribute('src')).toBe(
      'https://i.imgur.com/aaaaaaam.jpg',
    );
  });

  test('links the first image to the huge imgur thumbnail', () => {
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    expect(images()[0].closest('a')?.getAttribute('href')).toBe(
      'https://i.imgur.com/aaaaaaah.jpg',
    );
  });

  test('loads the image after the next slide when next is clicked', () => {
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    fireEvent.click(screen.getByRole('button', { name: 'Next slide' }));

    expect(loadedSlides()).toEqual([true, true, true, false, false]);
  });

  test('autoplays to the next slide after five seconds', () => {
    vi.useFakeTimers();
    render(<TeamRobotPicsCarousel media={fiveRobots} />);

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(currentDot()).toBe('Go to slide 2');
  });

  test('autoplay wraps from the last slide to the first', () => {
    vi.useFakeTimers();
    render(<TeamRobotPicsCarousel media={fiveRobots} />);
    fireEvent.click(screen.getByRole('button', { name: 'Go to slide 5' }));

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(currentDot()).toBe('Go to slide 1');
  });

  test('renders an unlinked image without a link', () => {
    render(
      <TeamRobotPicsCarousel
        media={[
          {
            type: 'external-link',
            foreign_key: '',
            team_keys: [],
            direct_url: 'https://robots.example/bot.png',
          } as Media,
        ]}
      />,
    );

    expect(screen.queryByRole('link')).toBeNull();
  });

  test('hides navigation for a single slide', () => {
    render(<TeamRobotPicsCarousel media={[imgur('aaaaaaa')]} />);

    expect(screen.queryByRole('button')).toBeNull();
  });

  test('skips media without an image', () => {
    render(
      <TeamRobotPicsCarousel
        media={[
          { type: 'youtube', foreign_key: 'x', team_keys: [] } as Media,
          imgur('aaaaaaa'),
        ]}
      />,
    );

    expect(loadedSlides()).toEqual([true]);
  });

  test('drops a slide whose image fails to load', () => {
    render(
      <TeamRobotPicsCarousel media={[imgur('aaaaaaa'), imgur('bbbbbbb')]} />,
    );

    fireEvent.error(images()[0]);

    expect(loadedSlides()).toEqual([true]);
  });

  test('hides the carousel when every image fails to load', () => {
    render(<TeamRobotPicsCarousel media={[imgur('aaaaaaa')]} />);

    fireEvent.error(images()[0]);

    expect(screen.queryByRole('region', { name: 'Robot pictures' })).toBeNull();
  });

  test('hides the carousel when the image failed before mounting', () => {
    vi.spyOn(HTMLImageElement.prototype, 'complete', 'get').mockReturnValue(
      true,
    );

    render(<TeamRobotPicsCarousel media={[imgur('aaaaaaa')]} />);

    expect(screen.queryByRole('region', { name: 'Robot pictures' })).toBeNull();
  });
});
