import { act, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { Media } from '~/api/tba/read';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';

interface FakeApi {
  selectedScrollSnap: () => number;
  on: (event: string, cb: () => void) => void;
  off: (event: string, cb: () => void) => void;
}

const { carousel } = vi.hoisted(() => ({
  carousel: {
    selected: 0,
    listeners: new Set<() => void>(),
    setApi: undefined as ((api: FakeApi) => void) | undefined,
  },
}));

vi.mock('embla-carousel-autoplay', () => ({
  default: (options: unknown) => ({ name: 'autoplay', options }),
}));

// Embla needs real layout, so the carousel shell is replaced with one that
// hands the component a controllable API.
vi.mock('~/components/ui/carousel', () => ({
  Carousel: ({
    children,
    setApi,
  }: {
    children: ReactNode;
    setApi: (api: FakeApi) => void;
  }) => {
    carousel.setApi = setApi;
    return <div data-testid="carousel">{children}</div>;
  },
  CarouselContent: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
  CarouselItem: ({ children }: { children: ReactNode }) => (
    <div data-testid="slide">{children}</div>
  ),
  CarouselPrevious: () => <button type="button">Previous</button>,
  CarouselNext: () => <button type="button">Next</button>,
}));

const fakeApi: FakeApi = {
  selectedScrollSnap: () => carousel.selected,
  on: (_event, cb) => carousel.listeners.add(cb),
  off: (_event, cb) => carousel.listeners.delete(cb),
};

function imgur(key: string): Media {
  return {
    type: 'imgur',
    foreign_key: key,
    team_keys: ['frc254'],
    direct_url: `https://i.imgur.com/${key}.jpg`,
    view_url: `https://imgur.com/${key}`,
  } as Media;
}

/** The slide images are decorative (empty alt), so they have no img role. */
function images() {
  return Array.from(document.querySelectorAll('img'));
}

function loadedSlides() {
  return screen
    .getAllByTestId('slide')
    .map((slide) => slide.querySelector('img') !== null);
}

describe('TeamRobotPicsCarousel', () => {
  test('lazily loads images around the selected slide', () => {
    carousel.selected = 0;
    carousel.listeners.clear();
    const media = ['aaaaaaa', 'bbbbbbb', 'ccccccc', 'ddddddd', 'eeeeeee'].map(
      imgur,
    );
    const { unmount } = render(<TeamRobotPicsCarousel media={media} />);
    expect(loadedSlides()).toEqual([true, true, false, false, false]);
    const first = images()[0];
    expect(first.getAttribute('loading')).toBe('eager');
    expect(first.getAttribute('fetchpriority')).toBe('high');
    expect(first.getAttribute('srcset')).toBe(
      'https://i.imgur.com/aaaaaaal.jpg 1x, https://i.imgur.com/aaaaaaah.jpg 2x',
    );
    expect(images()[1].getAttribute('loading')).toBe('lazy');
    expect(screen.getByRole('button', { name: 'Next' })).toBeTruthy();

    act(() => {
      carousel.setApi?.(fakeApi);
    });
    expect(carousel.listeners.size).toBe(1);

    carousel.selected = 3;
    act(() => {
      carousel.listeners.forEach((cb) => cb());
    });
    expect(loadedSlides()).toEqual([true, true, true, true, true]);

    unmount();
    expect(carousel.listeners.size).toBe(0);
  });

  test('renders unlinked images, skips media without images, and hides arrows for one slide', () => {
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
    expect(images()[0].parentElement?.tagName).toBe('DIV');
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
    expect(screen.getAllByTestId('slide')).toHaveLength(1);
    expect(screen.getByRole('link').getAttribute('href')).toBe(
      'https://imgur.com/aaaaaaa',
    );
  });
});
