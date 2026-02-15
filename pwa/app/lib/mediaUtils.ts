import { Media } from '~/api/tba/read';

/** Media types that represent displayable images. */
export const IMAGE_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'imgur',
  'cdphotothread',
  'instagram-image',
  'external-link',
]);

/** Media types that represent CAD models. */
export const CAD_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'grabcad',
  'onshape',
]);

/** Returns the image URL for a media item, handling type-specific URL formats. */
export function getMediaImageUrl(media: Media): string | undefined {
  switch (media.type) {
    case 'imgur':
      return `https://i.imgur.com/${media.foreign_key}m.jpg`;
    case 'cdphotothread':
      return media.direct_url;
    case 'instagram-image':
      return `https://www.thebluealliance.com/instagram_oembed/${media.foreign_key}`;
    case 'external-link':
      return media.direct_url;
    default:
      return media.direct_url;
  }
}

/** Returns the full-size image URL (for lightbox/detail views). */
export function getMediaImageUrlFull(media: Media): string | undefined {
  switch (media.type) {
    case 'imgur':
      return `https://i.imgur.com/${media.foreign_key}h.jpg`;
    case 'cdphotothread':
      return media.direct_url;
    case 'instagram-image':
      return `https://www.thebluealliance.com/instagram_oembed/${media.foreign_key}`;
    case 'external-link':
      return media.direct_url;
    default:
      return media.direct_url;
  }
}

/** Returns the link URL for a media item (where clicking should navigate). */
export function getMediaLinkUrl(media: Media): string | undefined {
  switch (media.type) {
    case 'imgur':
      return `https://imgur.com/${media.foreign_key}`;
    case 'cdphotothread': {
      const details = media.details as { image_partial?: string } | undefined;
      return details?.image_partial
        ? `https://www.chiefdelphi.com/media/img/${details.image_partial}`
        : undefined;
    }
    case 'instagram-image':
      return `https://www.instagram.com/p/${media.foreign_key}`;
    case 'grabcad':
      return `https://grabcad.com/library/${media.foreign_key}`;
    case 'onshape':
      return `https://cad.onshape.com/documents/${media.foreign_key}`;
    case 'external-link':
      return media.foreign_key;
    default:
      return undefined;
  }
}

/** Returns the display name for a CAD model media item. */
export function getCadModelName(media: Media): string {
  if (media.type === 'grabcad') {
    const details = media.details as { model_name?: string } | undefined;
    return details?.model_name ?? 'GrabCAD Model';
  }
  return 'CAD Model';
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
