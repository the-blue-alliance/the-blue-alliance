import { describe, expect, test } from 'vitest';

import type { Media } from '~/api/tba/read';
import {
  getCadModelName,
  getEmbedMedia,
  getEventVideos,
  getImageMedia,
  getMediaImageUrl,
  getMediaLinkUrl,
  getMediaThumbSrcSet,
  getMediaThumbUrl,
  getSmugmugAlbums,
  getTeamPreferredRobotPicMedium,
} from '~/lib/mediaUtils';

function imgurMedia(overrides: Partial<Media> = {}): Media {
  return {
    type: 'imgur',
    foreign_key: 'aB3d9Xk',
    team_keys: ['frc254'],
    preferred: true,
    view_url: 'https://imgur.com/aB3d9Xk',
    direct_url: 'https://i.imgur.com/aB3d9Xk.jpg',
    details: {},
    ...overrides,
  } as Media;
}

function cdThreadMedia(overrides: Partial<Media> = {}): Media {
  return {
    type: 'cd-thread',
    foreign_key: '12345',
    team_keys: ['frc254'],
    preferred: false,
    view_url: 'https://www.chiefdelphi.com/t/12345',
    direct_url: undefined,
    details: {
      thread_title: 'Robot',
      image_url: 'https://www.chiefdelphi.com/uploads/robot.jpg',
    },
    ...overrides,
  } as Media;
}

function externalLinkMedia(overrides: Partial<Media> = {}): Media {
  return {
    type: 'external-link',
    foreign_key: 'https://example.com/robot.jpg',
    team_keys: ['frc254'],
    preferred: false,
    direct_url: 'https://example.com/robot.jpg',
    details: {},
    ...overrides,
  } as Media;
}

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

