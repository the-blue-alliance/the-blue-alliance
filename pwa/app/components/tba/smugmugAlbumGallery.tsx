import { Media } from '~/api/tba/read';
import { getMediaLinkUrl } from '~/lib/mediaUtils';

export default function SmugmugAlbumGallery({
  albums,
}: {
  albums: Media[];
}): React.JSX.Element | null {
  if (albums.length === 0) {
    return null;
  }

  return (
    <div
      className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4"
      data-testid="smugmug-album-gallery"
    >
      {albums.map((album, index) => (
        <SmugmugAlbumCard key={index} album={album} />
      ))}
    </div>
  );
}

function SmugmugAlbumCard({
  album,
}: {
  album: Media;
}): React.JSX.Element | null {
  if (album.type !== 'smugmug-album') {
    return null;
  }

  const linkUrl = getMediaLinkUrl(album);
  const coverUrl = album.details?.cover_url_med;
  const title = album.details?.title || 'SmugMug Album';
  const imageCount = album.details?.image_count ?? 0;

  if (!linkUrl || !coverUrl) {
    return null;
  }

  return (
    <a
      href={linkUrl}
      target="_blank"
      rel="noreferrer"
      className="block overflow-hidden rounded-lg border-2 border-neutral-300
        hover:border-neutral-400"
    >
      <img src={coverUrl} alt={title} className="h-40 w-full object-cover" />
      <div className="px-2 py-1">
        <div className="truncate text-sm font-medium">{title}</div>
        <div className="text-xs text-muted-foreground">
          {imageCount} {imageCount === 1 ? 'photo' : 'photos'}
        </div>
      </div>
    </a>
  );
}
