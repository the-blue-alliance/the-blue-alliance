import { Media } from '~/api/tba/read';

/** Media types that represent displayable images. */
export const IMAGE_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'imgur',
  'cdphotothread',
  'cd-thread',
  'external-link',
]);

/** Media types that represent embeddable images (shown in the media gallery). */
export const EMBED_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'imgur',
  'instagram-image',
  'cd-thread',
]);

/** Media types that represent CAD models. */
export const CAD_MEDIA_TYPES: ReadonlySet<Media['type']> = new Set([
  'grabcad',
  'onshape',
]);

/** Returns the image URL for a media item, handling type-specific URL formats. */
export function getMediaImageUrl(media: Media): string | undefined {
  if (
    media.type === 'cd-thread' &&
    media.details &&
    'image_url' in media.details
  ) {
    return media.details.image_url ?? undefined;
  }
  return media.direct_url || undefined;
}

/** Returns all embeddable image media (imgur + instagram-image). */
export function getEmbedMedia(media: Media[]): Media[] {
  return media.filter((m) => EMBED_MEDIA_TYPES.has(m.type));
}

/** Returns the link URL for a media item (where clicking should navigate). */
export function getMediaLinkUrl(media: Media): string | undefined {
  switch (media.type) {
    case 'imgur':
      return media.view_url || `https://imgur.com/${media.foreign_key}`;
    case 'instagram-image':
      return (
        media.view_url || `https://www.instagram.com/p/${media.foreign_key}/`
      );
    case 'cdphotothread':
      if (media.details && 'image_partial' in media.details) {
        return `https://www.chiefdelphi.com/media/img/${media.details.image_partial}`;
      }
      return undefined;
    case 'cd-thread':
      return `https://www.chiefdelphi.com/t/${media.foreign_key}`;
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
  if (media.details && 'model_name' in media.details) {
    return media.details.model_name;
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
  const preferred = media.find(
    (m) => IMAGE_MEDIA_TYPES.has(m.type) && m.preferred,
  );
  return preferred ? getMediaImageUrl(preferred) : undefined;
}
