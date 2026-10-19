import { act, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import type { Media } from '~/api/tba/read';
import TeamMediaGallery from '~/components/tba/teamMediaGallery';

vi.mock('react-social-media-embed', () => ({
  InstagramEmbed: function InstagramEmbed({ url }: { url: string }) {
    const [embeddedUrl] = useState(url);
    return <div data-testid="instagram">{embeddedUrl}</div>;
  },
}));

function instagram(key: string): Media {
  return {
    type: 'instagram-image',
    foreign_key: key,
    team_keys: [],
  } as Media;
}

function imgur(key: string, directUrl?: string): Media {
  return {
    type: 'imgur',
    foreign_key: key,
    team_keys: ['frc254'],
    direct_url: directUrl ?? `https://i.imgur.com/${key}.jpg`,
    view_url: `https://imgur.com/${key}`,
  } as Media;
}

function cad(
  type: 'grabcad' | 'onshape',
  key: string,
  directUrl: string,
): Media {
  return {
    type,
    foreign_key: key,
    team_keys: ['frc1768'],
    direct_url: directUrl,
    details: {
      model_name: 'Nightshade 2026',
      model_description: null,
      model_image: directUrl,
      model_created: null,
    },
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

  test('links an Onshape model to its document', () => {
    render(
      <TeamMediaGallery
        media={[cad('onshape', 'abc/w/def', 'https://cad.example/s.png')]}
      />,
    );
    expect(screen.getByRole('link').getAttribute('href')).toBe(
      'https://cad.onshape.com/documents/abc/w/def',
    );
  });

  test('links a GrabCAD model to its library page', () => {
    render(
      <TeamMediaGallery
        media={[cad('grabcad', 'nightshade-1', 'https://cad.example/l.png')]}
      />,
    );
    expect(screen.getByRole('link').getAttribute('href')).toBe(
      'https://grabcad.com/library/nightshade-1',
    );
  });

  test('captions a CAD model with its name', () => {
    render(
      <TeamMediaGallery
        media={[cad('onshape', 'abc/w/def', 'https://cad.example/s.png')]}
      />,
    );
    expect(screen.getByRole('link').textContent).toBe('Nightshade 2026');
  });

  test('shows the CAD thumbnail', () => {
    render(
      <TeamMediaGallery
        media={[cad('onshape', 'abc/w/def', 'https://cad.example/s.png')]}
      />,
    );
    expect(
      screen.getByRole('img', { name: 'Nightshade 2026' }).getAttribute('src'),
    ).toBe('https://cad.example/s.png');
  });

  test('marks Onshape models with an Onshape badge', () => {
    render(
      <TeamMediaGallery
        media={[cad('onshape', 'abc/w/def', 'https://cad.example/s.png')]}
      />,
    );
    expect(screen.getAllByAltText('Onshape').length).toBeGreaterThan(0);
  });

  test('leaves the Onshape badge off GrabCAD models', () => {
    render(
      <TeamMediaGallery
        media={[cad('grabcad', 'nightshade-1', 'https://cad.example/l.png')]}
      />,
    );
    expect(screen.queryAllByAltText('Onshape')).toHaveLength(0);
  });

  test('skips CAD media without a thumbnail', () => {
    render(<TeamMediaGallery media={[cad('onshape', 'abc/w/def', '')]} />);
    expect(screen.getByTestId('team-media-gallery').innerHTML).toBe('');
  });

  test('lists instagram posts before imgur images', () => {
    stubImages({ complete: true, naturalWidth: 640, naturalHeight: 480 });
    render(<TeamMediaGallery media={[imgur('abcdefg'), instagram('xyz')]} />);
    expect(
      screen
        .getByTestId('team-media-gallery')
        .firstElementChild?.getAttribute('data-testid'),
    ).toBe('instagram');
  });

  test('replaces instagram embeds when the media list changes', () => {
    const { rerender } = render(
      <TeamMediaGallery media={[instagram('old')]} />,
    );
    rerender(
      <TeamMediaGallery media={[instagram('new1'), instagram('new2')]} />,
    );
    expect(
      screen.getAllByTestId('instagram').map((e) => e.textContent),
    ).toEqual([
      'https://www.instagram.com/p/new1/',
      'https://www.instagram.com/p/new2/',
    ]);
  });
});
