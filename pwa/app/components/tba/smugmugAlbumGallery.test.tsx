import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type { Media } from '~/api/tba/read';
import SmugmugAlbumGallery from '~/components/tba/smugmugAlbumGallery';

function album(details?: Partial<NonNullable<Media['details']>>): Media {
  return {
    type: 'smugmug-album',
    foreign_key: 'abc',
    team_keys: [],
    details: details && {
      cover_url: 'https://photos.example/c.jpg',
      cover_url_med: 'https://photos.example/c-med.jpg',
      cover_url_sm: 'https://photos.example/c-sm.jpg',
      image_count: 12,
      title: 'Day 1',
      web_uri: 'https://photos.example/album',
      ...details,
    },
  } as Media;
}

describe('SmugmugAlbumGallery', () => {
  test('renders nothing without albums', () => {
    const { container } = render(<SmugmugAlbumGallery albums={[]} />);
    expect(container.innerHTML).toBe('');
  });

  test('renders album cards and skips unusable media', () => {
    render(
      <SmugmugAlbumGallery
        albums={[
          album({}),
          album({ title: '', image_count: 1 }),
          album(undefined),
          album({ cover_url_med: '' }),
          {
            type: 'imgur',
            foreign_key: 'x',
            team_keys: [],
          } as Media,
        ]}
      />,
    );
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0].getAttribute('href')).toBe('https://photos.example/album');
    expect(screen.getByRole('img', { name: 'Day 1' }).getAttribute('src')).toBe(
      'https://photos.example/c-med.jpg',
    );
    expect(screen.getByText('12 photos')).toBeTruthy();
    expect(screen.getByRole('img', { name: 'SmugMug Album' })).toBeTruthy();
    expect(screen.getByText('1 photo')).toBeTruthy();
  });

  test('defaults the image count to zero', () => {
    const media = album({});
    if (media.details && 'image_count' in media.details) {
      Reflect.deleteProperty(media.details, 'image_count');
    }
    render(<SmugmugAlbumGallery albums={[media]} />);
    expect(screen.getByText('0 photos')).toBeTruthy();
  });
});