describe('getMediaLinkUrl', () => {
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

describe('getSmugmugAlbums', () => {
  test('keeps only smugmug-album media', () => {
    const media = [smugmugAlbum(), smugmugPhoto(), youtubeMedia('abc')];
    expect(getSmugmugAlbums(media)).toEqual([smugmugAlbum()]);
  });

  test('returns an empty array when there are no albums', () => {
    expect(getSmugmugAlbums([youtubeMedia('abc')])).toEqual([]);
  });
});

describe('getMediaThumbUrl', () => {
  test('imgur inserts the large size suffix before the extension', () => {
    expect(getMediaThumbUrl(imgurMedia())).toBe(
      'https://i.imgur.com/aB3d9Xkl.jpg',
    );
  });

  test('imgur preserves the original extension', () => {
    const media = imgurMedia({
      direct_url: 'https://i.imgur.com/aB3d9Xk.png',
    });
    expect(getMediaThumbUrl(media)).toBe('https://i.imgur.com/aB3d9Xkl.png');
  });

  test('imgur non-i.imgur.com URLs are returned unchanged', () => {
    const media = imgurMedia({
      direct_url: 'https://imgur.com/a/aB3d9Xk',
    });
    expect(getMediaThumbUrl(media)).toBe('https://imgur.com/a/aB3d9Xk');
  });

  test('imgur already-suffixed URLs are not double-suffixed', () => {
    const media = imgurMedia({
      direct_url: 'https://i.imgur.com/aB3d9Xkl.jpg',
    });
    expect(getMediaThumbUrl(media)).toBe('https://i.imgur.com/aB3d9Xkl.jpg');
  });

  test('imgur missing direct_url falls back to undefined', () => {
    const media = imgurMedia({ direct_url: undefined });
    expect(getMediaThumbUrl(media)).toBeUndefined();
  });

  test('imgur malformed direct_url falls back to the raw value', () => {
    const media = imgurMedia({ direct_url: 'not a url' });
    expect(getMediaThumbUrl(media)).toBe('not a url');
  });

  test('smugmug-photo uses the medium image', () => {
    expect(getMediaThumbUrl(smugmugPhoto())).toBe(
      'https://photos.smugmug.com/x-M.jpg',
    );
  });

  test('smugmug-photo falls back to direct_url without details', () => {
    const media = smugmugPhoto({ details: undefined });
    expect(getMediaThumbUrl(media)).toBe('https://photos.smugmug.com/x-L.jpg');
  });

  test('smugmug-album uses the medium cover image', () => {
    expect(getMediaThumbUrl(smugmugAlbum())).toBe(
      'https://photos.smugmug.com/i-57rxPBW-M.png',
    );
  });

  test('cd-thread matches getMediaImageUrl', () => {
    const media = cdThreadMedia();
    expect(getMediaThumbUrl(media)).toBe(getMediaImageUrl(media));
  });

  test('external-link matches getMediaImageUrl', () => {
    const media = externalLinkMedia();
    expect(getMediaThumbUrl(media)).toBe(getMediaImageUrl(media));
  });
});

describe('getMediaThumbSrcSet', () => {
  test('imgur returns 1x/2x descriptors', () => {
    expect(getMediaThumbSrcSet(imgurMedia())).toBe(
      'https://i.imgur.com/aB3d9Xkl.jpg 1x, https://i.imgur.com/aB3d9Xkh.jpg 2x',
    );
  });

  test('imgur without a usable direct_url returns undefined', () => {
    expect(
      getMediaThumbSrcSet(imgurMedia({ direct_url: 'https://imgur.com/x' })),
    ).toBeUndefined();
  });

  test('non-imgur media returns undefined', () => {
    expect(getMediaThumbSrcSet(smugmugPhoto())).toBeUndefined();
  });
});

describe('getEventVideos', () => {
  test('keeps only youtube media', () => {
    const media = [youtubeMedia('abc'), youtubeMedia('def'), smugmugAlbum()];
    expect(getEventVideos(media).map((m) => m.foreign_key)).toEqual([
      'abc',
      'def',
    ]);
  });
});

function media(type: Media['type'], overrides: Partial<Media> = {}): Media {
  return {
    type,
    foreign_key: 'key',
    team_keys: ['frc254'],
    preferred: false,
    details: {},
    ...overrides,
  } as Media;
}

describe('getMediaImageUrl', () => {
  test('cd-thread uses the thread image', () => {
    expect(getMediaImageUrl(cdThreadMedia())).toBe(
      'https://www.chiefdelphi.com/uploads/robot.jpg',
    );
  });

  test('cd-thread without an image has no url', () => {
    expect(
      getMediaImageUrl(cdThreadMedia({ details: {} as Media['details'] })),
    ).toBeUndefined();
  });

  test('other types use the direct url', () => {
    expect(getMediaImageUrl(imgurMedia())).toBe(
      'https://i.imgur.com/aB3d9Xk.jpg',
    );
  });

  test('an empty direct url is treated as missing', () => {
    expect(getMediaImageUrl(imgurMedia({ direct_url: '' }))).toBeUndefined();
  });
});

describe('getMediaThumbUrl', () => {
  test('imgur urls without an image extension are returned unchanged', () => {
    const url = 'https://i.imgur.com/gallery/aB3d9Xk';

    expect(getMediaThumbUrl(imgurMedia({ direct_url: url }))).toBe(url);
  });
});

describe('getEmbedMedia', () => {
  test('keeps only embeddable image media', () => {
    const items = [
      imgurMedia(),
      media('instagram-image'),
      cdThreadMedia(),
      externalLinkMedia(),
      youtubeMedia('abc'),
    ];

    expect(getEmbedMedia(items).map((m) => m.type)).toEqual([
      'imgur',
      'instagram-image',
      'cd-thread',
    ]);
  });
});

describe('getMediaLinkUrl', () => {
  test('imgur links to its view url', () => {
    expect(getMediaLinkUrl(imgurMedia())).toBe('https://imgur.com/aB3d9Xk');
  });

  test('imgur builds a link from the key without a view url', () => {
    expect(getMediaLinkUrl(imgurMedia({ view_url: undefined }))).toBe(
      'https://imgur.com/aB3d9Xk',
    );
  });

  test('instagram links to its view url', () => {
    const item = media('instagram-image', {
      view_url: 'https://www.instagram.com/p/xyz/',
    });

    expect(getMediaLinkUrl(item)).toBe('https://www.instagram.com/p/xyz/');
  });

  test('instagram builds a link from the key without a view url', () => {
    expect(
      getMediaLinkUrl(media('instagram-image', { foreign_key: 'xyz' })),
    ).toBe('https://www.instagram.com/p/xyz/');
  });

  test('cdphotothread links to the chief delphi image', () => {
    const item = media('cdphotothread', {
      details: { image_partial: 'abc.jpg' } as Media['details'],
    });

    expect(getMediaLinkUrl(item)).toBe(
      'https://www.chiefdelphi.com/media/img/abc.jpg',
    );
  });

  test('cdphotothread without an image partial has no link', () => {
    expect(getMediaLinkUrl(media('cdphotothread'))).toBeUndefined();
  });

  test('cd-thread links to the thread', () => {
    expect(getMediaLinkUrl(cdThreadMedia())).toBe(
      'https://www.chiefdelphi.com/t/12345',
    );
  });

  test('grabcad links to the model', () => {
    expect(getMediaLinkUrl(media('grabcad', { foreign_key: 'robot-1' }))).toBe(
      'https://grabcad.com/library/robot-1',
    );
  });

  test('onshape links to the document', () => {
    expect(getMediaLinkUrl(media('onshape', { foreign_key: 'doc1' }))).toBe(
      'https://cad.onshape.com/documents/doc1',
    );
  });

  test('external links use the key as the url', () => {
    expect(getMediaLinkUrl(externalLinkMedia())).toBe(
      'https://example.com/robot.jpg',
    );
  });

  test('video media has no link', () => {
    expect(getMediaLinkUrl(youtubeMedia('abc'))).toBeUndefined();
  });
});

describe('getCadModelName', () => {
  test('uses the model name from grabcad details', () => {
    const item = media('grabcad', {
      details: { model_name: 'Swerve Module' } as Media['details'],
    });

    expect(getCadModelName(item)).toBe('Swerve Module');
  });

  test('falls back to a generic name without details', () => {
    expect(getCadModelName(media('onshape'))).toBe('CAD Model');
  });

  test('non-CAD media gets the generic name', () => {
    expect(getCadModelName(imgurMedia())).toBe('CAD Model');
  });
});

describe('getImageMedia', () => {
  test('keeps only image media', () => {
    const items = [youtubeMedia('abc'), cdThreadMedia(), smugmugPhoto()];

    expect(getImageMedia(items).map((m) => m.type)).toEqual(['cd-thread']);
  });

  test('puts preferred images first', () => {
    const items = [
      imgurMedia({ foreign_key: 'second', preferred: false }),
      imgurMedia({ foreign_key: 'first', preferred: true }),
      imgurMedia({ foreign_key: 'third', preferred: false }),
    ];

    expect(getImageMedia(items).map((m) => m.foreign_key)).toEqual([
      'first',
      'second',
      'third',
    ]);
  });
});

describe('getTeamPreferredRobotPicMedium', () => {
  test('returns the url of the preferred image', () => {
    const items = [
      imgurMedia({ preferred: false, direct_url: 'https://i.imgur.com/a.jpg' }),
      imgurMedia({ preferred: true, direct_url: 'https://i.imgur.com/b.jpg' }),
    ];

    expect(getTeamPreferredRobotPicMedium(items)).toBe(
      'https://i.imgur.com/b.jpg',
    );
  });

  test('is undefined without a preferred image', () => {
    expect(
      getTeamPreferredRobotPicMedium([imgurMedia({ preferred: false })]),
    ).toBeUndefined();
  });
});
