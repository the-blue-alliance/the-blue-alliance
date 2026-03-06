import { match } from 'ts-pattern';

import { Media } from '~/api/tba/read';

/** Media types that represent displayable images. */
export const IMAGE_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'imgur',
  'cdphotothread',
  'cd-thread',
  'external-link',
]);

/** Media types that represent CAD models. */
export const CAD_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'grabcad',
  'onshape',
]);

/** Returns the image URL for a media item, handling type-specific URL formats. */
export function getMediaImageUrl(media: Media): string | undefined {
  return match(media)
    .with({ type: 'imgur' }, (m) => `https://i.imgur.com/${m.foreign_key}m.jpg`)
    .with({ type: 'cd-thread' }, (m) => {
      const details = m.details as { image_url?: string } | undefined;
      return details?.image_url;
    })
    .otherwise((m) => m.direct_url);
}

/** Returns the full-size image URL (for lightbox/detail views). */
export function getMediaImageUrlFull(media: Media): string | undefined {
  return match(media)
    .with({ type: 'imgur' }, (m) => `https://i.imgur.com/${m.foreign_key}h.jpg`)
    .with({ type: 'cd-thread' }, (m) => {
      const details = m.details as { image_url?: string } | undefined;
      return details?.image_url;
    })
    .otherwise((m) => m.direct_url);
}

/** Returns the link URL for a media item (where clicking should navigate). */
export function getMediaLinkUrl(media: Media): string | undefined {
  return match(media)
    .with({ type: 'imgur' }, (m) => `https://imgur.com/${m.foreign_key}`)
    .with({ type: 'cdphotothread' }, (m) => {
      const details = m.details as { image_partial?: string } | undefined;
      return details?.image_partial
        ? `https://www.chiefdelphi.com/media/img/${details.image_partial}`
        : undefined;
    })
    .with(
      { type: 'cd-thread' },
      (m) => `https://www.chiefdelphi.com/t/${m.foreign_key}`,
    )
    .with(
      { type: 'grabcad' },
      (m) => `https://grabcad.com/library/${m.foreign_key}`,
    )
    .with(
      { type: 'onshape' },
      (m) => `https://cad.onshape.com/documents/${m.foreign_key}`,
    )
    .with({ type: 'external-link' }, (m) => m.foreign_key)
    .otherwise(() => undefined);
}

/** Returns the display name for a CAD model media item. */
export function getCadModelName(media: Media): string {
  return match(media)
    .with({ type: 'grabcad' }, (m) => {
      const details = m.details as { model_name?: string } | undefined;
      return details?.model_name ?? 'GrabCAD Model';
    })
    .otherwise(() => 'CAD Model');
}

/** Returns all image-type media, sorted with preferred first. */
export function getImageMedia(media: Media[]): Media[] {
  return media
    .filter((m) => IMAGE_MEDIA_TYPES.has(m.type))
    .sort((a, b) => {
      if (a.preferred && !b.preferred) return -1;
      if (!a.preferred && b.preferred) return 1;
      return 0;
    });
}

export function getTeamPreferredRobotPicMedium(
  media: Media[],
): string | undefined {
  const maybePreferredImg = media.filter(
    (m) => IMAGE_MEDIA_TYPES.has(m.type) && m.preferred,
  );

  if (maybePreferredImg.length === 0) {
    return undefined;
  }

  return getMediaImageUrl(maybePreferredImg[0]);
}
