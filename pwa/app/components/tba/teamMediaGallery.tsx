import { useEffect, useRef, useState } from 'react';
import { InstagramEmbed } from 'react-social-media-embed';

import SimpleIconsInstagram from '~icons/simple-icons/instagram';

import { Media } from '~/api/tba/read';
import { Skeleton } from '~/components/ui/skeleton';
import {
  getEmbedMedia,
  getMediaLinkUrl,
  getMediaThumbUrl,
} from '~/lib/mediaUtils';

export default function TeamMediaGallery({
  media,
}: {
  media: Media[];
}): React.JSX.Element | null {
  const embedMedia = getEmbedMedia(media).toSorted(
    (a, b) =>
      Number(b.type === 'instagram-image') -
      Number(a.type === 'instagram-image'),
  );

  if (embedMedia.length === 0) {
    return null;
  }

  return (
    <div
      className="grid grid-flow-row-dense auto-rows-[16rem]
        grid-cols-[repeat(auto-fill,minmax(min(100%,18rem),1fr))] gap-4"
      data-testid="team-media-gallery"
    >
      {embedMedia.map((m): React.JSX.Element => {
        const key = `${m.type}-${m.foreign_key}`;
        switch (m.type) {
          case 'imgur':
            return <ImgurEmbed key={key} media={m} />;
          case 'instagram-image':
            return <InstagramImageEmbed key={key} media={m} />;
          case 'cd-thread':
            return <CdThreadEmbed key={key} media={m} />;
        }
      })}
    </div>
  );
}

function ImgurEmbed({ media }: { media: Media }): React.JSX.Element | null {
  // This component automatically hides imgur images that have been deleted or made unavailable
  const [failed, setFailed] = useState(false);
  const [visible, setVisible] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const thumbnailUrl = getMediaThumbUrl(media);

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
      <img
        src={thumbnailUrl}
        alt="Team media"
        className="h-full w-full object-cover"
      />
    </a>
  );
}

type CdThreadMedia = Extract<Media, { type: 'cd-thread' }>;

function CdThreadEmbed({
  media,
}: {
  media: CdThreadMedia;
}): React.JSX.Element | null {
  const details = media.details;
  const imageUrl = details?.image_url;
  const threadTitle = details?.thread_title;
  const linkUrl = getMediaLinkUrl(media);

  if (!imageUrl || !linkUrl) return null;

  return (
    <a
      href={linkUrl}
      target="_blank"
      rel="noreferrer"
      className="flex flex-col overflow-hidden rounded-lg border-2
        border-neutral-300 hover:border-neutral-400"
    >
      <img
        src={imageUrl}
        alt={threadTitle ?? ''}
        className="min-h-0 w-full flex-1 object-cover"
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
  return (
    <InstagramEmbed
      url={url}
      width="100%"
      className="row-span-2 rounded-lg! border-2 border-neutral-300
        hover:border-neutral-400 [&_iframe]:m-0! [&_iframe]:h-full!
        [&_iframe]:w-full! [&_iframe]:min-w-0! [&_iframe]:rounded-none!
        [&_iframe]:border-0!"
      embedPlaceholder={
        <Skeleton
          className="flex h-[512px] items-center justify-center rounded-none"
        >
          <SimpleIconsInstagram className="size-10 text-muted-foreground" />
        </Skeleton>
      }
    />
  );
}
