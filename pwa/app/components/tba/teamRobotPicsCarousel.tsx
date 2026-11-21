import { useEffect, useEffectEvent, useState } from 'react';

import { Media } from '~/api/tba/read';
import {
  Carousel,
  CarouselContent,
  CarouselIndicator,
  CarouselItem,
  CarouselNavigation,
} from '~/components/ui/carousel';
import { getRobotPicLinkUrl, getRobotPicUrl } from '~/lib/mediaUtils';

function neighbors(index: number, length: number): number[] {
  return [index - 1, index, index + 1].filter((i) => i >= 0 && i < length);
}

export default function TeamRobotPicsCarousel({
  media,
}: {
  media: Media[];
}): React.JSX.Element | null {
  const [failed, setFailed] = useState<ReadonlySet<string>>(() => new Set());
  const slides = media.flatMap((m) => {
    const url = getRobotPicUrl(m);
    return url && !failed.has(url) ? [{ media: m, url }] : [];
  });
  const [selected, setSelected] = useState(0);
  const index = Math.min(selected, slides.length - 1);
  const [visited, setVisited] = useState<ReadonlySet<string>>(() => new Set());
  const nearby = neighbors(index, slides.length);

  const select = (next: number) => {
    setSelected(next);
    setVisited(
      (prev) =>
        new Set([
          ...prev,
          ...neighbors(next, slides.length).map((i) => slides[i].url),
        ]),
    );
  };

  const markFailed = (url: string) =>
    setFailed((prev) => new Set([...prev, url]));

  const advance = useEffectEvent(() => select((index + 1) % slides.length));

  useEffect(() => {
    if (slides.length < 2) return;
    const timer = setTimeout(advance, 5000);
    return () => clearTimeout(timer);
  }, [index, slides.length]);

  if (slides.length === 0) return null;

  return (
    <Carousel
      className="w-full max-w-xs"
      aria-label="Robot pictures"
      index={index}
      onIndexChange={select}
    >
      <CarouselContent className="mb-6 items-center">
        {slides.map(({ media: m, url }, i) => {
          const linkUrl = getRobotPicLinkUrl(m);
          const isFirst = i === 0;
          const img =
            nearby.includes(i) || visited.has(url) ? (
              <img
                className="max-h-[250px] w-auto rounded-lg border-2
                  border-neutral-300"
                src={url}
                ref={(el) => {
                  if (el?.complete && el.naturalWidth === 0) markFailed(url);
                }}
                onError={() => markFailed(url)}
                width={320}
                height={250}
                alt=""
                decoding="async"
                loading={isFirst ? 'eager' : 'lazy'}
                fetchPriority={isFirst ? 'auto' : 'low'}
              />
            ) : (
              <div className="h-[250px] w-full" />
            );

          return (
            <CarouselItem key={i}>
              <div className="flex h-[250px] w-full items-center justify-center">
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
