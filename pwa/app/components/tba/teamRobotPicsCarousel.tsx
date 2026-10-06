import { useEffect, useEffectEvent, useState } from 'react';

import { Media } from '~/api/tba/read';
import {
  Carousel,
  CarouselContent,
  CarouselIndicator,
  CarouselItem,
  CarouselNavigation,
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
  const slides = media.filter((m) => getMediaThumbUrl(m));
  const [index, setIndex] = useState(0);
  const [loaded, setLoaded] = useState<ReadonlySet<number>>(
    () => new Set(neighbors(0, slides.length)),
  );

  const select = (next: number) => {
    setIndex(next);
    setLoaded((prev) => new Set([...prev, ...neighbors(next, slides.length)]));
  };

  const advance = useEffectEvent(() => select((index + 1) % slides.length));

  useEffect(() => {
    if (slides.length < 2) return;
    const timer = setTimeout(advance, 5000);
    return () => clearTimeout(timer);
  }, [index, slides.length]);

  return (
    <Carousel
      className="w-full max-w-xs"
      aria-label="Robot pictures"
      index={index}
      onIndexChange={select}
    >
      <CarouselContent className="mb-6 items-center">
        {slides.map((m, i) => {
          const linkUrl = getMediaLinkUrl(m);
          const isFirst = i === 0;
          const img = loaded.has(i) ? (
            <img
              className="max-h-[250px] w-full rounded object-contain"
              src={getMediaThumbUrl(m)}
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
            <CarouselItem key={i}>
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
      {slides.length > 1 && (
        <>
          <CarouselNavigation className="left-0 w-full" />
          <CarouselIndicator />
        </>
      )}
    </Carousel>
  );
}
