import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import type { Media } from '~/api/tba/read';
import TeamMediaGallery from '~/components/tba/teamMediaGallery';

vi.mock('react-social-media-embed', () => ({
  InstagramEmbed: ({ url }: { url: string }) => (
    <div data-testid="instagram">{url}</div>
  ),
}));

function imgur(key: string, directUrl?: string): Media {
  return {
    type: 'imgur',
    foreign_key: key,
    team_keys: ['frc254'],
    direct_url: directUrl ?? `https://i.imgur.com/${key}.jpg`,
    view_url: `https://imgur.com/${key}`,
  } as Media;
}

const imageProps = ['complete', 'naturalWidth', 'naturalHeight'] as const;

/** jsdom never loads images, so fake the load state every image reports. */
function stubImages(state: {
  complete: boolean;
  naturalWidth?: number;
  naturalHeight?: number;
}) {
  for (const prop of imageProps) {
    Object.defineProperty(HTMLImageElement.prototype, prop, {
      configurable: true,
      get: () => state[prop] ?? 0,
    });
  }
}

afterEach(() => {
  for (const prop of imageProps) {
    Reflect.deleteProperty(HTMLImageElement.prototype, prop);
  }
});

describe('TeamMediaGallery', () => {
  test('renders nothing without embeddable media', () => {
    const { container } = render(
      <TeamMediaGallery
        media={[
          { type: 'youtube', foreign_key: 'abc', team_keys: [] } as Media,
        ]}
      />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('shows imgur images that already loaded and hides removed ones', () => {
    stubImages({ complete: true, naturalWidth: 640, naturalHeight: 480 });
    render(<TeamMediaGallery media={[imgur('abcdefg')]} />);
    const link = screen.getByRole('link');
    expect(link.getAttribute('href')).toBe('https://imgur.com/abcdefg');
    expect(
      screen.getByRole('img', { name: 'Team media' }).getAttribute('src'),
    ).toBe('https://i.imgur.com/abcdefgl.jpg');
  });

  test('hides imgur removed placeholders', () => {
    stubImages({ complete: true, naturalWidth: 161, naturalHeight: 81 });
    render(<TeamMediaGallery media={[imgur('abcdefg')]} />);
    expect(screen.getByTestId('team-media-gallery').innerHTML).toBe('');
  });

  test('waits for in-flight imgur loads', () => {
    stubImages({ complete: false });
    const { unmount } = render(
      <TeamMediaGallery media={[imgur('aaaaaaa'), imgur('bbbbbbb')]} />,
    );
    const [first, second] = Array.from(
      screen.getByTestId('team-media-gallery').querySelectorAll('img'),
    );
    expect(first.className).toBe('hidden');

    act(() => {
      first.dispatchEvent(new Event('load'));
      second.dispatchEvent(new Event('error'));
    });
    expect(screen.getAllByRole('img', { name: 'Team media' })).toHaveLength(1);
    unmount();
  });

  test('skips imgur media without an image url', () => {
    render(<TeamMediaGallery media={[imgur('ccccccc', '')]} />);
    expect(screen.getByTestId('team-media-gallery').innerHTML).toBe('');
  });

  test('embeds instagram images and CD threads', () => {
    render(
      <TeamMediaGallery
        media={[
          {
            type: 'instagram-image',
            foreign_key: 'xyz',
            team_keys: [],
          } as Media,
          {
            type: 'cd-thread',
            foreign_key: '12345',
            team_keys: [],
            details: {
              image_url: 'https://cd.example/robot.jpg',
              thread_title: 'Robot reveal',
            },
          } as Media,
          {
            type: 'cd-thread',
            foreign_key: '67890',
            team_keys: [],
            details: {
              image_url: 'https://cd.example/untitled.jpg',
              thread_title: '',
            },
          } as Media,
          {
            type: 'cd-thread',
            foreign_key: '11111',
            team_keys: [],
          } as Media,
        ]}
      />,
    );
    expect(screen.getByTestId('instagram').textContent).toBe(
      'https://www.instagram.com/p/xyz/',
    );
    const [titled, untitled] = screen.getAllByRole('link');
    expect(titled.getAttribute('href')).toBe(
      'https://www.chiefdelphi.com/t/12345',
    );
    expect(titled.textContent).toBe('Robot reveal');
    expect(screen.getByRole('img', { name: 'Robot reveal' })).toBeTruthy();
    expect(untitled.textContent).toBe('');
    expect(untitled.querySelector('img')?.getAttribute('alt')).toBe('');
  });
});
