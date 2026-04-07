import { useEffect, useRef, useState } from 'react';
import { InstagramEmbed } from 'react-social-media-embed';

import { Media } from '~/api/tba/read';
import {
  getEmbedMedia,
  getMediaImageUrl,
  getMediaLinkUrl,
} from '~/lib/mediaUtils';

export default function TeamMediaGallery({
  media,
}: {
  media: Media[];
}): React.JSX.Element | null {
  const embedMedia = getEmbedMedia(media);

  if (embedMedia.length === 0) {
    return null;
  }

  return (
    <div
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      data-testid="team-media-gallery"
    >
      {embedMedia.map((m, index) => {
        if (m.type === 'imgur') {
          return <ImgurEmbed key={index} media={m} />;
        }
        if (m.type === 'instagram-image') {
          return <InstagramImageEmbed key={index} media={m} />;
        }
        if (m.type === 'cd-thread') {
          return <CdThreadEmbed key={index} media={m} />;
        }
        return null;
      })}
    </div>
  );
}

function ImgurEmbed({ media }: { media: Media }): React.JSX.Element | null {
  // This component automatically hides imgur images that have been deleted or made unavailable
  const [failed, setFailed] = useState(false);
  const [visible, setVisible] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const thumbnailUrl = getMediaImageUrl(media);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const check = () => {
      // Imgur serves a 302 redirect to /removed.png for deleted images rather
      // than a 404, so onError never fires. The removed placeholder is 161x81.
      if (img.naturalWidth === 161 && img.naturalHeight === 81) {
        setFailed(true);
      } else {
        setVisible(true);
      }
    };

    // React's synthetic onLoad misses images that finish loading before
    // hydration attaches the handler (common when the browser has the image
    // cached). Using a ref lets us check img.complete synchronously and fall
    // back to a native listener only when the load is still in flight.
    if (img.complete) {
      check();
    } else {
      img.addEventListener('load', check);
      img.addEventListener('error', () => setFailed(true));
      return () => img.removeEventListener('load', check);
    }
  }, []);

  if (!thumbnailUrl || failed) return null;

  // While the check is in flight, render a hidden img that takes no space.
  // Once confirmed valid, swap to the real card — same src hits browser cache.
  if (!visible) {
    return <img ref={imgRef} src={thumbnailUrl} alt="" className="hidden" />;
  }

  return (
    <a
      href={getMediaLinkUrl(media)}
      target="_blank"
      rel="noreferrer"
      className="block overflow-hidden rounded-lg border-2 border-neutral-300
        hover:border-neutral-400"
    >
      <img src={thumbnailUrl} alt="" className="h-64 w-full object-cover" />
    </a>
  );
}

function CdThreadEmbed({ media }: { media: Media }): React.JSX.Element | null {
  const details = media.details;
  const imageUrl =
    details && 'image_url' in details ? details.image_url : undefined;
  const threadTitle =
    details && 'thread_title' in details ? details.thread_title : undefined;
  const linkUrl = getMediaLinkUrl(media);

  if (!imageUrl || !linkUrl) return null;

  return (
    <a
      href={linkUrl}
      target="_blank"
      rel="noreferrer"
      className="block overflow-hidden rounded-lg border-2 border-neutral-300
        hover:border-neutral-400"
    >
      <img
        src={imageUrl}
        alt={threadTitle ?? ''}
        className="h-64 w-full object-cover"
      />
      {threadTitle && (
        <div className="truncate px-2 py-1 text-sm font-medium">
          {threadTitle}
        </div>
      )}
    </a>
  );
}

function InstagramImageEmbed({
  media,
}: {
  media: Media;
}): React.JSX.Element | null {
  const url = getMediaLinkUrl(media);
  if (!url) return null;
  return <InstagramEmbed url={url} width="100%" />;
}
