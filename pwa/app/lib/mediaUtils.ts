import { Media } from '~/api/tba/read';

export function getTeamPreferredRobotPicMedium(
  media: Media[],
): string | undefined {
  const maybePreferredImg = media.filter(
    (m) =>
      ['imgur', 'cdphotothread', 'instagram-image', 'external-link'].includes(
        m.type,
      ) && m.preferred,
  );

  if (maybePreferredImg.length === 0) {
    return undefined;
  }

  function imageUrl(media: Media) {
    if (media.type === 'imgur') {
      return `https://i.imgur.com/${media.foreign_key}m.jpg`;
    }

    if (media.type === 'instagram-image') {
      return `https://www.thebluealliance.com/instagram_oembed/${media.foreign_key}`;
    }

    return media.direct_url;
  }

  return imageUrl(maybePreferredImg[0]);
}
