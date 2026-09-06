import { describe, expect, test } from 'vitest';

import type { Media } from '~/api/tba/read';
import {
  getEventVideos,
  getMediaLinkUrl,
  getSmugmugAlbums,
} from '~/lib/mediaUtils';

function smugmugAlbum(overrides: Partial<Media> = {}): Media {
  return {
    type: 'smugmug-album',
    foreign_key: 'RRGxMR',
    team_keys: [],
    preferred: false,
    view_url: 'https://nefirst.smugmug.com/2026-INGENUITY-Awards',
    direct_url: 'https://photos.smugmug.com/i-57rxPBW-L.png',
    details: {
      cover_url: 'https://photos.smugmug.com/i-57rxPBW-L.png',
      cover_url_med: 'https://photos.smugmug.com/i-57rxPBW-M.png',
      cover_url_sm: 'https://photos.smugmug.com/i-57rxPBW-S.png',
      image_count: 1626,
      title: '2026 New England District Championship',
      web_uri: 'https://nefirst.smugmug.com/2026-INGENUITY-Awards',
    },
    ...overrides,
  } as Media;
}

function smugmugPhoto(overrides: Partial<Media> = {}): Media {
  return {
    type: 'smugmug-photo',
    foreign_key: 'xxrbgK6',
    team_keys: ['frc254'],
    preferred: false,
    view_url: 'https://nefirst.smugmug.com/i-xxrbgK6',
    direct_url: 'https://photos.smugmug.com/x-L.jpg',
    details: {
      caption: '',
      image_url: 'https://photos.smugmug.com/x-L.jpg',
      image_url_med: 'https://photos.smugmug.com/x-M.jpg',
      image_url_sm: 'https://photos.smugmug.com/x-S.jpg',
      title: 'Robot',
      web_uri: 'https://nefirst.smugmug.com/i-xxrbgK6',
    },
    ...overrides,
  } as Media;
}

function youtubeMedia(foreignKey: string): Media {
  return {
    type: 'youtube',
    foreign_key: foreignKey,
    team_keys: [],
    preferred: false,
    view_url: `https://youtu.be/${foreignKey}`,
    direct_url: `https://img.youtube.com/vi/${foreignKey}/hqdefault.jpg`,
    details: {},
  } as Media;
}

describe.concurrent('getMediaLinkUrl', () => {
  test('smugmug-album links to its web_uri', () => {
    expect(getMediaLinkUrl(smugmugAlbum())).toBe(
      'https://nefirst.smugmug.com/2026-INGENUITY-Awards',
    );
  });

  test('smugmug-photo links to its web_uri', () => {
    expect(getMediaLinkUrl(smugmugPhoto())).toBe(
      'https://nefirst.smugmug.com/i-xxrbgK6',
    );
  });

  test('smugmug falls back to view_url when details are missing', () => {
    const album = smugmugAlbum({ details: undefined });
    expect(getMediaLinkUrl(album)).toBe(
      'https://nefirst.smugmug.com/2026-INGENUITY-Awards',
    );
  });
});

describe.concurrent('getSmugmugAlbums', () => {
  test('keeps only smugmug-album media', () => {
    const media = [smugmugAlbum(), smugmugPhoto(), youtubeMedia('abc')];
    expect(getSmugmugAlbums(media)).toEqual([smugmugAlbum()]);
  });

  test('returns an empty array when there are no albums', () => {
    expect(getSmugmugAlbums([youtubeMedia('abc')])).toEqual([]);
  });
});

describe.concurrent('getEventVideos', () => {
  test('keeps only youtube media', () => {
    const media = [youtubeMedia('abc'), youtubeMedia('def'), smugmugAlbum()];
    expect(getEventVideos(media).map((m) => m.foreign_key)).toEqual([
      'abc',
      'def',
    ]);
  });
});
