import { useState } from 'react';
import { useInView } from 'react-intersection-observer';
import { InstagramEmbed } from 'react-social-media-embed';

import SimpleIconsInstagram from '~icons/simple-icons/instagram';

import { Media } from '~/api/tba/read';
import { Skeleton } from '~/components/ui/skeleton';
import onshapeLogoDark from '~/images/onshape/onshape-logo-dark.svg';
import onshapeLogo from '~/images/onshape/onshape-logo.svg';
import {
  getCadModelName,
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
            return (
              <CaptionedEmbed
                key={key}
                media={m}
                title={m.details?.thread_title}
              />
            );
          case 'grabcad':
            return (
              <CaptionedEmbed key={key} media={m} title={getCadModelName(m)} />
            );
          case 'onshape':
            return (
              <CaptionedEmbed
                key={key}
                media={m}
                title={getCadModelName(m)}
                badge={
                  <>
                    <img
                      src={onshapeLogo}
                      alt="Onshape"
                      className="-my-2.5 h-10 shrink-0 dark:hidden"
                    />
                    <img
                      src={onshapeLogoDark}
                      alt="Onshape"
                      className="-my-2.5 hidden h-10 shrink-0 dark:block"
                    />
                  </>
                }
              />
            );
        }
      })}
    </div>
  );
}

function isImgurRemovedPlaceholder(img: HTMLImageElement): boolean {
  return img.naturalWidth === 161 && img.naturalHeight === 81;
}

function ImgurEmbed({ media }: { media: Media }): React.JSX.Element | null {
  const [failed, setFailed] = useState(false);
  const thumbnailUrl = getMediaThumbUrl(media);

  if (!thumbnailUrl || failed) return null;

  return (
    <a
      href={getMediaLinkUrl(media)}
      target="_blank"
      rel="noreferrer"
      className="block overflow-hidden rounded-lg border-2 border-neutral-300
        hover:border-neutral-400"
    >
      <img
        ref={(el) => {
          if (el?.complete && isImgurRemovedPlaceholder(el)) setFailed(true);
        }}
        src={thumbnailUrl}
        alt="Team media"
        loading="lazy"
        decoding="async"
        onLoad={(e) => {
          if (isImgurRemovedPlaceholder(e.currentTarget)) setFailed(true);
        }}
        onError={() => setFailed(true)}
        className="h-full w-full object-cover"
      />
    </a>
  );
}

function CaptionedEmbed({
  media,
  title,
  badge,
}: {
  media: Media;
  title?: string | null;
  badge?: React.ReactNode;
}): React.JSX.Element | null {
  const imageUrl = getMediaThumbUrl(media);
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
        alt={title ?? ''}
        loading="lazy"
        decoding="async"
        className="min-h-0 w-full flex-1 object-cover"
      />
      {title && (
        <div className="flex items-center gap-1.5 px-2 py-1 text-sm font-medium">
          <span className="truncate">{title}</span>
          {badge && <span className="ml-auto flex">{badge}</span>}
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
  const { ref, inView } = useInView({ triggerOnce: true, rootMargin: '400px' });
  if (!url) return null;
  const placeholder = (
    <Skeleton
      className="flex h-[512px] items-center justify-center rounded-none"
    >
      <SimpleIconsInstagram className="size-10 text-muted-foreground" />
    </Skeleton>
  );
  return (
    <div ref={ref} className="row-span-2">
      {inView ? (
        <InstagramEmbed
          url={url}
          width="100%"
          className="h-full rounded-lg! border-2 border-neutral-300
            hover:border-neutral-400 [&_iframe]:m-0! [&_iframe]:h-full!
            [&_iframe]:w-full! [&_iframe]:min-w-0! [&_iframe]:rounded-none!
            [&_iframe]:border-0!"
          embedPlaceholder={placeholder}
        />
      ) : (
        <div
          className="h-full overflow-clip rounded-lg border-2
            border-neutral-300"
        >
          {placeholder}
        </div>
      )}
    </div>
  );
}
