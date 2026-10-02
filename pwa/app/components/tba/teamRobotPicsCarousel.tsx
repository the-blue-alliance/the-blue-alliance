import Autoplay from 'embla-carousel-autoplay';
import { useEffect, useState } from 'react';

import { Media } from '~/api/tba/read';
import {
  Carousel,
  type CarouselApi,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '~/components/ui/carousel';
import {
  getMediaLinkUrl,
  getMediaThumbSrcSet,
  getMediaThumbUrl,
} from '~/lib/mediaUtils';

function neighbors(index: number, length: number): number[] {
  return [index - 1, index, index + 1].filter((i) => i >= 0 && i < length);
}

export default function TeamRobotPicsCarousel({
  media,
}: {
  media: Media[];
}): React.JSX.Element {
  const [api, setApi] = useState<CarouselApi>();
  const [loaded, setLoaded] = useState<ReadonlySet<number>>(
    () => new Set(neighbors(0, media.length)),
  );

  useEffect(() => {
    if (!api) return;
    const sync = () => {
      const selected = api.selectedScrollSnap();
      setLoaded((prev) => {
        const next = new Set(prev);
        for (const i of neighbors(selected, media.length)) next.add(i);
        return next;
      });
    };
    sync();
    api.on('select', sync);
    return () => {
      api.off('select', sync);
    };
  }, [api, media.length]);

  return (
    <Carousel
      className="w-full max-w-xs"
      setApi={setApi}
      plugins={[Autoplay({ delay: 5000 })]}
    >
      <CarouselContent className="items-center">
        {media.map((m, index) => {
          const imageUrl = getMediaThumbUrl(m);
          const linkUrl = getMediaLinkUrl(m);
          if (!imageUrl) return null;

          const isFirst = index === 0;
          const img = loaded.has(index) ? (
            <img
              className="max-h-[250px] w-full rounded object-contain"
              src={imageUrl}
              srcSet={getMediaThumbSrcSet(m)}
              sizes="320px"
              width={320}
              height={250}
              alt=""
              decoding="async"
              loading={isFirst ? 'eager' : 'lazy'}
              fetchPriority={isFirst ? 'high' : 'low'}
            />
          ) : (
            <div className="h-[250px] w-full" />
          );

          return (
            <CarouselItem key={index}>
              <div
                className="flex h-[250px] w-full items-center justify-center
                  rounded-lg border-2 border-neutral-300"
              >
                {linkUrl ? (
                  <a href={linkUrl} target="_blank" rel="noreferrer">
                    {img}
                  </a>
                ) : (
                  img
                )}
              </div>
            </CarouselItem>
          );
        })}
      </CarouselContent>
      {media.length > 1 && (
        <div className="mt-1 flex justify-center gap-2">
          <CarouselPrevious className="relative left-0 transform-none" />
          <CarouselNext className="relative right-0 transform-none" />
        </div>
      )}
    </Carousel>
  );
}
